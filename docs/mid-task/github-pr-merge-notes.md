# GitHub PR 合并文案恢复

更新时间：2026-05-04

本文根据 GitHub 公共 API 恢复仓库 `FangNya/lsm-viz-sim` 的已合并 PR 信息，重点保留：

- PR 编号与标题
- 合并时间
- base/head 分支
- PR 正文中的目标、改动范围、范围边界和验证信息

用途：

- 还原之前分 task 推进时的阶段说明
- 为结题文档、论文撰写、答辩讲解提供一手过程材料
- 辅助判断哪些内容是“明确已完成”，哪些是“当时刻意未纳入范围”
- 先理清当前工作基础，再据此继续扩充功能并推进结题

## 获取方式

本次恢复使用公开 GitHub API：

- 仓库 PR 列表：`https://api.github.com/repos/FangNya/lsm-viz-sim/pulls`
- 单个 PR 详情：`https://api.github.com/repos/FangNya/lsm-viz-sim/pulls/{number}`

说明：

- 公开仓库可直接读取 PR `body`
- 如果某个 PR 的 `body` 为 `null`，说明当时提交 PR 时本来就没有正文

## 总体观察

从 GitHub 已合并 PR 看，当前能恢复到的 PR 编号为 `#1` 到 `#10`。

其中有两个需要单独说明：

1. `PR #3`
   - 不是单一 task 开发，而是把 task1-task4 作为第一个里程碑合并到 `master`

2. `PR #10`
   - 已合并，但 `body = null`
   - 说明它只有标题“完成两组基本的workloads测试”，没有额外正文说明

此外，当前本地 `task11` 上还有比 `PR #10` 更后的实验补充提交，因此 task11 的最终状态不能只看 `PR #10`。

## PR 恢复详情

### PR #1

- 标题：`feat(task3): implement write path stage1 (WAL + MemTable)`
- 合并时间：2026-03-07 08:56:22 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task3-write-path-wal-memtable`
- Merge commit：`edb1c8f7403fca935f208f9df7ca19435a0b08cb`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/1

核心目标：

- 实现教学型 LSM 模拟器的写路径第一阶段
- 即 `put(key, value) -> WAL append -> MemTable write -> flush-needed check`

PR 中明确包含：

- `WALManager`，采用 append-only JSONL
- 简化版 `MemTable`
- `LSMSimulator.put(...)` 与 `PutResult`
- `seq` 自增
- 基于记录数和字节数阈值的 `needs_flush`
- `backend/tests/test_put_path.py`

PR 中明确不包含：

- flush 执行
- SSTable 读写
- get 路径
- Bloom filter
- compaction

验证说明：

- PR 正文记录 `pytest -q` 通过，当时为 `13 passed`

### PR #2

- 标题：`feat(task2): define unified data models and interface contracts`
- 合并时间：2026-03-07 08:55:33 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task2-model-contract`
- Merge commit：`51a7aeb40650d86ff9b0b2f029f4de32aa19f67d`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/2

核心目标：

- 为后端建立统一数据模型与接口契约
- 当时明确只做模型与约束，不做 LSM 业务逻辑

PR 中明确包含：

- `backend/app/schemas/models.py`
- `backend/app/core/state.py`
- 模型导出模块
- `docs/task2-model-contract.md`
- `backend/tests/test_models.py`

PR 中列出的核心对象：

- `LSMConfig`
- `Record`
- `WALRecord`
- `SSTableMeta`
- `TraceEvent`
- `MetricsSnapshot`
- `CompactionTask`
- `LevelState`
- `SimulatorState`
- `WorkloadOperation`

PR 中明确不包含：

- put/get 逻辑
- WAL 实现
- flush
- SSTable 读写
- compaction 执行
- 新业务路由

验证说明：

- PR 正文记录 `pytest -q` 通过，当时为 `8 tests`

### PR #3

- 标题：`release: merge tasks 1-4 into master (scaffold -> models -> write path -> flush/sstable)`
- 合并时间：2026-03-07 12:14:37 UTC
- Base：`master`
- Head：`codex/task1-init-scaffold`
- Merge commit：`0a6c0c039d991296285d049175d68a025ba6d632`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/3

核心目标：

- 把 task1-task4 作为第一阶段里程碑发布到 `master`
- 标志项目从设计方案进入“可运行原型”阶段

PR 中明确总结的阶段成果：

