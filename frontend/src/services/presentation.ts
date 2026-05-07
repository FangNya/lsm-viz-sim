import type { MetricsSnapshot, SSTableMeta, TraceEvent } from "../types/sim";

export interface LevelBucket {
  id: number;
  label: string;
  tables: SSTableMeta[];
  tableCount: number;
  totalRecords: number;
  maxTableRecords: number;
}

export interface CanvasFocus {
  title: string;
  description: string;
  eventType: string;
  activeStages: string[];
  activeLevels: number[];
  activeTableIds: string[];
  chips: string[];
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

export function buildLevelBuckets(levels: Record<string, SSTableMeta[]>, maxLevels?: number): LevelBucket[] {
  const buckets = Object.entries(levels)
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

  if (maxLevels === undefined) {
    return buckets;
  }

  const bucketMap = new Map(buckets.map((bucket) => [bucket.id, bucket]));
  const filled: LevelBucket[] = [];
  for (let id = 0; id < maxLevels; id += 1) {
    filled.push(
      bucketMap.get(id) ?? {
        id,
        label: `Level ${id}`,
        tables: [],
        tableCount: 0,
        totalRecords: 0,
        maxTableRecords: 1
      }
    );
  }
  return filled;
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

export function buildCanvasFocus(events: TraceEvent[]): CanvasFocus {
  const event = events[0];
  if (!event) {
    return {
      title: "等待操作",
      description: "当前还没有新的 trace 事件。你可以执行一次 put、workload 或 reset 来观察结构变化。",
      eventType: "idle",
      activeStages: [],
      activeLevels: [],
      activeTableIds: [],
      chips: ["尚无事件"]
    };
  }

  const payload = event.payload;
  switch (event.event_type) {
    case "put":
      return {
        title: "写入路径",
        description: `key=${stringValue(payload.key)} 先追加到 WAL，再写入 MemTable。`,
        eventType: event.event_type,
        activeStages: ["wal", "memtable"],
        activeLevels: [],
        activeTableIds: [],
        chips: [`seq #${event.seq}`, "WAL 追加", "MemTable 更新"]
      };
    case "flush_start":
      return {
        title: "开始 Flush",
        description: `MemTable 正准备刷写到 Level 0，输入记录数为 ${numberValue(payload.input_records)}。`,
        eventType: event.event_type,
        activeStages: ["memtable", "level_0"],
        activeLevels: [numberValue(payload.target_level)],
        activeTableIds: [],
        chips: [`目标层 L${numberValue(payload.target_level)}`, `${numberValue(payload.input_records)} 条记录`]
      };
    case "flush_end":
      return {
        title: "Flush 完成",
        description: `新的 SSTable ${stringValue(payload.table_id)} 已经写入 Level ${numberValue(payload.level)}。`,
        eventType: event.event_type,
        activeStages: [`level_${numberValue(payload.level)}`],
        activeLevels: [numberValue(payload.level)],
        activeTableIds: [stringValue(payload.table_id)],
        chips: [`输出表 ${stringValue(payload.table_id)}`, `L${numberValue(payload.level)}`]
      };
    case "sstable_created":
      return {
        title: "SSTable 已生成",
        description: `生成表 ${stringValue(payload.table_id)}，当前位于 Level ${numberValue(payload.level)}。`,
        eventType: event.event_type,
        activeStages: [`level_${numberValue(payload.level)}`],
        activeLevels: [numberValue(payload.level)],
        activeTableIds: [stringValue(payload.table_id)],
        chips: [
          `table_id=${stringValue(payload.table_id)}`,
          payload.created_by ? `来源 ${stringValue(payload.created_by)}` : `记录数 ${numberValue(payload.record_count)}`
        ]
      };
    case "compaction_start":
      return {
        title: "开始 Compaction",
        description: `${String(payload.strategy).toUpperCase()} 正在把 Level ${numberValue(payload.source_level)} 的输入表合并到 Level ${numberValue(payload.target_level)}。`,
        eventType: event.event_type,
        activeStages: [`level_${numberValue(payload.source_level)}`, `level_${numberValue(payload.target_level)}`],
        activeLevels: [numberValue(payload.source_level), numberValue(payload.target_level)],
        activeTableIds: arrayStrings(payload.input_table_ids),
        chips: [
          `策略 ${String(payload.strategy).toUpperCase()}`,
          `L${numberValue(payload.source_level)} -> L${numberValue(payload.target_level)}`,
          `输入表 ${arrayLength(payload.input_table_ids)} 个`
        ]
      };
    case "compaction_end":
      return {
        title: "Compaction 完成",
        description: `合并输出表 ${stringValue(payload.output_table_id)} 已经落到 Level ${numberValue(payload.target_level)}。`,
        eventType: event.event_type,
        activeStages: [`level_${numberValue(payload.source_level)}`, `level_${numberValue(payload.target_level)}`],
        activeLevels: [numberValue(payload.source_level), numberValue(payload.target_level)],
        activeTableIds: [...arrayStrings(payload.input_table_ids), stringValue(payload.output_table_id)],
        chips: [
          `输出表 ${stringValue(payload.output_table_id)}`,
          `输入表 ${arrayLength(payload.input_table_ids)} 个`
        ]
      };
    case "get": {
      const path = Array.isArray(payload.path) ? payload.path : [];
      const sstableSteps = path.filter((item) => item && typeof item === "object" && "table_id" in item) as Array<Record<string, unknown>>;
      const levels = sstableSteps.map((item) => numberValue(item.level));
      const activeTables = sstableSteps.map((item) => stringValue(item.table_id));
      const skippedCount = sstableSteps.filter((item) => String(item.action) === "skip").length;
      const source = stringValue(payload.source);

      return {
        title: "查询路径",
        description: `key=${stringValue(payload.key)}，结果=${Boolean(payload.found) ? "命中" : "未命中"}，来源=${source}。`,
        eventType: event.event_type,
        activeStages: source === "memtable" ? ["memtable"] : levels.map((level) => `level_${level}`),
        activeLevels: levels,
        activeTableIds: activeTables,
        chips: [
          `扫描表 ${sstableSteps.length} 个`,
          `Bloom 跳过 ${skippedCount} 个`,
          Boolean(payload.found) ? "查询命中" : "查询未命中"
        ]
      };
    }
    case "bloom_hit":
    case "bloom_miss":
      return {
        title: event.event_type === "bloom_hit" ? "Bloom 命中" : "Bloom 过滤",
        description: `Level ${numberValue(payload.level)} 中的 ${stringValue(payload.table_id)} 参与了本次查询判断。`,
        eventType: event.event_type,
        activeStages: [`level_${numberValue(payload.level)}`],
        activeLevels: [numberValue(payload.level)],
        activeTableIds: [stringValue(payload.table_id)],
        chips: [`L${numberValue(payload.level)}`, stringValue(payload.table_id)]
      };
    default:
      return {
        title: formatEventLabel(event.event_type),
        description: summarizeEvent(event),
        eventType: event.event_type,
        activeStages: [],
        activeLevels: [],
        activeTableIds: [],
        chips: [`seq #${event.seq}`]
      };
  }
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

function arrayStrings(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}
