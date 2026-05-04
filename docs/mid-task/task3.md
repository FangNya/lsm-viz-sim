基于总控提示词，现在只完成“任务 3：实现写路径第一阶段（WAL + MemTable）”。

【前置假设】
任务 1 和任务 2 已完成。
请先检查当前已有模型和目录结构，再增量实现。

【本任务目标】
实现最小写路径：
put(key, value) → 先写 WAL → 再写 MemTable → 根据阈值判断是否需要 flush

【实现要求】
1. 实现 WALManager
   - WAL 使用 JSONL 文件
   - 每次 put 追加一行
   - 当前阶段不做 WAL 恢复，只做追加写
2. 实现 MemTable
   - 使用 Python dict 即可
   - 记录最新 key/value
   - 维护记录数与近似字节数
3. 实现 LSMSimulator 或等价核心类的 put 方法
   - 先写 WAL，再写 MemTable
   - 生成自增 seq
   - 返回一个结果对象，至少包含：
     - success
     - seq
     - needs_flush
     - memtable_size_records
     - memtable_size_bytes
4. Flush 触发条件
   - 当记录数达到 memtable_max_records
   - 或近似字节数达到 memtable_max_bytes
   - 只返回“需要 flush”的状态，不在本任务中真正 flush

【建议文件】
优先考虑：
- backend/app/core/wal.py
- backend/app/core/memtable.py
- backend/app/core/simulator.py
- backend/tests/test_put_path.py
- 如需要，可增加一个最小 CLI 示例脚本

【严格限制】
- 不要实现 flush
- 不要实现 SSTable
- 不要实现 get
- 不要实现 Bloom Filter
- 不要实现 compaction
- 不要修改前端

【测试要求】
至少覆盖：
1. put 后 WAL 中有追加记录
2. put 后 MemTable 能查到值
3. seq 正常递增
4. 达到阈值时 needs_flush 为 true
5. 未达到阈值时 needs_flush 为 false

【文档要求】
在 README 或代码注释中明确说明：
- 当前 WAL 只做写入，不做恢复
- 当前 MemTable 是教学型简化实现，不是跳表

请按总控提示词中的固定输出格式回复。