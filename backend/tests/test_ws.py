from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app


client = TestClient(app)


def test_ws_receives_key_event(tmp_path: Path) -> None:
    config_resp = client.post(
        "/sim/config",
        json={
            "memtable_max_records": 10,
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
    assert config_resp.status_code == 200
    client.post("/sim/reset")

    with client.websocket_connect("/ws/events") as ws:
        step_resp = client.post(
            "/sim/step",
            json={"operation": {"op": "put", "key": "ws_k", "value": "ws_v"}},
        )
        assert step_resp.status_code == 200

        msg = ws.receive_json()
        assert msg["type"] in ["trace_event", "metrics_update"]
