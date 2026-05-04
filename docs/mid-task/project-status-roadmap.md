# 项目现状梳理与结题推进建议

更新时间：2026-05-04

## 1. 本文目的

这份文档用于在原有对话历史丢失后，重新建立当前项目的统一认知，回答四个问题：

1. 项目已经做到哪里了？
2. 11 个 task 分别落成了什么？
3. 当前仓库应该以哪条分支为准？
4. 结题阶段接下来最值得做什么？

补充说明：当前这轮整理的目的不是停留在回顾中期成果，而是先把当前工作状态理清，再继续扩充功能，最终完成结题。

本文整理依据主要来自：

- 本地 Git 分支与 merge 历史
- 根目录 `README.md`
- `docs/mid-task/github-pr-merge-notes.md`
- `docs/mid-task/task-plan-reconstruction.md`
- `docs/task2-model-contract.md`
- `docs/task8-metrics-trace.md`
- `docs/task11-experiment-report.md`
- `docs/midterm-demo.md`
- `experiments/output/summary.csv`

说明：当前已经通过 GitHub 公共 API 恢复了 `PR #1` 到 `PR #10` 的合并信息，其中 `task2-task10` 的大部分正文说明已经整理到 `docs/github-pr-merge-notes.md`。只有 `PR #10` 本身没有填写正文，因此 task11 仍需结合本地提交与实验文档理解。

## 2. 当前仓库状态

### 2.1 当前工作分支

- 当前分支：`codex/task11-experiments-midterm`
- 工作区状态：干净，无未提交修改
- 额外状态：存在一个 stash
  - `stash@{0}: On codex/task11-experiments-midterm: task11测试`

### 2.2 分支结构结论

当前仓库最重要的结论不是“功能有没有做完”，而是“哪条分支才是完整集成线”：

- `origin/master` 不是最新、最完整的成果基线。
- 真正连续承接 task2-task10 的主集成链是：
  - `codex/task1-init-scaffold`
  - 再依次合入 task2-task10
- task11 当前在 `codex/task11-experiments-midterm` 上继续前进，包含实验补充与实验报告。

从提交关系看：

- `origin/master` 与当前 `HEAD` 的共同祖先是 `ff70dea`
- `origin/master` 仅额外包含一个“tasks 1-4 合并进 master”的发布型 merge commit
- 当前 `HEAD` 相比 `origin/master` 还有大量后续任务提交未进入 `master`

因此，后续结题、写论文、答辩截图、演示录像、最终交付，都应优先以 `codex/task11-experiments-midterm` 这条线作为事实基线，而不是直接把 `master` 当成最新版本。

## 3. 11 个 Task 的落地情况

根据本地分支与 merge 历史，可还原出如下任务推进链：

| Task | 分支/提交线索 | 当前结论 |
|---|---|---|
| task1 | `codex/task1-init-scaffold` | 初始化 monorepo，建立 backend/frontend/docs/experiments 基础结构 |
| task2 | PR #2 | 统一数据模型与接口契约 |
| task3 | PR #1 | 完成写路径第一阶段：WAL + MemTable |
| task4 | 本地 merge `ff70dea` | 完成 flush 与 Level 0 SSTable 落盘 |
| task5 | PR #4 | 完成读路径与每个 SSTable 的 Bloom Filter |
| task6 | PR #5 | 建立 compaction 框架并实现简化版 STC |
| task7 | PR #6 | 实现简化版 LCS，并支持策略切换 |
| task8 | PR #7 | 增加 metrics 收集与 trace 导出 |
| task9 | PR #8 | 用 FastAPI + WebSocket 暴露模拟器能力 |
| task10 | PR #9 | 增加 Vue3 最小可演示前端 |
| task11 | 当前分支直接提交 | 补充 workload、输出实验结果、形成实验分析文档 |

## 4. 当前已经具备的项目能力

结合 `README.md`、已有 docs 和实验结果，可以确认项目已经形成一个“可演示、可实验、可对比”的教学型 LSM-Tree 模拟系统。

### 4.1 后端能力

已完成：

- WAL 追加写
- MemTable 写入
- 阈值触发 flush
- Level 0 SSTable 落盘
- Bloom Filter
- 简化版 STC
- 简化版 LCS
- metrics 在线统计
- trace 事件导出
- FastAPI REST 接口
- WebSocket 事件推送

### 4.2 前端能力

已完成：

- Vue 3 + TypeScript 最小演示页面
- 参数配置面板
- 层级视图
- 时间线展示
- 指标图表展示

### 4.3 实验能力

已完成：

- workload 驱动的实验脚本：`experiments/run_workloads.py`
- 多 profile 配置：`baseline`、`aggressive_compaction`、`overlap_pressure`
- 多 workload 预设：
  - `write_heavy`
  - `mixed_read_write`
  - `write_heavy_long`
  - `overwrite_hotspot`
  - `range_overlap_stress`
- 自动导出：
  - `summary.json`
  - `summary.csv`
  - 每组实验的 `metrics.json/csv`
  - 每组实验的 `trace.json/csv`

## 5. 已验证的当前可用性

2026-05-04 本地验证结果如下：

- 后端测试：`39 passed`
- 前端构建：成功

前端构建时有一个值得记录但不阻塞答辩的警告：

- 打包后的主 JS chunk 约 `1110 kB`
- Vite 给出 chunk 过大的告警，说明前端后续若要做正式交付或继续扩展，最好再做一次按需拆包或图表依赖瘦身

这意味着当前仓库不是“半成品不可运行”的状态，而是已经具备完整的演示与实验闭环。

