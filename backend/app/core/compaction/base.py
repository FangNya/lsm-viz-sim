from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas import SSTableMeta


@dataclass(slots=True)
class CompactionResult:
    strategy: str
    source_level: int
    target_level: int
    input_table_ids: list[str]
    output_table_id: str
    before_levels: dict[str, list[dict]]
    after_levels: dict[str, list[dict]]


class CompactionStrategyBase(ABC):
    """Base contract for teaching compaction strategies."""

    @abstractmethod
    def should_trigger(self, simulator: "LSMSimulator", level: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def select_inputs(self, simulator: "LSMSimulator", level: int) -> list[SSTableMeta]:
        raise NotImplementedError

    @abstractmethod
    def compact(self, simulator: "LSMSimulator", level: int) -> CompactionResult:
        raise NotImplementedError


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.simulator import LSMSimulator
