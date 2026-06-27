# Plan 1：纯 pip 安装 + API Server
## 无 OpenClaw / 无 Docker 环境下的零门槛使用指南

> 本指南适用于：**没有安装 OpenClaw**、**没有 Docker**、但希望用 LLM 自然语言交互完成计量分析的用户。
>
> 另一种方式：若有 Docker，参见 [README](README.md) 的"方式三：Docker 免安装运行"。

---

## 目录

1. [目标](#目标)
2. [前置要求](#前置要求)
3. [安装步骤](#安装步骤)
4. [启动 API 服务](#启动-api-服务)
5. [使用方式](#使用方式)
6. [示例](#示例)
7. [目录结构说明](#目录结构说明)
8. [常见问题](#常见问题)

---

## 目标

在**没有 OpenClaw 也没有 Docker** 的情况下：
- 用 LLM 自然语言驱动完成计量分析
- 不需要懂 Python，不需要会写代码
- 所有分析通过 HTTP API 发起，结果自动返回

```
你的电脑（任意系统）
    │
    ├── 安装 Python 依赖
    │
    ├── 启动 API 服务（本地）
    │
    └── 对 http://localhost:8000 发起分析请求
         │
         ▼
        API 服务内部调用 LLM + skill 脚本
             │
             ▼
         返回发表级表格 / 回归结果 / 诊断报告
```

---

## 前置要求

| 项目 | 要求 |
|------|------|
| **Python** | 3.10 或更高版本 |
| **LLM API Key** | OpenAI API Key（或兼容 API，如 Claude via OpenAI-compatible endpoint） |
| **网络** | 能访问你的 LLM API 域名 |

> 不需要 Docker，不需要 OpenClaw，不需要 Homebrew，不需要 root 权限。

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/wanzehngyu/OpenISClaw.git
cd OpenISClaw
```

### 2. 安装 Python 依赖

```bash
# 核心计量依赖（所有技能通用）
pip install pandas numpy scipy linearmodels pyreadstat

# 表格导出
pip install stargazer python-docx

# 多时点 DID（可选）
pip install moderndid plotnine

# API Server 运行时依赖
pip install openai fastapi uvicorn
```

**或者，一行命令安装所有依赖：**

```bash
pip install pandas numpy scipy linearmodels pyreadstat stargazer python-docx moderndid plotnine openai fastapi uvicorn
```

### 3. 配置 API Key

```bash
# 方式一：写入环境变量（当前终端有效）
export OPENAI_API_KEY=sk-xxx

# 方式二：创建 .env 文件（永久生效）
echo "OPENAI_API_KEY=sk-xxx" > .env
echo "MODEL=gpt-4o" >> .env
```

---

## 启动 API 服务

```bash
cd OpenISClaw
export OPENAI_API_KEY=sk-xxx   # 若未用 .env 文件

# 启动服务（默认端口 8000）
python skills/agent-loop/api-server.py
```

看到以下输出即表示启动成功：

```
🚀 OpenISClaw API Server
   Skills:  /path/to/OpenISClaw/skills
   数据:    /path/to/OpenISClaw/user_data
   输出:    /path/to/OpenISClaw/user_output
   启动于   http://0.0.0.0:8000
```

**后台运行（Linux/macOS）：**

```bash
nohup python skills/agent-loop/api-server.py > api.log 2>&1 &
echo "API 服务已启动，PID: $!"
```

---

## 使用方式

启动后，在**另一个终端窗口**或用 **curl** 发起请求。

### 方式 A：curl 请求（最简单）

```bash
# 查看所有可用技能
curl http://localhost:8000/skills

# 发送分析任务（自然语言）
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task": "对面板数据做双向固定效应回归，被解释变量是ROA，解释变量是企业规模、资产负债率和年龄",
    "data_path": "./user_data/panel.csv"
  }'

# 直接执行指定脚本（无需 LLM 理解）
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "panel-regression",
    "args": [
      "--data", "./user_data/panel.csv",
      "--y", "roa",
      "--x", "co_size_ln lev age",
      "--entity", "firm_id",
      "--time", "year",
      "--output_pickle", "./user_output/panel_results.pkl"
    ]
  }'
```

### 方式 B：Python 客户端

```python
import requests

# 自然语言分析
resp = requests.post("http://localhost:8000/analyze", json={
    "task": "对面板数据做双向固定效应回归",
    "data_path": "./user_data/panel.csv"
})
print(resp.json()["reply"])

# 直接执行脚本
resp = requests.post("http://localhost:8000/execute", json={
    "skill": "panel-regression",
    "args": ["--data", "./user_data/panel.csv", "--y", "roa",
             "--entity", "firm_id", "--time", "year"]
})
print(resp.json()["stdout"])
```

### 方式 C：Postman / Insomnia

- **Method**: `POST`
- **URL**: `http://localhost:8000/analyze`
- **Body** (JSON):
  ```json
  {
    "task": "你的分析需求",
    "data_path": "./user_data/你的数据.csv"
  }
  ```

### 方式 D：浏览器（仅适合 GET 请求）

- 查看技能列表：http://localhost:8000/skills
- 健康检查：http://localhost:8000/health

---

## 示例

### 示例 1：面板回归分析

```bash
# 1. 放入数据
cp your_panel_data.csv user_data/panel.csv

# 2. 发起分析
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task": "用企业规模、资产负债率、年龄作为控制变量，对ROA做双向固定效应回归，聚类到企业层面",
    "data_path": "./user_data/panel.csv"
  }'
```

### 示例 2：工具变量回归

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task": "检验IT投资对企业绩效的内生性，使用政府信息化采购和数字基础设施作为工具变量",
    "data_path": "./user_data/panel.csv"
  }'
```

### 示例 3：多时点 DID

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task": "分析2018-2022年企业数字化转型对绩效的多时点DID效应，生成平行趋势图",
    "data_path": "./user_data/did_panel.csv"
  }'
```

### 示例 4：直接执行（跳过 LLM 理解）

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "panel-regression",
    "args": [
      "--data", "/app/user_data/panel.csv",
      "--y", "roa",
      "--x", "co_size_ln lev age",
      "--entity", "firm_id",
      "--time", "year",
      "--cluster", "entity",
      "--output_pickle", "/app/user_output/panel_results.pkl"
    ]
  }'
```

---

## 目录结构说明

```
OpenISClaw/
├── skills/                          # 所有技能（只读）
│   ├── panel-regression/            # 面板回归技能
│   │   └── scripts/
│   │       └── panel_regression.py  # 实际执行脚本
│   ├── iv-estimator/                # 工具变量技能
│   ├── staggered-did/               # 多时点 DID 技能
│   ├── stargazer-exporter/          # 表格导出技能
│   ├── agent-loop/
│   │   ├── api-server.py           # API 服务（启动这个）
│   │   ├── docker-entrypoint.py    # 对话式入口
│   │   └── skills_registry.py      # 技能注册表
│   └── ...                          # 其他 13 个技能
├── user_data/                       # 👈 放入你的数据文件
│   └── panel.csv                    # 支持 .dta / .csv / .xlsx
├── user_output/                      # 👈 分析结果输出目录
│   ├── panel_results.pkl            # 回归结果
│   └── *.tex                        # LaTeX 表格
└── user_workspace/                   # 交互式工作目录
```

---

## 常见问题

### Q: 启动时报错 "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY=sk-xxx   # 必须设置
python skills/agent-loop/api-server.py
```

### Q: 端口 8000 被占用

```bash
# 方法一：换端口
PORT=8080 python skills/agent-loop/api-server.py

# 方法二：杀掉占用进程
lsof -ti:8000 | xargs kill -9
```

### Q: 技能脚本找不到数据文件

API Server 会自动将 `./user_data/xxx` 映射到项目根目录的 `user_data/`。放入数据后，用相对路径发起请求即可：

```bash
# 放入数据
cp mydata.csv user_data/

# 请求时用相对路径
curl ... -d '{"data_path": "./user_data/mydata.csv"}'
```

### Q: 想用 Claude 或其他 LLM

修改 `OPENAI_BASE_URL` 为兼容端点：

```bash
export OPENAI_API_KEY=sk-ant-xxx
export OPENAI_BASE_URL=https://api.anthropic.com/v1
export MODEL=claude-3-5-sonnet

python skills/agent-loop/api-server.py
```

### Q: 报 "Module not found" 错误

漏装了依赖，补装即可：

```bash
pip install openai fastapi uvicorn linearmodels pandas pyreadstat
```

### Q: 想用 Docker 但没有 Python

参见 [README](README.md) 的"方式三：Docker 免安装运行"——只需安装 Docker，不需要 Python。

---

## 下一步

- 查看所有可用技能：`curl http://localhost:8000/skills`
- 学习每个技能的用法：阅读 `skills/<skill-name>/SKILL.md`
- 深入计量方法：参见 [计量经济学技能文档](https://github.com/wanzehngyu/OpenISClaw)
