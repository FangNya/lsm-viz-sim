<template>
  <section class="panel charts">
    <div class="section-head">
      <div>
        <h2>指标图表</h2>
        <p>同时展示层级分布、后台整理趋势以及读写代价的构成。</p>
      </div>
      <span class="summary">历史快照 {{ metricsHistory.length }} 条</span>
    </div>
    <div class="grid">
      <div ref="levelChartRef" class="chart" />
      <div ref="compactionChartRef" class="chart" />
      <div ref="ampChartRef" class="chart" />
      <div ref="readBreakdownChartRef" class="chart" />
      <div ref="writeBreakdownChartRef" class="chart chart-wide" />
    </div>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { formatBytes } from "../services/presentation";
import type { MetricsSnapshot } from "../types/sim";

const props = defineProps<{
  metrics: MetricsSnapshot;
  metricsHistory: MetricsSnapshot[];
}>();

const levelChartRef = ref<HTMLDivElement | null>(null);
const compactionChartRef = ref<HTMLDivElement | null>(null);
const ampChartRef = ref<HTMLDivElement | null>(null);
const readBreakdownChartRef = ref<HTMLDivElement | null>(null);
const writeBreakdownChartRef = ref<HTMLDivElement | null>(null);

let levelChart: echarts.ECharts | null = null;
let compactionChart: echarts.ECharts | null = null;
let ampChart: echarts.ECharts | null = null;
let readBreakdownChart: echarts.ECharts | null = null;
let writeBreakdownChart: echarts.ECharts | null = null;

const levelData = computed(() => {
  const entries = Object.entries(props.metrics.sstable_count_by_level || {}).sort((a, b) => Number(a[0]) - Number(b[0]));
  return {
    labels: entries.map(([level]) => `L${level}`),
    values: entries.map(([, count]) => count)
  };
});

const historyLabels = computed(() => props.metricsHistory.map((_, index) => String(index + 1)));

function renderCharts(): void {
  if (!levelChart || !compactionChart || !ampChart || !readBreakdownChart || !writeBreakdownChart) {
    return;
  }

  levelChart.setOption({
    title: { text: "各层 SSTable 数量", left: "center", textStyle: { fontSize: 13 } },
    xAxis: { type: "category", data: levelData.value.labels },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: levelData.value.values, itemStyle: { color: "#1f5fbf" } }],
    grid: { top: 40, left: 35, right: 10, bottom: 30 }
  });

  compactionChart.setOption({
    title: { text: "Flush / Compaction 趋势", left: "center", textStyle: { fontSize: 13 } },
    legend: { top: 20 },
    xAxis: { type: "category", data: historyLabels.value },
    yAxis: { type: "value" },
    series: [
      { name: "Flush", type: "line", smooth: true, data: props.metricsHistory.map((m) => m.flush_count) },
      { name: "Compaction", type: "line", smooth: true, data: props.metricsHistory.map((m) => m.compaction_count) }
    ],
    grid: { top: 55, left: 35, right: 10, bottom: 30 }
  });

  ampChart.setOption({
    title: { text: "读 / 写放大", left: "center", textStyle: { fontSize: 13 } },
    legend: { top: 20 },
    xAxis: { type: "category", data: historyLabels.value },
    yAxis: { type: "value" },
    series: [
      { name: "Read Amp", type: "line", smooth: true, data: props.metricsHistory.map((m) => m.read_amplification) },
      { name: "Write Amp", type: "line", smooth: true, data: props.metricsHistory.map((m) => m.write_amplification) }
    ],
    grid: { top: 55, left: 35, right: 10, bottom: 30 }
  });

  readBreakdownChart.setOption({
    title: { text: "用户查询读 IO 构成", left: "center", textStyle: { fontSize: 13 } },
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["35%", "68%"],
        data: [
          { name: "Bloom", value: props.metrics.bloom_read_io_total },
          { name: "Index Block", value: props.metrics.index_read_io_total },
          { name: "Data Block", value: props.metrics.data_block_read_io_total }
        ],
        label: { formatter: "{b}\n{c}" }
      }
    ]
  });

  writeBreakdownChart.setOption({
    title: { text: "写入字节构成", left: "center", textStyle: { fontSize: 13 } },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      valueFormatter: (value: string | number) => formatBytes(Number(value))
    },
    xAxis: {
      type: "category",
      data: ["WAL", "Flush Data", "Flush Meta", "Flush Bloom", "Compact Data", "Compact Meta", "Compact Bloom"],
      axisLabel: { interval: 0, rotate: 18 }
    },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        itemStyle: { color: "#1f5fbf" },
        data: [
          props.metrics.wal_write_bytes_total,
          props.metrics.flush_data_write_bytes_total,
          props.metrics.flush_meta_write_bytes_total,
          props.metrics.flush_bloom_write_bytes_total,
          props.metrics.compaction_data_write_bytes_total,
          props.metrics.compaction_meta_write_bytes_total,
          props.metrics.compaction_bloom_write_bytes_total
        ]
      }
    ],
    grid: { top: 40, left: 48, right: 10, bottom: 78 }
  });
}

function resizeCharts(): void {
  levelChart?.resize();
  compactionChart?.resize();
  ampChart?.resize();
  readBreakdownChart?.resize();
  writeBreakdownChart?.resize();
}

onMounted(async () => {
  await nextTick();
  if (levelChartRef.value) levelChart = echarts.init(levelChartRef.value);
  if (compactionChartRef.value) compactionChart = echarts.init(compactionChartRef.value);
  if (ampChartRef.value) ampChart = echarts.init(ampChartRef.value);
  if (readBreakdownChartRef.value) readBreakdownChart = echarts.init(readBreakdownChartRef.value);
  if (writeBreakdownChartRef.value) writeBreakdownChart = echarts.init(writeBreakdownChartRef.value);
  renderCharts();
  window.addEventListener("resize", resizeCharts);
});

watch(
  () => [props.metrics, props.metricsHistory],
  () => renderCharts(),
  { deep: true }
);

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeCharts);
  levelChart?.dispose();
  compactionChart?.dispose();
  ampChart?.dispose();
  readBreakdownChart?.dispose();
  writeBreakdownChart?.dispose();
});
</script>

<style scoped>
.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.section-head p {
  margin: 4px 0 0;
  color: #586273;
  font-size: 13px;
}

.summary {
  padding: 6px 10px;
  border-radius: 999px;
  background: #f2f5f8;
  color: #3d4752;
  font-size: 12px;
  font-weight: 600;
}

.grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.chart {
  height: 260px;
  border: 1px solid #d8d8d8;
  border-radius: 10px;
  background: #fcfdff;
}

.chart-wide {
  min-height: 300px;
}

@media (min-width: 1100px) {
  .chart-wide {
    grid-column: span 2;
  }
}
</style>
