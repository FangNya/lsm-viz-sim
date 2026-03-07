from __future__ import annotations

import json
import re
from pathlib import Path

from app.schemas import Record, SSTableMeta


class SSTableManager:
    """Teaching-format SSTable manager (JSONL data + JSON metadata)."""

    TABLE_ID_WIDTH = 6

    def __init__(self, data_dir: str) -> None:
        self.data_root = Path(data_dir)
        self.level0_dir = self.data_root / "level_0"
        self.level0_dir.mkdir(parents=True, exist_ok=True)

    def flush_to_level0(self, records: list[Record]) -> SSTableMeta:
        if not records:
            raise ValueError("cannot flush empty record list")

        table_id = self._next_table_id()
        data_file = self.level0_dir / f"{table_id}.jsonl"
        meta_file = self.level0_dir / f"{table_id}.meta.json"

        with data_file.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json() + "\n")

        meta = SSTableMeta(
            table_id=table_id,
            level=0,
            data_file=str(data_file),
            meta_file=str(meta_file),
            min_key=records[0].key,
            max_key=records[-1].key,
            record_count=len(records),
            size_bytes=data_file.stat().st_size,
        )

        with meta_file.open("w", encoding="utf-8") as f:
            json.dump(meta.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

        return meta

    def _next_table_id(self) -> str:
        pattern = re.compile(r"^sst_(\d{6})\.meta\.json$")
        max_id = 0

        for entry in self.level0_dir.glob("sst_*.meta.json"):
            match = pattern.match(entry.name)
            if match:
                max_id = max(max_id, int(match.group(1)))

        return f"sst_{max_id + 1:0{self.TABLE_ID_WIDTH}d}"
