基于总控提示词，现在只完成“任务 2：定义统一数据模型与接口契约”。

【前置假设】
任务 1 已完成，项目骨架已经存在。
请先检查当前仓库结构，再增量实现。

【本任务目标】
在 backend 中定义后续模块共用的数据模型、配置模型、事件模型、指标模型、状态模型。
本任务只定义模型和契约，不实现业务逻辑。

【需要定义的核心对象】
请至少定义以下对象，并保证字段清晰、可序列化、可测试：
1. LSMConfig
2. Record
3. WALRecord
4. SSTableMeta
5. TraceEvent
6. MetricsSnapshot
7. CompactionTask
8. LevelState
9. SimulatorState
10. WorkloadOperation

【字段要求】
请至少覆盖这些信息：
- LSMConfig：
  - memtable_max_records
  - memtable_max_bytes
  - max_levels
  - compaction_strategy（只允许 stc / lcs）
  - stc_trigger_tables
  - l0_compaction_trigger_tables
  - level_size_multiplier
  - bloom_bits_per_key
  - wal_dir
  - data_dir
- Record / WALRecord：
  - key
  - value
  - seq
  - op（当前只允许 put）
  - timestamp
- SSTableMeta：
  - table_id
  - level
  - data_file
  - meta_file
  - min_key
  - max_key
  - record_count
  - size_bytes
  - created_at
  - bloom_file（可选）
- TraceEvent：
  - event_id
  - event_type
  - timestamp
  - seq
  - payload
- MetricsSnapshot：
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
- CompactionTask：
  - strategy
  - source_level
  - target_level
  - input_table_ids
  - reason

【实现建议】
- API 输入输出模型可放在 backend/app/schemas/
- 内部状态模型可放在 backend/app/core/
- 优先使用 pydantic + dataclass 的组合，保持清晰
- 要写清楚序列化方式和默认值

【严格限制】
- 不要实现 put/get
- 不要实现 WAL
- 不要实现 flush
- 不要实现 SSTable 读写
- 不要实现 compaction
- 不要新增 FastAPI 业务路由

【必须产出】
1. 模型代码
2. 模型说明文档或注释
3. 单元测试，至少验证：
   - 配置校验
   - 枚举值限制
   - 序列化/反序列化
   - 默认值正确

请按总控提示词中的固定输出格式回复。