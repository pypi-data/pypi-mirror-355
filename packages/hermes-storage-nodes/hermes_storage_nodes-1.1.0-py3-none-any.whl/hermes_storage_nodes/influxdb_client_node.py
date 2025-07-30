from typing import Literal

import polars as pl
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision
from node_hermes_core.nodes.data_generator_node import AbstractWorker
from node_hermes_core.nodes.sink_node import SinkNode
from uuid import uuid4
from pydantic import Field


class InfluxDB(SinkNode, AbstractWorker):
    class Config(SinkNode.Config):
        type: Literal["influxdb"] = "influxdb"
        token: str
        org: str
        url: str
        bucket: str
        debug: bool = False
        measurement: str = "measurement"
        timeout: float = Field(default=100, ge=0, description="Timeout in seconds")
        tags: list[str] = Field(default_factory=list)

    config: Config

    client: InfluxDBClient | None = None

    def __init__(self, config: Config):
        super().__init__(config)

    def init(self):  # type: ignore
        super().init()
        self.client = InfluxDBClient(
            url=self.config.url, token=self.config.token, org=self.config.org, debug=self.config.debug, timeout=int(self.config.timeout*1000)
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.influxdb_session_id = str(uuid4())

    def work(self):
        while self.has_data():
            data = self.get_data()

            if data is None:
                continue

            data_df: pl.DataFrame = data.as_dataframe(add_prefix=True)

            # Convert to pandas dataframe
            pandas_df = data_df.to_pandas()

            # Set index to timestamp
            pandas_df.set_index("timestamp", inplace=True)

            # multiply by a million to convert to nanoseconds
            pandas_df.index = pandas_df.index * 1e6

            # Convert timestamp to UTC
            self.write_api.write(
                bucket=self.config.bucket,
                record=pandas_df,
                data_frame_measurement_name=self.influxdb_session_id,
                write_precision=WritePrecision.US, #type: ignore
                data_frame_tag_columns=self.config.tags,
            )

        self.write_api.flush()

    def deinit(self):
        if self.client is not None:
            self.client.close()
        super().deinit()