- Task 1：Monorepo scaffold
- Task 2：统一模型与接口契约
- Task 3：WAL + MemTable 写路径
- Task 4：flush + Level 0 SSTable 持久化

PR 中明确包含：

- FastAPI `/health`
- Vue3 + TypeScript + Vite 前端占位页
- Docker Compose 与 Dockerfiles
- 基础测试/构建/README
- flush 落盘流程
- Level 0 状态查询

PR 中明确的阶段限制：

- 尚未实现 `get`
- 尚未实现 Bloom
- 尚未实现 compaction
- 尚未实现多层调度
- 尚未实现 WAL recovery/cleanup
- SSTable 当前只写入 `level_0`

PR 中的意义说明：

- 这是第一个“端到端可运行里程碑”
- 为后续 compaction、API、前端可视化建立稳定基础

### PR #4

- 标题：`feat(task5): implement read path and per-sstable bloom filter`
- 合并时间：2026-03-09 06:57:22 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task5-read-bloom`
- Merge commit：`c4a90734c77e0cc8e2f405da400e950b9005caab`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/4

核心目标：

- 增加最小 `get(key)` 读路径
- 为每个 SSTable 增加简化版 Bloom filter
- 增强查询路径可观测性

PR 中明确包含：

- `LSMSimulator.get`
- 查询顺序：
  - MemTable
  - Level 0 SSTable（新表优先）
  - 更高层逻辑预留
- 返回字段：
  - `found`
  - `value`
  - `source`
  - `level`
  - `table_id`
  - `path`
- `backend/app/core/bloom.py`
- flush 时持久化 Bloom 文件
- `load_bloom(meta)` / `find_key(meta, key)`
- `backend/tests/test_get_path.py`

PR 中明确不包含：

- compaction
- tombstone/delete 语义
- range query
- frontend 改动

### PR #5

- 标题：`feat(task6): add compaction framework and simplified STC`
- 合并时间：2026-03-09 07:57:04 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task6-compaction-stc`
- Merge commit：`6a9d166d9b497cc1453e2da600afddf2c62cd4b1`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/5

核心目标：

- 建立 compaction 框架
- 在教学型范围内实现简化版 STC

PR 中明确包含：

- `backend/app/core/compaction/base.py`
- `CompactionResult`
- `backend/app/core/compaction/stc.py`
- STC 规则：
  - 达到 `stc_trigger_tables` 触发
  - 选择最早创建的若干表
  - 按 key 顺序归并
  - 重复 key 保留更大 `seq`
  - 输出到下一层
  - 删除输入表和文件
- `backend/app/core/sstable.py` 的跨层写表、读记录、删文件能力
- simulator 中的同步 compaction 触发
- `compaction_history`
- `backend/tests/test_compaction_stc.py`

PR 中明确不包含：

- LCS
- 异步 compaction 调度
- frontend 改动

### PR #6

- 标题：`feat(task7): add simplified LCS and strategy switching`
- 合并时间：2026-03-09 09:14:50 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task7-compaction-lcs`
- Merge commit：`d378a900c2e6246e17738eeec12902980c848983`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/6

核心目标：

- 增加教学型简化版 LCS
- 支持通过配置在 `stc` 和 `lcs` 间切换

PR 中明确包含：

- `backend/app/core/compaction/lcs.py`
- 简化 LCS 规则：
  - L0 达阈值触发
  - L0 compaction 选择全部 L0 表
  - 按 key range 查找 L1 overlap
  - 合并源表与重叠目标表
  - 重复 key 保留更大 `seq`
  - 输出到下一层
- 高层简化 pushdown 逻辑
- simulator 中的策略切换
- `backend/tests/test_compaction_lcs.py`

PR 中明确不包含：

- 工业级完整 LCS
- seek-based compaction
- tombstone 语义
- frontend 改动

### PR #7

- 标题：`feat(task8): add metrics collector and trace exporter`
- 合并时间：2026-03-09 12:12:37 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task8-metrics-trace`
- Merge commit：`02f375e0681bb7b69be164255ffff09b63a1082e`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/7

核心目标：

- 建立统一 runtime metrics 收集
- 建立 trace 事件发射与稳定 JSON/CSV 导出
- 为实验和可视化提供标准输出

PR 中明确包含：

- `backend/app/metrics/collector.py`
- `backend/app/trace/emitter.py`
- `MetricsSnapshot` 及历史记录
- metrics 导出：
  - JSON
  - CSV
