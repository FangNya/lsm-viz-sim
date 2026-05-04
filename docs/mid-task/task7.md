基于总控提示词，现在只完成“任务 7：新增简化版 LCS，并支持策略切换”。目前的分支都已经合并到task1，可以从task1创建task7分支，  

【前置假设】
任务 6 已完成，compaction 框架和 STC 已存在。
请先检查现有 compaction 抽象与配置模型，再增量实现。

【本任务目标】
新增一个“教学型简化版 Leveled Compaction（LCS）”，并支持通过配置在 STC / LCS 之间切换。

【LCS 简化规则】
1. 当 Level 0 的 SSTable 数量达到 l0_compaction_trigger_tables 时，触发 L0 → L1 compaction
2. L0 触发时：
   - 选择当前所有 L0 SSTable
   - 找出 L1 中与其 key range 重叠的 SSTable
   - 将这些表一起合并，输出到 L1
3. 对于 L1 及更高层：
   - 只需要实现一个简化的“层大小超限后向下合并”逻辑
   - 不需要实现工业级复杂挑选策略
4. 重复 key 仍然以 seq 更大的记录为准
5. 保持策略接口统一，可通过配置切换 stc / lcs

【需要实现的能力】
1. LCS 策略类
2. 配置切换逻辑
3. 策略选择入口
4. L0 → L1 的重叠范围 compaction
5. 至少一个高层继续向下压缩的简化逻辑

【建议文件】
- backend/app/core/compaction/lcs.py
- backend/app/core/compaction/base.py
- backend/app/core/simulator.py
- backend/tests/test_compaction_lcs.py

【严格限制】
- 不要追求工业级 LCS 完整实现
- 不要实现 seek-based compaction
- 不要实现 tombstone
- 不要修改前端

【测试要求】
至少覆盖：
1. 配置能在 stc / lcs 间切换
2. L0 达到阈值时会触发 LCS
3. 能正确找到重叠范围 SSTable
4. 合并后输出层正确
5. 同一 workload 下，STC 与 LCS 的层级行为不同
6. 两种策略都能跑通现有核心流程

【文档要求】
请明确写出：
- 这是教学型简化版 LCS
- 与工业级实现相比，省略了哪些复杂逻辑

请按总控提示词中的固定输出格式回复。