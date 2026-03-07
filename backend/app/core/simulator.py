from __future__ import annotations

from dataclasses import dataclass

from app.core.memtable import MemTable
from app.core.wal import WALManager
from app.schemas import LSMConfig, Record, WALRecord


@dataclass(slots=True)
class PutResult:
    success: bool
    seq: int
    needs_flush: bool
    memtable_size_records: int
    memtable_size_bytes: int

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "success": self.success,
            "seq": self.seq,
            "needs_flush": self.needs_flush,
            "memtable_size_records": self.memtable_size_records,
            "memtable_size_bytes": self.memtable_size_bytes,
        }


class LSMSimulator:
    """Minimal write-path simulator: WAL append then MemTable put."""

    def __init__(self, config: LSMConfig) -> None:
        self.config = config
        self._next_seq = 0
        self.wal = WALManager(config.wal_dir)
        self.memtable = MemTable()

    def put(self, key: str, value: str) -> PutResult:
        self._next_seq += 1
        seq = self._next_seq

        wal_record = WALRecord(key=key, value=value, seq=seq)
        self.wal.append(wal_record)

        self.memtable.put(Record(key=key, value=value, seq=seq))

        needs_flush = (
            self.memtable.size_records >= self.config.memtable_max_records
            or self.memtable.size_bytes >= self.config.memtable_max_bytes
        )

        return PutResult(
            success=True,
            seq=seq,
            needs_flush=needs_flush,
            memtable_size_records=self.memtable.size_records,
            memtable_size_bytes=self.memtable.size_bytes,
        )
