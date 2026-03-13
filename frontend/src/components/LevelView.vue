<template>
  <section class="panel">
    <h2>层级状态</h2>
    <div class="levels">
      <article v-for="(tables, levelName) in levels" :key="levelName" class="level-card">
        <h3>{{ levelName }}</h3>
        <p class="count">SSTable 数: {{ tables.length }}</p>
        <ul v-if="tables.length > 0">
          <li v-for="table in tables" :key="table.table_id">
            <strong>{{ table.table_id }}</strong>
            <span>[{{ table.min_key }} ~ {{ table.max_key }}]</span>
            <span>records={{ table.record_count }}</span>
          </li>
        </ul>
        <p v-else class="empty">暂无 SSTable</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { SSTableMeta } from "../types/sim";

defineProps<{
  levels: Record<string, SSTableMeta[]>;
}>();
</script>

<style scoped>
.levels {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.level-card {
  border: 1px solid #d6d6d6;
  border-radius: 8px;
  padding: 10px;
}

.count,
.empty {
  color: #555;
  font-size: 13px;
}

ul {
  margin: 8px 0 0;
  padding-left: 16px;
  display: grid;
  gap: 6px;
}

li {
  display: grid;
  gap: 2px;
  font-size: 12px;
}
</style>
