<template>
  <section class="panel config-panel">
    <div class="section-head">
      <div>
        <h2>参数配置</h2>
        <p>当前页面面向教学演示，支持手动配置写路径、查询路径和 compaction 相关参数。</p>
      </div>
      <span class="mode-badge">教学型模拟器</span>
    </div>

    <div class="field-group">
      <h3>预置模板</h3>
      <div class="preset-grid">
        <label>
          <span class="field-title">参数模板</span>
          <select v-model="selectedConfigPresetId">
            <option v-for="preset in configPresets" :key="preset.id" :value="preset.id">
              {{ preset.label }}
            </option>
          </select>
          <small>{{ selectedConfigPreset?.description }}</small>
        </label>
        <div class="preset-actions">
          <button type="button" @click="loadConfigPreset">填充参数模板</button>
          <small>仅填充表单，仍需点击“应用配置”后才会发送到后端。</small>
        </div>
        <label>
          <span class="field-title">Workload 模板</span>
          <select v-model="selectedWorkloadPresetId">
            <option v-for="preset in workloadPresets" :key="preset.id" :value="preset.id">
              {{ preset.label }}
            </option>
          </select>
          <small>{{ selectedWorkloadPreset?.description }}</small>
        </label>
        <div class="preset-actions">
          <button type="button" @click="loadWorkloadPreset">加载 workload 模板</button>
          <small>加载后可继续手工编辑，适合答辩演示与课堂说明。</small>
        </div>
      </div>
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
        <span class="field-code">支持 `put key value`、`get key`，也兼容旧格式 `key=value`</span>
        <textarea v-model="workloadText" rows="8" />
        <small>可混合写入与查询。空行和以 # 开头的注释行会被忽略。</small>
      </label>
      <p v-if="parseErrors.length > 0" class="parse-error">{{ parseErrors.join("；") }}</p>
      <div class="step-box">
        <label>
          <span class="field-title">单步操作</span>
          <select v-model="stepOp">
            <option value="put">put</option>
            <option value="get">get</option>
          </select>
        </label>
        <label>
          <span class="field-title">单步 key</span>
          <input v-model="stepKey" type="text" />
        </label>
        <label v-if="stepOp === 'put'">
          <span class="field-title">单步 value</span>
          <input v-model="stepValue" type="text" />
        </label>
      </div>
      <div v-if="lastStepResponse" class="last-step">
        <strong>最近一步结果</strong>
        <p>{{ summarizeStepResponse(lastStepResponse) }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import { configPresets, parseWorkloadText, workloadPresets, workloadToText } from "../services/demoPresets";
import type { LSMConfig, StepResponse, WorkloadOperation } from "../types/sim";

const props = defineProps<{
  config: LSMConfig;
  lastStepResponse: StepResponse | null;
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

const selectedConfigPresetId = ref(configPresets[0]?.id ?? "");
const selectedWorkloadPresetId = ref(workloadPresets[0]?.id ?? "");
const selectedConfigPreset = computed(() =>
  configPresets.find((preset) => preset.id === selectedConfigPresetId.value) ?? null
);
const selectedWorkloadPreset = computed(() =>
  workloadPresets.find((preset) => preset.id === selectedWorkloadPresetId.value) ?? null
);

const workloadText = ref(workloadToText(workloadPresets[0]?.operations ?? []));
const stepOp = ref<WorkloadOperation["op"]>("put");
const stepKey = ref("demo_key");
const stepValue = ref("demo_value");
const parsedWorkload = computed(() => parseWorkloadText(workloadText.value));
const parseErrors = computed(() => parsedWorkload.value.errors);

function loadConfigPreset(): void {
  if (!selectedConfigPreset.value) {
    return;
  }
  Object.assign(localConfig, selectedConfigPreset.value.values);
}

function loadWorkloadPreset(): void {
  if (!selectedWorkloadPreset.value) {
    return;
  }
  workloadText.value = workloadToText(selectedWorkloadPreset.value.operations);
}

function runWorkload(): void {
  if (parsedWorkload.value.errors.length > 0) {
    return;
  }

  emit("run-workload", parsedWorkload.value.operations);
}

function stepOnce(): void {
  const operation: WorkloadOperation =
    stepOp.value === "get"
      ? {
          op: "get",
          key: stepKey.value
        }
      : {
          op: "put",
          key: stepKey.value,
          value: stepValue.value
        };

  emit("step-once", operation);
}

function summarizeStepResponse(response: StepResponse): string {
  if (response.op === "get" && response.get_result) {
    return response.get_result.found
      ? `get 命中：value=${response.get_result.value}，来源=${response.get_result.source ?? "-"}`
      : "get 未命中：当前 key 不在 MemTable 或 SSTable 中。";
  }

  if (response.op === "put" && response.put_result) {
    return response.flushed_table_id
      ? `put 完成：seq=${response.put_result.seq}，并触发 flush，输出表 ${response.flushed_table_id}。`
      : `put 完成：seq=${response.put_result.seq}，当前 MemTable=${response.put_result.memtable_size_records} 条。`;
  }

  return "最近一步暂无可展示结果。";
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

.preset-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
}

.preset-actions {
  display: grid;
  gap: 6px;
  align-content: start;
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
  grid-template-columns: repeat(3, minmax(140px, 1fr));
}

.parse-error {
  margin: 0;
  color: #b42318;
  font-size: 13px;
}

.last-step {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid #d8e1eb;
  border-radius: 10px;
  background: #f8fbff;
}

.last-step p {
  margin: 0;
  color: #334155;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .section-head,
  .preset-grid,
  .form-grid,
  .step-box {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>
