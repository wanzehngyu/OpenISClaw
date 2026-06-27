# agent-loop

> **无需 OpenClaw 的对话式 Agent 运行时** — 通过 LLM API 实现自然语言驱动的完整分析流程。

## 运行环境

| 环境 | 使用方式 |
|------|----------|
| **有 Docker** | `make chat` / `make api-run` |
| **无 Docker，有 Python** | 直接运行 Python 脚本 |
| **有 OpenClaw** | `openclaw skill install ...`（原有方式，不受影响） |

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install agent-loop
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
# 核心依赖已包含在项目 requirements 中

# 运行脚本
python skills/agent-loop/scripts/docker-entrypoint.py --help
```

### 方式三：Docker 免安装（无需本地 Python 环境）

克隆项目后，用 Docker 运行 Agent Loop（自然语言交互）或 API Server：

```bash
git clone https://github.com/wanzehngyu/OpenISClaw.git
cd OpenISClaw
cp .env.example .env  # 编辑填入 OPENAI_API_KEY

# 对话式 Agent Loop（自然语言 → 自动分析）
make chat

# HTTP API 服务
make api-run
# 访问 http://localhost:8000 查看所有技能并发起分析
```

详见 [项目 README](https://github.com/wanzehngyu/OpenISClaw) 。


## 本地安装（无 Docker / 无 OpenClaw）

```bash
cd is-econometrics-skills

# 安装依赖
pip install -r skills/agent-loop/requirements-agent.txt

# 安装计量技能依赖（如需要）
pip install linearmodels pandas pyreadstat moderndid stargazer python-docx

# 设置 API Key
export OPENAI_API_KEY=sk-xxx

# 启动交互式对话
python skills/agent-loop/docker-entrypoint.py

# 或启动 HTTP API 服务
python skills/agent-loop/api-server.py
```

## Docker 运行

```bash
cp .env.example .env    # 填入 OPENAI_API_KEY
make build
make chat               # 对话式 Agent Loop
make api-run            # HTTP API 服务（后台）
```

## 两种模式

### 模式一：交互式 Agent Loop（对话式）

```
📩 你: 分析这个面板数据，对ROA做双向固定效应回归，聚类到企业层面

🤖 OpenISClaw：
  推荐技能：panel-regression
  📋 命令：
    python skills/panel-regression/scripts/panel_regression.py \
      --data ./user_data/panel.csv --y roa \
      --x "it_investment_g co_size_ln lev age" \
      --entity firm_id --time year --cluster entity \
      --output_pickle ./user_output/panel_results.pkl

⏎ 是否执行此命令？(y/n, 直接回车执行) → y
⚙️  执行中...
📊 执行结果：...
```

### 模式二：HTTP API（适合程序调用）

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "对面板数据做双向固定效应回归", "data_path": "./user_data/panel.csv"}'

curl http://localhost:8000/skills   # 查看所有可用技能

curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"skill": "panel-regression", "args": ["--data", "./user_data/panel.csv", "--y", "roa", "--entity", "firm_id", "--time", "year"]}'
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API Key（**必需**） | — |
| `OPENAI_BASE_URL` | API Base URL | `https://api.openai.com/v1` |
| `MODEL` | 模型名称 | `gpt-4o` |
| `PORT` | API Server 端口 | `8000` |

## 架构

```
用户输入（自然语言）
    │
    ▼
docker-entrypoint.py / api-server.py
    │  加载 skills_registry.py（动态路径适配）
    │  调用 LLM API
    ▼
LLM 理解任务 → 输出脚本命令
    │
    ▼
subprocess.run("python skills/xxx/scripts/xxx.py ...")
    │
    ▼
结果返回用户
```

## 与本地 OpenClaw 的关系

- **不影响**本地 OpenClaw 用户：`openclaw skill install` 照常工作
- **不依赖**：不依赖 OpenClaw 核心，是独立运行的能力
- **路径自适应**：自动检测 Docker 或本地环境，使用对应路径
- **可共存**：同一机器上可以同时有 OpenClaw 和这套 Agent Loop
