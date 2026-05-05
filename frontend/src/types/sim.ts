export type CompactionStrategy = "stc" | "lcs";

export interface LSMConfig {
  memtable_max_records: number;
  memtable_max_bytes: number;
  max_levels: number;
  compaction_strategy: CompactionStrategy;
  stc_trigger_tables: number;
  l0_compaction_trigger_tables: number;
  level_size_multiplier: number;
  bloom_bits_per_key: number;
  wal_dir: string;
  data_dir: string;
}

export interface WorkloadOperation {
  op: "put";
  key: string;
  value: string;
}

export interface StepResponse {
  op: "put";
  put_result: {
    success: boolean;
    seq: number;
    needs_flush: boolean;
    memtable_size_records: number;
    memtable_size_bytes: number;
  };
  flushed_table_id: string | null;
}

export interface RunWorkloadResponse {
  executed: number;
  step_results: StepResponse[];
}

export interface MetricsSnapshot {
  total_puts: number;
  total_gets: number;
  memtable_size_records: number;
  memtable_size_bytes: number;
  sstable_count_by_level: Record<string, number>;
  flush_count: number;
  compaction_count: number;
  read_amplification: number;
  write_amplification: number;
  logical_write_bytes_total: number;
  wal_write_bytes_total: number;
  flush_data_write_bytes_total: number;
  flush_meta_write_bytes_total: number;
  flush_bloom_write_bytes_total: number;
  compaction_data_write_bytes_total: number;
  compaction_meta_write_bytes_total: number;
  compaction_bloom_write_bytes_total: number;
  actual_disk_write_bytes_total: number;
  user_query_read_io_total: number;
  bloom_read_io_total: number;
  index_read_io_total: number;
  data_block_read_io_total: number;
}

export interface TraceEvent {
  event_id: string;
  event_type: string;
  timestamp: string;
  seq: number;
  payload: Record<string, unknown>;
}

export interface SimulatorState {
  config: LSMConfig;
  levels: Record<string, SSTableMeta[]>;
  metrics: MetricsSnapshot;
  recent_events: TraceEvent[];
}

export interface SSTableMeta {
  table_id: string;
  level: number;
  min_key: string;
  max_key: string;
  record_count: number;
  data_file: string;
  meta_file: string;
  bloom_file?: string | null;
  size_bytes: number;
  created_at: string;
}

export interface WsMessage {
  type: "trace_event" | "metrics_update" | "simulator_reset" | "config_updated";
  payload: any;
}
