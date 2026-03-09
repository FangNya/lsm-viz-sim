# Task 8: Metrics Collection and Trace Export

This task adds a unified metrics collector and trace emitter for the simulator runtime.

## Event Names

Supported trace events:
- `put`
- `flush_start`
- `flush_end`
- `sstable_created`
- `compaction_start`
- `compaction_end`
- `get`
- `bloom_hit`
- `bloom_miss`

## Event Payload Structure

Common fields come from `TraceEvent`:
- `event_id`: UUID string
- `event_type`: one of the names above
- `timestamp`: UTC ISO-8601 string
- `seq`: simulator sequence marker
- `payload`: event-specific object

Payload examples:
- `put`: `{ key, value_size, wal_file }`
- `flush_start`: `{ input_records, target_level }`
- `flush_end`: `{ table_id, level }`
- `sstable_created`: `{ table_id, level, ... }`
- `compaction_start`: `{ strategy, source_level, target_level, input_table_ids }`
- `compaction_end`: `{ strategy, source_level, target_level, input_table_ids, output_table_id }`
- `get`: `{ key, found, source, level, table_id, path, value }`
- `bloom_hit` / `bloom_miss`: `{ key, level, table_id }`

## Metrics Definitions

All metrics are exposed via `MetricsSnapshot` and updated online.

Actual counters:
- `total_puts`: count of completed `put` operations
- `total_gets`: count of completed `get` operations
- `flush_count`: count of completed flush operations
- `compaction_count`: count of completed compaction operations
- `memtable_size_records`: current unique keys in MemTable
- `memtable_size_bytes`: current approximate MemTable bytes
- `sstable_count_by_level`: current SSTable counts for each level

Simulated statistics:
- `simulated_io_reads`: simulated storage reads from bloom checks / SSTable scans / compaction inputs
- `simulated_io_writes`: simulated storage writes from WAL append / flush / compaction output

Derived metrics:
- `read_amplification = simulated_io_reads / total_gets` (0 if `total_gets == 0`)
- `write_amplification = simulated_io_writes / total_puts` (0 if `total_puts == 0`)

## Export Formats

- Metrics JSON: `{ snapshot, history }`
- Metrics CSV: stable header with all metric columns
- Trace JSON: list of `TraceEvent` objects
- Trace CSV: stable header `event_id,event_type,timestamp,seq,payload_json`
