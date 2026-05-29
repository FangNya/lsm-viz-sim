import type { LSMConfig, WorkloadOperation } from "../types/sim";
import { experimentWorkloadPresets } from "./experimentWorkloads";

export interface ConfigPreset {
  id: string;
  label: string;
  description: string;
  values: Partial<LSMConfig>;
}

export interface WorkloadPreset {
  id: string;
  label: string;
  description: string;
  operations: WorkloadOperation[];
}

export const configPresets: ConfigPreset[] = [
  {
    id: "stc-demo",
    label: "STC 演示",
    description: "较小 MemTable，适合快速观察 flush 与 STC compaction。",
    values: {
      memtable_max_records: 3,
      memtable_max_bytes: 512,
      max_levels: 4,
      compaction_strategy: "stc",
      stc_trigger_tables: 2,
      l0_compaction_trigger_tables: 2,
      level_size_multiplier: 4,
      bloom_bits_per_key: 10
    }
  },
  {
    id: "lcs-demo",
    label: "LCS 演示",
    description: "较小 MemTable，适合观察 Level 0 到高层的 LCS 整理行为。",
    values: {
      memtable_max_records: 3,
      memtable_max_bytes: 512,
      max_levels: 5,
      compaction_strategy: "lcs",
      stc_trigger_tables: 2,
      l0_compaction_trigger_tables: 2,
      level_size_multiplier: 3,
      bloom_bits_per_key: 10
    }
  },
  {
    id: "balanced-demo",
    label: "平衡演示",
    description: "常用演示配置，适合混合读写展示。",
    values: {
      memtable_max_records: 6,
      memtable_max_bytes: 1024,
      max_levels: 5,
      compaction_strategy: "stc",
      stc_trigger_tables: 3,
      l0_compaction_trigger_tables: 3,
      level_size_multiplier: 4,
      bloom_bits_per_key: 12
    }
  },
  {
    id: "baseline-profile",
    label: "baseline",
    description: "基础实验配置。",
    values: {
      memtable_max_records: 8,
      memtable_max_bytes: 4096,
      max_levels: 4,
      compaction_strategy: "stc",
      stc_trigger_tables: 3,
      l0_compaction_trigger_tables: 3,
      level_size_multiplier: 10,
      bloom_bits_per_key: 10
    }
  },
  {
    id: "aggressive-profile",
    label: "aggressive_compaction",
    description: "高 compaction 压力配置。",
    values: {
      memtable_max_records: 4,
      memtable_max_bytes: 512,
      max_levels: 4,
      compaction_strategy: "stc",
      stc_trigger_tables: 2,
      l0_compaction_trigger_tables: 2,
      level_size_multiplier: 4,
      bloom_bits_per_key: 10
    }
  },
  {
    id: "overlap-profile",
    label: "overlap_pressure",
    description: "更强调重叠范围与层级压力的配置。",
    values: {
      memtable_max_records: 3,
      memtable_max_bytes: 384,
      max_levels: 5,
      compaction_strategy: "lcs",
      stc_trigger_tables: 3,
      l0_compaction_trigger_tables: 2,
      level_size_multiplier: 3,
      bloom_bits_per_key: 10
    }
  },
  {
    id: "final-balanced-profile",
    label: "final_balanced",
    description: "结题实验中的平衡配置。",
    values: {
      memtable_max_records: 24,
      memtable_max_bytes: 4096,
      max_levels: 6,
      compaction_strategy: "stc",
      stc_trigger_tables: 4,
      l0_compaction_trigger_tables: 4,
      level_size_multiplier: 6,
      bloom_bits_per_key: 12
    }
  },
  {
    id: "final-dense-profile",
    label: "final_dense_compaction",
    description: "结题实验中的密集 compaction 配置。",
    values: {
      memtable_max_records: 12,
      memtable_max_bytes: 2048,
      max_levels: 6,
      compaction_strategy: "stc",
      stc_trigger_tables: 3,
      l0_compaction_trigger_tables: 3,
      level_size_multiplier: 3,
      bloom_bits_per_key: 12
    }
  },
  {
    id: "final-overlap-profile",
    label: "final_overlap_sensitive",
    description: "结题实验中的 overlap 敏感配置。",
    values: {
      memtable_max_records: 8,
      memtable_max_bytes: 1536,
      max_levels: 6,
      compaction_strategy: "lcs",
      stc_trigger_tables: 4,
      l0_compaction_trigger_tables: 2,
      level_size_multiplier: 2.5,
      bloom_bits_per_key: 12
    }
  }
];

