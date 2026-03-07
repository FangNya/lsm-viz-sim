from fastapi import FastAPI


app = FastAPI(title="LSM-Tree Simulator API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}