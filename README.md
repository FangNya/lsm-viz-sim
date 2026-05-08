# LSM-Tree Visual Simulator

本项目是一个面向教学演示与本科毕设答辩的 LSM-Tree 可视化与交互式模拟系统。
目标是用清晰、可观测、可复现实验的方式展示 LSM-Tree 的写入路径、查询路径、Flush、SSTable、Bloom Filter、STC/LCS Compaction、Metrics 与 Trace 行为。

## 1. 项目定位

- 后端：Python 3.11 + FastAPI
- 前端：Vue 3 + TypeScript + Vite + ECharts
- 部署：Docker Compose
- 存储：本地文件
- 测试：`pytest` + 前端 `npm run build`

当前系统为教学型模拟器，不追求工业级数据库实现复杂度。

## 2. 目录结构

- `backend/`：FastAPI 服务、LSM 模拟核心、测试
- `frontend/`：Vue 前端页面
- `docs/`：中期/结题说明文档、部署文档
- `experiments/`：workload、实验脚本、实验结果
- `docker-compose.yml`：一键部署入口
- `.env.example`：Docker 端口配置样例

## 3. 当前核心语义

- WAL：JSONL 追加写，当前不做恢复回放
- MemTable：教学型多版本语义实现；同 key 多次 `put` 会保留多个版本
- Flush：会把 MemTable 中的多版本记录落到 SSTable
- SSTable：`JSONL + metadata JSON + bloom JSON`
- Query：先查 MemTable，再查 SSTable；支持 Bloom Filter 快速跳过
- STC：同步触发的教学型简化实现
- LCS：同步触发的教学型简化实现，包含高层范围裁剪与候选表定位
- Metrics / Trace：进程内采集，可导出 JSON / CSV

## 4. 本地开发

### 4.1 后端

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

### 4.2 前端

```bash
cd frontend
npm install
npm run dev
```

打开：

- `http://127.0.0.1:5173`

### 4.3 测试

后端：

```bash
cd backend
pytest
```

前端构建：

```bash
cd frontend
npm run build
```

## 5. Docker 一键部署

### 5.1 准备配置

复制环境变量样例：

```bash
copy .env.example .env
```

或手动创建 `.env`：

```env
BACKEND_PORT=8000
FRONTEND_PORT=4173
```

### 5.2 启动服务

```bash
docker compose up --build -d
```

### 5.3 查看状态

```bash
docker compose ps
```

```bash
docker compose logs --no-color --tail 100
```

### 5.4 访问地址

- 前端主页：`http://127.0.0.1:4173`
- 后端健康检查：`http://127.0.0.1:8000/health`
- 后端状态接口：`http://127.0.0.1:8000/sim/state`

说明：

- Docker 部署下，前端容器运行的是 Vite 服务
- Vite 会把 `/sim` 和 `/ws` 代理到后端容器
- 浏览器访问前端时，不需要额外配置后端地址

### 5.5 停止服务

```bash
docker compose down
```

如果要连同数据卷一起删除：

```bash
docker compose down -v
```

## 6. Docker 镜像说明

### 6.1 后端镜像

- 基础镜像：`python:3.11-slim`
- 启动命令：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6.2 前端镜像

- 基础镜像：`node:20-alpine`
- 启动命令：

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

- 容器内通过 Vite 代理访问后端：
  - `VITE_BACKEND_HTTP_TARGET=http://backend:8000`
  - `VITE_BACKEND_WS_TARGET=ws://backend:8000`

### 6.3 数据持久化

Docker Compose 默认创建命名卷：

- `lsm_backend_data`

该卷挂载到容器内：

- `/app/data`

因此默认配置下生成的：

- `./data/wal`
- `./data/sst`

都会持久化在 Docker 卷中，而不是随着容器删除而丢失。

## 7. 后端接口

### 7.1 REST API

- `GET /health`
- `POST /sim/reset`
- `POST /sim/config`
- `POST /sim/run_workload`
- `POST /sim/step`
- `GET /sim/state`
- `GET /sim/export/trace?format=json|csv`

### 7.2 WebSocket

- `WS /ws/events`

推送消息类型包括：

- `trace_event`
- `metrics_update`
- `simulator_reset`
- `config_updated`

## 8. 示例请求

### 8.1 应用配置

```bash
curl -X POST http://127.0.0.1:8000/sim/config \
  -H "Content-Type: application/json" \
  -d '{
    "memtable_max_records": 4,
    "memtable_max_bytes": 1024,
    "max_levels": 4,
    "compaction_strategy": "stc",
    "stc_trigger_tables": 2,
    "l0_compaction_trigger_tables": 2,
    "level_size_multiplier": 4.0,
    "bloom_bits_per_key": 10,
    "wal_dir": "./data/wal",
    "data_dir": "./data/sst"
  }'
```

### 8.2 执行 workload

```bash
curl -X POST http://127.0.0.1:8000/sim/run_workload \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [
      {"op": "put", "key": "k1", "value": "v1"},
      {"op": "put", "key": "k1", "value": "v2"},
      {"op": "get", "key": "k1"}
    ]
  }'
```

### 8.3 查看状态

```bash
curl http://127.0.0.1:8000/sim/state
```

## 9. 实验脚本

运行默认实验集：

```bash
python experiments/run_workloads.py --out experiments/output_final_validation
```

实验输出包括：

- `summary.json` / `summary.csv`
- `metrics.json` / `metrics.csv`
- `trace.json` / `trace.csv`
- `validation.json`

## 10. 常见问题

### 10.1 为什么 Docker 前端地址是 4173，不是 5173？

- 本地 Vite 开发模式默认使用 `5173`
- Docker 部署时，Compose 默认把主机 `4173` 映射到容器 `5173`
- 具体以 `.env` 中的 `FRONTEND_PORT` 为准

### 10.2 为什么浏览器访问前端后还能直接请求 `/sim`？

- 因为前端容器内的 Vite 已经把 `/sim` 和 `/ws` 代理到后端容器
- Docker 部署时不需要手工修改前端接口地址

### 10.3 Docker 启动后数据存在哪里？

- 存在 Docker 命名卷 `lsm_backend_data` 中
- 对应容器内路径 `/app/data`

## 11. 详细部署文档

更详细的 Docker 打包、配置和运维说明见：

- [docs/docker-deployment.md](docs/docker-deployment.md)
