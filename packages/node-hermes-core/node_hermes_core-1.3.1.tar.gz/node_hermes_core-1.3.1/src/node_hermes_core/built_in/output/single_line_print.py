import time
from typing import Literal

import polars as pl
from node_hermes_core.nodes import AbstractWorker, SinkNode
from pydantic import Field


class SinglelinePrintNode(SinkNode, AbstractWorker):
    class Config(SinkNode.Config):
        type: Literal["single_line_print"]
        add_prefix: bool = Field(description="Add a prefix to the data", default=False)
        float_precision: int = Field(description="The precision of the floating point numbers", default=3)
        header_interval: int = Field(description="The interval at which to print the data", default=5)

    config: Config  # type: ignore

    def __init__(self, config: Config):
        super().__init__(config)

    def init(self):
        super().init()
        self.dataframe = pl.DataFrame()
        self.start_time = time.time()
        self.line_count = 0

    def work(self):
        while self.has_data():
            data = self.get_data()
            if data is None:
                continue

            df: pl.DataFrame = data.as_dataframe(add_prefix=self.config.add_prefix)

            # Append to dataframe
            self.dataframe = pl.concat(
                [
                    self.dataframe,  # Current data buffer
                    df,  # New data
                ],
                how="diagonal_relaxed",
            )

        if len(self.dataframe) == 0:
            return

        # reorder columns to put timestamp first
        self.dataframe = self.dataframe.select(
            ["timestamp"] + [col for col in self.dataframe.columns if col != "timestamp"]
        )

        # Fill data to last
        self.dataframe = self.dataframe.select(
            [pl.col("timestamp")] + [pl.col(col).forward_fill() for col in self.dataframe.columns if col != "timestamp"]
        )

        # print the values with 8 characters width and 3 decimal points
        last_row = self.dataframe.tail(1).to_dict()

        last_values = ""
        last_columns = ""
        for key, value in last_row.items():
            if key == "timestamp":
                continue

            if value[0] is None:
                values = "None "

            elif isinstance(value[0], str):
                values = f"{value[0]:>{len(key)}s} "
            else:
                values = f"{value[0]:{len(key)}.{self.config.float_precision}f} "

            column = f"{key:{len(values)}}"

            last_values += values
            last_columns += column

        if self.line_count % self.config.header_interval == 0:
            print(last_columns)
        print(last_values)
        self.line_count += 1

        # Clear the dataframe but keep the schema
        self.dataframe = self.dataframe.clear()

    def deinint(self):
        super().deinit()
