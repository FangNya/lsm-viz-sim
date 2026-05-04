基于总控提示词，现在只完成“任务 6：实现 Compaction 框架，先做 STC”。目前的分支都已经合并到task1，可以从task1创建task6分支， 

【前置假设】
任务 5 已完成，系统已有 flush、SSTable、get、Bloom Filter。
请先检查已有层级状态和 SSTable 元数据，再增量实现。

【本任务目标】
实现 compaction 的基础框架，并先完成 Size-Tiered Compaction（STC）。

【STC 简化规则】
1. 当某一层的 SSTable 数量达到 stc_trigger_tables 时，触发 compaction
2. 选择该层中最早生成的 stc_trigger_tables 个 SSTable 作为输入
3. 合并时按 key 排序
4. 若多个输入 SSTable 中存在相同 key，则以 seq 更大的记录为准
5. 合并结果写入下一层
6. 旧 SSTable 标记删除或物理删除，更新元数据
7. 要记录 compaction 前后层级状态

【需要实现的能力】
1. compaction 策略接口或抽象基类
2. STC 策略实现
3. 判断是否触发
4. 挑选输入文件
5. 执行合并
6. 生成新 SSTable
7. 更新层级状态

【建议文件】
- backend/app/core/compaction/base.py
- backend/app/core/compaction/stc.py
- backend/app/core/simulator.py
- backend/tests/test_compaction_stc.py

【严格限制】
- 本任务只做 STC
- 不要实现 LCS
- 不要修改前端
- 不要引入后台线程调度
- compaction 可以先采用同步触发方式

【测试要求】
至少覆盖：
1. 达到阈值时会触发 STC
2. 选中的输入表正确
3. 合并后 key 顺序正确
4. 重复 key 以最新 seq 为准
5. 新 SSTable 出现在下一层
6. 旧 SSTable 被正确移除
7. 层级状态更新正确

【文档要求】
请在注释或 README 中明确：
- 当前 STC 是教学型简化实现
- 当前 compaction 为同步触发，不是后台异步任务

请按总控提示词中的固定输出格式回复。