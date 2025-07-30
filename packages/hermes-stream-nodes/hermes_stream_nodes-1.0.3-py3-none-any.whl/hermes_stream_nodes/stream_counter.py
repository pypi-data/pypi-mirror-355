import time
from dataclasses import dataclass


@dataclass
class StreamStatistics:
    tx_bytes: int = 0
    rx_bytes: int = 0
    tx_rate: float = 0.0  # in bits per second
    rx_rate: float = 0.0  # in bits per second

    def to_dict(self) -> dict:
        return {
            "tx_bytes": self.tx_bytes,
            "rx_bytes": self.rx_bytes,
            "tx_rate": self.tx_rate,
            "rx_rate": self.rx_rate,
        }


class StreamStatisticsManager:
    def __init__(self):
        self.tx_bytes = 0
        self.rx_bytes = 0
        self.last_rate_update = time.time()
        self.last_stats = StreamStatistics()
        self.filter_factor = 0.1  # Smoothing factor for rate calculation

    def get_rates(self) -> StreamStatistics:
        now = time.time()

        elapsed = now - self.last_rate_update

        if elapsed < 0.1:
            return self.last_stats

        tx_rate = (self.tx_bytes - self.last_stats.tx_bytes) * 8 / elapsed
        rx_rate = (self.rx_bytes - self.last_stats.rx_bytes) * 8 / elapsed

        self.last_stats = StreamStatistics(
            tx_bytes=self.tx_bytes,
            rx_bytes=self.rx_bytes,
            tx_rate=self.filter_factor * self.last_stats.tx_rate + (1 - self.filter_factor) * tx_rate,
            rx_rate=self.filter_factor * self.last_stats.rx_rate + (1 - self.filter_factor) * rx_rate,
        )

        self.last_rate_update = now

        return self.last_stats

    def register_tx_bytes(self, bytes: int):
        self.tx_bytes += bytes

    def register_rx_bytes(self, bytes: int):
        self.rx_bytes += bytes
