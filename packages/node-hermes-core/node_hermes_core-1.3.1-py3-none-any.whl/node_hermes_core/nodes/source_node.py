from node_hermes_core.nodes.data_generator_node import AbstractDataGenerator, AbstractWorker

from ..data.datatypes import GenericDataPacket
from ..links.generic_link import DataTarget
from .generic_node import GenericNode


class SourceNode(GenericNode, AbstractDataGenerator, AbstractWorker):
    """The source node is a node that can send data to other nodes"""

    def __init__(self, config: GenericNode.Config | None):
        super().__init__(config)
        self.base_target = DataTarget("output")
        self.source_port_manager.add("output", self.base_target)

    def send_data(self, data: GenericDataPacket | None):
        """Push data to all targets

        Args:
            data (MultiPointDataPacket | SinglePointDataPacket): The data to push
        """
        # Block empty data from being pushed
        if data is None:
            return

        # Push to all targets
        self.base_target.put_data(data)

    def work(self):
        self.send_data(self.get_data())

    @property
    def info_string(self) -> str:
        return f"{self.base_target.frequency_counter.frequency:.2f} Hz"
