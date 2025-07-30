from typing import Literal

from node_hermes_core.nodes import AbstractWorker, SinkNode


class TerminalOutputNode(SinkNode, AbstractWorker):
    class Config(SinkNode.Config):
        type: Literal["print"]

        @classmethod
        def default(cls) -> "TerminalOutputNode.Config":
            return cls(type="print")

    config: Config  # type: ignore

    def work(self):
        while self.has_data():
            data = self.get_data()
            self.log.info(f"Received data: {data}")
