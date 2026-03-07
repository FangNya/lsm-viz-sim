from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LevelState, SimulatorState
from app.schemas import (
    CompactionStrategy,
    CompactionTask,
    LSMConfig,
    MetricsSnapshot,
    Record,
    SSTableMeta,
    WALRecord,
    WorkloadOperation,
)


def test_lsm_config_defaults_and_enum_serialization() -> None:
    cfg = LSMConfig()

    assert cfg.compaction_strategy == "stc"
    assert cfg.memtable_max_records == 1000
    assert cfg.max_levels == 4
    assert cfg.model_dump(mode="json")["compaction_strategy"] == "stc"


def test_lsm_config_rejects_invalid_compaction_strategy() -> None:
    with pytest.raises(ValidationError):
        LSMConfig(compaction_strategy="invalid")


def test_record_and_wal_record_reject_invalid_op() -> None:
    with pytest.raises(ValidationError):
        Record(key="k", value="v", seq=1, op="delete")

    with pytest.raises(ValidationError):
        WALRecord(key="k", value="v", seq=1, op="get")


def test_sstable_meta_roundtrip_json_serialization() -> None:
    meta = SSTableMeta(
        table_id="sst_001",
        level=0,
        data_file="./data/sst/sst_001.jsonl",
        meta_file="./data/sst/sst_001.meta.json",
        min_key="a",
        max_key="z",
        record_count=100,
        size_bytes=2048,
    )

    dumped = meta.model_dump(mode="json")
    loaded = SSTableMeta.model_validate(dumped)

    assert loaded.table_id == "sst_001"
    assert loaded.bloom_file is None


def test_metrics_snapshot_defaults() -> None:
    snapshot = MetricsSnapshot()

    assert snapshot.total_puts == 0
    assert snapshot.total_gets == 0
    assert snapshot.sstable_count_by_level == {}
    assert snapshot.read_amplification == 1.0
    assert snapshot.write_amplification == 1.0


def test_workload_and_compaction_enum_constraints() -> None:
    op = WorkloadOperation(key="k1", value="v1")
    task = CompactionTask(
        strategy=CompactionStrategy.LCS,
        source_level=0,
        target_level=1,
        input_table_ids=["sst_001"],
        reason="L0 overflow",
    )

    assert op.op == "put"
    assert task.model_dump(mode="json")["strategy"] == "lcs"


def test_simulator_state_dataclass_roundtrip() -> None:
    state = SimulatorState(
        config=LSMConfig(),
        current_seq=7,
        levels=[LevelState(level=0, table_ids=["sst_1"], total_size_bytes=128)],
    )

    serialized = state.to_dict()
    restored = SimulatorState.from_dict(serialized)

    assert restored.current_seq == 7
    assert restored.levels[0].to_dict()["table_count"] == 1
    assert restored.metrics.total_puts == 0