# 中期答辩演示流程

## 演示流程

1. 启动后端与前端
   - `docker compose up --build` 或本地分别启动。

2. 参数配置
   - 解释 memtable 阈值、compaction 策略与触发阈值。

3. 运行 workload（write_heavy）
   - 展示 WAL、MemTable、flush、SSTable 生成。
   - 观察 Level 0 表的变化。

4. 切换到 LCS 策略
   - 应用配置为 `lcs`，重新运行 workload。
   - 说明与 STC 的差异。

5. 事件时间线
   - 说明 `put`、`flush_start/end`、`sstable_created`、`compaction_*` 事件。

6. 指标图表
   - 各层 SSTable 数量
   - compaction 次数
   - 读放大/写放大

7. 导出 Trace
   - 调用 `/sim/export/trace` 展示 JSON/CSV 输出。

## 已完成

- LSM 核心流程：WAL、MemTable、flush、SSTable、Bloom
- STC + 简化版 LCS compaction
- Metrics 与 Trace 导出
- FastAPI REST + WebSocket
- Vue3 最小可演示页面
- 可复现实验脚本

## 未完成

- 删除语义（tombstone）
- 范围查询
- 工业级 compaction 策略与调度
- 更细致的前端可视化和美化

## 后续计划

- 丰富前端可视化（SSTable 布局、compaction 动画）
- 增加 workload 预设与回放控制
- 实验输出图表化
- 更完善的错误处理与参数校验
