from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import CompactionTask, LSMConfig, MetricsSnapshot


@dataclass(slots=True)
class LevelState:
    """Runtime summary of a single level (teaching-oriented state)."""

    level: int
    table_ids: list[str] = field(default_factory=list)
    total_size_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "table_ids": list(self.table_ids),
            "table_count": len(self.table_ids),
            "total_size_bytes": self.total_size_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LevelState":
        return cls(
            level=int(data["level"]),
            table_ids=list(data.get("table_ids", [])),
            total_size_bytes=int(data.get("total_size_bytes", 0)),
        )


@dataclass(slots=True)
class SimulatorState:
    """Top-level runtime state contract shared between modules."""

    config: LSMConfig
    current_seq: int = 0
    levels: list[LevelState] = field(default_factory=list)
    metrics: MetricsSnapshot = field(default_factory=MetricsSnapshot)
    pending_compaction: CompactionTask | None = None

    def to_dict(self) -> dict:
        return {
            "config": self.config.model_dump(mode="json"),
            "current_seq": self.current_seq,
            "levels": [level.to_dict() for level in self.levels],
            "metrics": self.metrics.model_dump(mode="json"),
            "pending_compaction": (
                None
                if self.pending_compaction is None
                else self.pending_compaction.model_dump(mode="json")
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimulatorState":
        return cls(
            config=LSMConfig.model_validate(data["config"]),
            current_seq=int(data.get("current_seq", 0)),
            levels=[LevelState.from_dict(item) for item in data.get("levels", [])],
            metrics=MetricsSnapshot.model_validate(data.get("metrics", {})),
            pending_compaction=(
                None
                if data.get("pending_compaction") is None
                else CompactionTask.model_validate(data["pending_compaction"])
            ),
        )
