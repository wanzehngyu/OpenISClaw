---
name: propensity-score-matching
description: 执行倾向得分匹配（Propensity Score Matching, PSM）分析。当用户提出"PSM"、"倾向得分匹配"、"匹配估计"、"反事实估计"、"倾向得分"、"控制组匹配"时激活。基于 pandas / statsmodels，提供最近邻、半径、核函数三种 PSM 估计方法，并检验匹配平衡性，直接对接 stargazer-exporter 输出表格。
metadata:
  {
    "openclaw": {
      "emoji": "🎯",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
        },
        {
          "id": "pip-statsmodels",
          "kind": "pip",
          "package": "statsmodels",
          "label": "Install statsmodels"
        },
        {
          "id": "pip-sklearn",
          "kind": "pip",
          "package": "scikit-learn",
          "label": "Install scikit-learn"
        }
      ]
    }
  }
---

# Propensity Score Matching: 倾向得分匹配

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install propensity-score-matching
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
pip install pandas numpy scipy statsmodels scikit-learn

# 运行脚本
python skills/propensity-score-matching/scripts/psm_analysis.py --help
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

当处理分配不满足随机化条件时，直接 OLS 估计存在选择性偏误。PSM 通过构建反事实对照组，估计处理组的平均处理效应（ATT / ATE / ATU）。

**核心思想：**

$$P(X) = Pr(D=1 | X) = \Lambda(X'\beta)$$

使用 Logit/Probit 模型估计倾向得分，对处理组与对照组个体进行匹配，消除可观测变量的选择性偏误。

## 核心功能

- **倾向得分估计**：Logit 模型计算每个个体的倾向得分
- **最近邻匹配（1:1 / 1:k）**：卡尺内最近邻匹配
- **半径匹配（Radius）**：卡尺范围内所有对照个体的加权平均
- **核函数匹配（Kernel）**：使用核函数加权匹配
- **匹配平衡性检验**：匹配后标准化均值差异（Bias Reduction）
- **共同支撑检验**：检验处理组与对照组倾向得分重叠区域
- **序列化输出**：结果 pickle 供 stargazer-exporter 调用

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 数据文件路径（.csv/.dta/.xlsx） |
| `--y` | string | ✅ | 因变量 $Y$ |
| `--treatment` | string | ✅ | 处理变量 $D$（0/1 二值） |
| `--covariates` | string | ✅ | 用于估计倾向得分的协变量列表 |
| `--method` | string | ❌ | 匹配方法：`nearest`（默认）/ `radius` / `kernel` |
| `--k` | int | ❌ | 最近邻匹配的最近邻个数（默认 1） |
| `--caliper` | float | ❌ | 卡尺（标准差倍数，默认 0.05） |
| `--output_pickle` | string | ✅ | 输出 pickle 路径 |

## 执行流程

```bash
python {baseDir}/scripts/psm_analysis.py \
  --data "./data/enterprise_panel.dta" \
  --y "roa" \
  --treatment "digital_adoption" \
  --covariates "co_size_ln lev age it_investment_g" \
  --method "nearest" \
  --k 3 \
  --caliper 0.05 \
  --output_pickle "./output/psm_results.pkl"
```

## 诊断输出规范

### 倾向得分分布

```
🎯 [倾向得分分布]
处理组样本量: 1,234
对照组样本量: 3,598
共同支撑范围: [0.032, 0.891]
共同支撑外处理组比例: 1.2%

✅ [共同支撑检验通过] 98.8% 的处理组个体落在共同支撑区域内
```

### 匹配平衡性检验

```
🎯 [匹配平衡性检验 — 匹配前后对比]
| 变量     | 匹配前均值差 | 匹配后均值差 | Bias Reduction |
|----------|-------------|-------------|----------------|
| co_size_ln | 0.342      | 0.021       | 93.8%          |
| lev        | 0.189      | 0.013       | 91.3%          |
| age        | 0.156      | 0.008       | 94.8%          |

✅ [平衡性检验通过] 所有协变量匹配后标准化均值差 < 5%，满足条件独立性假设
```

### ATT 估计结果

```
🎯 [PSM-ATT 估计结果]
| 估计方法    |  ATT  | 标准误  | t值   | 样本量(处理/对照) |
|-------------|-------|--------|-------|------------------|
| 最近邻(1:1) | 0.038 | 0.014  | 2.71  | 1,234 / 1,234    |
| 半径匹配    | 0.041 | 0.012  | 3.42  | 1,234 / 2,876    |
| 核函数匹配  | 0.039 | 0.011  | 3.55  | 1,234 / 3,598    |

✅ 三种方法估计结果相近，ATT 约为 3.9%—4.1%，稳健性良好
```