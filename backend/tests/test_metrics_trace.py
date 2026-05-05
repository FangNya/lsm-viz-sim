from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core import LSMSimulator
from app.schemas import LSMConfig


def test_trace_contains_required_events_for_core_flow(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
            stc_trigger_tables=2,
            memtable_max_records=100,
        )
    )

    sim.put("k1", "v1")
    sim.flush_memtable()
    sim.put("k2", "v2")
    sim.flush_memtable()  # triggers compaction with stc_trigger_tables=2
    sim.get("k1")
    sim.get("missing")

    names = [event.event_type for event in sim.trace.events]

    for required in [
        "put",
        "flush_start",
        "flush_end",
        "sstable_created",
        "compaction_start",
        "compaction_end",
        "get",
        "bloom_hit",
        "bloom_miss",
    ]:
        assert required in names


def test_metrics_accumulate_correctly(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
            stc_trigger_tables=2,
        )
    )

    sim.put("a", "1")
    sim.flush_memtable()
    sim.put("b", "2")
    sim.flush_memtable()
    sim.get("a")
    sim.get("missing")

    snapshot = sim.metrics.snapshot
    assert snapshot.total_puts == 2
    assert snapshot.total_gets == 2
    assert snapshot.flush_count == 2
    assert snapshot.compaction_count >= 1
    assert snapshot.memtable_size_records == 0
    assert isinstance(snapshot.sstable_count_by_level, dict)
    assert snapshot.logical_write_bytes_total == 4
    assert snapshot.wal_write_bytes_total > 0
    assert snapshot.actual_disk_write_bytes_total >= snapshot.wal_write_bytes_total


def test_export_json_readable(tmp_path: Path) -> None:
    sim = LSMSimulator(LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data")))
    sim.put("k", "v")
    sim.flush_memtable()
    sim.get("k")

    metrics_json = Path(sim.export_metrics_json(str(tmp_path / "exports" / "metrics.json")))
    trace_json = Path(sim.export_trace_json(str(tmp_path / "exports" / "trace.json")))

    metrics_payload = json.loads(metrics_json.read_text(encoding="utf-8"))
    trace_payload = json.loads(trace_json.read_text(encoding="utf-8"))

    assert "snapshot" in metrics_payload
    assert "history" in metrics_payload
    assert isinstance(trace_payload, list)
    assert len(trace_payload) > 0


def test_export_csv_headers_stable(tmp_path: Path) -> None:
    sim = LSMSimulator(LSMConfig(wal_dir=str(tmp_path / "wal"), data_dir=str(tmp_path / "data")))
    sim.put("k", "v")
    sim.flush_memtable()
    sim.get("missing")

    metrics_csv = Path(sim.export_metrics_csv(str(tmp_path / "exports" / "metrics.csv")))
    trace_csv = Path(sim.export_trace_csv(str(tmp_path / "exports" / "trace.csv")))

    with metrics_csv.open("r", encoding="utf-8") as f:
        header = f.readline().strip()
    with trace_csv.open("r", encoding="utf-8") as f:
        trace_header = f.readline().strip()

    assert header == (
        "timestamp,reason,total_puts,total_gets,memtable_size_records,memtable_size_bytes,"
        "sstable_count_by_level,flush_count,compaction_count,read_amplification,"
        "write_amplification,logical_write_bytes_total,wal_write_bytes_total,"
        "flush_data_write_bytes_total,flush_meta_write_bytes_total,flush_bloom_write_bytes_total,"
        "compaction_data_write_bytes_total,compaction_meta_write_bytes_total,"
        "compaction_bloom_write_bytes_total,actual_disk_write_bytes_total,"
        "user_query_read_io_total,bloom_read_io_total,index_read_io_total,data_block_read_io_total"
    )
    assert trace_header == "event_id,event_type,timestamp,seq,payload_json"


def test_amplification_formula_matches_documented_logic(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
            stc_trigger_tables=2,
        )
    )

    sim.put("k1", "v1")
    sim.flush_memtable()
    sim.put("k2", "v2")
    sim.flush_memtable()
    sim.get("k1")
    sim.get("missing")

    s = sim.metrics.snapshot
    expected_ra = s.user_query_read_io_total / s.total_gets if s.total_gets > 0 else 0.0
    expected_wa = (
        s.actual_disk_write_bytes_total / s.logical_write_bytes_total
        if s.logical_write_bytes_total > 0
        else 0.0
    )

    assert s.read_amplification == pytest.approx(expected_ra)
    assert s.write_amplification == pytest.approx(expected_wa)


def test_compaction_does_not_increase_query_read_metrics_before_get(tmp_path: Path) -> None:
    sim = LSMSimulator(
        LSMConfig(
            wal_dir=str(tmp_path / "wal"),
            data_dir=str(tmp_path / "data"),
            stc_trigger_tables=2,
        )
    )

    sim.put("k1", "v1")
    sim.flush_memtable()
    sim.put("k2", "v2")
    sim.flush_memtable()

    s = sim.metrics.snapshot

    assert s.compaction_count >= 1
    assert s.total_gets == 0
    assert s.user_query_read_io_total == 0
    assert s.read_amplification == 0.0
