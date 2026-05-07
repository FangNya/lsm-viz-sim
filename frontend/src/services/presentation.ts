import type { MetricsSnapshot, SSTableMeta, TraceEvent } from "../types/sim";

export interface LevelBucket {
  id: number;
  label: string;
  tables: SSTableMeta[];
  tableCount: number;
  totalRecords: number;
  maxTableRecords: number;
}

const EVENT_LABELS: Record<string, string> = {
  put: "写入",
  flush_start: "开始 Flush",
  flush_end: "完成 Flush",
  sstable_created: "生成 SSTable",
  compaction_start: "开始 Compaction",
  compaction_end: "完成 Compaction",
  get: "查询",
  bloom_hit: "Bloom 命中",
  bloom_miss: "Bloom 过滤"
};

const EVENT_TONES: Record<string, string> = {
  put: "blue",
  flush_start: "amber",
  flush_end: "green",
  sstable_created: "teal",
  compaction_start: "purple",
  compaction_end: "green",
  get: "slate",
  bloom_hit: "blue",
  bloom_miss: "amber"
};

export function buildLevelBuckets(levels: Record<string, SSTableMeta[]>): LevelBucket[] {
  return Object.entries(levels)
    .map(([levelName, tables]) => {
      const id = Number(levelName.replace("level_", ""));
      const orderedTables = [...tables].sort((left, right) => {
        if (left.created_at === right.created_at) {
          return left.table_id.localeCompare(right.table_id);
        }
        return left.created_at < right.created_at ? -1 : 1;
      });
      const recordCounts = orderedTables.map((item) => item.record_count);
      return {
        id,
        label: `Level ${id}`,
        tables: orderedTables,
        tableCount: orderedTables.length,
        totalRecords: recordCounts.reduce((sum, value) => sum + value, 0),
        maxTableRecords: Math.max(...recordCounts, 1)
      };
    })
    .sort((left, right) => left.id - right.id);
}

export function totalSstableCount(levels: Record<string, SSTableMeta[]>): number {
  return Object.values(levels).reduce((sum, tables) => sum + tables.length, 0);
}

export function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  const units = ["KB", "MB", "GB"];
  let current = value / 1024;
  let unitIndex = 0;
  while (current >= 1024 && unitIndex < units.length - 1) {
    current /= 1024;
    unitIndex += 1;
  }

  return `${current.toFixed(current >= 10 ? 1 : 2)} ${units[unitIndex]}`;
}

export function formatMetric(value: number, digits = 2): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(digits);
}

export function formatEventLabel(eventType: string): string {
  return EVENT_LABELS[eventType] ?? eventType;
}

export function eventTone(eventType: string): string {
  return EVENT_TONES[eventType] ?? "slate";
}

export function summarizeEvent(event: TraceEvent): string {
  const payload = event.payload;
  switch (event.event_type) {
    case "put":
      return `key=${stringValue(payload.key)}，写入 WAL 并更新 MemTable`;
    case "flush_start":
      return `准备将 ${numberValue(payload.input_records)} 条记录刷写到 Level 0`;
    case "flush_end":
      return `SSTable ${stringValue(payload.table_id)} 已写入 Level ${numberValue(payload.level)}`;
    case "sstable_created":
      return `生成 ${stringValue(payload.table_id)}，记录数=${numberValue(payload.record_count)}`;
    case "compaction_start":
      return `${String(payload.strategy).toUpperCase()}：Level ${numberValue(payload.source_level)} -> Level ${numberValue(payload.target_level)}`;
    case "compaction_end":
      return `输出表 ${stringValue(payload.output_table_id)}，输入表数=${arrayLength(payload.input_table_ids)}`;
    case "get":
      return `key=${stringValue(payload.key)}，结果=${Boolean(payload.found) ? "命中" : "未命中"}，来源=${stringValue(payload.source)}`;
    case "bloom_hit":
      return `Level ${numberValue(payload.level)} 的 ${stringValue(payload.table_id)} 可能包含该 key`;
    case "bloom_miss":
      return `Level ${numberValue(payload.level)} 的 ${stringValue(payload.table_id)} 被 Bloom Filter 快速跳过`;
    default:
      return "查看详细 payload";
  }
}

export function metricHighlights(metrics: MetricsSnapshot): Array<{ label: string; value: string; note: string }> {
  return [
    {
      label: "总写入次数",
      value: formatMetric(metrics.total_puts, 0),
      note: "用户 put 操作累计次数"
    },
    {
      label: "总查询次数",
      value: formatMetric(metrics.total_gets, 0),
      note: "用户 get 操作累计次数"
    },
    {
      label: "MemTable 记录数",
      value: formatMetric(metrics.memtable_size_records, 0),
      note: `近似大小 ${formatBytes(metrics.memtable_size_bytes)}`
    },
    {
      label: "Flush 次数",
      value: formatMetric(metrics.flush_count, 0),
      note: "MemTable 落盘累计次数"
    },
    {
      label: "Compaction 次数",
      value: formatMetric(metrics.compaction_count, 0),
      note: "同步 compaction 累计次数"
    },
    {
      label: "读放大",
      value: formatMetric(metrics.read_amplification),
      note: `累计查询 IO ${formatMetric(metrics.user_query_read_io_total, 0)}`
    },
    {
      label: "写放大",
      value: formatMetric(metrics.write_amplification),
      note: `实际磁盘写入 ${formatBytes(metrics.actual_disk_write_bytes_total)}`
    },
    {
      label: "WAL 写入量",
      value: formatBytes(metrics.wal_write_bytes_total),
      note: "仅统计 WAL 文件字节数"
    }
  ];
}

function stringValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return String(value);
}

function numberValue(value: unknown): number {
  if (typeof value === "number") {
    return value;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function arrayLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}
