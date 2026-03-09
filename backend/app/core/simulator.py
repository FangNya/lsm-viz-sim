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
from app.metrics import MetricsCollector
from app.trace import TraceEmitter
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

        self.metrics = MetricsCollector()
        self.trace = TraceEmitter()
        self._refresh_metrics("init")

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
        self.metrics.add_io_writes(1)

        self.memtable.put(Record(key=key, value=value, seq=seq))
        self.metrics.add_io_writes(1)
        self.metrics.inc_put()

        self.trace.emit(
            event_type="put",
            seq=seq,
            payload={"key": key, "value_size": len(value), "wal_file": str(self.wal.wal_file)},
        )

        needs_flush = (
            self.memtable.size_records >= self.config.memtable_max_records
            or self.memtable.size_bytes >= self.config.memtable_max_bytes
        )

        self._refresh_metrics("put")

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

        self.trace.emit(
            event_type="flush_start",
            seq=self._next_seq,
            payload={"input_records": len(records), "target_level": 0},
        )

        meta = self.sstable.flush_to_level0(records)
        self.level0_tables.append(meta)
        self.memtable.clear()

        self.metrics.inc_flush()
        self.metrics.add_io_writes(len(records) + 2)

        self.trace.emit(
            event_type="sstable_created",
            seq=self._next_seq,
            payload={
                "table_id": meta.table_id,
                "level": meta.level,
                "record_count": meta.record_count,
                "data_file": meta.data_file,
                "meta_file": meta.meta_file,
                "bloom_file": meta.bloom_file,
            },
        )
        self.trace.emit(
            event_type="flush_end",
            seq=self._next_seq,
            payload={"table_id": meta.table_id, "level": 0},
        )

        self._refresh_metrics("flush")
        self.run_compaction_cycle()
        return meta

    def run_compaction_cycle(self) -> list[CompactionResult]:
        results: list[CompactionResult] = []
        strategy_name = str(self.config.compaction_strategy)
        for level in range(max(self.config.max_levels - 1, 0)):
            while self.compaction_strategy.should_trigger(self, level):
                selected = self.compaction_strategy.select_inputs(self, level)
                self.trace.emit(
                    event_type="compaction_start",
                    seq=self._next_seq,
                    payload={
                        "strategy": strategy_name,
                        "source_level": level,
                        "target_level": level + 1,
                        "input_table_ids": [m.table_id for m in selected],
                    },
                )

                result = self.compaction_strategy.compact(self, level)
                self.compaction_history.append(result)
                results.append(result)

                self.metrics.inc_compaction()
                self.metrics.add_io_reads(max(len(result.input_table_ids), 1))
                output_count = 0
                target_tables = self.level_tables.get(result.target_level, [])
                for table in target_tables:
                    if table.table_id == result.output_table_id:
                        output_count = table.record_count
                        break
                self.metrics.add_io_writes(output_count + 2)

                self.trace.emit(
                    event_type="sstable_created",
                    seq=self._next_seq,
                    payload={
                        "table_id": result.output_table_id,
                        "level": result.target_level,
                        "created_by": "compaction",
                    },
                )
                self.trace.emit(
                    event_type="compaction_end",
                    seq=self._next_seq,
                    payload={
                        "strategy": result.strategy,
                        "source_level": result.source_level,
                        "target_level": result.target_level,
                        "input_table_ids": result.input_table_ids,
                        "output_table_id": result.output_table_id,
                    },
                )

                self._refresh_metrics("compaction")
        return results

    def get(self, key: str) -> GetResult:
        path: list[dict[str, Any]] = []
        self.metrics.inc_get()

        value = self.memtable.get(key)
        if value is not None:
            path.append({"step": "memtable", "result": "hit"})
            result = GetResult(
                found=True,
                value=value,
                source="memtable",
                level=None,
                table_id=None,
                path=path,
            )
            self.trace.emit("get", self._next_seq, {"key": key, **result.to_dict()})
            self._refresh_metrics("get")
            return result
        path.append({"step": "memtable", "result": "miss"})

        for level in range(self.config.max_levels):
            tables = self.level_tables.get(level, [])
            ordered_tables = list(reversed(tables))

            level_hit = False
            for meta in ordered_tables:
                bloom = self.sstable.load_bloom(meta)
                if bloom is not None:
                    self.metrics.add_io_reads(1)
                    if not bloom.might_contain(key):
                        self.trace.emit(
                            event_type="bloom_miss",
                            seq=self._next_seq,
                            payload={"key": key, "level": level, "table_id": meta.table_id},
                        )
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

                    self.trace.emit(
                        event_type="bloom_hit",
                        seq=self._next_seq,
                        payload={"key": key, "level": level, "table_id": meta.table_id},
                    )

                path.append(
                    {
                        "step": "sstable",
                        "level": level,
                        "table_id": meta.table_id,
                        "bloom": "maybe_present" if bloom is not None else "missing",
                        "action": "scan",
                    }
                )
                self.metrics.add_io_reads(1)
                value = self.sstable.find_key(meta, key)
                if value is not None:
                    level_hit = True
                    result = GetResult(
                        found=True,
                        value=value,
                        source="sstable",
                        level=level,
                        table_id=meta.table_id,
                        path=path,
                    )
                    self.trace.emit("get", self._next_seq, {"key": key, **result.to_dict()})
                    self._refresh_metrics("get")
                    return result

            if not level_hit:
                path.append({"step": "level", "level": level, "result": "miss"})

        result = GetResult(
            found=False,
            value=None,
            source=None,
            level=None,
            table_id=None,
            path=path,
        )
        self.trace.emit("get", self._next_seq, {"key": key, **result.to_dict()})
        self._refresh_metrics("get")
        return result

    def list_levels(self) -> dict[str, list[dict]]:
        return {
            f"level_{level}": [meta.model_dump(mode="json") for meta in tables]
            for level, tables in sorted(self.level_tables.items(), key=lambda item: item[0])
        }

    def export_metrics_json(self, file_path: str) -> str:
        self._refresh_metrics("export_metrics_json")
        return self.metrics.export_json(file_path)

    def export_metrics_csv(self, file_path: str) -> str:
        self._refresh_metrics("export_metrics_csv")
        return self.metrics.export_csv(file_path)

    def export_trace_json(self, file_path: str) -> str:
        return self.trace.export_json(file_path)

    def export_trace_csv(self, file_path: str) -> str:
        return self.trace.export_csv(file_path)

    def _refresh_metrics(self, reason: str) -> None:
        self.metrics.set_memtable_stats(
            records=self.memtable.size_records,
            size_bytes=self.memtable.size_bytes,
        )
        counts = {level: len(tables) for level, tables in self.level_tables.items()}
        self.metrics.set_sstable_counts(counts)
        self.metrics.capture(reason)
