from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LSMSimulator
from app.schemas import LSMConfig


def test_put_appends_wal_record(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), memtable_max_records=100, memtable_max_bytes=1000)
    simulator = LSMSimulator(config=config)

    result = simulator.put("k1", "v1")

    wal_file = tmp_path / "wal" / "wal.jsonl"
    assert wal_file.exists()
    lines = wal_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["key"] == "k1"
    assert payload["value"] == "v1"
    assert payload["seq"] == result.seq


def test_put_writes_memtable_and_seq_increments(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), memtable_max_records=100, memtable_max_bytes=1000)
    simulator = LSMSimulator(config=config)

    first = simulator.put("k1", "v1")
    second = simulator.put("k1", "v2")

    assert first.seq == 1
    assert second.seq == 2
    assert simulator.memtable.get("k1") == "v2"
    assert simulator.memtable.size_records == 2


def test_duplicate_versions_count_toward_flush_threshold(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), memtable_max_records=2, memtable_max_bytes=10_000)
    simulator = LSMSimulator(config=config)

    simulator.put("dup", "v1")
    result = simulator.put("dup", "v2")

    assert result.needs_flush is True
    assert result.memtable_size_records == 2


def test_needs_flush_false_before_threshold(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), memtable_max_records=3, memtable_max_bytes=10_000)
    simulator = LSMSimulator(config=config)

    result = simulator.put("k1", "v1")

    assert result.needs_flush is False


def test_needs_flush_true_when_record_threshold_hit(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), memtable_max_records=2, memtable_max_bytes=10_000)
    simulator = LSMSimulator(config=config)

    simulator.put("k1", "v1")
    result = simulator.put("k2", "v2")

    assert result.needs_flush is True
    assert result.memtable_size_records == 2


def test_needs_flush_true_when_bytes_threshold_hit(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), memtable_max_records=100, memtable_max_bytes=20)
    simulator = LSMSimulator(config=config)

    result = simulator.put("key", "value")

    assert result.needs_flush is True
