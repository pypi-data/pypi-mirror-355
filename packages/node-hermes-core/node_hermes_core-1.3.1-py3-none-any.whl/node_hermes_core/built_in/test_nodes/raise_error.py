import time
from typing import Literal

from node_hermes_core.data import SinglePointDataPacket
from node_hermes_core.nodes.source_node import SourceNode
from pydantic import Field


class RaiseErrorComponent(SourceNode):
    class Config(SourceNode.Config):
        type: Literal["raise_error"]
        timeout: int = Field(description="The number of seconds to wait before raising an error", default=5)

        @classmethod
        def default(cls) -> "RaiseErrorComponent.Config":
            return cls(type="raise_error")

    config: Config  # type: ignore

    def __init__(self, config: Config):
        super().__init__(config)

    def init(self):
        self.start_time = time.time()
        super().init()

    def process(self) -> SinglePointDataPacket:
        if time.time() - self.start_time > self.config.timeout:
            raise ValueError("This component raises an error after a certain amount of time")

        return SinglePointDataPacket(
            timestamp=time.time(),
            data={"dummy": 0},
            source=self.name,
        )
