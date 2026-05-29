# Docker 部署与使用配置文档

## 1. 目标

本文档用于说明如何将本项目构建为 Docker 镜像，并通过 Docker Compose 完成一键部署、启动、验证、停止与故障排查。

适用对象：

- 答辩演示环境部署
- 本地复现环境部署
- 交付给老师或同学进行运行验证

## 2. 部署架构

当前 Docker 部署包含两个服务：

1. `backend`
   - FastAPI 服务
   - 负责模拟器核心逻辑、REST API、WebSocket

2. `frontend`
   - Vue 前端容器
   - 运行 Vite 服务
   - 通过代理转发 `/sim`、`/ws` 到后端服务

浏览器访问路径：

```text
Browser -> Frontend(Vite) -> Backend(FastAPI)
```

## 3. 相关文件说明

- `docker-compose.yml`
  - 统一定义前后端服务、端口映射、数据卷、健康检查
- `backend/Dockerfile`
  - 构建后端镜像
- `frontend/Dockerfile`
  - 构建前端镜像
- `.env.example`
  - Docker Compose 环境变量样例

## 4. 镜像构建策略

### 4.1 后端镜像

后端镜像采用：

- `python:3.11-slim`

构建流程：

1. 设置工作目录 `/app`
2. 复制 `requirements.txt`
3. 安装依赖
4. 复制 `app/`
5. 暴露 `8000`
6. 使用 `uvicorn` 启动服务

### 4.2 前端镜像

前端镜像采用：

- `node:20-alpine`

构建流程：

1. 设置工作目录 `/app`
2. 复制 `package.json` 与 `package-lock.json`
3. 执行 `npm ci`
4. 复制前端源码
5. 暴露 `5173`
6. 使用 Vite 启动前端服务

说明：

- 当前 Docker 方案优先保证“可稳定构建并运行”
- 前端容器使用 Vite 运行，而不是 Nginx 静态托管
- 这样可以直接复用现有 `/sim` 和 `/ws` 代理配置

## 5. 环境变量配置

创建 `.env` 文件，可以从 `.env.example` 复制：

```env
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

字段说明：

- `BACKEND_PORT`
  - 主机侧暴露的后端端口
  - 默认 `8000`
- `FRONTEND_PORT`
  - 主机侧暴露的前端端口
  - 默认 `5173`

说明：

- 容器内部端口固定为：
  - 后端 `8000`
  - 前端 `5173`
- `.env` 只控制主机映射端口

## 6. 数据持久化配置

Compose 中定义了命名卷：

- `lsm_backend_data`

挂载位置：

- 容器内 `/app/data`

默认配置下，系统运行时产生的数据会落到：

- `/app/data/wal`
- `/app/data/sst`

作用：

- 容器重建后数据仍然保留
- 便于答辩演示过程中重复查看运行结果

如需彻底清理数据：

```bash
docker compose down -v
```

## 7. 一键启动流程

### 7.1 准备 `.env`

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

或手工创建。

### 7.2 构建并启动

```bash
docker compose up --build -d
```

### 7.3 查看容器状态

```bash
docker compose ps
```

### 7.4 查看日志

```bash
docker compose logs --no-color --tail 100
```

分别查看某个服务：

```bash
docker compose logs --no-color --tail 100 backend
```

```bash
docker compose logs --no-color --tail 100 frontend
```

## 8. 部署后验证

### 8.1 后端健康检查

```bash
curl http://127.0.0.1:8000/health
```

### 8.2 前端页面检查

打开：

- `http://127.0.0.1:5173`

预期：页面能够正常显示 `LSM-Tree Simulator`。

### 8.3 状态接口检查

```bash
curl http://127.0.0.1:8000/sim/state
```

### 8.4 WebSocket 检查

前端页面打开后，应能自动连接：

- `/ws/events`

由于前端容器运行 Vite，浏览器对 `/ws` 的访问会由前端代理到后端。

## 9. 运行方式说明

### 9.1 前端工作方式

Docker 部署时：

- 前端容器运行的是 Vite 服务
- Vite 会直接提供前端页面
- 同时负责把 `/sim` 和 `/ws` 转发给后端

### 9.2 接口代理方式

Compose 中为前端设置了：

- `VITE_BACKEND_HTTP_TARGET=http://backend:8000`
- `VITE_BACKEND_WS_TARGET=ws://backend:8000`

因此浏览器访问前端时：

- 不需要额外修改前端接口地址
- 不需要处理跨域问题

## 10. 常用运维命令

### 10.1 停止服务

```bash
docker compose down
```

### 10.2 停止并删除数据卷

```bash
docker compose down -v
```

### 10.3 重新构建并启动

```bash
docker compose up --build -d
```

### 10.4 仅查看配置展开结果

```bash
docker compose config
```

## 11. 常见问题

### 11.1 `docker compose config` 能过，但 `up --build` 失败

这通常不是项目文件语法问题，而是本机 Docker 权限或镜像拉取问题。

请优先检查：

1. Docker Desktop 是否已启动
2. 当前终端是否有权限访问 Docker 守护进程
3. 网络是否允许拉取所需镜像

### 11.2 前端打不开

检查：

1. `docker compose ps`
2. `FRONTEND_PORT` 是否被占用
3. `docker compose logs frontend`

### 11.3 后端接口不可用

检查：

1. `docker compose logs backend`
2. `http://127.0.0.1:8000/health` 是否可访问
3. `backend` 服务健康检查是否通过

### 11.4 Docker 启动后数据存在哪里？

- 存在 Docker 命名卷 `lsm_backend_data` 中
- 对应容器内路径 `/app/data`

## 12. 当前验证结论

本轮已完成：

- `docker-compose.yml` 配置校验通过
- 前后端 Dockerfile 已整理
- README 与部署文档已补齐

本机验证中遇到的外部问题：

- Docker 守护进程权限受限时，`compose up` 无法连接
- 网络拉取特定基础镜像时可能超时

因此：

- 项目部署文件已经收口到可交付状态
- 如果目标机器的 Docker 权限与网络环境正常，按文档即可启动
