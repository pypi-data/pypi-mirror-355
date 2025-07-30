import datetime
import time
from typing import Literal

import polars
import pyarrow as pa
from node_hermes_core.nodes import AbstractWorker, SinkNode
from pydantic import Field


class ArrowWriterNode(SinkNode, AbstractWorker):
    class Config(SinkNode.Config):
        type: Literal["arrow_writer"]
        filename: str = Field(description="Base file path for Arrow IPC stream")
        add_prefix: bool = Field(description="Add a prefix to column names", default=False)
        time_format: Literal["relative", "absolute"] = Field(
            description="The time format for the timestamp column", default="relative"
        )
        add_timestamp_suffix: bool = Field(description="If true, add a timestamp suffix to the file name", default=True)
        compression: Literal["lz4", "zstd", "uncompressed"] = Field(
            description="Compression codec for Arrow IPC stream", default="uncompressed"
        )

    config: Config  # type: ignore

    def __init__(self, config: Config):
        super().__init__(config)

    stream: pa.ipc.RecordBatchStreamWriter | None = None

    def init(self):
        super().init()
        # Prepare file path with optional timestamp suffix
        ts = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        if self.config.add_timestamp_suffix:
            self.file_path = f"{self.config.filename}_{ts}.arrow"
        else:
            self.file_path = self.config.filename

        self.start_time = time.time()
        self.first_packet_timestamp = None
        self.header_columns = None
        self.buffered_batches: list[polars.DataFrame] = []
        self.filesink = None
        self.stream = None

    def _open_stream(self, df: polars.DataFrame):
        # Initialize Arrow IPC stream using schema from first batch
        table = df.to_arrow()
        schema = table.schema
        self.filesink = pa.OSFile(self.file_path, "wb")
        if self.config.compression == "uncompressed":
            self.stream = pa.ipc.new_stream(self.filesink, schema)
        else:
            write_options = pa.ipc.IpcWriteOptions(compression=self.config.compression)
            self.stream = pa.ipc.new_stream(self.filesink, schema, options=write_options)

        # Write any buffered batches
        for batch_df in self.buffered_batches:
            self.stream.write_batch(batch_df.to_arrow())  # type: ignore
        self.filesink.flush()

        # Lock in schema for subsequent batches
        self.header_columns = list(df.columns)
        self.buffered_batches = []

    def work(self):
        while self.has_data():
            data = self.get_data()
            if data is None:
                continue

            # Track first timestamp for relative timing
            if self.first_packet_timestamp is None:
                self.first_packet_timestamp = data.timestamp

            # Compute time offset
            if self.config.time_format == "relative":
                offset = data.timestamp - self.first_packet_timestamp
            else:
                offset = None

            df: polars.DataFrame = data.as_dataframe(
                add_prefix=self.config.add_prefix,
                time_offset=offset,
            )

            # Enforce original schema if set
            if self.header_columns is not None:
                df = df.select([c for c in self.header_columns if c in df.columns])

            # Open stream on first real write
            if self.stream is None:
                self._open_stream(df)

            # Append batch and flush
            # Append batch and flush
            tbl = df.to_arrow()
            for record_batch in tbl.to_batches():
                self.stream.write_batch(record_batch)  # type: ignore
            self.filesink.flush()  # type: ignore

    def deinit(self):
        if self.stream:
            self.stream.close()
        if self.filesink:
            self.filesink.close()

        super().deinit()
