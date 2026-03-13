<template>
  <section class="panel charts">
    <h2>指标图表</h2>
    <div class="grid">
      <div ref="levelChartRef" class="chart" />
      <div ref="compactionChartRef" class="chart" />
      <div ref="ampChartRef" class="chart" />
    </div>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { MetricsSnapshot } from "../types/sim";

const props = defineProps<{
  metrics: MetricsSnapshot;
  metricsHistory: MetricsSnapshot[];
}>();

const levelChartRef = ref<HTMLDivElement | null>(null);
const compactionChartRef = ref<HTMLDivElement | null>(null);
const ampChartRef = ref<HTMLDivElement | null>(null);

let levelChart: echarts.ECharts | null = null;
let compactionChart: echarts.ECharts | null = null;
let ampChart: echarts.ECharts | null = null;

const levelData = computed(() => {
  const entries = Object.entries(props.metrics.sstable_count_by_level || {}).sort((a, b) => Number(a[0]) - Number(b[0]));
  return {
    labels: entries.map(([level]) => `L${level}`),
    values: entries.map(([, count]) => count)
  };
});

function renderCharts(): void {
  if (!levelChart || !compactionChart || !ampChart) {
    return;
  }

  levelChart.setOption({
    title: { text: "各层 SSTable 数量", left: "center", textStyle: { fontSize: 13 } },
    xAxis: { type: "category", data: levelData.value.labels },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: levelData.value.values }],
    grid: { top: 40, left: 35, right: 10, bottom: 30 }
  });

  compactionChart.setOption({
    title: { text: "Compaction 次数", left: "center", textStyle: { fontSize: 13 } },
    xAxis: { type: "category", data: props.metricsHistory.map((_, i) => String(i + 1)) },
    yAxis: { type: "value" },
    series: [{ type: "line", smooth: true, data: props.metricsHistory.map((m) => m.compaction_count) }],
    grid: { top: 40, left: 35, right: 10, bottom: 30 }
  });

  ampChart.setOption({
    title: { text: "读/写放大", left: "center", textStyle: { fontSize: 13 } },
    legend: { top: 20 },
    xAxis: { type: "category", data: props.metricsHistory.map((_, i) => String(i + 1)) },
    yAxis: { type: "value" },
    series: [
      { name: "Read Amp", type: "line", smooth: true, data: props.metricsHistory.map((m) => m.read_amplification) },
      { name: "Write Amp", type: "line", smooth: true, data: props.metricsHistory.map((m) => m.write_amplification) }
    ],
    grid: { top: 55, left: 35, right: 10, bottom: 30 }
  });
}

onMounted(async () => {
  await nextTick();
  if (levelChartRef.value) levelChart = echarts.init(levelChartRef.value);
  if (compactionChartRef.value) compactionChart = echarts.init(compactionChartRef.value);
  if (ampChartRef.value) ampChart = echarts.init(ampChartRef.value);
  renderCharts();
});

watch(
  () => [props.metrics, props.metricsHistory],
  () => renderCharts(),
  { deep: true }
);

onBeforeUnmount(() => {
  levelChart?.dispose();
  compactionChart?.dispose();
  ampChart?.dispose();
});
</script>

<style scoped>
.grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.chart {
  height: 260px;
  border: 1px solid #d8d8d8;
  border-radius: 8px;
}
</style>
