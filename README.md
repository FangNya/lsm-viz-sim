# LSM-Tree Visual Simulator (Teaching Prototype)

This repository is the monorepo scaffold for a teaching-oriented LSM-Tree simulator.
Current task scope only includes project skeleton and health check.

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