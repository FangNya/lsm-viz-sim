<template>
  <section class="panel config-panel">
    <h2>参数配置</h2>

    <div class="form-grid">
      <label>
        memtable_max_records
        <input v-model.number="localConfig.memtable_max_records" type="number" min="1" />
      </label>
      <label>
        memtable_max_bytes
        <input v-model.number="localConfig.memtable_max_bytes" type="number" min="1" />
      </label>
      <label>
        compaction_strategy
        <select v-model="localConfig.compaction_strategy">
          <option value="stc">stc</option>
          <option value="lcs">lcs</option>
        </select>
      </label>
      <label>
        stc_trigger_tables
        <input v-model.number="localConfig.stc_trigger_tables" type="number" min="2" />
      </label>
      <label>
        l0_compaction_trigger_tables
        <input v-model.number="localConfig.l0_compaction_trigger_tables" type="number" min="2" />
      </label>
      <label>
        max_levels
        <input v-model.number="localConfig.max_levels" type="number" min="1" />
      </label>
    </div>

    <div class="actions">
      <button type="button" @click="emit('apply-config', localConfig)">应用配置</button>
      <button type="button" @click="emit('reset-sim')">重置模拟器</button>
      <button type="button" @click="runWorkload">运行 workload</button>
      <button type="button" @click="stepOnce">单步执行</button>
      <button type="button" @click="emit('refresh-state')">刷新状态</button>
    </div>

    <div class="inputs">
      <label>
        workload（每行: key=value）
        <textarea v-model="workloadText" rows="5" />
      </label>
      <div class="step-box">
        <label>
          单步 key
          <input v-model="stepKey" type="text" />
        </label>
        <label>
          单步 value
          <input v-model="stepValue" type="text" />
        </label>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";

import type { LSMConfig, WorkloadOperation } from "../types/sim";

const props = defineProps<{
  config: LSMConfig;
}>();

const emit = defineEmits<{
  (e: "apply-config", config: LSMConfig): void;
  (e: "reset-sim"): void;
  (e: "run-workload", operations: WorkloadOperation[]): void;
  (e: "step-once", operation: WorkloadOperation): void;
  (e: "refresh-state"): void;
}>();

const localConfig = reactive<LSMConfig>({ ...props.config });

watch(
  () => props.config,
  (next) => {
    Object.assign(localConfig, next);
  },
  { deep: true }
);

const workloadText = ref("k1=v1\nk2=v2\nk3=v3");
const stepKey = ref("demo_key");
const stepValue = ref("demo_value");

function runWorkload(): void {
  const operations = workloadText.value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const [key, ...rest] = line.split("=");
      return {
        op: "put",
        key: key.trim(),
        value: rest.join("=").trim()
      } satisfies WorkloadOperation;
    })
    .filter((op) => op.key.length > 0);

  emit("run-workload", operations);
}

function stepOnce(): void {
  emit("step-once", {
    op: "put",
    key: stepKey.value,
    value: stepValue.value
  });
}
</script>

<style scoped>
.config-panel {
  display: grid;
  gap: 12px;
}

.form-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
}

label {
  display: grid;
  gap: 4px;
  font-size: 13px;
}

input,
select,
textarea,
button {
  font: inherit;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.inputs {
  display: grid;
  gap: 10px;
}

.step-box {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(140px, 1fr));
}
</style>
