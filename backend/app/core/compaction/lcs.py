from __future__ import annotations

from bisect import bisect_left

from app.core.compaction.base import CompactionResult, CompactionStrategyBase
from app.schemas import CompactionStrategy, Record, SSTableMeta


class LCSCompactionStrategy(CompactionStrategyBase):
    """Teaching-oriented simplified Leveled Compaction Strategy (LCS)."""

    @staticmethod
    def sort_tables_by_key_range(tables: list[SSTableMeta]) -> list[SSTableMeta]:
        return sorted(tables, key=lambda meta: (meta.min_key, meta.max_key, meta.table_id))

    def should_trigger(self, simulator: "LSMSimulator", level: int) -> bool:
        tables = simulator.level_tables.get(level, [])
        if level == 0:
            return len(tables) >= simulator.config.l0_compaction_trigger_tables

        capacity = self._level_record_capacity(simulator, level)
        return self._level_record_total(tables) > capacity

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

        simulator.level_tables[target_level] = self.sort_tables_by_key_range(
            simulator.level_tables.get(target_level, []) + [output_meta]
        )

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

    def _level_record_capacity(self, simulator: "LSMSimulator", level: int) -> int:
        base_run_records = simulator.config.memtable_max_records
        l0_capacity = base_run_records * simulator.config.l0_compaction_trigger_tables
        return max(1, int(l0_capacity * (simulator.config.level_size_multiplier ** level)))

    @staticmethod
    def _level_record_total(tables: list[SSTableMeta]) -> int:
        return sum(meta.record_count for meta in tables)

    def find_candidate_tables(
        self,
        simulator: "LSMSimulator",
        level: int,
        key: str,
    ) -> list[SSTableMeta]:
        if level <= 0:
            return list(reversed(simulator.level_tables.get(level, [])))

        tables = self.sort_tables_by_key_range(simulator.level_tables.get(level, []))
        simulator.level_tables[level] = tables
        if not tables:
            return []

        min_keys = [meta.min_key for meta in tables]
        probe = bisect_left(min_keys, key)
        candidate_indexes = {probe - 1, probe}

        candidates: list[SSTableMeta] = []
        seen_ids: set[str] = set()
        for index in sorted(candidate_indexes):
            if index < 0 or index >= len(tables):
                continue
            meta = tables[index]
            if meta.min_key <= key <= meta.max_key and meta.table_id not in seen_ids:
                candidates.append(meta)
                seen_ids.add(meta.table_id)

                left = index - 1
                while left >= 0 and tables[left].max_key >= key:
                    if tables[left].min_key <= key <= tables[left].max_key:
                        if tables[left].table_id not in seen_ids:
                            candidates.insert(0, tables[left])
                            seen_ids.add(tables[left].table_id)
                    left -= 1

                right = index + 1
                while right < len(tables) and tables[right].min_key <= key:
                    if tables[right].min_key <= key <= tables[right].max_key:
                        if tables[right].table_id not in seen_ids:
                            candidates.append(tables[right])
                            seen_ids.add(tables[right].table_id)
                    right += 1

        return candidates


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.simulator import LSMSimulator
