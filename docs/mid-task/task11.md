基于总控提示词，现在只完成“任务 11：实验脚本、Docker 完善与中期答辩材料”。目前的分支都已经合并到task1，可以从task1创建task11分支    

【前置假设】
任务 10 已完成，系统前后端都能跑通。
请先检查当前 README、docker-compose、experiments、docs 目录，再增量实现。

【本任务目标】
补齐可复现实验、Docker 启动、README、以及中期答辩演示说明。

【必须完成的内容】
1. experiments 目录
   - 提供至少 2 组 workload：
     - write_heavy
     - mixed_read_write
   - 能自动运行模拟并导出结果
2. 策略对比
   - 在相同 workload 下比较 STC 与 LCS
   - 导出至少以下结果：
     - flush_count
     - compaction_count
     - sstable_count_by_level
     - read_amplification
     - write_amplification
3. Docker Compose 完善
   - 保证前后端都能通过 docker compose up 启动
4. README 完善
   - 项目简介
   - 一键启动
   - 本地开发
   - 运行实验
   - 常见目录说明
5. docs/midterm-demo.md
   - 写出中期演示流程
   - 列出“已完成 / 未完成 / 后续计划”

【实验脚本要求】
- 优先使用 Python 脚本
- 输出 JSON 或 CSV
- 如需要图表，可生成简单 PNG，但不要引入复杂实验框架
- 每组实验要能重复执行

【建议文件】
- experiments/run_workloads.py
- experiments/workloads/write_heavy.json
- experiments/workloads/mixed_read_write.json
- experiments/output/（如需要）
- docs/midterm-demo.md
- README.md
- docker-compose.yml

【严格限制】
- 不要新增中期范围外特性
- 不要大改前后端架构
- 不要把实验系统做成复杂 benchmark 平台

【验收标准】
至少满足：
1. 通过 README 可以完成启动
2. 至少两组 workload 可以复现
3. 至少一组 STC / LCS 对比结果可导出
4. docs/midterm-demo.md 可以直接拿来准备中期答辩
5. docker compose up 能跑起系统

请按总控提示词中的固定输出格式回复。