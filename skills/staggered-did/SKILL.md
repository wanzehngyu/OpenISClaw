---
name: staggered-did
description: 执行多时点/渐进式双重差分（Staggered DID）因果效应分析。当用户提出"多时点DID"、"Staggered DID"、"Callaway-Sant'Anna"、"事件研究"、"平行趋势"、"动态处理效应"、"ATT(g,t)"或"交错DID"时激活。基于 moderndid 库的 Callaway-Sant'Anna 双重稳健估计量，自动完成群组-时间 ATT 估计、事件研究聚合、平行趋势检验可视化。
metadata:
  {
    "openclaw": {
      "emoji": "🦀",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-moderndid",
          "kind": "pip",
          "package": "moderndid",
          "label": "Install moderndid (pip install moderndid)"
        },
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
        },
        {
          "id": "pip-plotnine",
          "kind": "pip",
          "package": "plotnine",
          "label": "Install plotnine (for causal trend plotting)"
        },
        {
          "id": "pip-pyreadstat",
          "kind": "pip",
          "package": "pyreadstat",
          "label": "Install pyreadstat (for .dta support)"
        }
      ]
    }
  }
---

# Staggered DID: 多时点双重差分因果推断

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install staggered-did
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
pip install pandas numpy scipy moderndid plotnine pyreadstat

# 运行脚本
python skills/staggered-did/scripts/staggered_did_pipeline.py --help
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

当政策或干预（如 ERP 系统上线、数字化工具推广）在不同主体上错时发生时，传统的双向固定效应（TWFE）模型常因异质性处理效应（Hetero Treatment Effects）而产生负权重和严重的估计偏误。Callaway 和 Sant'Anna (2021) 提出的双重稳健估计量可以有效解决这一问题。

**核心估计量**：群组-时间平均处理效应 $ATT(g,t)$

$$ATT(g,t) = \mathbb{E}[Y_t^{(1)} - Y_t^{(0)} | G=g]$$

其中 $G$ 为首次接受干预的群组，$t$ 为时间，$Y_t^{(1)}$ 为处理状态，$Y_t^{(0)}$ 为反事实状态。

## 核心功能

- **Callaway-Sant'Anna 估计量**：使用"尚未采纳"或"永不采纳"组作为纯净对照组
- **双重稳健性**：同时利用倾向得分与回归模型，提升估计稳健性
- **事件研究法聚合**：将 $ATT(g,t)$ 聚合为动态滞后与领先效应 $\mathbb{E}[ATT(l)]$，$l = -k, ..., +k$
- **平行趋势检验**：自动生成包含联合置信区间的学术级平行趋势图
- **Goodman-Bacon 分解**：可选诊断，分解 TWFE 偏误来源
- **HonestDiD 敏感性分析**：可选诊断，评估未观测混淆变量的最大偏误容忍度

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 数据文件路径（.dta/.csv/.xlsx），须为 long 格式面板 |
| `--y` | string | ✅ | 因变量 $Y$ |
| `--t` | string | ✅ | 时间项变量（如 `year`） |
| `--id` | string | ✅ | 个体唯一数字 ID（面板 ID） |
| `--g` | string | ✅ | 首次接受干预的时间（永不干预的个体标记为 0） |
| `--cov` | string | ❌ | 协变量公式，默认为 `~1`（无协变量） |
| `--control_group` | string | ❌ | 对照组类型：`notyettreated`（默认）或 `nevertreated` |
| `--est_method` | string | ❌ | 估计方法：`dr`（双重稳健，默认）或 `ipw`（逆概率加权） |
| `--output_pickle` | string | ✅ | 输出 pickle 路径 |
| `--plot_path` | string | ❌ | 平行趋势图输出路径（.png） |

## 执行流程

