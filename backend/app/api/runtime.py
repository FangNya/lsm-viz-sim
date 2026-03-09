from __future__ import annotations

from threading import Lock

from fastapi import WebSocket

from app.core import LSMSimulator
from app.schemas import LSMConfig, MetricsSnapshot, TraceEvent, WorkloadOperation
from app.schemas.api import StepResponse


class EventBroadcaster:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


class StepExecution:
    """Internal helper object for API orchestration."""

    def __init__(self, response: StepResponse, new_events: list[TraceEvent], metrics: MetricsSnapshot):
        self.response = response
        self.new_events = new_events
        self.metrics = metrics


class SimulatorService:
    """Thin orchestration layer between API and core simulator."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._config = LSMConfig()
        self._sim = LSMSimulator(self._config)
        self.broadcaster = EventBroadcaster()

    @property
    def config(self) -> LSMConfig:
        return self._config

    @property
    def simulator(self) -> LSMSimulator:
        return self._sim

    def reset(self) -> None:
        with self._lock:
            self._sim = LSMSimulator(self._config)

    def set_config(self, config: LSMConfig) -> None:
        with self._lock:
            self._config = config
            self._sim = LSMSimulator(config)

    def run_step(self, operation: WorkloadOperation) -> StepExecution:
        with self._lock:
            event_start = len(self._sim.trace.events)
            op_name = str(operation.op)
            if op_name != "put":
                raise ValueError("only put operation is supported in current stage")

            put_result = self._sim.put(operation.key, operation.value)
            flushed_table_id: str | None = None
            if put_result.needs_flush:
                flushed = self._sim.flush_memtable()
                flushed_table_id = None if flushed is None else flushed.table_id

            new_events = self._sim.trace.events[event_start:]
            response = StepResponse(op="put", put_result=put_result.to_dict(), flushed_table_id=flushed_table_id)
            metrics = MetricsSnapshot.model_validate(self._sim.metrics.snapshot.model_dump(mode="json"))
            return StepExecution(response=response, new_events=new_events, metrics=metrics)

    def run_workload(self, operations: list[WorkloadOperation]) -> list[StepExecution]:
        return [self.run_step(op) for op in operations]

    def state(self, recent_event_limit: int = 50) -> dict:
        with self._lock:
            events = self._sim.trace.events[-recent_event_limit:]
            return {
                "config": self._config,
                "levels": self._sim.list_levels(),
                "metrics": MetricsSnapshot.model_validate(self._sim.metrics.snapshot.model_dump(mode="json")),
                "recent_events": events,
            }

    def export_trace(self, fmt: str) -> str:
        with self._lock:
            export_dir = self._sim.sstable.data_root / "exports"
            if fmt == "json":
                out = self._sim.export_trace_json(str(export_dir / "trace.json"))
            elif fmt == "csv":
                out = self._sim.export_trace_csv(str(export_dir / "trace.csv"))
            else:
                raise ValueError("format must be json or csv")

        return out


service = SimulatorService()
