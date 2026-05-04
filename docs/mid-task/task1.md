基于我刚刚给你的总控提示词，现在只完成“任务 1：初始化仓库和目录骨架”。

【本任务目标】
初始化一个 monorepo 项目骨架，固定技术栈：
- 后端：FastAPI
- 前端：Vue 3 + TypeScript + Vite
- 部署：Docker Compose

【本任务范围】
只做工程骨架，不实现任何 LSM-Tree 业务逻辑。
只需要：
1. 创建 backend / frontend / docs / experiments 的基本目录
2. 后端提供一个 GET /health 健康检查接口
3. 前端提供一个占位页面，页面上明确显示“LSM-Tree Simulator”
4. 提供 docker-compose.yml
5. 提供 backend 和 frontend 各自的 Dockerfile
6. 提供 README.md 和 .env.example
7. 后端提供最小测试，验证 /health 可访问
8. 前端至少保证本地 build 能通过

【建议文件】
优先创建或补充以下文件：
- backend/app/main.py
- backend/requirements.txt
- backend/tests/test_health.py
- backend/Dockerfile
- frontend/package.json
- frontend/tsconfig.json
- frontend/vite.config.ts
- frontend/src/main.ts
- frontend/src/App.vue
- frontend/Dockerfile
- docker-compose.yml
- README.md
- .env.example

【严格限制】
- 不要实现模拟器
- 不要实现 API 业务路由
- 不要引入数据库
- 不要引入 UI 组件库
- 不要引入状态管理库
- 不要做任何和 LSM 逻辑有关的代码

【验收标准】
必须满足：
1. 后端能启动并访问 /health
2. 前端能启动并显示占位页面
3. docker compose up 可以启动前后端
4. pytest 至少通过一个健康检查测试
5. README 写清楚启动方式

请按总控提示词中的固定输出格式回复。