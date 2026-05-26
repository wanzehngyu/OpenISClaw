---
name: difference-in-discontinuities
description: 执行断点回归（Regression Discontinuity Design / RDD）因果效应分析。当用户提出"断点回归"、"RDD"、"模糊断点"、"清晰断点"、"边界效应"、"阈值效应"时激活。基于 pandas / statsmodels，提供精确断点与模糊断点两种 RDD 估计，直接对接 stargazer-exporter 输出发表级表格。
metadata:
  {
    "openclaw": {
      "emoji": "🔀",
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
          "id": "pip-numpy",
          "kind": "pip",
          "package": "numpy",
          "label": "Install numpy"
        }
      ]
    }
  }
---

# Difference-in-Discontinuities: 断点回归设计

## 概述

当处理分配由一个连续变量是否超过某一阈值决定时，断点回归（Sharp RDD / Fuzzy RDD）可以估计出在阈值处的局部平均处理效应（Local ATE），被视为"准自然实验"。

**模型设定：**

$$\text{Sharp RDD: } Y_i = \alpha + \tau D_i + f(X_i - c) + \varepsilon_i$$

$$\text{Fuzzy RDD: } Y_i = \alpha + \tau \hat{D}_i + f(X_i - c) + \varepsilon_i$$

其中 $c$ 为断点，$D_i = \mathbf{1}[X_i \geq c]$，$f(\cdot)$ 为控制函数（多项式或局部线性）。

## 核心功能

- **精确断点（Sharp RDD）**：处理分配完全由阈值决定
- **模糊断点（Fuzzy RDD）**：阈值仅影响处理概率（工具变量框架）
- **局部多项式估计**：三角形核函数 + 最优带宽选择（Imbens-Kalyanaraman 2012）
- **带宽敏感性分析**：不同带宽下的估计值稳健性
- ** Manipulation 检验**：McCrary 密度检验，确认分组在阈值处无异常跳跃
- **发表级输出**：序列化至 pickle，对接 stargazer-exporter

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 数据文件路径（.csv/.dta/.xlsx） |
| `--y` | string | ✅ | 因变量 $Y$ |
| `--x` | string | ✅ | 驱动变量（分配变量）$X$ |
| `--cutoff` | float | ✅ | 断点阈值 $c$ |
| `--fuzzy` | string | ❌ | 模糊断点模式下的处理变量（若指定则为 Fuzzy RDD） |
| `--kernel` | string | ❌ | 核函数：`triangular`（默认）/ `rectangular` / `uniform` |
| `--bandwidth` | float | ❌ | 带宽（若不指定则自动 IK 优化） |
| `--order` | int | ❌ | 多项式阶数（默认 1，局部线性） |
| `--output_pickle` | string | ✅ | 输出 pickle 路径 |
| `--output_plot` | string | ❌ | RDD 可视化图路径（.png） |

## 执行流程

```bash
python {baseDir}/scripts/rdd_analysis.py \
  --data "./data/policy_panel.dta" \
  --y "roa" \
  --x "gov_proc_ratio" \
  --cutoff 0.5 \
  --fuzzy "digital_adoption" \
  --kernel "triangular" \
  --bandwidth 0.15 \
  --order 1 \
  --output_pickle "./output/rdd_results.pkl" \
  --output_plot "./output/rdd_plot.png"
```

## 诊断输出规范

### Manipulation 检验（密度连续性）

```
🔀 [McCrary 密度检验]
- 断点左侧密度: 0.342
- 断点右侧密度: 0.338
- 密度比值: 0.989
- P 值: 0.873

✅ [密度连续性通过] 断点两侧密度无显著差异，不存在异常分组现象
```

### 带宽敏感性分析

```
🔀 [带宽敏感性分析]
| 带宽（相对IK最优）| ATE估计值 | 标准误 | 95% CI |
|-----------------|-----------|--------|--------|
| 0.5× BW         | 0.0382    | 0.0189 | [0.001, 0.075] |
| 1.0× BW (IK)    | 0.0417    | 0.0143 | [0.013, 0.070] |
| 1.5× BW         | 0.0398    | 0.0121 | [0.016, 0.064] |
| 2.0× BW         | 0.0375    | 0.0108 | [0.016, 0.059] |
```