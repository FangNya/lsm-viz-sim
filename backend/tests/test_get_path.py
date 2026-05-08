from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LSMSimulator
from app.schemas import LSMConfig, Record, SSTableMeta


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


def test_get_returns_latest_value_for_duplicate_versions_in_same_sstable(tmp_path: Path) -> None:
    config = LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data"))
    simulator = LSMSimulator(config=config)

    simulator.put("dup", "old")
    simulator.put("dup", "new")
    meta = simulator.flush_memtable()
    result = simulator.get("dup")

    assert meta is not None
    assert result.found is True
    assert result.value == "new"
    assert result.table_id == meta.table_id


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


def test_lcs_high_level_lookup_uses_range_pruning_and_binary_candidates(tmp_path: Path) -> None:
    config = LSMConfig(
        compaction_strategy="lcs",
        wal_dir=str(tmp_path / "wal"),
        data_dir=str(tmp_path / "data"),
        max_levels=4,
        bloom_bits_per_key=16,
    )
    simulator = LSMSimulator(config=config)

    left = simulator.sstable.write_table(
        level=1,
        records=[Record(key="a", value="1", seq=1), Record(key="c", value="3", seq=3)],
    )
    middle = simulator.sstable.write_table(
        level=1,
        records=[Record(key="m", value="10", seq=10), Record(key="n", value="11", seq=11)],
    )
    right = simulator.sstable.write_table(
        level=1,
        records=[Record(key="x", value="20", seq=20), Record(key="z", value="22", seq=22)],
    )
    simulator.level_tables[1] = [right, left, middle]

    result = simulator.get("n")

    assert result.found is True
    assert result.value == "11"
    lookup_steps = [step for step in result.path if step.get("step") == "level_lookup"]
    sstable_steps = [step for step in result.path if step.get("step") == "sstable"]

    assert lookup_steps
    assert lookup_steps[0]["level"] == 1
    assert lookup_steps[0]["mode"] == "binary_range_lookup"
    assert lookup_steps[0]["candidate_table_ids"] == [middle.table_id]
    assert lookup_steps[0]["pruned_table_count"] == 2
    assert len(sstable_steps) == 1
    assert sstable_steps[0]["table_id"] == middle.table_id

    bloom_pages = simulator.sstable.bloom_pages(middle)
    snapshot = simulator.metrics.snapshot
    assert snapshot.user_query_read_io_total == bloom_pages + 2


def test_lcs_high_level_tables_are_kept_sorted_by_key_range(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            compaction_strategy="lcs",
            l0_compaction_trigger_tables=2,
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
        )
    )

    sim.put("k1", "v1")
    sim.flush_memtable()
    sim.put("k2", "v2")
    sim.flush_memtable()
    sim.put("k8", "v8")
    sim.flush_memtable()
    sim.put("k9", "v9")
    sim.flush_memtable()

    level1 = sim.level_tables.get(1, [])
    min_keys = [meta.min_key for meta in level1]

    assert len(level1) == 2
    assert min_keys == sorted(min_keys)
