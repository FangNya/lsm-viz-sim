from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app


client = TestClient(app)


def _set_temp_config(tmp_path: Path) -> None:
    resp = client.post(
        "/sim/config",
        json={
            "memtable_max_records": 2,
            "memtable_max_bytes": 1024,
            "max_levels": 4,
            "compaction_strategy": "stc",
            "stc_trigger_tables": 2,
            "l0_compaction_trigger_tables": 2,
            "level_size_multiplier": 10.0,
            "bloom_bits_per_key": 10,
            "wal_dir": str(tmp_path / "wal"),
            "data_dir": str(tmp_path / "data"),
        },
    )
    assert resp.status_code == 200


def test_sim_config_and_reset(tmp_path: Path) -> None:
    _set_temp_config(tmp_path)

    state = client.get("/sim/state")
    assert state.status_code == 200
    payload = state.json()
    assert payload["config"]["wal_dir"].endswith("wal")

    reset = client.post("/sim/reset")
    assert reset.status_code == 200
    assert reset.json()["status"] == "ok"


def test_run_workload_and_state_metrics(tmp_path: Path) -> None:
    _set_temp_config(tmp_path)
    client.post("/sim/reset")

    workload = {
        "operations": [
            {"op": "put", "key": "k1", "value": "v1"},
            {"op": "put", "key": "k2", "value": "v2"},
            {"op": "put", "key": "k3", "value": "v3"},
        ]
    }
    run_resp = client.post("/sim/run_workload", json=workload)
    assert run_resp.status_code == 200
    run_payload = run_resp.json()
    assert run_payload["executed"] == 3
    assert len(run_payload["step_results"]) == 3

    state = client.get("/sim/state")
    assert state.status_code == 200
    s = state.json()
    assert "level_0" in s["levels"]
    assert "total_puts" in s["metrics"]
    assert s["metrics"]["total_puts"] >= 3


def test_export_trace_json_and_csv(tmp_path: Path) -> None:
    _set_temp_config(tmp_path)
    client.post("/sim/reset")
    client.post("/sim/step", json={"operation": {"op": "put", "key": "x", "value": "1"}})

    export_json = client.get("/sim/export/trace", params={"format": "json"})
    assert export_json.status_code == 200
    json_payload = export_json.json()
    assert json_payload["format"] == "json"
    assert "event_type" in json_payload["content"]

    export_csv = client.get("/sim/export/trace", params={"format": "csv"})
    assert export_csv.status_code == 200
    csv_payload = export_csv.json()
    assert csv_payload["format"] == "csv"
    assert "event_id,event_type,timestamp,seq,payload_json" in csv_payload["content"]