- trace 导出：
  - JSON
  - CSV
- 事件名：
  - `put`
  - `flush_start`
  - `flush_end`
  - `sstable_created`
  - `compaction_start`
  - `compaction_end`
  - `get`
  - `bloom_hit`
  - `bloom_miss`
- `backend/tests/test_metrics_trace.py`
- `docs/task8-metrics-trace.md`

PR 中明确说明：

- `simulated_io_reads` / `simulated_io_writes` 是教学型模拟统计，不是硬件级真实 I/O

PR 中明确不包含：

- FastAPI 包装
- frontend 改动
- 外部队列/数据库

### PR #8

- 标题：`feat(task9): expose simulator via FastAPI REST and WebSocket`
- 合并时间：2026-03-09 12:32:33 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task9-fastapi-ws`
- Merge commit：`9ae546f4a3baea3c8aa20c7bcf260da621ca9e59`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/8

核心目标：

- 用 FastAPI 把 simulator 封装成服务
- 同时提供 REST API 和 WebSocket 事件流

PR 中明确包含：

- REST：
  - `POST /sim/reset`
  - `POST /sim/config`
  - `POST /sim/run_workload`
  - `POST /sim/step`
  - `GET /sim/state`
  - `GET /sim/export/trace?format=json|csv`
- WebSocket：
  - `WS /ws/events`
- `backend/app/api/runtime.py` 中的薄服务层 `SimulatorService`
- `backend/app/api/sim.py`
- API 专用 schema：
  - `backend/app/schemas/api.py`
- `backend/tests/test_api_sim.py`
- `backend/tests/test_ws.py`

PR 中明确不包含：

- auth
- 数据库集成
- 外部队列/worker
- frontend 改动

### PR #9

- 标题：`feat(task10): add minimal Vue3 demo dashboard`
- 合并时间：2026-03-13 02:48:32 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task10-frontend-min-demo`
- Merge commit：`cd9fd6a0881675d710f494f276b817c5ae494368`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/9

核心目标：

- 为中期演示增加单页最小前端
- 明确“功能完整优先于界面精修”

PR 中明确包含：

- 配置面板：
  - `memtable_max_records`
  - `memtable_max_bytes`
  - `compaction_strategy`
  - `stc_trigger_tables`
  - `l0_compaction_trigger_tables`
  - `max_levels`
- 操作按钮：
  - apply config
  - reset simulator
  - run workload
  - step once
  - refresh state
- Level 状态视图
- 实时事件时间线
- ECharts 指标图表：
  - SSTable count by level
  - Compaction count
  - Read/Write amplification
- API 与 WebSocket 接入
- Vite proxy
- Docker compose 注入后端地址

PR 中明确不包含：

- UI framework
- 多页面路由
- 重度样式与动画

### PR #10

- 标题：`完成两组基本的workloads测试`
- 合并时间：2026-03-16 05:48:53 UTC
- Base：`codex/task1-init-scaffold`
- Head：`codex/task11-experiments-midterm`
- Merge commit：`2fc29de50038ce78d3073aa1532cf15013eadd50`
- 页面：https://github.com/FangNya/lsm-viz-sim/pull/10

恢复结果：

- 该 PR 已合并
- 但 GitHub API 返回的 `body` 为 `null`
- 因此无法从 PR 正文恢复更细粒度的“Summary / Changes / Verification”

当前可确认信息：

- 这一步对应 task11 的早期实验推进阶段
- 标题表明当时先完成了“两组基本 workload 测试”
- 后续 task11 在本地分支上还有继续提交，说明 PR #10 不是 task11 的最终完整说明

## 结论

通过 GitHub PR 正文恢复，可以更准确地还原出 task2-task10 每一步的设计边界：

- 每个 task 都有比较清楚的目标控制
- 几乎每个阶段都明确写了 `Out of Scope`
- 中期系统不是“随手堆功能”，而是按任务逐步扩展

这对结题很重要，因为它意味着你后面写论文和答辩时，可以把项目过程讲成一条非常清楚的演进链：

1. 先搭骨架
2. 再立模型契约
3. 再补写路径
4. 再补 flush 与 SSTable
5. 再补读路径与 Bloom
6. 再补 compaction
7. 再补 metrics/trace
8. 再服务化
9. 再前端可视化
10. 最后做实验与分析

这份材料可以直接作为“项目实施过程”和“阶段性成果”章节的依据。
