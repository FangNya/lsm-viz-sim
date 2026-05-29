from __future__ import annotations

from pathlib import Path

from app.schemas import WALRecord


class WALManager:
    """Append-only JSONL WAL writer (no recovery in this stage)."""

    def __init__(self, wal_dir: str, file_name: str = "wal.jsonl") -> None:
        self.wal_dir = Path(wal_dir)
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        self.wal_file = self.wal_dir / file_name

    def append(self, record: WALRecord) -> int:
        before_size = self.wal_file.stat().st_size if self.wal_file.exists() else 0
        line = record.model_dump_json()
        with self.wal_file.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
        return self.wal_file.stat().st_size - before_size
