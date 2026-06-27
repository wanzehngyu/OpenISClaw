---
name: survival-analysis
description: 执行生存分析（Cox 比例风险模型、Kaplan-Meier估计）。当用户提出"生存分析"、"Cox模型"、"风险比率"、"Kaplan-Meier"、"事件历史分析"、"失效时间分析"时激活。基于 lifelines，提供 CoxPH 回归与 Kaplan-Meier 生存曲线估计，直接对接 stargazer-exporter 输出发表级表格。
metadata:
  {
    "openclaw": {
      "emoji": "📉",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-lifelines",
          "kind": "pip",
          "package": "lifelines",
          "label": "Install lifelines (pip install lifelines)"
        },
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
        },
        {
          "id": "pip-matplotlib",
          "kind": "pip",
          "package": "matplotlib",
          "label": "Install matplotlib"
        }
      ]
    }
  }
---

# Survival Analysis: 生存分析技能

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install survival-analysis
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
pip install pandas numpy scipy lifelines matplotlib

# 运行脚本
python skills/survival-analysis/scripts/survival_analysis.py --help
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

当研究对象为"从起点到事件发生所经历的时间"时（如企业存活时间、客户流失时间、IPO到退市时间），传统 OLS 回归不适用，需要使用生存分析框架。

**核心概念：**

- **生存函数** $S(t)$：个体存活时间超过 $t$ 的概率
- **风险函数** $h(t)$：个体在 $t$ 时刻的瞬间事件发生率
- **Cox 比例风险模型**：$h(t) = h_0(t) \exp(X'\beta)$

## 核心功能

- **Cox 比例风险模型**：估计协变量对风险率的影响（HR < 1 表示降低风险）
- **Kaplan-Meier 生存曲线**：分组生存概率估计与对数秩检验（Log-rank test）
- **Nelson-Aalen 累积风险估计**：非参数累积风险估计
- **比例风险假设检验**：检验 PH 假设是否成立
- **共曲线性诊断**：基于 Schoenfeld 残差的 PH 假设检验
- **序列化输出**：Cox 回归结果 pickle 供 stargazer-exporter 调用

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 数据文件路径（.csv/.dta/.xlsx） |
| `--duration` | string | ✅ | 生存时间变量 |
| `--event` | string | ✅ | 事件指示变量（1=发生，0=截断） |
| `--covariates` | string | ✅ | 协变量列表（空格分隔） |
| `--strata` | string | ❌ | 分层变量（用于 KM 曲线分组） |
| `--output_pickle` | string | ✅ | 输出 pickle 路径 |
| `--output_plot` | string | ❌ | KM 曲线图路径（.png） |

## 执行流程

```bash
python {baseDir}/scripts/survival_analysis.py \
  --data "./data/enterprise_survival.dta" \
  --duration "survival_years" \
  --event "failure" \
  --covariates "co_size_ln lev it_investment_g age" \
  --strata "industry" \
  --output_pickle "./output/cox_results.pkl" \
  --output_plot "./output/km_curve.png"
```

## 诊断输出规范

### Cox 回归结果

```
📉 [Cox 比例风险回归结果]

| 变量         | HR（风险比） | 95% CI           | P值   | 显著性 |
|--------------|-------------|------------------|-------|--------|
| IT投资 (每+1%) | 0.973      | [0.961, 0.986]   | 0.001 | ***   |
| 企业规模 (log) | 0.892      | [0.834, 0.954]   | 0.002 | **    |
| 资产负债率    | 1.234      | [1.089, 1.401]   | 0.001 | ***   |

解读：IT投资每增加1个百分点，企业失败风险降低约 2.7%。
```

### PH 假设检验

```
📉 [比例风险假设检验 — Schoenfeld 残差法]
| 变量           | rho  | chi2   | P值   | 结论     |
|----------------|------|--------|-------|----------|
| it_investment_g | -0.03 | 0.21  | 0.646 | ✅ 通过  |
| co_size_ln     |  0.05 | 0.87  | 0.351 | ✅ 通过  |
| GLOBAL         |       |  1.34  | 0.248 | ✅ 整体通过 |
```

### KM 分组比较（Log-rank）

```
📉 [Kaplan-Meier 分组比较 — Log-rank 检验]
分组变量: it_investment_g（高低两组）
- 高IT投资组中位生存期: 8.7 年
- 低IT投资组中位生存期: 6.1 年
- Log-rank 统计量: 23.4
- P 值: < 0.001

✅ [分组差异显著] 高IT投资组生存率显著高于低IT投资组
```