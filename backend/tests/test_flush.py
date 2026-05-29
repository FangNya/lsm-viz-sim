from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LSMSimulator
from app.schemas import LSMConfig


def test_flush_creates_data_and_meta_files(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("b", "2")
    simulator.put("a", "1")
    meta = simulator.flush_memtable()

    assert meta is not None
    data_file = Path(meta.data_file)
    meta_file = Path(meta.meta_file)
    assert data_file.exists()
    assert meta_file.exists()


def test_flush_updates_level0_and_clears_memtable(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("b", "2")
    simulator.put("a", "1")
    simulator.flush_memtable()

    levels = simulator.list_levels()
    assert len(levels["level_0"]) == 1
    assert simulator.memtable.size_records == 0
    assert simulator.memtable.size_bytes == 0


def test_flush_writes_sorted_records_and_correct_metadata(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("k3", "v3")
    simulator.put("k1", "v1")
    simulator.put("k2", "v2")
    meta = simulator.flush_memtable()

    assert meta is not None
    lines = Path(meta.data_file).read_text(encoding="utf-8").strip().splitlines()
    keys = [json.loads(line)["key"] for line in lines]

    assert keys == ["k1", "k2", "k3"]
    assert meta.min_key == "k1"
    assert meta.max_key == "k3"
    assert meta.record_count == 3

    meta_payload = json.loads(Path(meta.meta_file).read_text(encoding="utf-8"))
    assert meta_payload["min_key"] == "k1"
    assert meta_payload["max_key"] == "k3"
    assert meta_payload["record_count"] == 3
    assert meta_payload["level"] == 0


def test_flush_preserves_duplicate_versions_in_seq_desc_order(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("dup", "old")
    simulator.put("dup", "new")
    simulator.put("z", "tail")
    meta = simulator.flush_memtable()

    assert meta is not None
    records = [json.loads(line) for line in Path(meta.data_file).read_text(encoding="utf-8").strip().splitlines()]

    assert [(item["key"], item["value"]) for item in records] == [
        ("dup", "new"),
        ("dup", "old"),
        ("z", "tail"),
    ]
    assert meta.record_count == 3
