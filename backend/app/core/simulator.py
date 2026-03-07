from __future__ import annotations

from dataclasses import dataclass

from app.core.memtable import MemTable
from app.core.sstable import SSTableManager
from app.core.wal import WALManager
from app.schemas import LSMConfig, Record, SSTableMeta, WALRecord


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
    """Minimal write path + flush to level-0 SSTable for teaching use."""

    def __init__(self, config: LSMConfig) -> None:
        self.config = config
        self._next_seq = 0
        self.wal = WALManager(config.wal_dir)
        self.memtable = MemTable()
        self.sstable = SSTableManager(config.data_dir)
        self.level0_tables: list[SSTableMeta] = []

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

    def flush_memtable(self) -> SSTableMeta | None:
        records = self.memtable.sorted_records()
        if not records:
            return None

        # Midterm simplification: WAL cleanup/replay is out of scope in this stage.
        meta = self.sstable.flush_to_level0(records)
        self.level0_tables.append(meta)
        self.memtable.clear()
        return meta

    def list_levels(self) -> dict[str, list[dict]]:
        return {
            "level_0": [meta.model_dump(mode="json") for meta in self.level0_tables],
        }
