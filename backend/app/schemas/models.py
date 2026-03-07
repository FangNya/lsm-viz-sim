from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CompactionStrategy(str, Enum):
    STC = "stc"
    LCS = "lcs"


class OperationType(str, Enum):
    PUT = "put"


class LSMConfig(BaseModel):
    """Static configuration contract for the teaching simulator."""

    model_config = ConfigDict(use_enum_values=True)

    memtable_max_records: int = Field(default=1000, gt=0)
    memtable_max_bytes: int = Field(default=1_048_576, gt=0)
    max_levels: int = Field(default=4, ge=1)
    compaction_strategy: CompactionStrategy = CompactionStrategy.STC
    stc_trigger_tables: int = Field(default=4, ge=2)
    l0_compaction_trigger_tables: int = Field(default=4, ge=2)
    level_size_multiplier: float = Field(default=10.0, gt=1.0)
    bloom_bits_per_key: int = Field(default=10, ge=1)
    wal_dir: str = "./data/wal"
    data_dir: str = "./data/sst"


class Record(BaseModel):
    """Canonical in-memory record shape."""

    model_config = ConfigDict(use_enum_values=True)

    key: str
    value: str
    seq: int = Field(ge=0)
    op: OperationType = OperationType.PUT
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WALRecord(Record):
    """Write-ahead log record contract."""


class SSTableMeta(BaseModel):
    """SSTable metadata contract for file-based storage."""

    table_id: str
    level: int = Field(ge=0)
    data_file: str
    meta_file: str
    min_key: str
    max_key: str
    record_count: int = Field(ge=0)
    size_bytes: int = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bloom_file: str | None = None


class TraceEvent(BaseModel):
    """Trace event contract exported by backend runtime."""

    event_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    seq: int = Field(default=0, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)


class MetricsSnapshot(BaseModel):
    """Point-in-time metrics contract for monitoring and export."""

    total_puts: int = Field(default=0, ge=0)
    total_gets: int = Field(default=0, ge=0)
    memtable_size_records: int = Field(default=0, ge=0)
    memtable_size_bytes: int = Field(default=0, ge=0)
    sstable_count_by_level: dict[int, int] = Field(default_factory=dict)
    flush_count: int = Field(default=0, ge=0)
    compaction_count: int = Field(default=0, ge=0)
    read_amplification: float = Field(default=1.0, ge=0.0)
    write_amplification: float = Field(default=1.0, ge=0.0)
    simulated_io_reads: int = Field(default=0, ge=0)
    simulated_io_writes: int = Field(default=0, ge=0)


class CompactionTask(BaseModel):
    """Compaction scheduling contract without execution semantics."""

    model_config = ConfigDict(use_enum_values=True)

    strategy: CompactionStrategy
    source_level: int = Field(ge=0)
    target_level: int = Field(ge=0)
    input_table_ids: list[str] = Field(default_factory=list)
    reason: str


class WorkloadOperation(BaseModel):
    """Input workload operation contract for simulation runner."""

    model_config = ConfigDict(use_enum_values=True)

    op: OperationType = OperationType.PUT
    key: str
    value: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))