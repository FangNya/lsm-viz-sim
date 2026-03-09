from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LCSCompactionStrategy, LSMSimulator, STCCompactionStrategy
from app.schemas import LSMConfig, Record


def test_compaction_strategy_switching() -> None:
    stc_sim = LSMSimulator(LSMConfig(compaction_strategy="stc"))
    lcs_sim = LSMSimulator(LSMConfig(compaction_strategy="lcs"))

    assert isinstance(stc_sim.compaction_strategy, STCCompactionStrategy)
    assert isinstance(lcs_sim.compaction_strategy, LCSCompactionStrategy)


def test_lcs_triggers_when_l0_reaches_threshold(tmp_path: Path) -> None:
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
    assert len(sim.compaction_history) == 0

    sim.put("k2", "v2")
    sim.flush_memtable()

    assert len(sim.compaction_history) == 1
    result = sim.compaction_history[0]
    assert result.strategy == "lcs"
    assert result.source_level == 0
    assert result.target_level == 1


def test_lcs_finds_l1_overlaps_and_outputs_to_l1(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            compaction_strategy="lcs",
            l0_compaction_trigger_tables=2,
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
        )
    )

    l1_meta = sim.sstable.write_table(
        level=1,
        records=[
            Record(key="m", value="1", seq=1),
            Record(key="z", value="2", seq=2),
        ],
    )
    sim.level_tables.setdefault(1, []).append(l1_meta)

    sim.put("a", "v1")
    sim.flush_memtable()
    sim.put("x", "v2")
    sim.flush_memtable()

    result = sim.compaction_history[0]
    assert l1_meta.table_id in result.input_table_ids
    assert len(sim.level_tables.get(1, [])) == 1
    output = sim.level_tables[1][0]
    assert output.table_id == result.output_table_id


def test_lcs_higher_level_pushdown_simplified(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            compaction_strategy="lcs",
            l0_compaction_trigger_tables=2,
            level_size_multiplier=1.01,
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
            max_levels=4,
        )
    )

    # 6 flushes -> 3 L0->L1 compactions (threshold=2), then L1 over limit (2) and pushdown to L2.
    for i in range(6):
        sim.put(f"k{i}", f"v{i}")
        sim.flush_memtable()

    assert any(item.target_level == 2 for item in sim.compaction_history)


def test_stc_and_lcs_behave_differently_on_same_workload(tmp_path: Path) -> None:
    stc_sim = LSMSimulator(
        LSMConfig(
            compaction_strategy="stc",
            stc_trigger_tables=3,
            wal_dir=str(tmp_path / "stc_wal"),
            data_dir=str(tmp_path / "stc_data"),
        )
    )
    lcs_sim = LSMSimulator(
        LSMConfig(
            compaction_strategy="lcs",
            l0_compaction_trigger_tables=3,
            wal_dir=str(tmp_path / "lcs_wal"),
            data_dir=str(tmp_path / "lcs_data"),
        )
    )

    pre_l1 = lcs_sim.sstable.write_table(
        level=1,
        records=[Record(key="k1", value="base", seq=1)],
    )
    lcs_sim.level_tables.setdefault(1, []).append(pre_l1)

    for sim in [stc_sim, lcs_sim]:
        sim.put("k1", "v1")
        sim.flush_memtable()
        sim.put("k2", "v2")
        sim.flush_memtable()
        sim.put("k3", "v3")
        sim.flush_memtable()

    stc_inputs = stc_sim.compaction_history[0].input_table_ids
    lcs_inputs = lcs_sim.compaction_history[0].input_table_ids

    # STC compacts only selected source-level files, while LCS includes overlapped next-level files.
    assert len(stc_inputs) == 3
    assert len(lcs_inputs) == 4


def test_both_strategies_run_core_put_flush_get_flow(tmp_path: Path) -> None:
    stc = LSMSimulator(
        LSMConfig(
            compaction_strategy="stc",
            stc_trigger_tables=2,
            wal_dir=str(tmp_path / "stc_wal"),
            data_dir=str(tmp_path / "stc_data"),
        )
    )
    lcs = LSMSimulator(
        LSMConfig(
            compaction_strategy="lcs",
            l0_compaction_trigger_tables=2,
            wal_dir=str(tmp_path / "lcs_wal"),
            data_dir=str(tmp_path / "lcs_data"),
        )
    )

    for sim in [stc, lcs]:
        sim.put("x", "1")
        sim.flush_memtable()
        sim.put("x", "2")
        sim.flush_memtable()
        result = sim.get("x")
        assert result.found is True
        assert result.value == "2"
