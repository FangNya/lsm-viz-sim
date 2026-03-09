from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.compaction import (
    CompactionResult,
    CompactionStrategyBase,
    LCSCompactionStrategy,
    STCCompactionStrategy,
)
from app.core.memtable import MemTable
from app.core.sstable import SSTableManager
from app.core.wal import WALManager
from app.schemas import CompactionStrategy, LSMConfig, Record, SSTableMeta, WALRecord


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


@dataclass(slots=True)
class GetResult:
    found: bool
    value: str | None
    source: str | None
    level: int | None
    table_id: str | None
    path: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "value": self.value,
            "source": self.source,
            "level": self.level,
            "table_id": self.table_id,
            "path": self.path,
        }


class LSMSimulator:
    """Teaching simulator for write/read path and simplified compaction strategies."""

    def __init__(self, config: LSMConfig) -> None:
        self.config = config
        self._next_seq = 0
        self.wal = WALManager(config.wal_dir)
        self.memtable = MemTable()
        self.sstable = SSTableManager(config.data_dir, config.bloom_bits_per_key)
        self.level_tables: dict[int, list[SSTableMeta]] = {0: []}

        # Midterm simplification: compaction runs synchronously after flush.
        self.compaction_strategy = self._build_compaction_strategy()
        self.compaction_history: list[CompactionResult] = []

    @property
    def level0_tables(self) -> list[SSTableMeta]:
        return self.level_tables.setdefault(0, [])

    def _build_compaction_strategy(self) -> CompactionStrategyBase:
        if self.config.compaction_strategy == CompactionStrategy.LCS.value:
            return LCSCompactionStrategy()
        return STCCompactionStrategy()

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

        self.run_compaction_cycle()
        return meta

    def run_compaction_cycle(self) -> list[CompactionResult]:
        results: list[CompactionResult] = []
        for level in range(max(self.config.max_levels - 1, 0)):
            while self.compaction_strategy.should_trigger(self, level):
                result = self.compaction_strategy.compact(self, level)
                self.compaction_history.append(result)
                results.append(result)
        return results

    def get(self, key: str) -> GetResult:
        path: list[dict[str, Any]] = []

        value = self.memtable.get(key)
        if value is not None:
            path.append({"step": "memtable", "result": "hit"})
            return GetResult(
                found=True,
                value=value,
                source="memtable",
                level=None,
                table_id=None,
                path=path,
            )
        path.append({"step": "memtable", "result": "miss"})

        for level in range(self.config.max_levels):
            tables = self.level_tables.get(level, [])
            ordered_tables = list(reversed(tables))

            level_hit = False
            for meta in ordered_tables:
                bloom = self.sstable.load_bloom(meta)
                if bloom is not None and not bloom.might_contain(key):
                    path.append(
                        {
                            "step": "sstable",
                            "level": level,
                            "table_id": meta.table_id,
                            "bloom": "definitely_not_present",
                            "action": "skip",
                        }
                    )
                    continue

                path.append(
                    {
                        "step": "sstable",
                        "level": level,
                        "table_id": meta.table_id,
                        "bloom": "maybe_present" if bloom is not None else "missing",
                        "action": "scan",
                    }
                )
                value = self.sstable.find_key(meta, key)
                if value is not None:
                    level_hit = True
                    return GetResult(
                        found=True,
                        value=value,
                        source="sstable",
                        level=level,
                        table_id=meta.table_id,
                        path=path,
                    )

            if not level_hit:
                path.append({"step": "level", "level": level, "result": "miss"})

        return GetResult(
            found=False,
            value=None,
            source=None,
            level=None,
            table_id=None,
            path=path,
        )

    def list_levels(self) -> dict[str, list[dict]]:
        return {
            f"level_{level}": [meta.model_dump(mode="json") for meta in tables]
            for level, tables in sorted(self.level_tables.items(), key=lambda item: item[0])
        }
