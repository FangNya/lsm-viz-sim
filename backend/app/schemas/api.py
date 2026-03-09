from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.models import LSMConfig, MetricsSnapshot, TraceEvent, WorkloadOperation


class RunWorkloadRequest(BaseModel):
    operations: list[WorkloadOperation] = Field(default_factory=list)


class StepRequest(BaseModel):
    operation: WorkloadOperation


class StepResponse(BaseModel):
    op: Literal["put"]
    put_result: dict
    flushed_table_id: str | None = None


class RunWorkloadResponse(BaseModel):
    executed: int
    step_results: list[StepResponse]


class SimulatorStateResponse(BaseModel):
    config: LSMConfig
    levels: dict[str, list[dict]]
    metrics: MetricsSnapshot
    recent_events: list[TraceEvent]


class ResetResponse(BaseModel):
    status: str


class ConfigResponse(BaseModel):
    status: str
    config: LSMConfig


class ExportTraceResponse(BaseModel):
    format: Literal["json", "csv"]
    content: str
