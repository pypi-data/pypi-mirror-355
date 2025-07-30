import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import odin_db
import polars as pl
from hermes_framing_nodes import BurstLinkNode
from node_hermes_core.data.datatypes import MultiPointDataPacket
from node_hermes_core.depencency.node_dependency import NodeDependency
from node_hermes_core.nodes.source_node import SourceNode
from odin_stream import StreamProcessor
from pydantic import BaseModel, Field

TIMESTAMP_COLUMN = "__timestamp"


@dataclass
class TimeCorrectionInstance:
    """Data class to hold time correction information."""

    remote_time: float
    local_time: float
    counts_per_second: float
    last_remote_time_received: float | None = None

    @classmethod
    def create(
        cls, remote_time: float, counts_per_second: float, local_time: float | None = None
    ) -> "TimeCorrectionInstance":
        """Create a new instance with the current local time."""
        local_time = local_time if local_time is not None else time.time()

        return cls(remote_time=remote_time, local_time=local_time, counts_per_second=counts_per_second)

    def check_validity(self, remote_time: float) -> bool:
        """Check if the remote time is valid for this instance."""
        return  self.last_remote_time_received is None or remote_time > self.last_remote_time_received
    
    def apply(self, data: pl.DataFrame, target_column: str = "timestamp") -> pl.DataFrame:
        # Calculate the time difference
        time_difference = self.local_time - self.remote_time / self.counts_per_second
        
        self.last_remote_time_received = data[TIMESTAMP_COLUMN].last()  # type: ignore
        
        # Apply the correction to the target column
        data = data.with_columns(
            (pl.col(TIMESTAMP_COLUMN) / self.counts_per_second + time_difference).alias(target_column)
        )

        return data


class OdinStreamNode(SourceNode):
    class TimeCorrection(BaseModel):
        counts_per_second: float = Field(
            description="The number of counts per second.",
        )
        reset_automatically: bool = Field(default=True, description="Reset when the count resets")

    class Config(SourceNode.Config):
        type: Literal["odin-stream"] = "odin-stream"
        burst_node: BurstLinkNode.Config | str | None = None
        odin_definitions: str = Field(
            description="Path to the Odin definitions file used for processing the stream.",
        )

        time_correction: "OdinStreamNode.TimeCorrection | None" = Field(
            default=None,
            description="Time correction to apply to the data, used to correct the timestamp based on the local time.",
        )

    burst_node: BurstLinkNode | None = None
    config: Config
    time_correction: TimeCorrectionInstance | None = None

    def __init__(self, config: Config):
        super().__init__(config)

        self.base_dependency = NodeDependency(name="burst_node", config=config.burst_node, reference=BurstLinkNode)
        self.dependency_manager.add(self.base_dependency)

    def init(self, burst_node: BurstLinkNode | None):  # type: ignore
        super().init()
        self.burst_node = burst_node
        self.time_correction = None

        try:
            with open(Path(self.config.odin_definitions).resolve(), "r") as f:
                odin_definitions = odin_db.OdinDBModel.model_validate_json(f.read())

        except Exception as e:
            raise RuntimeError(f"Failed to load Odin definitions from {self.config.odin_definitions}: {e}")

        self.processor = StreamProcessor(odin_definitions)

    def deinit(self):
        self.burst_node = None

    def read(self) -> dict[int, pl.DataFrame]:
        if self.burst_node is None:
            raise RuntimeError("Burst node not initialized")

        packets = self.burst_node.read()
        if len(packets) == 0:
            return {}

        # Ingest data
        self.processor.process_bytes_list(packets)

        # Return the processed data
        return self.processor.flush()

    def read_merged(self) -> pl.DataFrame | None:
        data = self.read()
        if not data:
            return None

        merged_df = pl.concat(list(data.values()), how="diagonal_relaxed")

        if self.config.time_correction is not None:
            last_timestamp: float = float(merged_df[TIMESTAMP_COLUMN].last())  # type: ignore
            if self.time_correction is not None:
                if not self.time_correction.check_validity(last_timestamp):
                    # Reset the time correction if the remote time is not valid
                    self.time_correction = None

            if self.time_correction is None:
                self.time_correction = TimeCorrectionInstance.create(
                    remote_time=last_timestamp,
                    counts_per_second=self.config.time_correction.counts_per_second,
                )

            merged_df = self.time_correction.apply(merged_df)
        else:
            merged_df = merged_df.with_columns(pl.col(TIMESTAMP_COLUMN).alias("timestamp"))

        return merged_df

    def get_data(self):
        data = self.read_merged()
        if data is None:
            return None

        return MultiPointDataPacket.from_dataframe(
            dataframe=data,
            source=self.name,
        )
