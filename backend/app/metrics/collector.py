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
        "simulated_io_reads",
        "simulated_io_writes",
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

    def add_io_reads(self, value: int = 1) -> None:
        self.snapshot.simulated_io_reads += value

    def add_io_writes(self, value: int = 1) -> None:
        self.snapshot.simulated_io_writes += value

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
                        "simulated_io_reads": item["simulated_io_reads"],
                        "simulated_io_writes": item["simulated_io_writes"],
                    }
                )

        return str(path)

    def _refresh_amplification(self) -> None:
        gets = self.snapshot.total_gets
        puts = self.snapshot.total_puts

        self.snapshot.read_amplification = (
            self.snapshot.simulated_io_reads / gets if gets > 0 else 0.0
        )
        self.snapshot.write_amplification = (
            self.snapshot.simulated_io_writes / puts if puts > 0 else 0.0
        )
