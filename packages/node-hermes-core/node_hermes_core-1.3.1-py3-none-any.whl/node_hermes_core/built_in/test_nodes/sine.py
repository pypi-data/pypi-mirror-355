import math
import time
from typing import Literal

from node_hermes_core.data import SinglePointDataPacket
from node_hermes_core.nodes import SourceNode
from pydantic import Field


class SineNode(SourceNode):
    class Config(SourceNode.Config):
        type: Literal["sine"]
        frequency: float = Field(description="The frequency of the sine wave", default=1)
        amplitude: float = Field(description="The amplitude of the sine wave", default=1)
        offset: float = Field(description="The offset of the sine wave", default=0)

        @classmethod
        def default(cls) -> "SineNode.Config":
            return cls(type="sine")

    config: Config  # type: ignore

    def __init__(self, config: Config):
        super().__init__(config)

    def get_data(self) -> SinglePointDataPacket:
        timestamp = time.time()
        return SinglePointDataPacket(
            timestamp=timestamp,
            data={
                "value": self.config.amplitude * math.sin(2 * math.pi * self.config.frequency * timestamp)
                + self.config.offset
            },
            source=self.config._device_name,
        )
