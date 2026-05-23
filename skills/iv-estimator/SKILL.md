---
name: iv-estimator
description: 执行两阶段最小二乘法（2SLS）工具变量回归与内生性诊断。当用户提出"工具变量"、"2SLS"、"IV回归"、"弱工具变量检验"、"Hausman检验"、"Durbin-Wu-Hausman"、"过度识别检验"或"Sargan检验"时激活。基于 linearmodels.iv.IV2SLS，自动执行第一阶段偏F统计量、Cragg-Donald 统计量、Stock-Yogo 临界值比对、Hansen J 过度识别检验，并对接 stargazer-exporter 输出发表级表格。
metadata:
  {
    "openclaw": {
      "emoji": "⚖️",
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

# IV-Estimator: 工具变量二阶段回归

## 概述

当解释变量与误差项相关（即存在内生性）时，OLS 估计量有偏且不一致。工具变量（IV）估计通过寻找与内生解释变量相关但与误差项无关的外部变量 $Z$，实现对内生变量的"清洗"，从而获得一致性估计。

**两阶段最小二乘法（2SLS）模型：**

$$\text{第一阶段：} \quad X_{it} = \pi_0 + \pi_1 Z_{it} + \mathbf{W'}_{it}\mathbf{\Pi} + v_{it}$$

$$\text{第二阶段：} \quad Y_{it} = \beta_0 + \beta_1 \hat{X}_{it} + \mathbf{W'}_{it}\mathbf{B} + u_{it}$$

其中 $Z$ 为工具变量，$\mathbf{W}$ 为外生控制变量，$\hat{X}$ 为第一阶段拟合值。

## 核心功能

- **2SLS 估计**：两阶段最小二乘法，无偏的局部平均处理效应（LATE）估计
- **弱工具变量检验**：第一阶段偏 F 统计量 > 10 为通过阈值
- **内生性检验**：Durbin-Wu-Hausman 检验，判断内生性是否存在
- **过度识别检验**：Hansen J / Sargan 统计量，检验工具变量外生性
- **Cragg-Donald 统计量**：多内生变量时判断是否存在弱工具变量（比对 Stock-Yogo 临界值）
- **序列化输出**：结果 pickle 供 stargazer-exporter 链式调用

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 数据文件路径（.dta/.csv/.xlsx） |
| `--y` | string | ✅ | 因变量 $Y$ |
| `--exog` | string | ❌ | 外生控制变量列表（空格分隔），为空时仅含常数项 |
| `--endog` | string | ✅ | 内生解释变量列表 $X$（空格分隔） |
| `--iv` | string | ✅ | 工具变量列表 $Z$（空格分隔） |
| `--output_pickle` | string | ✅ | 输出 pickle 路径 |

## 执行流程

```bash
python {baseDir}/scripts/iv_regression.py \
  --data "./data/enterprise_panel.dta" \
  --y "roa" \
  --exog "co_size_ln lev age" \
  --endog "it_investment_g" \
  --iv "ln_gov_proc digital_infrastructure" \
  --output_pickle "./output/iv_results.pkl"
```

## 诊断输出规范

### 样本量检查

```
⚠️ [样本量警告] 当前有效观测值仅为 342，建议针对本模型
   推荐的最低样本量为 10 × (3 控制变量 + 2 工具变量) = 50。
   样本量偏低可能导致标准误估计不稳定。
```

### 第一阶段 F 统计量（弱工具变量检验）

```
### [弱工具变量检验]
- **第一阶段偏 F 统计量**: 14.32

✅ [弱 IV 检验通过] F = 14.32 > 10，工具变量对内生变量的
   关联强度满足传统学术要求（Stock & Yogo, 2005）。
```

若 F < 10：
```
⚠️ [弱工具变量警告] 第一阶段偏 F 统计量 = 6.87 < 10，
   工具变量对内生变量的关联程度较弱，可能会导致二阶段
   估计偏误放大。建议更换更强工具变量或增加工具变量数量。
```

### Durbin-Wu-Hausman 内生性检验

```
- **Durbin-Wu-Hausman 内生性检验 P值**: 0.003

✅ [内生性判定] 拒绝外生性原假设 (p=0.003 < 0.05)，
   解释变量的确存在显著的内生性偏误，确有必要使用 IV 回归。
```

或：

```
⚠️ [内生性判定] 无法拒绝外生性 (p=0.213 >= 0.05)，
   OLS 估计可能是有效的，使用 IV 估计可能会损失部分估计精度。
   建议保留 OLS 基准回归作为对照。
```

### Hansen J 过度识别检验

```
- **Hansen J 过度识别检验 P值**: 0.456

✅ [过度识别检验通过] p = 0.456 >= 0.05，不能拒绝原假设，
   工具变量的外生性得到支持，排他性约束成立。
```

若 p < 0.05：
```
❌ [排除限制失败] 拒绝外生工具变量原假设 (p=0.038 < 0.05)，
   至少有一个工具变量与内生残差相关，可能通过不可观测渠道
   直接作用于因变量，排他性约束未通过。请检查工具变量有效性。
```

## 完整输出示例

```
================================================================
⚖️ IV-Estimator: 两阶段最小二乘法（2SLS）工具变量回归报告
================================================================

【模型设定】
- 因变量 (Y): roa（企业绩效）
- 内生解释变量 (X): it_investment_g（IT投资）
- 外生控制变量 (W): co_size_ln, lev, age
- 工具变量 (Z): ln_gov_proc, digital_infrastructure

【样本量】N = 4,832（有效观测值）

【诊断结果】
✅ 第一阶段偏 F 统计量 = 18.74 > 10（弱 IV 检验通过）
✅ Durbin-Wu-Hausman 内生性检验 p = 0.002 < 0.05（确认内生性，使用 IV 合理）
✅ Hansen J 过度识别检验 p = 0.381 > 0.05（工具变量外生性支持）

【第二阶段回归结果】
================================================================
  变量                    系数        标准误        t值       P值
----------------------------------------------------------------
  IT Investment (%)       0.0612      0.0187       3.27     0.001  ***
  Firm Size (log)         0.0234      0.0089       2.63     0.009  **
  Leverage Ratio         -0.0763      0.0312      -2.45     0.015  **
  Age (years)             0.0045      0.0021       2.14     0.033  **
----------------------------------------------------------------
  R²: 0.2941
  F 统计量: 21.67 (p < 0.001)
================================================================

【学术结论】
工具变量回归结果表明，IT投资每增加1个百分点，企业绩效提升
约0.061个百分点。Durbin-Wu-Hausman检验确认了内生性问题
的必要性（p=0.002），弱工具变量检验通过（F=18.74 > 10），
过度识别检验支持工具变量外生性（p=0.381 > 0.05）。
```

## 错误处理

| 场景 | 触发条件 | 处理方式 |
|------|----------|----------|
| 样本量不足 | N < 10×(K_exog + K_iv) | 输出警告，继续估计但不保证渐近有效性 |
| 弱工具变量 | F < 10 | 停止回归，要求用户更换工具变量 |
| 工具变量共线性 | 第一阶段 R² 异常高或低 | 检查工具变量间是否存在高度相关 |
| 内生性不显著 | p > 0.05 | 提示用户 IV 可能不必要，建议保留 OLS 基准 |
| 过度识别失败 | Hansen J p < 0.05 | 输出警告，提示至少一个工具变量可能违规 |

## 局限性说明

- 2SLS 仅能估计局部平均处理效应（LATE），而非平均处理效应（ATE）
- 若工具变量对部分样本无效（异质性处理效应），LATE 可能不代表目标人群
- 过度识别检验对分布敏感，在小样本下检验力不足

## 相关资源

- `references/iv-diagnostics.md` — 完整诊断逻辑与 Stock-Yogo 临界值表
- `references/weak-iv-standards.md` — 弱工具变量检验的学术标准演进

## 依赖安装确认

```bash
python -c "from linearmodels.iv import IV2SLS; print('linearmodels IV OK')"
python -c "import pandas; print('pandas OK')"
python -c "import pyreadstat; print('pyreadstat OK')"
```