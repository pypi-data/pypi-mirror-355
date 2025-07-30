from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

# --- Storage Models ---

class StorageRecord(BaseModel):
    """Represents a single record in Storage."""

    key: str
    value: Any
    binary: Optional[bool] = None  # True if the value is stored as binary
    tx: Optional[int] = None       # Transaction ID when the value was written

    model_config = ConfigDict(extra="ignore")  # Allow unknown fields (forward compatibility)


class StorageReadResponse(BaseModel):
    """Response from a batch Storage read operation."""

    count: int                     # Number of records returned
    data: List[StorageRecord]       # List of StorageRecord objects
    duration: str                   # API processing time (e.g., "12ms")

    model_config = ConfigDict(extra="ignore")


class StorageWriteResponse(BaseModel):
    """Response from a Storage write or delete operation."""

    tx: int                         # Transaction ID assigned to the operation
    duration: str                   # API processing time

    model_config = ConfigDict(extra="ignore")


# --- Stream Models ---

class StreamPushResponse(BaseModel):
    """Response from pushing events to a stream."""

    count: int                      # Number of events successfully committed
    duration: str                   # API processing time

    model_config = ConfigDict(extra="ignore")


class StreamCommitResponse(BaseModel):
    """Response from committing a batch of events to a stream."""

    tx: int                         # Transaction ID assigned to the batch
    duration: str                   # API processing time

    model_config = ConfigDict(extra="ignore")


class StreamEvent(BaseModel):
    """Represents a single event in a stream."""

    tx: int                         # Transaction ID of the event
    data: Dict[str, Any]             # Event payload (decoded JSON)
    time: str                        # Commit timestamp in ISO 8601 format
    binary: Optional[bool] = None    # True if the event payload was binary

    model_config = ConfigDict(extra="ignore")
