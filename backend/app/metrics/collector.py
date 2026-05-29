from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import MetricsSnapshot


class MetricsCollector:
    """Collects and exports simulator metrics snapshots."""

    CSV_HEADER = [
        "timestamp",
        "reason",
        "total_puts",
        "total_gets",
        "memtable_size_records",
        "memtable_size_bytes",
        "sstable_count_by_level",
        "flush_count",
        "compaction_count",
        "read_amplification",
        "write_amplification",
        "logical_write_bytes_total",
        "wal_write_bytes_total",
        "flush_data_write_bytes_total",
        "flush_meta_write_bytes_total",
        "flush_bloom_write_bytes_total",
        "compaction_data_write_bytes_total",
        "compaction_meta_write_bytes_total",
        "compaction_bloom_write_bytes_total",
        "actual_disk_write_bytes_total",
        "user_query_read_io_total",
        "bloom_read_io_total",
        "index_read_io_total",
        "data_block_read_io_total",
    ]

    def __init__(self) -> None:
        self.snapshot = MetricsSnapshot()
        self.history: list[dict] = []
        self.capture("init")

    def capture(self, reason: str) -> None:
        self._refresh_amplification()
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            **self.snapshot.model_dump(mode="json"),
        }
        self.history.append(row)

    def set_memtable_stats(self, records: int, size_bytes: int) -> None:
        self.snapshot.memtable_size_records = records
        self.snapshot.memtable_size_bytes = size_bytes

    def set_sstable_counts(self, counts: dict[int, int]) -> None:
        self.snapshot.sstable_count_by_level = dict(sorted(counts.items(), key=lambda item: item[0]))

    def inc_put(self) -> None:
        self.snapshot.total_puts += 1

    def inc_get(self) -> None:
        self.snapshot.total_gets += 1

    def inc_flush(self) -> None:
        self.snapshot.flush_count += 1

    def inc_compaction(self) -> None:
        self.snapshot.compaction_count += 1

    def add_logical_write_bytes(self, value: int) -> None:
        self.snapshot.logical_write_bytes_total += value

    def add_wal_write_bytes(self, value: int) -> None:
        self.snapshot.wal_write_bytes_total += value
        self.snapshot.actual_disk_write_bytes_total += value

    def add_flush_write_bytes(self, data_bytes: int, meta_bytes: int, bloom_bytes: int) -> None:
        self.snapshot.flush_data_write_bytes_total += data_bytes
        self.snapshot.flush_meta_write_bytes_total += meta_bytes
        self.snapshot.flush_bloom_write_bytes_total += bloom_bytes
        self.snapshot.actual_disk_write_bytes_total += data_bytes + meta_bytes + bloom_bytes

    def add_compaction_write_bytes(self, data_bytes: int, meta_bytes: int, bloom_bytes: int) -> None:
        self.snapshot.compaction_data_write_bytes_total += data_bytes
        self.snapshot.compaction_meta_write_bytes_total += meta_bytes
        self.snapshot.compaction_bloom_write_bytes_total += bloom_bytes
        self.snapshot.actual_disk_write_bytes_total += data_bytes + meta_bytes + bloom_bytes

    def add_query_bloom_io(self, value: int) -> None:
        self.snapshot.bloom_read_io_total += value
        self.snapshot.user_query_read_io_total += value

    def add_query_index_io(self, value: int = 1) -> None:
        self.snapshot.index_read_io_total += value
        self.snapshot.user_query_read_io_total += value

    def add_query_data_io(self, value: int = 1) -> None:
        self.snapshot.data_block_read_io_total += value
        self.snapshot.user_query_read_io_total += value

    def export_json(self, file_path: str) -> str:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "snapshot": self.snapshot.model_dump(mode="json"),
            "history": self.history,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def export_csv(self, file_path: str) -> str:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER)
            writer.writeheader()
            for item in self.history:
                writer.writerow(
                    {
                        "timestamp": item["timestamp"],
                        "reason": item["reason"],
                        "total_puts": item["total_puts"],
                        "total_gets": item["total_gets"],
                        "memtable_size_records": item["memtable_size_records"],
                        "memtable_size_bytes": item["memtable_size_bytes"],
                        "sstable_count_by_level": json.dumps(
                            item["sstable_count_by_level"],
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        "flush_count": item["flush_count"],
                        "compaction_count": item["compaction_count"],
                        "read_amplification": item["read_amplification"],
                        "write_amplification": item["write_amplification"],
                        "logical_write_bytes_total": item["logical_write_bytes_total"],
                        "wal_write_bytes_total": item["wal_write_bytes_total"],
                        "flush_data_write_bytes_total": item["flush_data_write_bytes_total"],
                        "flush_meta_write_bytes_total": item["flush_meta_write_bytes_total"],
                        "flush_bloom_write_bytes_total": item["flush_bloom_write_bytes_total"],
                        "compaction_data_write_bytes_total": item["compaction_data_write_bytes_total"],
                        "compaction_meta_write_bytes_total": item["compaction_meta_write_bytes_total"],
                        "compaction_bloom_write_bytes_total": item["compaction_bloom_write_bytes_total"],
                        "actual_disk_write_bytes_total": item["actual_disk_write_bytes_total"],
                        "user_query_read_io_total": item["user_query_read_io_total"],
                        "bloom_read_io_total": item["bloom_read_io_total"],
                        "index_read_io_total": item["index_read_io_total"],
                        "data_block_read_io_total": item["data_block_read_io_total"],
                    }
                )

        return str(path)

    def _refresh_amplification(self) -> None:
        gets = self.snapshot.total_gets
        self.snapshot.read_amplification = (
            self.snapshot.user_query_read_io_total / gets if gets > 0 else 0.0
        )
        self.snapshot.write_amplification = (
            self.snapshot.actual_disk_write_bytes_total / self.snapshot.logical_write_bytes_total
            if self.snapshot.logical_write_bytes_total > 0
            else 0.0
        )
