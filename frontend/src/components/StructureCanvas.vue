<template>
  <section class="panel">
    <div class="section-head">
      <div>
        <h2>结构演化画布</h2>
        <p>基于最近一次 trace 事件高亮写入、flush、compaction 与查询路径，帮助演示层级变化。</p>
      </div>
      <span class="summary">当前焦点：{{ focus.title }}</span>
    </div>

    <div class="focus-banner" :data-tone="eventTone(focus.eventType)">
      <div>
        <strong>{{ focus.title }}</strong>
        <p>{{ focus.description }}</p>
      </div>
      <div class="chips">
        <span v-for="chip in focus.chips" :key="chip" class="chip">{{ chip }}</span>
      </div>
    </div>

    <div class="canvas">
      <div class="stage-strip">
        <article class="stage-card" :data-active="isStageActive('wal')">
          <span class="stage-label">WAL</span>
          <strong>{{ formatBytes(metrics.wal_write_bytes_total) }}</strong>
          <small>追加写日志</small>
        </article>
        <div class="flow-arrow" :data-active="isStageActive('wal') || isStageActive('memtable')">→</div>
        <article class="stage-card" :data-active="isStageActive('memtable')">
          <span class="stage-label">MemTable</span>
          <strong>{{ metrics.memtable_size_records }}</strong>
          <small>{{ formatBytes(metrics.memtable_size_bytes) }}</small>
        </article>
      </div>

      <div class="levels-grid">
        <article
          v-for="bucket in buckets"
          :key="bucket.id"
          class="level-card"
          :data-active="isLevelActive(bucket.id)"
        >
          <div class="level-head">
            <div>
              <h3>{{ bucket.label }}</h3>
              <p>{{ bucket.tableCount }} 个表 / {{ bucket.totalRecords }} 条记录</p>
            </div>
            <span class="level-badge">L{{ bucket.id }}</span>
          </div>

          <div v-if="bucket.tables.length > 0" class="tables">
            <div
              v-for="table in bucket.tables"
              :key="table.table_id"
              class="table-node"
              :data-active="isTableActive(table.table_id)"
            >
              <strong>{{ table.table_id }}</strong>
              <span>{{ table.min_key }} ~ {{ table.max_key }}</span>
              <span>{{ table.record_count }} records</span>
            </div>
          </div>
          <p v-else class="empty">当前层暂无 SSTable</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { buildCanvasFocus, buildLevelBuckets, eventTone, formatBytes } from "../services/presentation";
import type { LSMConfig, MetricsSnapshot, SSTableMeta, TraceEvent } from "../types/sim";

const props = defineProps<{
  config: LSMConfig;
  levels: Record<string, SSTableMeta[]>;
  metrics: MetricsSnapshot;
  events: TraceEvent[];
}>();

const focus = computed(() => buildCanvasFocus(props.events));
const buckets = computed(() => buildLevelBuckets(props.levels, props.config.max_levels));

function isStageActive(stage: string): boolean {
  return focus.value.activeStages.includes(stage);
}

function isLevelActive(level: number): boolean {
  return focus.value.activeLevels.includes(level) || isStageActive(`level_${level}`);
}

function isTableActive(tableId: string): boolean {
  return focus.value.activeTableIds.includes(tableId);
}
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

.focus-banner {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #d8e1eb;
  background: linear-gradient(135deg, #ffffff, #f8fbff);
}

.focus-banner strong {
  font-size: 18px;
}

.focus-banner p {
  margin: 6px 0 0;
  line-height: 1.5;
  color: #334155;
}

.focus-banner[data-tone="blue"] {
  background: linear-gradient(135deg, #f4f8ff, #eef5ff);
}

.focus-banner[data-tone="amber"] {
  background: linear-gradient(135deg, #fff9ef, #fff4dc);
}

.focus-banner[data-tone="green"] {
  background: linear-gradient(135deg, #f3fff7, #e9f8ef);
}

.focus-banner[data-tone="purple"] {
  background: linear-gradient(135deg, #faf7ff, #f1eaff);
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(17, 32, 51, 0.08);
  color: #223247;
  font-size: 12px;
  font-weight: 600;
}

.canvas {
  margin-top: 14px;
  display: grid;
  gap: 14px;
}

.stage-strip {
  display: grid;
  grid-template-columns: minmax(180px, 220px) 40px minmax(180px, 220px);
  gap: 12px;
  align-items: center;
}

.stage-card {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #d9e1eb;
  background: #fcfdff;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.stage-card[data-active="true"] {
  border-color: #1f5fbf;
  box-shadow: 0 10px 24px rgba(31, 95, 191, 0.18);
  transform: translateY(-2px);
}

.stage-label {
  color: #526074;
  font-size: 12px;
  font-weight: 600;
}

.stage-card strong {
  font-size: 22px;
  color: #112033;
}

.stage-card small {
  color: #586273;
}

.flow-arrow {
  text-align: center;
  font-size: 28px;
  color: #97a3b6;
  transition: color 0.25s ease, transform 0.25s ease;
}

.flow-arrow[data-active="true"] {
  color: #1f5fbf;
  transform: scale(1.08);
}

.levels-grid {
  display: grid;
  gap: 12px;
}

.level-card {
  border: 1px solid #d8e0ea;
  border-radius: 14px;
  padding: 12px;
  background: #fcfdff;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.level-card[data-active="true"] {
  border-color: #1f5fbf;
  box-shadow: 0 10px 24px rgba(31, 95, 191, 0.12);
}

.level-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.level-head h3,
.level-head p {
  margin: 0;
}

.level-head p,
.empty {
  color: #586273;
  font-size: 13px;
}

.level-badge {
  padding: 5px 10px;
  border-radius: 999px;
  background: #edf1f5;
  color: #344052;
  font-size: 12px;
  font-weight: 600;
}

.tables {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.table-node {
  min-width: 150px;
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d8e1eb;
  background: linear-gradient(135deg, #ffffff, #f7faff);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.table-node[data-active="true"] {
  border-color: #1f5fbf;
  box-shadow: 0 10px 24px rgba(31, 95, 191, 0.16);
  transform: translateY(-2px);
}

.table-node strong {
  color: #12315d;
}

.table-node span {
  color: #4f5f76;
  font-size: 12px;
}

@media (max-width: 900px) {
  .stage-strip {
    grid-template-columns: 1fr;
  }

  .flow-arrow {
    transform: rotate(90deg);
  }

  .flow-arrow[data-active="true"] {
    transform: rotate(90deg) scale(1.08);
  }
}
</style>
