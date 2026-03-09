from __future__ import annotations

import json
import re
from pathlib import Path

from app.core.bloom import BloomFilter
from app.schemas import Record, SSTableMeta


class SSTableManager:
    """Teaching-format SSTable manager (JSONL data + JSON metadata)."""

    TABLE_ID_WIDTH = 6

    def __init__(self, data_dir: str, bloom_bits_per_key: int) -> None:
        self.data_root = Path(data_dir)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.level_dir(0).mkdir(parents=True, exist_ok=True)
        self.bloom_bits_per_key = bloom_bits_per_key

    def level_dir(self, level: int) -> Path:
        return self.data_root / f"level_{level}"

    def flush_to_level0(self, records: list[Record]) -> SSTableMeta:
        return self.write_table(level=0, records=records)

    def write_table(self, level: int, records: list[Record]) -> SSTableMeta:
        if not records:
            raise ValueError("cannot flush empty record list")

        level_dir = self.level_dir(level)
        level_dir.mkdir(parents=True, exist_ok=True)

        table_id = self._next_table_id()
        data_file = level_dir / f"{table_id}.jsonl"
        meta_file = level_dir / f"{table_id}.meta.json"
        bloom_file = level_dir / f"{table_id}.bloom.json"

        with data_file.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(record.model_dump_json() + "\n")

        bloom = BloomFilter.create(
            bits=max(self.bloom_bits_per_key * len(records), 8),
            num_hashes=3,
        )
        for record in records:
            bloom.add(record.key)

        with bloom_file.open("w", encoding="utf-8") as f:
            json.dump(bloom.to_dict(), f, ensure_ascii=False, indent=2)

        meta = SSTableMeta(
            table_id=table_id,
            level=level,
            data_file=str(data_file),
            meta_file=str(meta_file),
            min_key=records[0].key,
            max_key=records[-1].key,
            record_count=len(records),
            size_bytes=data_file.stat().st_size,
            bloom_file=str(bloom_file),
        )

        with meta_file.open("w", encoding="utf-8") as f:
            json.dump(meta.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

        return meta

    def load_bloom(self, meta: SSTableMeta) -> BloomFilter | None:
        if not meta.bloom_file:
            return None
        bloom_path = Path(meta.bloom_file)
        if not bloom_path.exists():
            return None
        payload = json.loads(bloom_path.read_text(encoding="utf-8"))
        return BloomFilter.from_dict(payload)

    def find_key(self, meta: SSTableMeta, key: str) -> str | None:
        data_path = Path(meta.data_file)
        if not data_path.exists():
            return None

        with data_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if payload.get("key") == key:
                    return str(payload.get("value"))
        return None

    def read_records(self, meta: SSTableMeta) -> list[Record]:
        data_path = Path(meta.data_file)
        if not data_path.exists():
            return []

        records: list[Record] = []
        with data_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                records.append(Record.model_validate_json(line))
        return records

    def delete_table_files(self, meta: SSTableMeta) -> None:
        for path_str in [meta.data_file, meta.meta_file, meta.bloom_file]:
            if not path_str:
                continue
            path = Path(path_str)
            if path.exists():
                path.unlink()

    def _next_table_id(self) -> str:
        pattern = re.compile(r"^sst_(\d{6})\.meta\.json$")
        max_id = 0

        for entry in self.data_root.rglob("sst_*.meta.json"):
            match = pattern.match(entry.name)
            if match:
                max_id = max(max_id, int(match.group(1)))

        return f"sst_{max_id + 1:0{self.TABLE_ID_WIDTH}d}"