const basicWorkloadPresets: WorkloadPreset[] = [
  {
    id: "flush-demo",
    label: "Flush 演示",
    description: "连续写入少量 key，快速观察 MemTable 满后刷写到 Level 0。",
    operations: [
      { op: "put", key: "k001", value: "v001" },
      { op: "put", key: "k002", value: "v002" },
      { op: "put", key: "k003", value: "v003" },
      { op: "put", key: "k004", value: "v004" }
    ]
  },
  {
    id: "read-path-demo",
    label: "查询路径演示",
    description: "包含 put 与 get，便于观察命中、未命中和 Bloom 过滤事件。",
    operations: [
      { op: "put", key: "k001", value: "v001" },
      { op: "put", key: "k002", value: "v002" },
      { op: "put", key: "k003", value: "v003" },
      { op: "get", key: "k002" },
      { op: "get", key: "k999" },
      { op: "put", key: "k004", value: "v004" },
      { op: "get", key: "k001" }
    ]
  },
  {
    id: "overwrite-demo",
    label: "覆盖写演示",
    description: "重复写入热点 key，再查询最新值，用于展示最新 seq 生效。",
    operations: [
      { op: "put", key: "hot_001", value: "v1" },
      { op: "put", key: "hot_002", value: "v1" },
      { op: "put", key: "hot_001", value: "v2" },
      { op: "put", key: "hot_003", value: "v1" },
      { op: "get", key: "hot_001" },
      { op: "get", key: "hot_004" }
    ]
  }
];

const importedExperimentPresets: WorkloadPreset[] = experimentWorkloadPresets.map((preset) => ({
  id: `exp-${preset.id}`,
  label: `实验 · ${preset.label}`,
  description: `${preset.description} 共 ${preset.operations.length} 条操作，适合观察较长时间的层级演化。`,
  operations: preset.operations
}));

export const workloadPresets: WorkloadPreset[] = [...basicWorkloadPresets, ...importedExperimentPresets];

export function parseWorkloadText(text: string): { operations: WorkloadOperation[]; errors: string[] } {
  const operations: WorkloadOperation[] = [];
  const errors: string[] = [];

  text.split(/\r?\n/).forEach((rawLine, index) => {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      return;
    }

    const putMatch = line.match(/^put\s+(\S+)\s+(.+)$/i);
    if (putMatch) {
      operations.push({
        op: "put",
        key: putMatch[1],
        value: putMatch[2]
      });
      return;
    }

    const getMatch = line.match(/^get\s+(\S+)$/i);
    if (getMatch) {
      operations.push({
        op: "get",
        key: getMatch[1]
      });
      return;
    }

    const legacyPut = line.match(/^([^=\s]+)\s*=\s*(.+)$/);
    if (legacyPut) {
      operations.push({
        op: "put",
        key: legacyPut[1].trim(),
        value: legacyPut[2].trim()
      });
      return;
    }

    errors.push(`第 ${index + 1} 行无法解析：${line}`);
  });

  return { operations, errors };
}

export function workloadToText(operations: WorkloadOperation[]): string {
  return operations
    .map((operation) => {
      if (operation.op === "get") {
        return `get ${operation.key}`;
      }
      return `put ${operation.key} ${operation.value ?? ""}`.trimEnd();
    })
    .join("\n");
}
