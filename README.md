# LSM-Tree Visual Simulator (Teaching Prototype)

This repository is the monorepo scaffold for a teaching-oriented LSM-Tree simulator.
Current task scope only includes project skeleton and health check.

## Current Stage Notes

- WAL is append-only JSONL in current stage; recovery/replay is intentionally not implemented yet.
- MemTable is a teaching-oriented simplified implementation based on Python `dict` (not skiplist).
- SSTable uses teaching-format files: data as JSONL and metadata as JSON.
- Current flush implementation only writes to `level_0` (no multi-level scheduling yet).
- Read path supports memtable + SSTable lookup, with per-SSTable Bloom filter fast skip.
- STC compaction is a teaching-oriented simplified implementation, triggered synchronously after flush (not background async tasks).
- LCS compaction is also a teaching-oriented simplified implementation; omitted industrial features include seek-based trigger, advanced file picking heuristics, and tombstone-aware handling.
- Metrics and trace are collected in-process, with stable JSON/CSV export for experiments.

## Structure

- `backend/`: FastAPI service
- `frontend/`: Vue 3 + TypeScript + Vite app
- `docs/`: project docs
- `experiments/`: reproducible experiment outputs

## Backend

### Run locally

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### API Endpoints

- `POST /sim/reset`
- `POST /sim/config`
- `POST /sim/run_workload`
- `POST /sim/step`
- `GET /sim/state`
- `GET /sim/export/trace?format=json|csv`
- `WS /ws/events`

### Example requests

Set config:

```bash
curl -X POST http://127.0.0.1:8000/sim/config \
  -H "Content-Type: application/json" \
  -d '{
    "memtable_max_records": 2,
    "memtable_max_bytes": 1024,
    "max_levels": 4,
    "compaction_strategy": "stc",
    "stc_trigger_tables": 2,
    "l0_compaction_trigger_tables": 2,
    "level_size_multiplier": 10.0,
    "bloom_bits_per_key": 10,
    "wal_dir": "./data/wal",
    "data_dir": "./data/sst"
  }'
```

Run workload:

```bash
curl -X POST http://127.0.0.1:8000/sim/run_workload \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [
      {"op": "put", "key": "k1", "value": "v1"},
      {"op": "put", "key": "k2", "value": "v2"}
    ]
  }'
```

Get state:

```bash
curl http://127.0.0.1:8000/sim/state
```

### WebSocket

Connect to `ws://127.0.0.1:8000/ws/events`.
Server pushes messages like:

```json
{"type":"trace_event","payload":{...}}
```

```json
{"type":"metrics_update","payload":{...}}
```

### Test

```bash
cd backend
pytest
```

## Frontend

### Run locally

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` and verify page title `LSM-Tree Simulator`.

This frontend is the midterm minimum demo page: feature completeness first, visual polish can be iterated later.

### Build

```bash
cd frontend
npm install
npm run build
```

## Docker Compose

```bash
docker compose up --build
```

- Backend: `http://127.0.0.1:8000/health`
- Frontend: `http://127.0.0.1:5173`

