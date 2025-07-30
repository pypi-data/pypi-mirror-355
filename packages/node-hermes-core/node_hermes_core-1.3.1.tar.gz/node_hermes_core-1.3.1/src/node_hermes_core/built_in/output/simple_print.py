from typing import Literal

from node_hermes_core.nodes.data_generator_node import AbstractWorker
from node_hermes_core.nodes.sink_node import SinkNode


class PrintNode(SinkNode, AbstractWorker):
    class Config(SinkNode.Config):
        type: Literal["simple_print"]

        @classmethod
        def default(cls) -> "PrintNode.Config":
            return cls(type="simple_print")

    config: Config | SinkNode.Config

    def work(self):
        while self.has_data():
            data = self.get_data()
            print(data)
