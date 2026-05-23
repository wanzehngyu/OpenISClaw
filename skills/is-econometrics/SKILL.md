---
name: is-econometrics
description: 面向管理信息系统（IS）专业师生的因果推断与计量分析智能体技能矩阵。当用户提供数据集（.dta/.csv/.xlsx 等）并提出回归分析、内生性检验、工具变量、双重差分或学术表格输出等需求时激活。通过调用 panel-regression、iv-estimator、staggered-did 等子技能，提供从数据探查到因果推断再到发表级表格输出的全流程自动化实证分析服务。
metadata:
  {
    "openclaw": {
      "emoji": "📊",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      }
    }
  }
---

# IS-Econometrics: 因果推断与计量分析技能矩阵

## 概述

本技能是 IS 专业计量分析的统一入口，通过协调三个核心子技能完成完整的实证研究流程：

```
用户: "分析这个DTA文件，做双向固定效应回归，检验内生性"
  │
  ▼
is-econometrics (主控)
  │  识别用户意图 → panel-regression
  │  若用户提到"工具变量"、"2SLS"、"内生性" → 同时触发 iv-estimator
  │
  ▼
panel-regression ──→ 双向固定效应回归结果
iv-estimator    ──→ 工具变量诊断报告（可选）
  │
  ▼ (结果序列化至 pickle，供后续调用)
stargazer-exporter ──→ 发表级 LaTeX/Word 表格
```

## 技能架构

| 子技能 | 功能 | 触发关键词 |
|--------|------|------------|
| `panel-regression` | 双向固定效应（TWFE）面板回归，含聚类稳健标准误 | "面板回归"、"固定效应"、"双向固定"、"TWFE"、"Clustered SE" |
| `iv-estimator` | 2SLS 工具变量回归，含弱工具变量检验与过度识别检验 | "工具变量"、"2SLS"、"IV"、"内生性检验"、"Hausman"、"Sargan"、"弱工具" |
| `staggered-did` | 多时点/渐进双重差分（Callaway-Sant'Anna 估计量） | "多时点DID"、"Staggered DID"、"Callaway"、"事件研究"、"平行趋势"、"ATT" |
| `stargazer-exporter` | 学术表格格式化输出（LaTeX/HTML/Word） | "输出表格"、"生成表格"、"LaTeX"、"发表级" |

## 数据格式支持

本技能自动识别并处理以下格式：

| 格式 | 扩展名 | 读取方式 |
|------|--------|----------|
| Stata 数据集 | `.dta` | `pandas.read_stata`, `pyreadstat` |
| CSV | `.csv` | `pandas.read_csv` |
| Excel | `.xlsx`, `.xls` | `pandas.read_excel` |
| Parquet | `.parquet` | `pandas.read_parquet` |

数据须为 **long 格式面板数据**，包含个体 ID 与时间 ID 两类标识变量。

## 工作流程

### 标准流程（panel-regression 为主）

```python
# 伪代码流程
1. 接收数据路径 + 分析需求
2. 推断数据类型（自动检测 .dta / .csv / .xlsx）
3. 推断面板结构（entity_var, time_var）
4. 执行 panel-regression：
   - PanelOLS(dep_var, exog_vars, entity_effects=True, time_effects=True)
   - cov_type='clustered', cluster_entity=True
   - 输出回归表 + 诊断信息
5. 检查是否需要 iv-estimator（用户提及内生性 / 工具变量）
6. 若需要，调用 iv-estimator 补充分析
7. 调用 stargazer-exporter 输出发表级表格
8. 向用户报告结果文件路径
```

### 交互式干预点

技能支持用户在以下节点介入：

- **变量指定**：用户可自定义被解释变量 Y、解释变量 X、控制变量
- **固定效应设定**：默认识别个体+时间双固定效应，用户可改为单向
- **聚类维度**：默认按个体聚类，用户可改为双向聚类或按行业聚类
- **工具变量选择**：用户可提供候选 IV 列表，技能做排他性与相关性验证
- **DID 设定**：用户指定 treatment/control 组、时间窗口

### 输出成果

| 输出类型 | 格式 | 用途 |
|----------|------|------|
| 回归结果简报 | Markdown | 快速浏览系数、标准误、显著性 |
| 学术表格 | LaTeX (.tex) | 嵌入 Overleaf / ShareLaTeX |
| 学术表格 | Word (.docx) | 直接插入论文章节 |
| 学术表格 | HTML | 期刊网络附件 |
| 事件研究图 | PNG (.png) | 平行趋势检验可视化 |
| 诊断报告 | Markdown | 弱工具变量、内生性等警告 |
| 序列化对象 | Pickle (.pkl) | 下游技能链式调用 |

## 数据探查规范

启动任何回归分析前，技能应先探查数据：

```bash
# 探查 DTA 文件元数据（免内存）
python {baseDir}/scripts/dta_meta_explorer.py --path <file_path>

# 探查 CSV/Excel 通用方法
python {baseDir}/scripts/data_profiler.py --path <file_path>
```

探查内容包括：
- 观测值行数 (N)、变量列数 (K)
- 变量名与变量标签对照
- 面板结构验证（个体 ID 是否随时间重复、时间 ID 是否唯一）
- 缺失值分布
- 主要连续变量的描述性统计

## 子技能调用约定

子技能通过 OpenClaw `exec` 工具调用，遵循以下约定：

```
exec command: """
  python {baseDir}/scripts/<skill_script>.py \
    --data <data_path> \
    --output <output_dir> \
    [技能特定参数...]
"""
```

结果通过 `print()` 输出并序列化至 `<skill>.pkl`，供后续技能使用。

## 错误处理与安全边界

- **样本量不足警告**：当 N < 10 × (K 解释变量 + K 工具变量) 时，强制输出警告，建议用户扩充样本
- **弱工具变量拦截**：第一阶段偏 F < 10 时，停止 IV 回归，强制要求用户更换工具变量
- **平行趋势预检**：DID 分析前，自动检验处理组与对照组在干预前的时间趋势是否平行
- **沙盒执行**：所有 Python 代码在沙盒环境运行，禁止直接读取宿主机敏感文件

## 变量标签与重命名规范

学术表格中变量须使用清晰的中文/英文标签：

```python
# 标准重命名映射示例
RENAME_MAP = {
    "co_size_ln": "Firm Size (log)",
    "it_investment_g": "IT Investment (%)",
    "roa": "Return on Assets",
    "lev": "Leverage Ratio",
    "predicted_it": "IT Investment (IV)",
    "ln_gov_proc": "Government Procurement (log)",
}
```

本技能默认使用学术标准命名，用户可通过 `RENAME_MAP` 自定义覆盖。

## 相关资源

- `references/panel-regression-guide.md` — 面板回归操作手册与诊断标准
- `references/iv-diagnostics.md` — 工具变量检验逻辑与临界值
- `references/staggered-did-guide.md` — 多时点 DID 完整操作指南
- `references/stargazer-usage.md` — 表格导出与重命名配置

---

**设计原则**：用户提需求 → 技能全自动 → 输出可直接发表的结果。分析师只需审查逻辑正确性，无需手工操作代码。