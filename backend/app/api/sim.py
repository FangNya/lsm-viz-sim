from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.runtime import service
from app.schemas import LSMConfig
from app.schemas.api import (
    ConfigResponse,
    ExportTraceResponse,
    ResetResponse,
    RunWorkloadRequest,
    RunWorkloadResponse,
    SimulatorStateResponse,
    StepRequest,
    StepResponse,
)

router = APIRouter(prefix="/sim", tags=["simulator"])
ws_router = APIRouter(tags=["simulator"])


@router.post("/reset", response_model=ResetResponse)
async def reset_simulator() -> ResetResponse:
    service.reset()
    await service.broadcaster.broadcast({"type": "simulator_reset", "payload": {"status": "ok"}})
    return ResetResponse(status="ok")


@router.post("/config", response_model=ConfigResponse)
async def configure_simulator(config: LSMConfig) -> ConfigResponse:
    service.set_config(config)
    await service.broadcaster.broadcast(
        {"type": "config_updated", "payload": config.model_dump(mode="json")}
    )
    return ConfigResponse(status="ok", config=config)


@router.post("/run_workload", response_model=RunWorkloadResponse)
async def run_workload(request: RunWorkloadRequest) -> RunWorkloadResponse:
    executions = service.run_workload(request.operations)

    for exec_result in executions:
        for event in exec_result.new_events:
            await service.broadcaster.broadcast(
                {"type": "trace_event", "payload": event.model_dump(mode="json")}
            )
        await service.broadcaster.broadcast(
            {
                "type": "metrics_update",
                "payload": exec_result.metrics.model_dump(mode="json"),
            }
        )

    return RunWorkloadResponse(executed=len(executions), step_results=[e.response for e in executions])


@router.post("/step", response_model=StepResponse)
async def run_step(request: StepRequest) -> StepResponse:
    execution = service.run_step(request.operation)

    for event in execution.new_events:
        await service.broadcaster.broadcast({"type": "trace_event", "payload": event.model_dump(mode="json")})
    await service.broadcaster.broadcast(
        {"type": "metrics_update", "payload": execution.metrics.model_dump(mode="json")}
    )

    return execution.response


@router.get("/state", response_model=SimulatorStateResponse)
def get_state() -> SimulatorStateResponse:
    data = service.state()
    return SimulatorStateResponse(**data)


@router.get("/export/trace", response_model=ExportTraceResponse)
def export_trace(format: str = Query(default="json", pattern="^(json|csv)$")) -> ExportTraceResponse:
    out = service.export_trace(format)
    content = Path(out).read_text(encoding="utf-8")
    return ExportTraceResponse(format=format, content=content)


@ws_router.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    await service.broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        service.broadcaster.disconnect(websocket)
