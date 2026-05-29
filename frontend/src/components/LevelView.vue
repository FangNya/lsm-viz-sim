<template>
  <section class="panel">
    <div class="section-head">
      <div>
        <h2>结构总览</h2>
        <p>用结构块展示 WAL、MemTable 和各层 SSTable 的当前状态。</p>
      </div>
      <span class="summary">SSTable 总数 {{ totalTables }}</span>
    </div>

    <div class="source-lane">
      <article class="source-card wal">
        <h3>WAL</h3>
        <p>{{ formatBytes(metrics.wal_write_bytes_total) }}</p>
        <small>累计 WAL 写入量</small>
      </article>
      <article class="source-card memtable">
        <h3>MemTable</h3>
        <p>{{ metrics.memtable_size_records }} 条记录</p>
        <small>近似大小 {{ formatBytes(metrics.memtable_size_bytes) }}</small>
      </article>
    </div>

    <div class="levels">
      <article v-for="bucket in buckets" :key="bucket.id" class="level-card">
        <div class="level-head">
          <div>
            <h3>{{ bucket.label }}</h3>
            <p>表数 {{ bucket.tableCount }} / 记录数 {{ bucket.totalRecords }}</p>
          </div>
          <span class="level-tag">L{{ bucket.id }}</span>
        </div>

        <div v-if="bucket.tables.length > 0" class="table-row">
          <div
            v-for="table in bucket.tables"
            :key="table.table_id"
            class="table-pill"
            :style="tableStyle(table.record_count, bucket.maxTableRecords)"
          >
            <strong>{{ table.table_id }}</strong>
            <span>{{ table.min_key }} ~ {{ table.max_key }}</span>
            <span>{{ table.record_count }} records</span>
            <span>{{ formatBytes(table.size_bytes) }}</span>
          </div>
        </div>

        <p v-else class="empty">当前层暂无 SSTable</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { buildLevelBuckets, formatBytes, totalSstableCount } from "../services/presentation";
import type { MetricsSnapshot, SSTableMeta } from "../types/sim";

const props = defineProps<{
  levels: Record<string, SSTableMeta[]>;
  metrics: MetricsSnapshot;
}>();

const buckets = computed(() => buildLevelBuckets(props.levels));
const totalTables = computed(() => totalSstableCount(props.levels));

function tableStyle(recordCount: number, maxRecords: number): Record<string, string> {
  const ratio = maxRecords > 0 ? recordCount / maxRecords : 0;
  const minWidth = 160;
  const width = Math.max(minWidth, 160 + Math.round(ratio * 160));
  return { width: `${width}px` };
}
</script>

<style scoped>
.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 14px;
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

.source-lane {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  margin-bottom: 14px;
}

.source-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #d9e1eb;
  color: #112033;
}

.source-card h3,
.source-card p {
  margin: 0;
}

.source-card p {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 700;
}

.source-card small {
  display: block;
  margin-top: 6px;
  color: #59657a;
}

.wal {
  background: linear-gradient(135deg, #fef7ea, #fffdf7);
}

.memtable {
  background: linear-gradient(135deg, #eef7ff, #f9fbff);
}

.levels {
  display: grid;
  gap: 12px;
}

.level-card {
  border: 1px solid #d8e0ea;
  border-radius: 12px;
  padding: 12px;
  background: #fcfdff;
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

.level-tag {
  padding: 5px 9px;
  border-radius: 999px;
  background: #edf1f5;
  color: #344052;
  font-size: 12px;
  font-weight: 600;
}

.table-row {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.table-pill {
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1f5fbf, #4b84df);
  color: #fff;
  font-size: 12px;
}

.table-pill strong {
  font-size: 13px;
}

@media (max-width: 900px) {
  .source-lane {
    grid-template-columns: 1fr;
  }
}
</style>
