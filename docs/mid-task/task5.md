基于总控提示词，现在只完成“任务 5：实现读路径与 Bloom Filter”。目前的分支都已经合并到task1，可以从task1创建task5分支 

【前置假设】
任务 4 已完成，系统已有 MemTable、Level 0 SSTable、metadata。
请先检查已有实现，再增量实现。

【本任务目标】
实现最小 get 查询路径，并为每个 SSTable 增加简化版 Bloom Filter。

【查询规则】
1. 先查 MemTable
2. 再查 Level 0，按“最新 SSTable 优先”顺序查找
3. 再查更高层（即使当前可能还没有数据，也要预留逻辑）
4. 查询结果要返回“命中路径”，供后续 Trace 和前端展示

【Bloom Filter 规则】
1. 每个 SSTable 对应一个简化版 Bloom Filter
2. 不要引入重型第三方依赖
3. 可使用标准库手写最小实现
4. Bloom Filter 需要支持：
   - add(key)
   - might_contain(key)
   - 序列化与反序列化
5. 查询时：
   - 若 Bloom Filter 判定“一定不存在”，跳过该 SSTable
   - 若判定“可能存在”，再读取 SSTable 数据文件

【返回结果要求】
get(key) 的返回结果至少包含：
- found
- value（若存在）
- source（memtable / sstable）
- level（若来自 SSTable）
- table_id（若来自 SSTable）
- path（查询经过了哪些层、哪些表、Bloom 是否跳过）

【建议文件】
- backend/app/core/bloom.py
- backend/app/core/sstable.py
- backend/app/core/simulator.py
- backend/tests/test_get_path.py

【严格限制】
- 不要实现 compaction
- 不要实现删除语义
- 不要实现范围查询
- 不要修改前端

【测试要求】
至少覆盖：
1. 能从 MemTable 命中
2. 能从 SSTable 命中
3. 重复 key 时返回最新值
4. 不存在的 key 能被 Bloom Filter 快速过滤
5. path 字段中能看到查询过程
6. Bloom Filter 能正确持久化并被加载

请按总控提示词中的固定输出格式回复。