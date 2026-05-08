<template>
  <div class="page">
    <header class="hero">
      <div>
        <h1>LSM-Tree Simulator</h1>
        <p>面向教学与答辩演示的 LSM-Tree 可视化模拟系统。</p>
        <p class="subline">当前页面聚焦结构演化、关键事件与读写代价，便于观察 LSM-Tree 在不同 workload 下的动态行为。</p>
      </div>
      <div class="status-group">
        <span class="status-badge" :data-ok="!error">REST {{ error ? "异常" : "正常" }}</span>
        <span class="status-badge" :data-ok="wsConnected">WebSocket {{ wsConnected ? "已连接" : "未连接" }}</span>
        <span class="status-badge neutral">SSTable {{ totalTables }}</span>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </header>

    <ConfigPanel
      :config="config"
      :last-step-response="lastStepResponse"
      @apply-config="applyConfig"
      @reset-sim="resetSimulator"
      @run-workload="runWorkload"
      @step-once="runStep"
      @refresh-state="refreshState"
    />

    <MetricsSummary :metrics="metrics" />

    <StructureCanvas :config="config" :levels="levels" :metrics="metrics" :events="events" />

    <div class="main-grid">
      <LevelView :levels="levels" :metrics="metrics" />
      <EventTimeline :events="events" />
    </div>

    <MetricsCharts :metrics="metrics" :metrics-history="metricsHistory" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";

import ConfigPanel from "../components/ConfigPanel.vue";
import EventTimeline from "../components/EventTimeline.vue";
import LevelView from "../components/LevelView.vue";
import MetricsCharts from "../components/MetricsCharts.vue";
import MetricsSummary from "../components/MetricsSummary.vue";
import StructureCanvas from "../components/StructureCanvas.vue";
import { totalSstableCount } from "../services/presentation";
import { simApi } from "../services/api";
import { createEventsSocket } from "../services/ws";
import type {
  LSMConfig,
  MetricsSnapshot,
  StepResponse,
  TraceEvent,
  WorkloadOperation,
  WsMessage
} from "../types/sim";

const config = reactive<LSMConfig>({
  memtable_max_records: 1000,
  memtable_max_bytes: 1048576,
  max_levels: 4,
  compaction_strategy: "stc",
  stc_trigger_tables: 4,
  l0_compaction_trigger_tables: 4,
  level_size_multiplier: 10,
  bloom_bits_per_key: 10,
  wal_dir: "./data/wal",
  data_dir: "./data/sst"
});

const levels = ref<Record<string, any[]>>({});
const events = ref<TraceEvent[]>([]);
const metrics = reactive<MetricsSnapshot>({
  total_puts: 0,
  total_gets: 0,
  memtable_size_records: 0,
  memtable_size_bytes: 0,
  sstable_count_by_level: {},
  flush_count: 0,
  compaction_count: 0,
  read_amplification: 0,
  write_amplification: 0,
  logical_write_bytes_total: 0,
  wal_write_bytes_total: 0,
  flush_data_write_bytes_total: 0,
  flush_meta_write_bytes_total: 0,
  flush_bloom_write_bytes_total: 0,
  compaction_data_write_bytes_total: 0,
  compaction_meta_write_bytes_total: 0,
  compaction_bloom_write_bytes_total: 0,
  actual_disk_write_bytes_total: 0,
  user_query_read_io_total: 0,
  bloom_read_io_total: 0,
  index_read_io_total: 0,
  data_block_read_io_total: 0
});
const metricsHistory = ref<MetricsSnapshot[]>([]);
const lastStepResponse = ref<StepResponse | null>(null);
const error = ref("");
const wsConnected = ref(false);
let ws: WebSocket | null = null;

const totalTables = computed(() => totalSstableCount(levels.value));

function pushMetricSnapshot(next: MetricsSnapshot): void {
  Object.assign(metrics, next);
  metricsHistory.value.push(JSON.parse(JSON.stringify(next)) as MetricsSnapshot);
  if (metricsHistory.value.length > 50) {
    metricsHistory.value.shift();
  }
}

function handleWsMessage(msg: WsMessage): void {
  if (msg.type === "trace_event") {
    events.value.unshift(msg.payload as TraceEvent);
    if (events.value.length > 100) {
      events.value.pop();
    }
  }
  if (msg.type === "metrics_update") {
    pushMetricSnapshot(msg.payload as MetricsSnapshot);
  }
}

async function refreshState(): Promise<void> {
  try {
    const state = await simApi.getState();
    Object.assign(config, state.config);
    levels.value = state.levels;
    events.value = state.recent_events.slice().reverse();
    pushMetricSnapshot(state.metrics);
    error.value = "";
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function applyConfig(next: LSMConfig): Promise<void> {
  try {
    await simApi.applyConfig(next);
    lastStepResponse.value = null;
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function resetSimulator(): Promise<void> {
  try {
    await simApi.reset();
    lastStepResponse.value = null;
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function runWorkload(operations: WorkloadOperation[]): Promise<void> {
  try {
    const response = await simApi.runWorkload(operations);
    lastStepResponse.value = response.step_results.at(-1) ?? null;
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function runStep(operation: WorkloadOperation): Promise<void> {
  try {
    lastStepResponse.value = await simApi.step(operation);
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

onMounted(async () => {
  ws = createEventsSocket(handleWsMessage);
  ws.addEventListener("open", () => {
    wsConnected.value = true;
  });
  ws.addEventListener("close", () => {
    wsConnected.value = false;
  });
  ws.addEventListener("error", () => {
    wsConnected.value = false;
  });
  await refreshState();
});

onBeforeUnmount(() => {
  ws?.close();
});
</script>

<style scoped>
.page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 16px 32px;
  display: grid;
  gap: 16px;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #112033;
  background:
    radial-gradient(circle at top left, rgba(79, 132, 223, 0.12), transparent 28%),
    linear-gradient(180deg, #f6f9fc 0%, #eef3f8 100%);
  min-height: 100vh;
}

h1,
h2,
h3 {
  margin: 0;
}

.hero {
  display: grid;
  gap: 12px;
  padding: 20px;
  border-radius: 18px;
  background: linear-gradient(135deg, #ffffff, #f3f7fc);
  border: 1px solid #d8e1eb;
}

header p {
  margin: 4px 0 0;
  color: #566273;
  font-size: 13px;
}

.subline {
  max-width: 860px;
  line-height: 1.5;
}

.status-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-badge {
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #fff1f0;
  color: #b42318;
}

.status-badge[data-ok="true"] {
  background: #e9f8ef;
  color: #177245;
}

.status-badge.neutral {
  background: #eef2f7;
  color: #425164;
}

.error {
  color: #b90000;
}

.main-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: 1.1fr 0.9fr;
}

.panel {
  border: 1px solid #d8e1eb;
  border-radius: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.04);
}

@media (max-width: 900px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}
</style>
