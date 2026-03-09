from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LSMSimulator
from app.schemas import LSMConfig


def _build_simulator(tmp_path: Path) -> LSMSimulator:
    config = LSMConfig(
        wal_dir=str(tmp_path / "wal"),
        data_dir=str(tmp_path / "data"),
        memtable_max_records=10,
        memtable_max_bytes=10_000,
        stc_trigger_tables=3,
        max_levels=4,
    )
    return LSMSimulator(config=config)


def test_stc_triggers_at_threshold_and_selects_oldest_inputs(tmp_path: Path) -> None:
    sim = _build_simulator(tmp_path)

    sim.put("k1", "v1")
    m1 = sim.flush_memtable()
    sim.put("k1", "v2")
    m2 = sim.flush_memtable()

    assert m1 is not None and m2 is not None
    assert len(sim.compaction_history) == 0

    sim.put("k2", "v3")
    m3 = sim.flush_memtable()

    assert m3 is not None
    assert len(sim.compaction_history) == 1

    result = sim.compaction_history[0]
    assert result.source_level == 0
    assert result.target_level == 1
    assert result.input_table_ids == [m1.table_id, m2.table_id, m3.table_id]


def test_stc_merge_order_dedup_and_level_state_updates(tmp_path: Path) -> None:
    sim = _build_simulator(tmp_path)

    sim.put("b", "v1")
    m1 = sim.flush_memtable()
    sim.put("a", "v2")
    m2 = sim.flush_memtable()
    sim.put("b", "v3")
    m3 = sim.flush_memtable()

    assert m1 is not None and m2 is not None and m3 is not None
    assert len(sim.compaction_history) == 1

    result = sim.compaction_history[0]

    # (5) new SSTable appears in next level
    assert len(sim.level_tables.get(1, [])) == 1
    output_meta = sim.level_tables[1][0]
    assert output_meta.table_id == result.output_table_id

    # (3) merged keys are sorted
    merged = sim.sstable.read_records(output_meta)
    merged_keys = [r.key for r in merged]
    assert merged_keys == sorted(merged_keys)

    # (4) duplicate keys keep latest seq/value
    merged_map = {r.key: r for r in merged}
    assert merged_map["b"].value == "v3"
    assert merged_map["b"].seq > 0

    # (6) old SSTables are removed from level0 and files deleted
    assert len(sim.level_tables.get(0, [])) == 0
    for meta in [m1, m2, m3]:
        assert not Path(meta.data_file).exists()
        assert not Path(meta.meta_file).exists()
        if meta.bloom_file:
            assert not Path(meta.bloom_file).exists()

    # (7) level state snapshot updated before/after
    assert len(result.before_levels["level_0"]) == 3
    assert len(result.after_levels["level_0"]) == 0
    assert len(result.after_levels["level_1"]) == 1
