基于总控提示词，现在只完成“任务 10：实现 Vue3 最小可演示前端”。目前的分支都已经合并到task1，可以从task1创建task10分支   

【前置假设】
任务 9 已完成，FastAPI REST 和 WebSocket 已可用。
请先检查 frontend 当前结构，再增量实现。

【本任务目标】
实现一个“最小可演示”的单页面前端，用于中期答辩展示。
重点是可用和清晰，不追求 UI 美化。

【页面必须包含 4 个区域】
1. 参数配置区
2. 层级状态展示区
3. 事件时间线区
4. 指标图表区

【功能要求】
1. 参数配置区
   - 支持编辑主要参数：
     - memtable_max_records
     - memtable_max_bytes
     - compaction_strategy
     - stc_trigger_tables
     - l0_compaction_trigger_tables
     - max_levels
   - 提供按钮：
     - 应用配置
     - 重置模拟器
     - 运行 workload
     - 单步执行
2. 层级状态展示区
   - 展示各 level 下的 SSTable 列表
   - 每个 SSTable 至少显示：
     - table_id
     - key range
     - record_count
3. 事件时间线区
   - 实时显示来自 WebSocket 的事件
4. 指标图表区
   - 至少 3 张图：
     - 各层 SSTable 数量
     - compaction 次数
     - 写放大或读放大

【技术限制】
- 前端固定使用 Vue 3 + TypeScript + Vite
- 图表使用 ECharts
- 不要引入 Element Plus、Ant Design Vue 等 UI 框架
- 不要引入 Pinia，优先使用 Composition API + 本地状态
- 不需要登录页，不需要多页面路由；如已有 router，可保留但只做一个主页面

【建议文件】
- frontend/src/views/SimulatorView.vue
- frontend/src/components/ConfigPanel.vue
- frontend/src/components/LevelView.vue
- frontend/src/components/EventTimeline.vue
- frontend/src/components/MetricsCharts.vue
- frontend/src/services/api.ts
- frontend/src/services/ws.ts
- frontend/src/types/

【严格限制】
- 不要修改后端核心逻辑
- 不要做复杂样式系统
- 不要过度动画
- 不要加入与中期无关的页面

【测试/验证要求】
至少做到：
1. 前端能拉取 /sim/state
2. 前端能调用配置、重置、运行接口
3. 前端能接收 WebSocket 事件
4. 图表能更新
5. npm run build 能通过

【文档要求】
请补充前端本地运行说明，并注明：
- 这是中期最小可演示页面
- 后续可以再做美化，但当前以功能完整为主

请按总控提示词中的固定输出格式回复。