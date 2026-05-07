<template>
  <section class="panel">
    <div class="section-head">
      <div>
        <h2>事件时间线</h2>
        <p>展示最近发生的关键事件，便于解释 flush、Bloom 过滤与 compaction 行为。</p>
      </div>
      <span class="summary">最近 {{ events.length }} 条事件</span>
    </div>

    <div class="timeline">
      <div v-for="event in events" :key="event.event_id" class="item">
        <div class="head">
          <span class="badge" :data-tone="eventTone(event.event_type)">{{ formatEventLabel(event.event_type) }}</span>
          <span>#{{ event.seq }}</span>
          <span>{{ formatTime(event.timestamp) }}</span>
        </div>
        <p class="summary-text">{{ summarizeEvent(event) }}</p>
        <details>
          <summary>查看 payload</summary>
          <pre>{{ stringify(event.payload) }}</pre>
        </details>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { eventTone, formatEventLabel, summarizeEvent } from "../services/presentation";
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

.timeline {
  max-height: 500px;
  overflow: auto;
  display: grid;
  gap: 10px;
}

.item {
  border: 1px solid #d7e0ea;
  border-radius: 10px;
  padding: 10px;
  background: #fcfdff;
}

.head {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  font-size: 12px;
}

.badge {
  padding: 4px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.badge[data-tone="blue"] {
  background: #eaf2ff;
  color: #1c4fa1;
}

.badge[data-tone="amber"] {
  background: #fff4dc;
  color: #986200;
}

.badge[data-tone="green"] {
  background: #e9f8ef;
  color: #177245;
}

.badge[data-tone="purple"] {
  background: #f2ebff;
  color: #5b3db1;
}

.badge[data-tone="teal"] {
  background: #e7fbfa;
  color: #0d6c67;
}

.badge[data-tone="slate"] {
  background: #eef1f5;
  color: #465365;
}

.summary-text {
  margin: 8px 0 0;
  color: #243244;
  line-height: 1.5;
  font-size: 13px;
}

details {
  margin-top: 8px;
}

summary {
  cursor: pointer;
  color: #3b5f98;
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