## 6. 中期阶段已经讲清楚了什么

从 `docs/midterm-demo.md` 和 `docs/task11-experiment-report.md` 来看，你的中期叙事已经具备一条比较完整的主线：

1. 用前端或接口配置模拟参数
2. 运行 workload
3. 观察写入、flush、SSTable 变化
4. 切换 STC/LCS 对比行为差异
5. 通过 timeline 展示事件过程
6. 通过 metrics 展示放大效应与层级变化
7. 导出 trace/metrics 作为实验证据

实验层面已经得到几类清晰结论：

- 在持续写入压力下，STC 更容易产生更高的 compaction 次数与写放大
- 在重叠范围场景下，LCS 更能体现“按范围整理”的策略特征，但会付出更高写放大
- 在热点覆盖场景下，LCS 相比 STC 有一定读写开销优势，但差异弱于前两类场景

因此，从“中期可讲”角度，这个项目已经不是只停留在功能堆砌，而是形成了“机制实现 + 可视化观察 + 实验对比分析”的基本闭环。

## 7. 当前仍然明确未完成的部分

根据 `README.md` 与 `docs/midterm-demo.md`，当前明确尚未覆盖或仅做了教学简化的部分包括：

- WAL recovery / replay 尚未实现
- MemTable 仍为教学型 `dict`，不是 skiplist
- 删除语义（tombstone）未实现
- 范围查询未实现
- compaction 仍为教学型简化实现
- 没有工业级后台调度、异步 compaction、复杂选表策略
- 前端仍以“最小演示”为主，可视化深度和美观度还有提升空间

这些未完成项并不代表项目失败，反而可以直接作为论文中的“范围控制”和“后续工作”部分。

## 8. 目前最值得警惕的结题风险

### 8.1 仓库主线不清

这是当前最现实的风险。

如果后续论文、答辩 PPT、GitHub 仓库展示、最终提交材料仍然混用 `master` 和 `task11`，会导致：

- 功能清单说不清
- 演示截图和仓库页面对不上
- 评审查看仓库时可能看到的不是最终完整版本

### 8.2 文档分散

目前 docs 里已有 task2、task8、task11 和中期演示文档，但缺少一份统一总览，容易让后来阅读者不知道：

- 总体架构是什么
- 11 个 task 如何串起来
- 哪些功能已完成
- 哪些结果能直接用于论文

### 8.3 结题目标还没有被“收口”

当前项目已经具备中期答辩级别的完整度，但结题要比中期多回答两个问题：

1. 你最终想强调的是“系统实现”还是“实验分析”？
2. 你还要不要做一个额外增强点，作为结题亮点？

如果这两个问题不先定，后续时间很容易分散在很多价值不等的改动上。

## 9. 结题阶段的建议推进顺序

下面这条路线默认以“尽量稳妥完成毕业设计结题”为目标，而不是继续无限扩展功能。

### 第一阶段：先固定最终基线

建议优先完成：

- 明确最终基线分支，以 `codex/task11-experiments-midterm` 为主
- 处理好现有 stash，避免后续误用旧测试现场
- 决定最终是否需要把 task11 合入一条“final/release”分支或 `master`
- 在仓库内补一份总览文档、架构图和任务演化说明

这一步的目标是：先让“你到底完成了什么版本”变得绝对清晰。

### 第二阶段：把论文和答辩直接需要的材料做扎实

建议优先产出：

- 系统架构图
- 写路径 / 读路径 / compaction 流程图
- 任务拆分与阶段成果表
- 实验结果图表化材料
- 最终演示脚本
- 仓库 README 的结题版说明

这一步通常比继续加功能更重要，因为它直接决定结题材料是否有说服力。

### 第三阶段：只挑一个“高性价比增强点”

如果时间允许，建议只补一个增强点，不要同时开多个新坑。候选优先级如下：

- 学术价值优先：补 `tombstone` 删除语义
- 系统完整性优先：补 WAL recovery / replay
- 演示效果优先：加强前端可视化与交互讲解能力

不建议在结题前同时做 tombstone、范围查询、复杂 compaction 和大规模前端重构，这样风险太高。

### 第四阶段：做一次正式收尾验证

结题前建议做：

- 后端全量测试
- 前端生产构建
- 关键 workload 复跑
- 用最终版本重新生成实验图表与截图
- 按答辩脚本完整走一遍

## 10. 我对后续方向的建议

如果目标是“稳妥结题并且讲得漂亮”，我建议后续优先级如下：

1. 先做文档与总规划收口
2. 再做论文/答辩材料沉淀
3. 最后视时间补一个增强点

原因是：

- 你现在已经有完整的系统闭环，不缺“能跑的东西”
- 你当前更缺的是“把成果组织成结题叙事”
- 论文与答辩最怕的不是少一个功能，而是主线不清、版本不清、结论不清

## 11. 下一步可直接展开的工作清单

下一轮如果继续推进，最适合先做的是以下几项之一：

- 把这份总览继续扩展成“毕业设计总规划文档”
- 统一整理 11 个 task 的技术说明与成果摘要
- 生成论文可直接使用的“系统设计 + 实验设计”提纲
- 规划最终分支收口方案（是否合并到 `master` / 新建 release 分支）
- 设计结题阶段唯一的增强点，并拆成可执行任务

---

当前判断：这个项目已经完成了一个质量不错的“教学型 LSM-Tree 可视化模拟器”中期闭环，结题阶段的关键不再是从 0 到 1 补功能，而是从“已有成果”中提炼出稳定版本、清晰叙事和可信实验结论。
