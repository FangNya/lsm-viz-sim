from __future__ import annotations

from app.core.compaction.base import CompactionResult, CompactionStrategyBase
from app.schemas import CompactionStrategy, Record


class STCCompactionStrategy(CompactionStrategyBase):
    """Teaching-oriented simplified Size-Tiered Compaction (STC)."""

    def should_trigger(self, simulator: "LSMSimulator", level: int) -> bool:
        return len(simulator.level_tables.get(level, [])) >= simulator.config.stc_trigger_tables

    def select_inputs(self, simulator: "LSMSimulator", level: int) -> list:
        # STC simplified rule: select earliest-created tables from this level.
        return list(simulator.level_tables.get(level, []))[: simulator.config.stc_trigger_tables]

    def compact(self, simulator: "LSMSimulator", level: int) -> CompactionResult:
        inputs = self.select_inputs(simulator, level)
        if not inputs:
            raise ValueError("no input tables selected for compaction")

        before = simulator.list_levels()
        target_level = level + 1

        latest_by_key: dict[str, Record] = {}
        for meta in inputs:
            records = simulator.sstable.read_records(meta)
            for record in records:
                current = latest_by_key.get(record.key)
                if current is None or record.seq > current.seq:
                    latest_by_key[record.key] = record

        merged_records = [latest_by_key[key] for key in sorted(latest_by_key.keys())]
        output_meta = simulator.sstable.write_table(target_level, merged_records)

        source_tables = simulator.level_tables.setdefault(level, [])
        input_ids = {meta.table_id for meta in inputs}
        simulator.level_tables[level] = [meta for meta in source_tables if meta.table_id not in input_ids]

        for meta in inputs:
            simulator.sstable.delete_table_files(meta)

        simulator.level_tables.setdefault(target_level, []).append(output_meta)

        after = simulator.list_levels()

        return CompactionResult(
            strategy=CompactionStrategy.STC.value,
            source_level=level,
            target_level=target_level,
            input_table_ids=[meta.table_id for meta in inputs],
            output_table_id=output_meta.table_id,
            before_levels=before,
            after_levels=after,
        )


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.simulator import LSMSimulator
