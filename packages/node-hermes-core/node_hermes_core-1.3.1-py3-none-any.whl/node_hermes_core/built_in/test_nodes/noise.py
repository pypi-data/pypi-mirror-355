import time
from typing import Literal

import numpy as np
from node_hermes_core.data import SinglePointDataPacket
from node_hermes_core.nodes.source_node import SourceNode
from pydantic import Field


class NoiseNode(SourceNode):
    class Config(SourceNode.Config):
        type: Literal["noise"]
        sigma: float = Field(description="The standard deviation of the noise", default=1)
        mu: float = Field(description="The mean of the noise", default=0)

        @classmethod
        def default(cls):
            return cls(type="noise")

    config: Config  # type: ignore

    def get_data(self):
        return SinglePointDataPacket(
            timestamp=time.time(),
            data={"value": np.random.normal(self.config.mu, self.config.sigma)},
            source=self.config._device_name,
        )
