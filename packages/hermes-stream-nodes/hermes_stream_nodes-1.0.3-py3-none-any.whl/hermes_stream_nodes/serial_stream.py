import time
from typing import List, Literal

from node_hermes_core.data.datatypes import (
    PhysicalDatapacket,
)
from node_hermes_core.links.generic_link import DataTarget
from node_hermes_core.nodes.data_generator_node import AbstractDataGenerator, AbstractWorker
from pydantic import BaseModel
from serial import Serial
from serial.tools import list_ports

from .generic_stream import GenericStreamTransport
from .stream_counter import StreamStatisticsManager


class SerialPortInfo(BaseModel):
    port: str
    description: str
    pid: int | None
    vid: int | None
    serial_number: str | None


def get_serial_ports(pid: str | int | None = None, vid: str | int | None = None) -> List[SerialPortInfo]:
    """Get a list of serial ports

    Args:
        pid (str, optional): Filter by product id. Defaults to None.
        vid (str, optional): Filter by vendor id. Defaults to None.

    Returns:
        List[serial_port_info]: List of serial ports

    """
    if isinstance(pid, str):
        pid = int(pid, 16)
    if isinstance(vid, str):
        vid = int(vid, 16)

    discovered_ports = []
    for port in list_ports.comports():
        # Check if the port should be filtered
        if pid is not None and port.pid != pid:
            continue

        if vid is not None and port.vid != vid:
            continue

        discovered_ports.append(
            SerialPortInfo(
                port=port.device,
                description=port.description,
                pid=port.pid,
                vid=port.vid,
                serial_number=port.serial_number,
            )
        )
    return discovered_ports


class SerialStream(GenericStreamTransport, AbstractDataGenerator, AbstractWorker):
    class Config(GenericStreamTransport.Config):
        type: Literal["serial_stream"] = "serial_stream"
        baudrate: int = 115200
        port: str
        rx_buffer_size: int = 16 * 1024
        tx_buffer_size: int = 16 * 1024

    config: Config

    serial: Serial | None = None
    statistics: StreamStatisticsManager | None

    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config
        self.statistics_metadata = {
            "tx_bytes": PhysicalDatapacket.PointDefinition(unit="B", precision=3, si=True),
            "rx_bytes": PhysicalDatapacket.PointDefinition(unit="B", precision=3, si=True),
            "tx_rate": PhysicalDatapacket.PointDefinition(unit="bps", precision=3, si=True),
            "rx_rate": PhysicalDatapacket.PointDefinition(unit="bps", precision=3, si=True),
        }

        self.base_target = DataTarget("output")
        self.source_port_manager.add("output", self.base_target)

    def init(self):
        super().init()
        self.serial = Serial(port=self.config.port, baudrate=self.config.baudrate)
        self.serial.set_buffer_size(rx_size=self.config.rx_buffer_size, tx_size=self.config.tx_buffer_size)
        self.statistics = StreamStatisticsManager()

    def deinit(self):
        if self.serial is not None:
            self.serial.close()

        self.serial = None
        self.statistics = None
        super().deinit()

    def read(self) -> bytes:
        assert self.serial is not None, "Serial port not initialized"

        data = self.serial.read_all()

        if not data:
            data = b""

        if self.statistics is not None:
            self.statistics.register_rx_bytes(len(data))

        return data

    def write(self, data: bytes):
        assert self.serial is not None, "Serial port not initialized"
        self.serial.write(data)
        self.serial.flush()

        if self.statistics is not None:
            self.statistics.register_tx_bytes(len(data))

    def get_data(self) -> PhysicalDatapacket:
        assert self.statistics is not None, "Statistics not initialized"
        rates = self.statistics.get_rates()
        return PhysicalDatapacket(
            source=self.name, timestamp=time.time(), data=rates.to_dict(), metadata=self.statistics_metadata
        )

    def work(self):
        stats = self.get_data()
        self.base_target.put_data(stats)
