基于总控提示词，现在只完成“任务 8：实现 Metrics 采集和 Trace 导出”。目前的分支都已经合并到task1，可以从task1创建task8分支 

【前置假设】
任务 7 已完成，系统已有 put/get/flush/STC/LCS。
请先检查已有核心流程，再增量实现。

【本任务目标】
为模拟器增加统一的 metrics collector 和 trace emitter，支持 JSON / CSV 导出。

【必须采集的事件】
请至少支持以下事件名：
- put
- flush_start
- flush_end
- sstable_created
- compaction_start
- compaction_end
- get
- bloom_hit
- bloom_miss

【必须采集的指标】
至少包括：
- total_puts
- total_gets
- memtable_size_records
- memtable_size_bytes
- sstable_count_by_level
- flush_count
- compaction_count
- read_amplification
- write_amplification
- simulated_io_reads
- simulated_io_writes

【实现要求】
1. 所有关键路径都能发出 TraceEvent
2. MetricsSnapshot 能在系统运行中持续更新
3. 支持导出 JSON
4. 支持导出 CSV
5. 导出的格式要稳定，方便后续实验脚本和前端读取

【建议文件】
- backend/app/metrics/collector.py
- backend/app/trace/emitter.py
- backend/app/core/simulator.py
- backend/tests/test_metrics_trace.py

【严格限制】
- 本任务不做 FastAPI 封装
- 本任务不改前端
- 不要引入消息队列
- 不要引入数据库

【测试要求】
至少覆盖：
1. put / get / flush / compaction 会产生对应 trace
2. metrics 能正确累加
3. JSON 导出可读
4. CSV 导出表头稳定
5. read_amplification / write_amplification 有明确的计算逻辑并体现在文档中

【文档要求】
请明确说明：
- 各指标的定义
- 事件 payload 的结构
- 哪些值是模拟统计值，哪些值是实际计数值

请按总控提示词中的固定输出格式回复。