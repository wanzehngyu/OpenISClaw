---
name: panel-regression
description: 执行面板数据的双向固定效应（TWFE）回归分析。当用户提出"面板回归"、"双向固定效应"、"TWFE"、"个体时间双固定"、"聚类稳健标准误"或"固定效应模型估计"时激活。基于 linearmodels.panel.PanelOLS，提供含企业/行业聚类稳健标准误的双向固定效应回归，并对接 stargazer-exporter 输出发表级表格。
metadata:
  {
    "openclaw": {
      "emoji": "📊",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-linearmodels",
          "kind": "pip",
          "package": "linearmodels",
          "label": "Install linearmodels (pip install linearmodels)"
        },
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
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

# Panel Regression (TWFE)

## 概述

执行双向固定效应（Two-Way Fixed Effects, TWFE）面板回归，默认输出企业层面聚类稳健标准误：

$$Y_{it} = \beta_0 + \beta_1 X_{it} + \mathbf{Controls'}_{it}\mathbf{\Gamma} + \alpha_i + \gamma_t + \varepsilon_{it}$$

其中 $\alpha_i$ 为个体固定效应，$\gamma_t$ 为时间固定效应，$\varepsilon_{it}$ 为误差项，标准误按个体维度聚类以纠正序列相关。

## 核心功能

- **双向固定效应**：同时控制个体与时间不可观测异质性
- **聚类稳健标准误**：默认按个体聚类，支持双向聚类（个体×时间）
- **固定效应指示行**：自动追加 $\alpha_i$ 和 $\gamma_t$ 状态行至结果表
- **VIF 共线性检验**：检测解释变量间多重共线性
- **序列化输出**：结果 pickle 供 stargazer-exporter 链式调用

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 数据文件路径（.dta/.csv/.xlsx） |
| `--y` | string | ✅ | 被解释变量名 |
| `--x` | string | ✅ | 外生控制变量列表（空格分隔） |
| `--entity` | string | ✅ | 个体 ID 列名（如 firm、company） |
| `--time` | string | ✅ | 时间 ID 列名（如 year） |
| `--cluster` | string | ❌ | 聚类维度，默认 `entity`，可设为 `two-way` |
| `--output_pickle` | string | ✅ | 输出 pickle 路径 |

## 执行流程

```bash
python {baseDir}/scripts/panel_regression.py \
  --data "./data/enterprise_panel.dta" \
  --y "roa" \
  --x "it_investment_g co_size_ln lev age" \
  --entity "firm_id" \
  --time "year" \
  --cluster "entity" \
  --output_pickle "./output/panel_results.pkl"
```

## 输出内容

### 1. 控制台输出（Markdown 格式）

```
### [双向固定效应面板回归结果]

| 变量 | 系数 | 标准误 | t值 | P值 | 显著性 |
|------|------|--------|-----|-----|--------|
| IT Investment (%) | 0.0423 | 0.0121 | 3.49 | 0.000 | *** |
| Firm Size (log) | 0.0156 | 0.0067 | 2.33 | 0.021 | ** |
| Leverage Ratio | -0.0892 | 0.0289 | -3.09 | 0.002 | *** |

- 个体固定效应: ✅ 已控制
- 时间固定效应: ✅ 已控制
- 聚类维度: 企业层面（cluster_entity=True）
- 样本量: N = 4,832（企业×年份）
- R² (within): 0.3412
- F 统计量: 28.34 (p < 0.001)
- VIF 检验: 最大 VIF = 2.14（< 5，无严重共线性）
```

### 2. pickle 文件

序列化的 `linearmodels.panel.results.PanelResults` 对象，供后续 stargazer 调用。

### 3. 诊断警告

| 场景 | 触发条件 | 输出内容 |
|------|----------|----------|
| 弱共线性警告 | 最大 VIF > 5 | ⚠️ [VIF警告] 变量 co_size_ln VIF=6.2，建议移除或合并 |
| 样本量不足 | N < 100 | ⚠️ [样本量警告] 当前样本量偏小，标准误估计可能不稳定 |
| 固定效应共线性 | 某变量在组内无变异 | ❌ [固定效应错误] 变量 gend 在个体内部无变异，无法估计 |

## 诊断标准

- **R² (within)**: 反映个体内部变异解释力度，越高越好（通常 > 0.2 为可接受）
- **F 统计量**: 联合显著性检验，p < 0.05 为模型整体显著
- **VIF**: 方差膨胀因子，VIF > 5 表明存在中等以上共线性
- **聚类标准误**: 若未聚类则低估标准误，导致 t 值膨胀，统计推断失效

## 局限性说明

TWFE 模型在异质性处理效应（Hetero Treatment Effects）下可能产生偏误。当用户同时使用 `staggered-did` 技能时，系统会自动提示 TWFE 与 Callaway-Sant'Anna 估计量的选择问题。

## 相关资源

- `references/panel-regression-guide.md` — 完整操作手册（含双向聚类、稳健标准误推导）
- `references/diagnostics-standards.md` — 计量诊断标准与临界值

## 依赖安装确认

```bash
python -c "from linearmodels.panel import PanelOLS; print('linearmodels OK')"
python -c "import pandas; print('pandas OK')"
python -c "import pyreadstat; print('pyreadstat OK')"
```

若缺失，智能体应提示用户运行 `pip install linearmodels pandas pyreadstat`。