---
name: regression-diagnostics-report
description: 汇总所有回归诊断结果，调用大模型生成结构化诊断报告。当用户提出"生成诊断报告"、"回归诊断报告"、"输出回归报告"时激活。读取 panel-regression、iv-estimator、staggered-did 的 pickle 输出，综合所有模型输出并通过大模型生成「模型设定→诊断结果→学术结论」完整诊断报告，直接用于论文的"实证结果"章节。
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
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
        },
        {
          "id": "pip-pickle",
          "kind": "pip",
          "package": "pickle",
          "label": "Built-in pickle (part of Python standard library)"
        }
      ]
    }
  }
---

# Regression Diagnostics Report: 回归诊断报告生成

## 概述

本技能是计量分析流程的最后一环，负责汇总所有子技能的诊断输出，调用大模型生成完整的结构化诊断报告。

> **关于大模型调用**：本技能不独立调用外部 API，而是**通过智能体自身的推理能力**汇总各 pickle 结果中的诊断指标，使用结构化 prompt 引导智能体生成符合学术规范的完整诊断报告。这是 OpenClaw 智能体的原生能力，所有技能共享同一个大模型通路。

## 工作流程

```
用户: "生成诊断报告"

▼ regressor 输出 pickle (panel_regression / iv_regression / did_pipeline)
  │
  ▼ stargazer-exporter 输出表格 (LaTeX / HTML)
  │
  ▼ regression-diagnostics-report 汇总所有结果
  │
  ▼ 大模型（智能体自身）综合分析，生成结构化报告
  │
  ▼ 输出 Markdown / LaTeX 诊断报告
```

## 诊断报告结构

### 第一部分：模型设定

```markdown
## 一、研究设计与模型设定

### 1.1 数据来源与样本描述
- 数据来源：[数据文件名]
- 时间范围：[start] — [end]
- 样本量：[N] 个企业 × [T] 期 = [N×T] 观测值
- 变量定义：[关键变量中英文对照表]

### 1.2 计量模型
- **基准回归模型**：双向固定效应（TWFE）模型
  $$Y_{it} = \beta_0 + \beta_1 X_{it} + \mathbf{Controls'}_{it}\mathbf{\Gamma} + \alpha_i + \gamma_t + \varepsilon_{it}$$
- **内生性处理**：工具变量（2SLS）/ 多时点 DID（视用户需求）
- **标准误估计**：企业层面聚类稳健标准误
```

### 第二部分：诊断结果

```markdown
## 二、模型诊断结果

### 2.1 基准回归（TWFE）

| 变量 | 系数 | 标准误 | t值 | P值 | 显著性 |
|------|------|--------|-----|-----|--------|
| IT投资 | 0.0423 | 0.0121 | 3.49 | 0.000 | *** |
| 企业规模 | 0.0156 | 0.0067 | 2.33 | 0.021 | ** |

**模型质量指标：**
- R²（within）：0.3412
- F 统计量：28.34 (p < 0.001)
- VIF 最大值：2.14（< 5，无严重共线性）
- 聚类数：1,208 个企业

### 2.2 内生性检验（IV）

| 检验项 | 统计量 | 临界值 | 结论 |
|--------|--------|--------|------|
| 第一阶段偏 F 统计量 | 18.74 | > 10 | ✅ 通过 |
| Durbin-Wu-Hausman p 值 | 0.002 | < 0.05 | ✅ 确认内生性 |
| Hansen J 过度识别 p 值 | 0.381 | > 0.05 | ✅ 工具变量外生 |

### 2.3 平行趋势检验（DID）

**事件研究图**：[自动插入 event_study_plot.png]
- 预处理期（t=-3, t=-2）：置信区间均包含 0，✅
- 处理后（t=0, t=1, t=2）：效应显著为正，✅
- 总体 ATT：0.0382 (95% CI: [0.0134, 0.0630])
```

### 第三部分：学术结论

```markdown
## 三、学术结论与启示

### 3.1 主要发现
[大模型根据上述诊断结果自动生成的学术结论段落]

### 3.2 结果解读
- IT投资对企业绩效的因果效应约为 [β]个百分点
- 内生性检验确认了IV估计的必要性
- 平行趋势假设成立，DID估计结果可信

### 3.3 研究启示
- 对管理层：数字化转型投入对企业绩效有显著正向作用
- 对政策制定者：政府信息化采购可作为企业数字化的有效工具变量

### 3.4 研究局限
- [大模型根据模型局限性自动生成的客观局限说明]
- 潜在内生性来源（如遗漏变量、测量误差）
- 外生性工具有限性的说明

### 3.5 稳健性检验建议
- 替换核心解释变量的度量方式
- 增加行业固定效应
- 使用不同聚类维度
```

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--pickles` | string | ✅ | 所有 pickle 结果路径（空格分隔，最多 4 个） |
| `--models` | string | ✅ | 模型名称对应关系，格式：`pickle路径:模型名` |
| `--plots` | string | ❌ | 图表文件路径（空格分隔） |
| `--rename` | string | ❌ | 变量重命名，格式：`原名:新名,原名:新名` |
| `--title` | string | ❌ | 报告标题 |
| `--output_markdown` | string | ✅ | 输出 Markdown 路径 |
| `--output_latex` | string | ❌ | 输出 LaTeX 路径 |

## 执行流程

```bash
python {baseDir}/scripts/generate_diagnostics_report.py \
  --pickles "./output/panel_results.pkl ./output/iv_results.pkl ./output/did_results.pkl" \
  --models "panel_results.pkl:基准TWFE回归,iv_results.pkl:IV工具变量回归,did_results.pkl:多时点DID回归" \
  --plots "./output/event_study_plot.png" \
  --rename "it_investment_g:IT投资,roa:企业绩效,co_size_ln:企业规模" \
  --title "实证分析报告：数字化转型对企业绩效的影响" \
  --output_markdown "./output/diagnostics_report.md" \
  --output_latex "./output/diagnostics_report.tex"
```

## 输出内容

### 1. 完整 Markdown 报告

包含模型设定表格、回归结果表格、诊断检验结果、学术结论与启示，可直接粘贴至论文对应章节。

### 2. LaTeX 源文件（可选）

符合中文期刊格式的 LaTeX 源码，可直接编译。

### 3. 图表（自动插入）

回归系数森林图、事件研究平行趋势图自动插入报告对应位置。

## 错误处理

| 场景 | 触发条件 | 处理方式 |
|------|----------|----------|
| pickle 不存在 | 文件路径错误 | 报错并列出可用 pickle 路径 |
| pickle 版本不兼容 | 旧版本 linearmodels 输出 | 警告并尝试读取，失败则要求用户重新运行回归 |
| 图表不存在 | --plots 指定了不存在的图 | 生成警告但不阻止报告生成 |
| 变量名不匹配 | rename 中的变量名在 pickle 中不存在 | 跳过并警告用户 |

## 相关资源

- `references/report-template.md` — 学术诊断报告模板（中英文期刊格式）
- `references/diagnostic-checklist.md` — 诊断完整性检查清单

## 依赖安装确认

```bash
python -c "import pandas; print('pandas OK')"
python -c "import pickle; print('pickle OK')"
```