from fastapi import FastAPI

from app.api.sim import router as sim_router
from app.api.sim import ws_router


app = FastAPI(title="LSM-Tree Simulator API")
app.include_router(sim_router)
app.include_router(ws_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
