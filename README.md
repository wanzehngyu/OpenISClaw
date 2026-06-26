# IS-Econometrics Skills

![Banner](OpenClaw_README_banner.png)

**面向管理信息系统（IS）专业师生的因果推断与计量分析 OpenClaw 技能矩阵**

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue.svg)](https://docs.openclaw.ai)
[![Skills Count](https://img.shields.io/badge/Skills-18-brightgreen?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPjwvc3ZnPg==)](https://github.com/wanzehngyu/OpenISClaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-OpenClaw-orange?style=for-the-badge)](https://github.com/openclaw/openclaw)

---

## 🗞️ 最新更新（Changelog）

### v0.2.1 — 2026-06-26

**新增：agent-loop 模块 — 无 OpenClaw 环境的对话式 Agent 支持**

- 新增 `skills/agent-loop/` 模块，为没有安装 OpenClaw 的用户提供两种无门槛交互方式：
  - **对话式 Agent Loop**（`docker-entrypoint.py`）：交互式命令行，自然语言 → 自动执行分析
  - **HTTP API Server**（`api-server.py`）：REST API，支持 `POST /analyze` 自然语言任务提交
- 新增 `skills_registry.py`：统一注册表，包含 17 个技能的脚本路径、参数说明和使用示例，供 LLM 调用
- 路径自适应：自动检测 Docker 环境或本地原生环境，适配不同路径
- 新增 `requirements-agent.txt`：本地（无 Docker）运行所需依赖清单
- 新增 `make chat` / `make api-run` / `make api` 快捷命令
- 详情见 [方式三：Docker 免安装运行](#方式三docker-免安装运行无需本地-openclaw)

### v0.2.0 — 2026-06-25

**新功能：Docker 免安装运行方式**

- 新增 `Dockerfile` + `docker-compose.yml`，无需本地安装 OpenClaw 即可运行所有技能
- 新增 `Makefile`，一键构建镜像、运行示例分析脚本
- 重新组织目录结构：`user_data/`（数据）、`user_output/`（输出）、`user_workspace/`（工作区）

---

## 🎯 目标

用户上传数据（.dta/.csv/.xlsx）并提出分析需求 → 全自动完成从数据探查到因果推断再到发表级表格输出。

```
用户: "分析这个面板数据，做双向固定效应回归，检验内生性"
  │
  ▼
is-econometrics (主控技能)
  │  识别意图 → panel-regression + iv-estimator
  │
  ▼
panel-regression ──→ TWFE 回归结果 (pickle)
iv-estimator    ──→ 2SLS 诊断报告 (pickle)
  │
  ▼
stargazer-exporter ──→ LaTeX/HTML/Word 发表级表格
```

## 📦 技能清单

| 技能 | 功能 | 触发关键词 |
|------|------|------------|
| **[is-theory-matcher](skills/is-theory-matcher/)** | IS理论推荐与研究设计生成 | "用什么理论"、"理论推荐"、"帮我找理论框架"、"这个现象用XX理论" |
| **[is-econometrics](skills/is-econometrics/)** | 主控入口，协调所有子技能 | "因果推断"、"计量分析"、"回归分析" |
| **[panel-regression](skills/panel-regression/)** | 双向固定效应（TWFE）面板回归 | "面板回归"、"固定效应"、"TWFE"、"聚类标准误" |
| **[iv-estimator](skills/iv-estimator/)** | 2SLS 工具变量回归与内生性诊断 | "工具变量"、"2SLS"、"IV"、"Hausman"、"Sargan" |
| **[staggered-did](skills/staggered-did/)** | 多时点 DID（Callaway-Sant'Anna 估计量） | "多时点DID"、"Staggered DID"、"事件研究"、"平行趋势" |
| **[stargazer-exporter](skills/stargazer-exporter/)** | 学术表格格式化输出 | "输出表格"、"LaTeX"、"三线表"、"发表级" |
| **[economic-database](skills/economic-database/)** | 世界银行/FRED/CSMAR 宏观数据获取 | "下载宏观数据"、"GDP"、"CPI"、"FRED" |
| **[data-cleaning](skills/data-cleaning/)** | 面板数据系统性清洗与预处理 | "清洗数据"、"缺失值"、"异常值"、"数据质量" |
| **[variable-construction](skills/variable-construction/)** | 变量构建、滞后项、增长率、行业调整 | "构建变量"、"生成新变量"、"行业均值"、"去中心化" |
| **[regression-plotter](skills/regression-plotter/)** | 学术级回归系数森林图生成 | "回归系数图"、"森林图"、"系数可视化" |
| **[regression-diagnostics-report](skills/regression-diagnostics-report/)** | 汇总诊断结果，生成完整 Markdown 报告 | "生成诊断报告"、"回归报告" |
| **[difference-in-discontinuities](skills/difference-in-discontinuities/)** | 断点回归（RDD）因果效应分析 | "断点回归"、"RDD"、"模糊断点"、"阈值效应" |
| **[propensity-score-matching](skills/propensity-score-matching/)** | 倾向得分匹配（PSM）反事实估计 | "PSM"、"倾向得分匹配"、"匹配估计" |
| **[survival-analysis](skills/survival-analysis/)** | Cox 比例风险模型与生存分析 | "生存分析"、"Cox模型"、"Kaplan-Meier" |
| **[paper-writer](skills/paper-writer/)** | 实证论文写作：将实证结果整合为完整学术论文 | "写论文"、"生成论文"、"学术论文"、"发表级论文" |
| **[markdown-to-paper](skills/markdown-to-paper/)** | Markdown 论文转换为 Word/PDF，支持 LaTeX 模板 | "转换格式"、"生成 PDF"、"导出 Word" |
| **[word-template-filler](skills/word-template-filler/)** | 将 Markdown 内容填充至 Word 模板，保持格式样式 | "填充模板"、"生成 Word 文档"、"按模板生成论文" |
| **[agent-loop](skills/agent-loop/)** | 无 OpenClaw 环境的对话式 Agent 运行时（LLM 驱动） | "对话式分析"、"AI 助手"、"自然语言分析" |

## 🔧 安装依赖

### 核心计量依赖

```bash
pip install linearmodels pandas pyreadstat

# 多时点 DID（可选）
pip install moderndid plotnine

# 表格导出（可选）
pip install stargazer python-docx
```

### Agent Loop / API Server 依赖（方式三：无 OpenClaw 环境）

```bash
pip install -r skills/agent-loop/requirements-agent.txt
```

包含：`openai` `fastapi` `uvicorn` 及上述核心计量依赖。

## 📥 安装技能

### 方式一：从 ClawHub 安装（推荐）

```bash
openclaw skill install is-theory-matcher
openclaw skill install is-econometrics
openclaw skill install panel-regression
openclaw skill install iv-estimator
openclaw skill install staggered-did
openclaw skill install stargazer-exporter
```

### 方式二：本地 .skill 文件安装

```bash
openclaw skill install ./dist/is-econometrics.skill
openclaw skill install ./dist/iv-estimator.skill
openclaw skill install ./dist/panel-regression.skill
openclaw skill install ./dist/staggered-did.skill
openclaw skill install ./dist/stargazer-exporter.skill
```

### 方式三：Docker 免安装运行（无需本地 OpenClaw）

> 适用于**没有安装 OpenClaw** 的用户，支持三种 Docker 模式：
> 1. **纯脚本** — 直接运行 Python 脚本，适合有技术背景的用户
> 2. **对话式 Agent Loop** — 自然语言交互，LLM 理解需求后自动执行分析
> 3. **HTTP API Server** — 提供 REST API，适合程序调用或二次开发

```bash
# 克隆项目
git clone https://github.com/wanzehngyu/OpenISClaw.git
cd OpenISClaw

# 构建镜像（首次运行需几分钟）
make build

# 放入数据：将你的 .csv/.dta/.xlsx 文件放入 ./user_data/
```

#### 模式一：纯脚本执行（原有，适合有技术背景的用户）

```bash
make example-panel                    # 运行面板回归示例
make skills-list                      # 查看所有可用脚本
docker compose run --rm is-econometrics-shell   # 进入交互式环境
```

#### 模式二：对话式 Agent Loop（自然语言 → 自动分析）

```bash
# 设置 API Key
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY

# 启动交互式对话
make chat
```

对话示例：
```
📩 你: 分析这个面板数据，对ROA做双向固定效应回归，聚类到企业层面
🤖 OpenISClaw： 自动选择 panel-regression 技能，推荐脚本命令
⏎ 是否执行此命令？ → y
⚙️  执行中...
📊 回归结果：...（自动输出发表级表格）
```

#### 模式三：HTTP API Server（适合程序调用）

```bash
# 启动 API 服务
make api-run

# 查看所有可用技能
curl http://localhost:8000/skills

# 发送分析任务
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "对面板数据做双向固定效应回归", "data_path": "/app/user_data/panel.csv"}'

# 直接执行指定脚本
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"skill": "panel-regression", "args": ["--data", "/app/user_data/panel.csv", "--y", "roa", "--entity", "firm_id", "--time", "year"]}'
```

**环境变量（写入 `.env` 文件）：**
```bash
OPENAI_API_KEY=sk-xxx      # 必需（Agent Loop / API 模式）
MODEL=gpt-4o               # 可选，默认 gpt-4o
OPENAI_BASE_URL=...        # 可选，自定义 API 地址
```

**目录说明：**
- `./user_data/` — 放入你的数据文件（.csv/.dta/.xlsx），容器内外共享
- `./user_output/` — 分析结果输出目录，容器内外共享
- `./user_workspace/` — 交互式工作目录
- `./skills/` — 技能包（只读），对应 Git 仓库 skills 目录

**前置要求：** [Docker Desktop](https://www.docker.com/products/docker-desktop/)（macOS/Windows）或 Docker Engine（Linux）

**与本地 OpenClaw 的关系：** 三种 Docker 模式完全独立，不影响本地 OpenClaw 用户的使用体验（`openclaw skill install ...` 照常工作）。

---

## 🚀 快速开始

### 1. 准备数据

将面板数据保存为 `.dta`、`.csv` 或 `.xlsx` 格式，包含：
- 个体 ID 列（如 `firm_id`）
- 时间 ID 列（如 `year`）
- 因变量（如 `roa`）
- 解释变量（如 `it_investment_g`、`co_size_ln`）

### 2. 对话示例

#### 示例一：理论推荐 → 实证研究（新增功能！）

```
用户: 我想研究某个政策对行业的影响是长期的还是短期的现象

智能体: 好的，我来帮你匹配最适合的理论框架。

🔍 语义匹配结果：
  最匹配理论：Punctuated Equilibrium Theory（间断均衡）  匹配度 91%

📐 基于间断均衡理论的研究设计：

  研究问题：政策冲击是否触发行业绩效的结构性断点？
  推荐方法：事件研究法 + 断点回归RDD + 双重差分DID

  是否需要我调用 staggered-did 技能执行实证分析？
```

#### 示例二：传统计量分析

### 3. 单独使用子技能

```bash
# 面板回归
用户: 用企业规模、资产负债率、年龄作为控制变量，对 roa 做双向固定效应回归

# 工具变量
用户: 检验 IT 投资的内生性，使用政府信息化采购和数字基础设施作为工具变量

# 多时点 DID
用户: 分析2018-2022年企业数字化转型对绩效的多时点DID效应，生成平行趋势图
```

## 📊 核心功能

### Panel Regression（双向固定效应回归）

```bash
python skills/panel-regression/scripts/panel_regression.py \
  --data "./data/enterprise_panel.dta" \
  --y "roa" \
  --x "it_investment_g co_size_ln lev age" \
  --entity "firm_id" \
  --time "year" \
  --cluster "entity" \
  --output_pickle "./output/panel_results.pkl"
```

输出：
- 企业层面聚类稳健标准误
- VIF 共线性诊断
- R² (within) 与 F 统计量
- 固定效应状态行

### IV Estimator（工具变量回归）

```bash
python skills/iv-estimator/scripts/iv_regression.py \
  --data "./data/enterprise_panel.dta" \
  --y "roa" \
  --exog "co_size_ln lev age" \
  --endog "it_investment_g" \
  --iv "ln_gov_proc digital_infrastructure" \
  --output_pickle "./output/iv_results.pkl"
```

诊断：
- 第一阶段偏 F 统计量（弱工具变量检验）
- Durbin-Wu-Hausman 内生性检验
- Hansen J 过度识别检验

### Staggered DID（多时点双重差分）

```bash
python skills/staggered-did/scripts/staggered_did_pipeline.py \
  --data "./data/digitalization_panel.dta" \
  --y "roa" \
  --t "year" \
  --id "firm_id" \
  --g "first_adoption_year" \
  --cov "~ co_size_ln + lev + age" \
  --control_group "notyettreated" \
  --est_method "dr" \
  --output_pickle "./output/did_results.pkl" \
  --plot_path "./output/event_study_plot.png"
```

输出：
- 群组-时间 ATT(g,t) 估计
- 事件研究法聚合结果
- 总体 ATT 与置信区间
- 平行趋势检验图（PNG）

### Stargazer Exporter（学术表格输出）

```bash
python skills/stargazer-exporter/scripts/generate_table.py \
  --pickles "./output/panel_results.pkl" "./output/iv_results.pkl" \
  --models "双向固定效应" "工具变量回归" \
  --rename "it_investment_g:IT投资,co_size_ln:企业规模,roa:企业绩效" \
  --title "表1：数字化转型对企业绩效的影响" \
  --output_dir "./output" \
  --formats "latex,html,docx"
```

输出格式：
- LaTeX（Overleaf/ShareLaTeX）
- HTML（网络附件）
- Word（论文章节）

### Paper Writer（实证论文写作）

```bash
# 步骤一：检索文献综述
python skills/paper-writer/scripts/literature_fetcher.py \
  --query "数字化转型对企业绩效的影响" \
  --topic "digital transformation firm performance" \
  --top_k 10 \
  --output "./output/literature_review.md"

# 步骤二：生成论文（整合所有素材）
python skills/paper-writer/scripts/paper_writer.py \
  --research_question "数字化转型对企业绩效的影响" \
  --data_description "A股上市公司2010-2023年面板数据" \
  --variables "roa,digital_transformation,firm_size,leverage,age" \
  --theory "dynamic_capabilities" \
  --hypotheses "H1:数字化转型对企业绩效有显著正向影响;H2:组织冗余正向调节上述关系" \
  --method "panel-regression" \
  --pickle_results "./output/panel_results.pkl" \
  --literature "./output/literature_review.md" \
  --output "./output/paper.md"
```


输出：
- 完整六章学术论文（引言/理论基础/研究假设/方法论/实证结果/讨论）
- 文献综述基于 Tavily 检索的真实 IS 顶刊文献
- 讨论部分含理论贡献、实践贡献、局限与未来方向
- 引用 stargazer-exporter 输出的发表级表格

## 📁 项目结构

```
is-econometrics-skills/
├── README.md
├── LICENSE
├── OpenClaw_README_banner.png     # README 顶部 Banner 图
├── OpenClaw_repo_icon_card.png    # 仓库图标卡片
├── skills/
│   ├── is-theory-matcher/    # IS理论推荐与研究设计生成
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── theory_db.json              # 15个IS理论数据库
│   │   │   ├── matcher.py                  # 语义匹配引擎
│   │   │   └── research_design_generator.py # 研究设计生成器
│   │   └── references/
│   │       └── theory-list.md
│   ├── is-econometrics/        # 主控技能（协调层）
│   │   └── SKILL.md
│   ├── panel-regression/       # 双向固定效应回归
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── panel_regression.py
│   │   └── references/
│   │       └── panel-regression-guide.md
│   ├── iv-estimator/           # 工具变量回归
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── iv_regression.py
│   │   └── references/
│   │       └── iv-diagnostics.md
│   ├── staggered-did/          # 多时点 DID
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── staggered_did_pipeline.py
│   │   └── references/
│   │       └── staggered-did-guide.md
│   ├── stargazer-exporter/     # 表格导出
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── generate_table.py
│   │   └── references/
│   │       └── default_rename_map.md
│   ├── economic-database/     # 宏观经济数据库连接
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── fetch_macro_data.py
│   │   └── references/
│   │       ├── worldbank-indicator-codes.md
│   │       └── fred-common-series.md
│   ├── data-cleaning/          # 数据清洗与预处理
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── data_cleaning.py
│   │   └── references/
│   │       └── data-quality-standards.md
│   ├── variable-construction/ # 变量构建与衍生计算
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── build_variables.py
│   │   └── references/
│   │       └── variable-construction-guide.md
│   ├── regression-plotter/    # 学术级系数可视化
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── plot_regression.py
│   │   └── references/
│   ├── regression-diagnostics-report/ # 诊断报告生成
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── generate_diagnostics_report.py
│   │   └── references/
│   │       └── report-template.md
│   ├── difference-in-discontinuities/ # 断点回归
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── rdd_analysis.py
│   │   └── references/
│   │       └── rdd-guide.md
│   ├── propensity-score-matching/ # 倾向得分匹配
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   └── psm_analysis.py
│   │   └── references/
│   │       └── psm-guide.md
│   └── survival-analysis/      # 生存分析
│       ├── SKILL.md
│       ├── scripts/
│       │   └── survival_analysis.py
│       └── references/
│           └── survival-analysis-guide.md
│   ├── paper-writer/            # 实证论文写作
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── outline_generator.py       # 论文大纲生成
│       │   ├── literature_fetcher.py       # 文献检索（Tavily）
│       │   └── paper_writer.py             # 完整论文生成
│       └── references/
│           ├── paper-structure-template.md # 论文结构模板
│           └── is-journal-standards.md      # IS 期刊格式规范
│   ├── markdown-to-paper/        # Markdown → Word/PDF 格式转换
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── converter.py              # 主转换器（LaTeX/Word）
│       │   └── markdown_parser.py         # Markdown 解析器
│       └── references/
│           ├── default_latex_template.tex  # 默认 LaTeX 模板
│           └── template_config.yaml      # 模板配置
│   ├── word-template-filler/     # Word 模板填充（占位符替换）
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── filler.py                 # 主填充脚本
│   │   │   └── md_parser.py              # Markdown 解析器
│   │   └── references/
│   │       └── template-guide.md         # 模板制作指南
│   └── agent-loop/               # 无 OpenClaw 环境的 Agent 运行时
│       ├── SKILL.md
│       ├── skills_registry.py     # 技能注册表（供 LLM 调用）
│       ├── docker-entrypoint.py   # 对话式 Agent Loop
│       ├── api-server.py          # HTTP API Server
│       └── requirements-agent.txt # 本地运行依赖
└── dist/                       # 打包的 .skill 文件
    ├── is-econometrics.skill
    ├── panel-regression.skill
    ├── iv-estimator.skill
    ├── staggered-did.skill
    └── stargazer-exporter.skill
```

## 🔒 安全说明

- 所有数据分析在沙盒环境运行，敏感数据不外传
- 默认只读模式，禁止自动删除文件
- 高风险操作（如 exec）默认需人工确认
- 建议配合 Docker 沙盒模式（`sandbox.mode: all`）使用

## 📚 学术引用

若在学术研究中使用这些技能，建议引用：

> 万院士 (2026). IS-Econometrics: 面向信息系统专业的因果推断与计量分析 OpenClaw 技能矩阵. GitHub Repository.

相关计量方法论：

- Callaway, B., & Sant'Anna, P. H. (2021). "Difference-in-differences with multiple time periods." *Journal of Econometrics*.
- Stock, J. H., & Yogo, M. (2005). "Testing for weak instruments in linear IV regression."
- Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel Data*.

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！请确保：
1. 新技能符合 OpenClaw Skill 规范
2. 所有 Python 脚本通过语法检查
3. SKILL.md 通过 `quick_validate.py` 验证

## 📄 License

MIT License