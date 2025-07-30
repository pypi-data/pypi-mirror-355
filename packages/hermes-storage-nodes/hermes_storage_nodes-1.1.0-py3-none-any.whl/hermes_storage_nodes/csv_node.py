import datetime
import time
from typing import Literal

import polars
from node_hermes_core.nodes import AbstractWorker, SinkNode
from pydantic import Field


class CSVWriterNode(SinkNode, AbstractWorker):
    class Config(SinkNode.Config):
        type: Literal["csv_writer"]
        filename: str = Field(description="The file path to write the data to")
        separator: str = Field(default=",")
        startup_delay: float = Field(
            description="The delay in seconds before actually writing data to the file", default=2
        )
        add_prefix: bool = Field(description="Add a prefix to the data", default=False)
        float_precision: int = Field(description="The precision of the floating point numbers", default=3)
        time_format: Literal["relative", "absolute"] = Field(description="The time format to use", default="relative")
        add_timestamp_suffix: bool = Field(description="If true a timestamp suffix will be added to the end")

    config: Config  # type: ignore

    def __init__(self, config: Config):
        super().__init__(config)

    def init(self):
        super().init()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        self.file_handle = open(f"{self.config.filename}_{timestamp}.csv", "w", encoding="utf8")
        self.dataframe = polars.DataFrame()
        self.start_time = time.time()
        self.first_packet_timestamp = None

        self.header_columns = None  # To store the original column names

    def work(self):
        while self.has_data():
            data = self.get_data()

            if data is None:
                continue

            if self.first_packet_timestamp is None:
                self.first_packet_timestamp = data.timestamp

            if self.config.time_format == "relative":
                delta_time = -self.first_packet_timestamp
            else:
                delta_time = None

            df: polars.DataFrame = data.as_dataframe(add_prefix=self.config.add_prefix, time_offset=delta_time)

            if self.header_columns is not None:
                df: polars.DataFrame = df.select([col for col in self.header_columns if col in df.columns])

            # Append to dataframe
            self.dataframe = polars.concat(
                [
                    self.dataframe,  # Current data buffer
                    df,  # New data
                ],
                how="diagonal_relaxed",
            )

        if time.time() - self.start_time < self.config.startup_delay:
            return

        if len(self.dataframe) == 0:
            return

        # reorder columns to put timestamp first
        self.dataframe = self.dataframe.select(
            ["timestamp"] + [col for col in self.dataframe.columns if col != "timestamp"]
        )

        self.dataframe.write_csv(
            file=self.file_handle,
            include_header=self.header_columns is None,
            separator=self.config.separator,
            float_precision=self.config.float_precision,
        )

        if not self.header_columns:
            self.header_columns = self.dataframe.columns
            self.log.info(f"Written header: {self.header_columns}")

        # Clear the dataframe but keep the schema
        self.dataframe = self.dataframe.clear()

        # Flush the file handle to write the data to the file
        self.file_handle.flush()

    def deinit(self):
        self.file_handle.close()
        super().deinit()
