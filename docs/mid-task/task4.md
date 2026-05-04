我们先转移到task4的新分支，基于总控提示词，现在只完成“任务 4：实现 Flush 和 SSTable 落盘”。

【前置假设】
任务 3 已完成，已有 WAL + MemTable + put。
请先检查已有写路径实现，再增量实现。

【本任务目标】
实现 MemTable flush 到磁盘，生成 Level 0 SSTable 和对应 metadata。

【明确规则】
1. SSTable 采用教学型简化格式：
   - 数据文件：JSONL
   - 元数据文件：JSON
2. flush 时：
   - 将 MemTable 中的数据按 key 排序
   - 落盘为一个不可变 SSTable
   - 生成 SSTableMeta
   - 写入 Level 0
   - 清空 MemTable
3. 需要提供列出当前 level 状态的方法
4. 当前阶段不要求处理 WAL 清理和恢复，只需在注释中说明这是中期简化

【文件组织建议】
请优先采用类似结构：
- data/level_0/
  - sst_000001.jsonl
  - sst_000001.meta.json
- 后续 level 目录可预留但本任务只写 level_0

【需要实现的能力】
1. flush_memtable()
2. 创建 SSTableMeta
3. list_levels() 或等价状态查询函数
4. flush 成功后的状态更新

【建议文件】
- backend/app/core/sstable.py
- backend/app/core/simulator.py
- backend/tests/test_flush.py

【严格限制】
- 不要实现 get
- 不要实现 Bloom Filter
- 不要实现 compaction
- 不要修改前端
- 不要做多级层级调度

【测试要求】
至少覆盖：
1. flush 后生成 JSONL 数据文件
2. flush 后生成 metadata 文件
3. Level 0 中能看到新 SSTable
4. flush 后 MemTable 被清空
5. SSTable 数据按 key 有序
6. metadata 中 min_key / max_key / record_count 正确

【文档要求】
需要在注释或 README 中明确：
- 当前 SSTable 是教学型文件格式
- 当前实现只支持写入 Level 0

请按总控提示词中的固定输出格式回复。