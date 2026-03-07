from __future__ import annotations

from pathlib import Path

from app.schemas import WALRecord


class WALManager:
    """Append-only JSONL WAL writer (no recovery in this stage)."""

    def __init__(self, wal_dir: str, file_name: str = "wal.jsonl") -> None:
        self.wal_dir = Path(wal_dir)
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        self.wal_file = self.wal_dir / file_name

    def append(self, record: WALRecord) -> None:
        line = record.model_dump_json()
        with self.wal_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
