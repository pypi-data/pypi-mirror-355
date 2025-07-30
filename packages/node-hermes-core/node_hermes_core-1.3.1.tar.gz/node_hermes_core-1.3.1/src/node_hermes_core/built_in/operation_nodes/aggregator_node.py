import time
from typing import Literal

from node_hermes_core.utils.frequency_counter import FrequencyCounter
import polars as pl
from node_hermes_core.data import MultiPointDataPacket
from node_hermes_core.links.generic_link import DataTarget
from node_hermes_core.links.queued_link import QueuedLink
from node_hermes_core.nodes import SinkNode, SourceNode
from node_hermes_core.nodes.data_generator_node import AbstractWorker
from node_hermes_core.nodes.generic_node import GenericNode
from pydantic import BaseModel, ConfigDict, Field


class AggegatorNode(GenericNode, AbstractWorker):
    TIMESTAMP_COLUMN = "timestamp"

    class InterpolationConfig(BaseModel):
        model_config = ConfigDict(extra="forbid")  # Don't allow extra fields
        mode: Literal["linear", "last", "next"] = Field(description="The interpolation mode")

    class ResamplingConfig(BaseModel):
        model_config = ConfigDict(extra="forbid")  # Don't allow extra fields
        interval: str = Field(description="The resampling interval")

    class Config(SinkNode.Config, SourceNode.Config):
        type: Literal["aggregator"]
        buffering_delay: float = Field(description="The buffering delay in seconds", default=1)
        interpolation: "AggegatorNode.InterpolationConfig | None" = Field(
            description="The interpolation configuration", default=None
        )
        resampling: "AggegatorNode.ResamplingConfig | None" = Field(
            description="The resampling configuration", default=None
        )
        add_prefix: bool = Field(description="Add prefix to the columns", default=True)

    config: Config
    dataframe: pl.DataFrame
    frequency_counter: FrequencyCounter | None = None

    def __init__(self, config: Config):
        super().__init__(config)

        self.base_sink = QueuedLink(config=self.config.source)
        self.sink_port_manager.add("input", self.base_sink)

        self.base_target = DataTarget("output")
        self.source_port_manager.add("output", self.base_target)

        # self.ingest_handle = ManagedTask(self.ingest_task, f"{self.name}_ingest_task")
        # self.ingest_handle.stopped.connect(self.attempt_deinit)

        # self.process_handle = ManagedTask(self.process_task, f"{self.name}_process_task")
        # self.process_handle.stopped.connect(self.attempt_deinit)

    def init(self):
        self.dataframe = pl.DataFrame()

        # Apply interpolation
        self.prev_end_of_packet_timestamp = 0
        self.prev_start_of_packet_timestamp = 0
        self.frequency_counter = FrequencyCounter()

    def work(self):
        start_time = time.time()
        self.temp_dataframe = pl.DataFrame()

        buffered_dfs = [self.dataframe]
        
        assert self.frequency_counter is not None
        
        while self.base_sink.has_data():
            if time.time() - start_time > 0.5:
                break

            data = self.base_sink.get_data()
            if data is None:
                continue

            self.frequency_counter.update(len(data))

            df = data.as_dataframe(add_prefix=self.config.add_prefix)
            buffered_dfs.append(df)

        if len(buffered_dfs) == 0:
            return

        self.dataframe = pl.concat(
            buffered_dfs,
            how="diagonal_relaxed",
        )

        if len(self.dataframe) == 0:
            return

        # Sort by timestamp, needed?
        self.dataframe = self.dataframe.sort(self.TIMESTAMP_COLUMN)

        old_data_timestamp = self.prev_start_of_packet_timestamp - self.config.buffering_delay
        end_of_packet_timestamp = time.time() - self.config.buffering_delay
        start_of_packet_timestamp = self.prev_end_of_packet_timestamp

        # Calculate resampling
        data = self.dataframe

        if self.config.resampling is not None:
            # convert to timestamped collumn
            data_datetime = self.dataframe.with_columns(
                [pl.from_epoch(pl.col("timestamp").mul(1000000), time_unit="us")]
            )
            fields = [pl.col(column).drop_nulls().last() for column in data.columns if column != "timestamp"]
            _data = data_datetime.group_by_dynamic(
                index_column="timestamp",
                every=self.config.resampling.interval,
                # check_sorted=True,
            ).agg(*fields)

            data = _data.with_columns([pl.col("timestamp").dt.epoch(time_unit="us").mul(1 / 1000000)])

        # Calculate interpolation
        if self.config.interpolation is not None:
            if self.config.interpolation.mode == "linear":
                data = data.select(
                    [pl.col("timestamp")] + [pl.col(col).interpolate() for col in data.columns if col != "timestamp"]
                )
            elif self.config.interpolation.mode == "last":
                data = data.select(
                    [pl.col("timestamp")] + [pl.col(col).forward_fill() for col in data.columns if col != "timestamp"]
                )
            elif self.config.interpolation.mode == "next":
                data = data.select(
                    [pl.col("timestamp")] + [pl.col(col).backward_fill() for col in data.columns if col != "timestamp"]
                )
            else:
                raise ValueError(f"Unknown interpolation mode: {self.config.interpolation.mode}")

        # Select data to send
        output_data = data.filter(
            (pl.col(self.TIMESTAMP_COLUMN) >= start_of_packet_timestamp)
            & (pl.col(self.TIMESTAMP_COLUMN) < end_of_packet_timestamp)
        )

        # remove old data
        self.dataframe = self.dataframe.filter(pl.col(self.TIMESTAMP_COLUMN) >= old_data_timestamp)

        # Update the end of the packet timestamp
        self.prev_end_of_packet_timestamp = end_of_packet_timestamp
        self.prev_start_of_packet_timestamp = start_of_packet_timestamp

        # Only send data if there is data to send
        if len(output_data) == 0:
            return

        output_packet = MultiPointDataPacket.from_dataframe(self.name, output_data)

        # Send data to all targets
        self.base_target.put_data(output_packet)

        return output_packet

    @property
    def info_string(self) -> str:
        if self.frequency_counter is None:
            return "No data"

        return f"{self.frequency_counter.frequency:.2f}Hz / {self.base_target.frequency_counter.frequency:.2f} Hz"

    @property
    def queue_string(self) -> str:
        return f"{self.base_sink.queue.qsize()} items in queue"
