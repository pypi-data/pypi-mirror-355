from abc import ABC, abstractmethod

from ..data import GenericDataPacket


class AbstractDataGenerator(ABC):
    @abstractmethod
    def get_data(self) -> GenericDataPacket | None:
        raise NotImplementedError("Method not implemented")


class AbstractWorker(ABC):
    @abstractmethod
    def work(self):
        raise NotImplementedError("Method not implemented")
