---
name: regression-plotter
description: 生成学术级回归系数可视化图表。当用户提出"回归系数图"、"森林图"、"系数可视化"、"画回归结果图"时激活。基于 matplotlib/plotnine，读取 panel-regression 或 iv-estimator 输出的 pickle 结果文件，生成发表级系数森林图（Forest Plot），直接用于论文。
metadata:
  {
    "openclaw": {
      "emoji": "📈",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-matplotlib",
          "kind": "pip",
          "package": "matplotlib",
          "label": "Install matplotlib"
        },
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
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

# Regression Plotter: 学术系数可视化

## 概述

将回归结果以发表级森林图（Forest Plot）形式输出，支持单模型系数展示、多模型系数对比、系数大小与显著性热力图。

## 核心功能

### 1. 单模型森林图

读取 pickle 结果，直接输出系数、置信区间与显著性标注：

```
| 变量       | 系数   | 95% CI          | P值   |
|------------|--------|-----------------|-------|
| IT投资     | 0.042  | [0.018, 0.066]  | 0.001 |
| 企业规模   | 0.016  | [0.003, 0.029]  | 0.021 |
```

### 2. 多模型对比图

将 2-4 个模型的回归系数并列展示，便于比较不同模型设定下的效应稳定性。

### 3. 输出规格

- 格式：PNG / PDF
- 分辨率：300 DPI
- 字体：Times New Roman / Arial（论文标准）
- 尺寸：单栏（3.5英寸）或双栏（7英寸）

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pickle` | string | ✅ | panel-regression 或 iv-estimator 的 pickle 结果路径 |
| `--output` | string | ✅ | 输出图片路径（.png/.pdf） |
| `--rename` | string | ❌ | 变量重命名，格式 `原名:新名,原名:新名` |
| `--title` | string | ❌ | 图表标题 |
| `--width` | float | ❌ | 图表宽度（英寸，默认 6） |
| `--height` | float | ❌ | 图表高度（英寸，默认 4） |
| `--format` | string | ❌ | 输出格式：`png`（默认）/ `pdf` / `both` |

## 执行流程

```bash
python {baseDir}/scripts/plot_regression.py \
  --pickle "./output/panel_results.pkl" \
  --output "./output/forest_plot.png" \
  --rename "it_investment_g:IT投资,co_size_ln:企业规模,lev:资产负债率" \
  --title "图1: 数字化转型对企业绩效的影响（TWFE回归）" \
  --width 6 \
  --height 4 \
  --format png
```