```bash
python {baseDir}/scripts/staggered_did_pipeline.py \
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

## 数据结构要求

数据须为 **long 格式面板数据**，包含以下关键列：

| 列名 | 类型 | 说明 |
|------|------|------|
| `firm_id` | int | 个体唯一标识 |
| `year` | int | 时间标识（年份） |
| `first_adoption_year` | int | 首次处理时间（从未处理者为 0） |
| `roa` | float | 因变量（企业绩效） |
| `co_size_ln` | float | 控制变量（企业规模） |

**判定逻辑**：
- `gname = 0`：永不接受干预的对照组
- `gname > 0`：在给定年份首次接受干预的处理组
- 处理状态一旦生效不得逆转（Absorbing Treatment）

## 诊断输出规范

### 1. 平行趋势检验（事件研究图）

```
📊 [事件研究法聚合结果]
- 总体 ATT: 0.0382 (SE: 0.0127, 95% CI: [0.0134, 0.0630])
- 预处理期（t=-3, t=-2）置信区间均包含 0，平行趋势假设成立
- 处理后（t=0, t=1, t=2）效应显著为正，表明政策效果显著
```

平行趋势图保存在 `--plot_path`，包含：
- X 轴：相对时间（预处理期负值，处理期正值）
- Y 轴：处理效应估计值
- 阴影：95% 联合置信区间
- 垂直线：干预时点（t=0）

### 2. 群组-时间 ATT 分解表

```
### [群组-时间 ATT(g,t) 分解]
| 群组 (首次处理年) | t=-2 | t=-1 | t=0 | t=1 | t=2 |
|------------------|------|------|-----|-----|-----|
| 2018             | 0.01 | 0.02 | 0.04 | 0.05 | 0.06 |
| 2019             | -    | 0.01 | 0.03 | 0.04 |   -  |
| 2020             |  -   |  -   | 0.02 | 0.03 |  -  |
```

### 3. TWFE 偏误诊断（可选）

```bash
# Goodman-Bacon 分解（需要安装 did 模块）
python {baseDir}/scripts/goodman_bacon_decomp.py \
  --data "./data/digitalization_panel.dta" \
  --y "roa" \
  --t "year" \
  --id "firm_id" \
  --g "first_adoption_year"
```

输出：
```
### [Goodman-Bacon 分解]
- 早期处理组权重占比: 0.42
- 晚期处理组权重占比: 0.31
- 未处理组权重占比: 0.27
- TWFE 偏误风险: ⚠️ 中等（存在异质性处理效应）
```

## 输出内容

### 1. 控制台输出

Markdown 格式的因果推断诊断报告，包含所有统计检验结果。

### 2. pickle 文件

```python
{
    "att_gt": moderndid.att_gt 结果对象,
    "event_study": moderndid.aggte 结果对象（事件研究聚合）,
    "overall_att": float,
    "overall_se": float,
    "pretrend_pvalue": float  # 平行趋势检验 p 值
}
```

### 3. 事件研究图

PNG 格式的学术级平行趋势图，默认 300 DPI，宽度 8 英寸，高度 5 英寸。

## 错误处理

| 场景 | 触发条件 | 处理方式 |
|------|----------|----------|
| 面板结构异常 | 处理状态逆转 | 报错退出，要求数据满足 absorbing treatment 假设 |
| 对照组不足 | nevertreated 组 < 5% | 警告，建议使用 notyettreated 作为对照 |
| 样本量不足 | 处理组某群组观测值 < 10 | 警告，该群组估计可能不稳定 |
| 平行趋势失败 | 预处理期 ATT 显著非零（p < 0.05） | 输出红色警告，结果须谨慎解读 |
| 共线性 | 协变量与处理变量高度相关 | 警告，可能影响双重稳健估计精度 |

## 局限性说明

- Callaway-Sant'Anna 估计量假设"稳定单位处理值假设"（SUTVA）
- 若存在溢出效应（处理组影响对照组），估计量有偏
- 事件研究图仅显示点估计与置信区间，未显示样本量权重

## 相关资源

- `references/staggered-did-guide.md` — 完整操作手册（含 Goodman-Bacon 分解与 HonestDiD）
- `references/moderndid-api.md` — moderndid API 详解
- `references/callaway-santanna-math.md` — 数学推导与识别策略
