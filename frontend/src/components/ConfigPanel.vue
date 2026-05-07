<template>
  <section class="panel config-panel">
    <div class="section-head">
      <div>
        <h2>参数配置</h2>
        <p>当前页面面向教学演示，支持手动配置写路径与 compaction 相关参数。</p>
      </div>
      <span class="mode-badge">教学型模拟器</span>
    </div>

    <div class="field-group">
      <h3>核心参数</h3>
      <div class="form-grid">
        <label>
          <span class="field-title">MemTable 最大记录数</span>
          <span class="field-code">memtable_max_records</span>
          <input v-model.number="localConfig.memtable_max_records" type="number" min="1" />
          <small>达到该阈值后，下一次写入将提示需要 flush。</small>
        </label>
        <label>
          <span class="field-title">MemTable 最大字节数</span>
          <span class="field-code">memtable_max_bytes</span>
          <input v-model.number="localConfig.memtable_max_bytes" type="number" min="1" />
          <small>教学型近似字节统计，不是精确内存占用。</small>
        </label>
        <label>
          <span class="field-title">Compaction 策略</span>
          <span class="field-code">compaction_strategy</span>
          <select v-model="localConfig.compaction_strategy">
            <option value="stc">stc</option>
            <option value="lcs">lcs</option>
          </select>
          <small>可在 STC 与教学型简化 LCS 之间切换。</small>
        </label>
        <label>
          <span class="field-title">STC 触发表数</span>
          <span class="field-code">stc_trigger_tables</span>
          <input v-model.number="localConfig.stc_trigger_tables" type="number" min="2" />
          <small>某层表数达到阈值后触发 STC 合并。</small>
        </label>
        <label>
          <span class="field-title">L0 触发表数</span>
          <span class="field-code">l0_compaction_trigger_tables</span>
          <input v-model.number="localConfig.l0_compaction_trigger_tables" type="number" min="2" />
          <small>LCS 下 Level 0 到 Level 1 的触发条件。</small>
        </label>
        <label>
          <span class="field-title">最大层数</span>
          <span class="field-code">max_levels</span>
          <input v-model.number="localConfig.max_levels" type="number" min="1" />
          <small>前端会按该上限预留层级展示空间。</small>
        </label>
      </div>
    </div>

    <div class="field-group">
      <h3>扩展参数</h3>
      <div class="form-grid">
        <label>
          <span class="field-title">层级扩展倍数</span>
          <span class="field-code">level_size_multiplier</span>
          <input v-model.number="localConfig.level_size_multiplier" type="number" min="1" step="0.5" />
          <small>用于教学型层容量控制，不直接代表工业级真实大小限制。</small>
        </label>
        <label>
          <span class="field-title">Bloom 每键位数</span>
          <span class="field-code">bloom_bits_per_key</span>
          <input v-model.number="localConfig.bloom_bits_per_key" type="number" min="1" />
          <small>影响 Bloom Filter 体积与误判率。</small>
        </label>
      </div>
    </div>

    <div class="actions">
      <button type="button" class="primary" @click="emit('apply-config', localConfig)">应用配置</button>
      <button type="button" @click="emit('reset-sim')">重置模拟器</button>
      <button type="button" @click="runWorkload">运行 workload</button>
      <button type="button" @click="stepOnce">单步执行</button>
      <button type="button" @click="emit('refresh-state')">刷新状态</button>
    </div>

    <div class="inputs">
      <label>
        <span class="field-title">Workload 输入</span>
        <span class="field-code">当前阶段每行解析为一条 put：key=value</span>
        <textarea v-model="workloadText" rows="6" />
      </label>
      <div class="step-box">
        <label>
          <span class="field-title">单步 key</span>
          <input v-model="stepKey" type="text" />
        </label>
        <label>
          <span class="field-title">单步 value</span>
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
  gap: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.section-head p,
.field-group h3 {
  margin: 4px 0 0;
}

.mode-badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: #edf4ff;
  color: #1c4fa1;
  font-size: 12px;
  font-weight: 600;
}

.field-group {
  display: grid;
  gap: 10px;
}

.form-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
}

label {
  display: grid;
  gap: 5px;
  font-size: 13px;
}

.field-title {
  font-weight: 600;
}

.field-code {
  color: #5f6b7a;
  font-size: 12px;
}

small {
  color: #5f6b7a;
  line-height: 1.4;
}

input,
select,
textarea,
button {
  font: inherit;
}

input,
select,
textarea {
  border: 1px solid #cad3df;
  border-radius: 8px;
  padding: 10px 12px;
}

button {
  border: 1px solid #cad3df;
  border-radius: 8px;
  padding: 10px 14px;
  background: #fff;
  cursor: pointer;
}

.primary {
  background: #1f5fbf;
  color: #fff;
  border-color: #1f5fbf;
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

@media (max-width: 900px) {
  .section-head,
  .form-grid,
  .step-box {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>
