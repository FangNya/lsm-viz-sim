from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LSMSimulator
from app.schemas import LSMConfig, SSTableMeta


def test_get_hits_memtable_first(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("k1", "v1")
    result = simulator.get("k1")

    assert result.found is True
    assert result.value == "v1"
    assert result.source == "memtable"
    assert result.path[0]["step"] == "memtable"
    assert result.path[0]["result"] == "hit"


def test_get_hits_sstable_after_flush(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("k1", "v1")
    meta = simulator.flush_memtable()
    result = simulator.get("k1")

    assert meta is not None
    assert result.found is True
    assert result.source == "sstable"
    assert result.level == 0
    assert result.table_id == meta.table_id


def test_get_returns_latest_value_for_duplicate_key(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("dup", "old")
    old_meta = simulator.flush_memtable()
    simulator.put("dup", "new")
    new_meta = simulator.flush_memtable()

    result = simulator.get("dup")

    assert old_meta is not None and new_meta is not None
    assert result.found is True
    assert result.value == "new"
    assert result.table_id == new_meta.table_id


def test_get_uses_bloom_to_skip_sstable_for_absent_key(tmp_path: Path) -> None:
    config = LSMConfig(
        wal_dir=str(tmp_path / "wal"),
        data_dir=str(tmp_path / "data"),
        bloom_bits_per_key=16,
    )
    simulator = LSMSimulator(config=config)

    simulator.put("present", "v")
    simulator.flush_memtable()

    result = simulator.get("missing")

    assert result.found is False
    assert any(
        step.get("step") == "sstable"
        and step.get("action") == "skip"
        and step.get("bloom") == "definitely_not_present"
        for step in result.path
    )


def test_get_path_contains_lookup_flow(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"), max_levels=3)
    simulator = LSMSimulator(config=config)

    simulator.put("k1", "v1")
    simulator.flush_memtable()

    result = simulator.get("missing")

    assert result.path[0]["step"] == "memtable"
    assert result.path[0]["result"] == "miss"
    assert any(step.get("step") == "level" and step.get("level") == 0 for step in result.path)
    assert any(step.get("step") == "level" and step.get("level") == 1 for step in result.path)


def test_bloom_filter_persisted_and_loadable(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"), bloom_bits_per_key=12)
    simulator = LSMSimulator(config=config)

    simulator.put("alpha", "1")
    meta = simulator.flush_memtable()

    assert meta is not None
    assert meta.bloom_file is not None

    bloom_payload = json.loads(Path(meta.bloom_file).read_text(encoding="utf-8"))
    loaded_meta = SSTableMeta.model_validate(
        {
            **meta.model_dump(mode="json"),
            "bloom_file": meta.bloom_file,
        }
    )
    bloom = simulator.sstable.load_bloom(loaded_meta)

    assert "bit_array_base64" in bloom_payload
    assert bloom is not None
    assert bloom.might_contain("alpha") is True


def test_get_read_io_breakdown_for_bloom_miss(tmp_path: Path) -> None:
    config = LSMConfig(
        wal_dir=str(tmp_path / "wal"),
        data_dir=str(tmp_path / "data"),
        bloom_bits_per_key=16,
    )
    simulator = LSMSimulator(config=config)

    simulator.put("present", "value")
    meta = simulator.flush_memtable()
    result = simulator.get("missing")

    assert meta is not None
    bloom_pages = simulator.sstable.bloom_pages(meta)
    s = simulator.metrics.snapshot
    sstable_steps = [step for step in result.path if step.get("step") == "sstable"]

    assert s.user_query_read_io_total == bloom_pages
    assert s.bloom_read_io_total == bloom_pages
    assert s.index_read_io_total == 0
    assert s.data_block_read_io_total == 0
    assert sstable_steps[0]["query_io"] == bloom_pages


def test_get_read_io_breakdown_for_sstable_hit(tmp_path: Path) -> None:
    config = LSMConfig(
        wal_dir=str(tmp_path / "wal"),
        data_dir=str(tmp_path / "data"),
        bloom_bits_per_key=16,
    )
    simulator = LSMSimulator(config=config)

    simulator.put("present", "value")
    meta = simulator.flush_memtable()
    result = simulator.get("present")

    assert meta is not None
    bloom_pages = simulator.sstable.bloom_pages(meta)
    s = simulator.metrics.snapshot
    sstable_steps = [step for step in result.path if step.get("step") == "sstable"]

    assert result.found is True
    assert s.user_query_read_io_total == bloom_pages + 2
    assert s.bloom_read_io_total == bloom_pages
    assert s.index_read_io_total == 1
    assert s.data_block_read_io_total == 1
    assert sstable_steps[0]["query_io"] == bloom_pages + 2
