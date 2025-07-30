import logging
from abc import ABC, abstractmethod
from typing import List

from node_hermes_core.data.datatypes import GenericDataPacket
from node_hermes_core.utils.frequency_counter import FrequencyCounter


class DataTarget:
    targets: "List[GenericLink]"

    def __init__(self, name: str = "output"):
        self.name = name
        self.targets = []
        self.frequency_counter = FrequencyCounter()

    def add_target(self, target: "GenericLink"):
        logging.info(f"Adding target for {self} -> {target}")
        self.targets.append(target)

    def remove_target(self, target: "GenericLink"):
        self.targets.remove(target)

    def put_data(self, data: GenericDataPacket):
        # Push to all targets
        for target_node in self.targets:
            target_node.put_data(data)

        self.frequency_counter.update(len(data))


class GenericLink(ABC):
    """Generic data target class that can be used to handle received data"""

    @abstractmethod
    def put_data(self, data): ...
