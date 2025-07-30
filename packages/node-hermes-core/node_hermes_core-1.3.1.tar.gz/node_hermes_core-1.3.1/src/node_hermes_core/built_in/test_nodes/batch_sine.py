import math
import time
from typing import Literal

import numpy as np
import polars as pl
from node_hermes_core.data import MultiPointDataPacket
from node_hermes_core.nodes import SourceNode
from pydantic import Field


class BatchSineNode(SourceNode):
    class Config(SourceNode.Config):
        type: Literal["batch_sine"]
        frequency: float = Field(description="The frequency of the sine wave", default=1)
        amplitude: float = Field(description="The amplitude of the sine wave", default=1)
        offset: float = Field(description="The offset of the sine wave", default=0)
        batch_size: int = Field(description="The number of samples per cycle", default=100)

        @classmethod
        def default(cls) -> "BatchSineNode.Config":
            return cls(type="batch_sine")

    config: Config  # type: ignore

    def __init__(self, config: Config):
        super().__init__(config)

    def init(self):
        self.last_time = time.time()
        super().init()

    def get_data(self) -> MultiPointDataPacket:
        timestamp = time.time()
        delta_time = timestamp - self.last_time

        # Create a range of values from 0 to (samples_per_cycle - 1)
        indices = pl.Series(np.arange(self.config.batch_size))

        # Calculate time_points directly
        time_points = self.last_time + delta_time * indices / self.config.batch_size

        # Calculate sine_points directly using a vectorized approach
        sine_points = (
            self.config.amplitude * pl.Series(np.sin(2 * math.pi * self.config.frequency * time_points))
            + self.config.offset
        )

        self.last_time = timestamp

        return MultiPointDataPacket(
            timestamp=time_points[0],
            timestamps=time_points,
            data=pl.DataFrame({"value": sine_points}),
            source=self.config._device_name,
        )
