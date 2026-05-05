<template>
  <div class="page">
    <header>
      <h1>LSM-Tree Simulator</h1>
      <p>中期最小可演示页面（功能优先，样式从简）</p>
      <p v-if="error" class="error">{{ error }}</p>
    </header>

    <ConfigPanel
      :config="config"
      @apply-config="applyConfig"
      @reset-sim="resetSimulator"
      @run-workload="runWorkload"
      @step-once="runStep"
      @refresh-state="refreshState"
    />

    <div class="main-grid">
      <LevelView :levels="levels" />
      <EventTimeline :events="events" />
    </div>

    <MetricsCharts :metrics="metrics" :metrics-history="metricsHistory" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from "vue";

import ConfigPanel from "../components/ConfigPanel.vue";
import EventTimeline from "../components/EventTimeline.vue";
import LevelView from "../components/LevelView.vue";
import MetricsCharts from "../components/MetricsCharts.vue";
import { simApi } from "../services/api";
import { createEventsSocket } from "../services/ws";
import type { LSMConfig, MetricsSnapshot, TraceEvent, WorkloadOperation, WsMessage } from "../types/sim";

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
const error = ref("");
let ws: WebSocket | null = null;

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
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function resetSimulator(): Promise<void> {
  try {
    await simApi.reset();
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function runWorkload(operations: WorkloadOperation[]): Promise<void> {
  try {
    await simApi.runWorkload(operations);
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function runStep(operation: WorkloadOperation): Promise<void> {
  try {
    await simApi.step(operation);
    await refreshState();
  } catch (e) {
    error.value = (e as Error).message;
  }
}

onMounted(async () => {
  ws = createEventsSocket(handleWsMessage);
  await refreshState();
});

onBeforeUnmount(() => {
  ws?.close();
});
</script>

<style scoped>
.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 16px;
  display: grid;
  gap: 14px;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

h1,
h2,
h3 {
  margin: 0;
}

header p {
  margin: 4px 0 0;
  color: #555;
  font-size: 13px;
}

.error {
  color: #b90000;
}

.main-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr;
}

.panel {
  border: 1px solid #d9d9d9;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

@media (max-width: 900px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}
</style>
