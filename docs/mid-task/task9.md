基于总控提示词，现在只完成“任务 9：封装为 FastAPI 服务并提供 WebSocket”。目前的分支都已经合并到task1，可以从task1创建task9分支  

【前置假设】
任务 8 已完成，后端模拟器、metrics、trace 已经存在。
请先检查已有核心类，再增量实现 API 层。

【本任务目标】
将模拟器封装成 FastAPI 服务，提供 REST API 和 WebSocket 事件推送。

【必须提供的接口】
请实现以下接口：
1. POST /sim/reset
2. POST /sim/config
3. POST /sim/run_workload
4. POST /sim/step
5. GET /sim/state
6. GET /sim/export/trace
7. WebSocket /ws/events

【接口要求】
- /sim/config：接收并保存 LSMConfig
- /sim/reset：重置模拟器状态
- /sim/run_workload：接收一组 WorkloadOperation 并顺序执行
- /sim/step：执行单步操作，便于前端逐步演示
- /sim/state：返回当前配置、levels、metrics、最近事件
- /sim/export/trace：支持导出 json 或 csv
- /ws/events：推送关键事件和指标更新

【实现要求】
1. API 层不要直接堆业务逻辑，应调用核心模拟器
2. WebSocket 要能在 put / flush / compaction 等阶段推送事件
3. 需要清晰的 request/response schema
4. 需要至少一个集成测试，覆盖 run_workload 或 state 查询

【建议文件】
- backend/app/api/sim.py
- backend/app/main.py
- backend/app/schemas/
- backend/tests/test_api_sim.py
- backend/tests/test_ws.py（如可行）

【严格限制】
- 不要加鉴权
- 不要接数据库
- 不要修改前端
- 不要引入 Celery、Redis 等外部组件

【测试要求】
至少覆盖：
1. /sim/config 可正常写入配置
2. /sim/reset 可重置状态
3. /sim/run_workload 能驱动模拟器执行
4. /sim/state 能返回 levels 和 metrics
5. /sim/export/trace 能导出内容
6. WebSocket 至少能收到一类关键事件

【文档要求】
README 中补充：
- API 启动方式
- 示例请求
- WebSocket 使用方式

请按总控提示词中的固定输出格式回复。
