---
name: stargazer-exporter
description: 将 linearmodels 回归结果输出为发表级学术表格（LaTeX/HTML/Word）。当用户提出"输出表格"、"生成表格"、"LaTeX"、"发表级表格"、"三线表"、"回归表格"、"Stargazer"时激活。自动读取 panel-regression、iv-estimator、staggered-did 的 pickle 结果，进行变量重命名、显著性星标排版、固定效应指示行追加，输出可直接嵌入 Overleaf 或 Microsoft Word 的标准化格式。
metadata:
  {
    "openclaw": {
      "emoji": "📋",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-stargazer",
          "kind": "pip",
          "package": "stargazer",
          "label": "Install stargazer (pip install stargazer)"
        },
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
        }
      ]
    }
  }
---

# Stargazer Exporter: 学术表格格式化输出

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install stargazer-exporter
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
pip install pandas numpy scipy stargazer

# 运行脚本
python skills/stargazer-exporter/scripts/generate_table.py --help
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

## 概述

将多个回归模型的结果聚合为标准化学术表格，支持 LaTeX（Overleaf/ShareLaTeX）、HTML、ASCII 和 Word 四种输出格式。自动完成：

- 变量重命名（中英文标签映射）
- 显著性星标排版（`*** p<0.01`, `** p<0.05`, `* p<0.1`）
- 固定效应状态指示行
- 模型元数据注释（样本量、R²、F 统计量）
- 跨模型并排输出（不同模型列对比）

## 核心功能

- **多模型并排**：支持 2-4 个模型列并排对比（FE、IV、DID 等）
- **变量标签重命名**：通过映射表将数据库晦涩简写转为学术清晰标签
- **固定效应指示行**：自动追加个体/时间固定效应状态
- **聚类标准误标注**：标注聚类维度和聚类数
- **跨库兼容**：原生支持 `linearmodels` 结果对象（PanelOLS、IV2SLS）
- **多格式输出**：LaTeX（默认）、HTML、ASCII、Word

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pickles` | string | ✅ | pickle 文件路径列表（空格分隔，至少 1 个） |
| `--models` | string | ❌ | 模型名称标签列表（空格分隔，如 "TWFE" "IV-2SLS"） |
| `--rename` | string | ❌ | 重命名映射，格式：`old1:new1,old2:new2` |
| `--title` | string | ❌ | 表格标题（默认："实证计量回归分析结果"） |
| `--output_dir` | string | ✅ | 输出目录路径 |
| `--formats` | string | ❌ | 输出格式，如 `latex,html,docx`（默认：`latex`） |

## 执行流程

```bash
python {baseDir}/scripts/generate_table.py \
  --pickles "./output/panel_results.pkl" "./output/iv_results.pkl" \
  --models "双向固定效应" "工具变量回归" \
  --rename "it_investment_g:IT投资,co_size_ln:企业规模,roa:企业绩效" \
  --title "表1：数字化转型对企业绩效的影响" \
  --output_dir "./output" \
  --formats "latex,html"
```

## 重命名映射规范

| 原变量名 | 学术标签 |
|----------|----------|
| `it_investment_g` | IT Investment (%) |
| `co_size_ln` | Firm Size (log) |
| `lev` | Leverage Ratio |
| `roa` | Return on Assets |
| `predicted_it` | IT Investment (IV) |
| `ln_gov_proc` | Government Procurement (log) |
| `age` | Firm Age |
| `tfp_lp` | Total Factor Productivity (LP) |

默认重命名映射定义在 `references/default_rename_map.md`。

## 输出格式说明

### LaTeX 三线表（默认）

输出文件：`regression_table.tex`

```latex
\begin{table}[htbp]
  \centering
  \caption{表1：数字化转型对企业绩效的影响}
  \begin{tabular}{lcc}
    \hline
    & (1) TWFE & (2) IV-2SLS \\
    \hline
    IT Investment (\%) & 0.0423^{**} & 0.0612^{***} \\
                       & (0.0121) & (0.0187) \\
    Firm Size (log)    & 0.0156^{**} & 0.0234^{***} \\
                       & (0.0067) & (0.0089) \\
    \hline
    个体固定效应       & Yes & Yes \\
    时间固定效应       & Yes & Yes \\
    样本量             & 4,832 & 4,832 \\
    R² (within)        & 0.3412 & 0.2941 \\
    \hline
    \multicolumn{3}{l}{\footnotesize 括号内为聚类稳健标准误；*** p<0.01, ** p<0.05, * p<0.1} \\
  \end{tabular}
\end{table}
```

### HTML 表格

输出文件：`regression_table.html`，可直接嵌入期刊网络附件或电子邮件。

### Word 表格

输出文件：`regression_table.docx`，可直接插入 Microsoft Word 论文章节。

## 多模型并排输出

当传入多个 pickle 时，表格列依次排列：

```
| 变量       | (1) TWFE  | (2) IV-2SLS | (3) DID    |
|------------|-----------|-------------|------------|
| IT投资     | 0.0423**  | 0.0612***   | 0.0382*    |
|            | (0.0121)  | (0.0187)    | (0.0127)   |
| 企业规模   | 0.0156**  | 0.0234***   |            |
|            | (0.0067)  | (0.0089)    |            |
|------------|-----------|-------------|------------|
| 固定效应   | Yes       | Yes         | Yes        |
| 样本量     | 4,832     | 4,832       | 4,832      |
| R²         | 0.3412    | 0.2941      |            |
```

## 显著性星标规范

| P 值 | 星标 | LaTeX |
|------|------|-------|
| p < 0.01 | `***` | `^{***}` |
| p < 0.05 | `**` | `^{**}` |
| p < 0.1 | `*` | `^{*}` |
| p ≥ 0.1 | （无） | （无） |

## 固定效应行规范

学术表格通常在底部追加固定效应状态行：

```
个体固定效应       & Yes & Yes \\
时间固定效应       & Yes & Yes \\
双向聚类标准误      & 企业层面 & 企业层面 \\
样本量             & 4,832 & 4,832 \\
R² (within)        & 0.3412 & 0.2941 \\
```

## 局限性说明

- Stargazer 对 `linearmodels.PanelOLS` 的支持需要通过适配器桥接（见 `scripts/generate_table.py` 中的适配逻辑）
- `moderndid` 的 `aggte` 对象输出需要先提取标量再传入 Stargazer
- Word 输出依赖 `docx` 库，须提前安装

## 相关资源

- `references/default_rename_map.md` — 默认变量重命名映射表
- `references/table-format-guide.md` — 期刊表格格式规范（含三线表排版要求）
- `references/stargazer-api.md` — Stargazer API 详解与自定义选项
