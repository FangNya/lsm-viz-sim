<template>
  <section class="panel">
    <div class="section-head">
      <div>
        <h2>指标摘要</h2>
        <p>把最重要的运行统计集中在一屏内，便于演示时快速解释当前状态。</p>
      </div>
      <span class="summary">快照字段 {{ cards.length }} 项</span>
    </div>

    <div class="card-grid">
      <article v-for="card in cards" :key="card.label" class="metric-card">
        <span class="label">{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.note }}</small>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { metricHighlights } from "../services/presentation";
import type { MetricsSnapshot } from "../types/sim";

const props = defineProps<{
  metrics: MetricsSnapshot;
}>();

const cards = computed(() => metricHighlights(props.metrics));
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

.card-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.metric-card {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #d8e0ea;
  background: linear-gradient(135deg, #ffffff, #f7faff);
}

.label {
  color: #566273;
  font-size: 13px;
}

strong {
  font-size: 24px;
  color: #112033;
}

small {
  color: #5f6b7a;
  line-height: 1.4;
}
</style>
