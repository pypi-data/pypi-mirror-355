from abc import ABC, abstractmethod

from node_hermes_core.nodes import GenericNode


class GenericStreamTransport(GenericNode, ABC):
    @abstractmethod
    def read(self) -> bytes: ...

    @abstractmethod
    def write(self, data: bytes): ...
