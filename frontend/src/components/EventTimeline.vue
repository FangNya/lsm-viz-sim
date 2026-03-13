<template>
  <section class="panel">
    <h2>事件时间线</h2>
    <div class="timeline">
      <div v-for="event in events" :key="event.event_id" class="item">
        <div class="head">
          <strong>{{ event.event_type }}</strong>
          <span>#{{ event.seq }}</span>
          <span>{{ formatTime(event.timestamp) }}</span>
        </div>
        <pre>{{ stringify(event.payload) }}</pre>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { TraceEvent } from "../types/sim";

defineProps<{
  events: TraceEvent[];
}>();

function formatTime(input: string): string {
  return new Date(input).toLocaleTimeString();
}

function stringify(payload: Record<string, unknown>): string {
  return JSON.stringify(payload, null, 2);
}
</script>

<style scoped>
.timeline {
  max-height: 380px;
  overflow: auto;
  display: grid;
  gap: 8px;
}

.item {
  border: 1px solid #dcdcdc;
  border-radius: 8px;
  padding: 8px;
}

.head {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

pre {
  margin: 6px 0 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #333;
}
</style>
