from __future__ import annotations

from app.core.compaction.base import CompactionResult, CompactionStrategyBase
from app.schemas import CompactionStrategy, Record, SSTableMeta


class LCSCompactionStrategy(CompactionStrategyBase):
    """Teaching-oriented simplified Leveled Compaction Strategy (LCS)."""

    def should_trigger(self, simulator: "LSMSimulator", level: int) -> bool:
        tables = simulator.level_tables.get(level, [])
        if level == 0:
            return len(tables) >= simulator.config.l0_compaction_trigger_tables

        limit = self._level_limit(simulator, level)
        return len(tables) > limit

    def select_inputs(self, simulator: "LSMSimulator", level: int) -> list[SSTableMeta]:
        if level == 0:
            return list(simulator.level_tables.get(0, []))

        level_tables = simulator.level_tables.get(level, [])
        if not level_tables:
            return []
        return [level_tables[0]]

    def compact(self, simulator: "LSMSimulator", level: int) -> CompactionResult:
        source_inputs = self.select_inputs(simulator, level)
        if not source_inputs:
            raise ValueError("no input tables selected for LCS compaction")

        target_level = level + 1
        before = simulator.list_levels()

        overlaps = self.find_overlaps(simulator, source_inputs, target_level)
        all_inputs = source_inputs + overlaps

        latest_by_key: dict[str, Record] = {}
        for meta in all_inputs:
            for record in simulator.sstable.read_records(meta):
                current = latest_by_key.get(record.key)
                if current is None or record.seq > current.seq:
                    latest_by_key[record.key] = record

        merged_records = [latest_by_key[key] for key in sorted(latest_by_key.keys())]
        output_meta = simulator.sstable.write_table(target_level, merged_records)

        source_ids = {meta.table_id for meta in source_inputs}
        target_ids = {meta.table_id for meta in overlaps}

        simulator.level_tables[level] = [
            meta for meta in simulator.level_tables.get(level, []) if meta.table_id not in source_ids
        ]
        simulator.level_tables[target_level] = [
            meta for meta in simulator.level_tables.get(target_level, []) if meta.table_id not in target_ids
        ]

        for meta in all_inputs:
            simulator.sstable.delete_table_files(meta)

        simulator.level_tables.setdefault(target_level, []).append(output_meta)

        after = simulator.list_levels()
        return CompactionResult(
            strategy=CompactionStrategy.LCS.value,
            source_level=level,
            target_level=target_level,
            input_table_ids=[meta.table_id for meta in all_inputs],
            output_table_id=output_meta.table_id,
            before_levels=before,
            after_levels=after,
        )

    def find_overlaps(
        self,
        simulator: "LSMSimulator",
        source_tables: list[SSTableMeta],
        target_level: int,
    ) -> list[SSTableMeta]:
        target_tables = simulator.level_tables.get(target_level, [])
        if not source_tables or not target_tables:
            return []

        min_key = min(meta.min_key for meta in source_tables)
        max_key = max(meta.max_key for meta in source_tables)

        overlaps: list[SSTableMeta] = []
        for meta in target_tables:
            if not (meta.max_key < min_key or meta.min_key > max_key):
                overlaps.append(meta)
        return overlaps

    def _level_limit(self, simulator: "LSMSimulator", level: int) -> int:
        base = simulator.config.l0_compaction_trigger_tables
        return max(1, int(base * (simulator.config.level_size_multiplier ** level)))


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.simulator import LSMSimulator
