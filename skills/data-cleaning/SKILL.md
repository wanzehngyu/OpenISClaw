---
name: data-cleaning
description: 对面板数据进行系统性清洗与预处理。当用户提出"清洗数据"、"处理缺失值"、"异常值检测"、"数据去重"、"变量清洗"、"数据质量检查"时激活。基于 pandas/pyreadstat，提供从原始数据到可回归格式的全套清洗流程，输出可直接对接 panel-regression 和 iv-estimator 的 CSV。
metadata:
  {
    "openclaw": {
      "emoji": "🧹",
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
          "id": "pip-pyreadstat",
          "kind": "pip",
          "package": "pyreadstat",
          "label": "Install pyreadstat"
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

# Data Cleaning: 数据清洗与预处理技能

## 安装与使用

本技能支持三种安装运行方式：

### 方式一：有 OpenClaw（推荐）

OpenClaw 用户直接通过命令安装：

```bash
openclaw skill install data-cleaning
```

OpenClaw 会自动检测并安装所需 pip 依赖。

### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）

安装 pip 依赖后，直接运行脚本：

```bash
# 安装依赖（核心计量包）
pip install pandas numpy scipy pyreadstat

# 运行脚本
python skills/data-cleaning/scripts/data_cleaning.py --help
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

实证研究的数据质量直接决定回归结果的可靠性。本技能提供从原始数据到"可分析格式"的全套清洗流程，覆盖缺失值处理、异常值检测、去重与一致性检验四大模块。

## 核心功能

### 1. 缺失值处理

| 方法 | 适用场景 | 操作 |
|------|----------|------|
| 删除（listwise） | 变量缺失比例 > 30% | 直接删除该行 |
| 均值填充 | 连续变量，无明显趋势 | `df[col].fillna(df[col].mean())` |
| 中位数填充 | 连续变量，存在极端值 | `df[col].fillna(df[col].median())` |
| 前向填充（ffill） | 时间序列，有序面板 | `df[col].ffill()` |
| 线性插值 | 面板数据，短期缺失 | `df[col].interpolate(method='linear')` |
| 插值后标记 | 需要控制缺失指示变量 | 生成 `_missing` 虚拟变量 |

**缺失值报告输出：**

```
🧹 [缺失值报告]
| 变量         | 缺失数 | 缺失率  | 建议处理  |
|--------------|--------|---------|-----------|
| it_investment_g | 234  | 4.8%   | ffill+插值 |
| roa             | 0    | 0.0%   | 无需处理   |
| co_size_ln      | 12   | 0.2%   | 均值填充   |
| lev             | 89   | 1.8%   | 线性插值   |

⚠️ 建议: it_investment_g 缺失率 4.8%，建议使用线性插值并生成 _missing 标记
```

### 2. 异常值检测

| 方法 | 判定标准 | 处理方式 |
|------|----------|----------|
| IQR 法则 | Q3 + 1.5×IQR 之外 | 缩尾（Winsorize）或删除 |
| Z-score | \|Z\| > 3 | 缩尾或删除 |
| 面板固定效应 | 在组内无变异（std=0） | 标记并报告 |
| 逻辑校验 | 资产负债率 > 1 或 < 0 | 修正或删除 |

**缩尾操作：**

```python
def winsorize(series, lower=0.01, upper=0.99):
    return series.clip(series.quantile(lower), series.quantile(upper))
```

### 3. 数据去重

```python
# 完全重复行删除
df.drop_duplicates(inplace=True)

# 面板ID-时间组合唯一性（强制保留第一条）
df.drop_duplicates(subset=['firm_id', 'year'], keep='first')
```

### 4. 一致性检验

| 检验项 | 触发条件 | 输出 |
|--------|----------|------|
| ID重复 | 同一 firm_id 在同一年份出现多条记录 | 报错退出 |
| 负数检验 | 规模、利润率出现负值 | 标记警告 |
| 逻辑矛盾 | 成立年份 > 解散年份 | 标记并设为缺失 |
| 时间断裂 | 面板时间序列不连续 | 报告断裂点 |

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 输入数据路径（.dta/.csv/.xlsx） |
| `--entity` | string | ✅ | 个体ID列名 |
| `--time` | string | ✅ | 时间ID列名 |
| `--missing_strategy` | string | ❌ | 缺失值策略：`drop`/`ffill`/`interpolate`（默认`interpolate`） |
| `--winsorize` | string | ❌ | 是否缩尾：`yes`（默认）/`no`，格式 `lower,upper` 如 `0.01,0.99` |
| `--output_csv` | string | ✅ | 输出 CSV 路径 |
| `--report_path` | string | ❌ | 诊断报告路径（.txt） |

## 执行流程

```bash
python {baseDir}/scripts/data_cleaning.py \
  --data "./data/raw_enterprise_panel.dta" \
  --entity "firm_id" \
  --time "year" \
  --missing_strategy "interpolate" \
  --winsorize "yes,0.01,0.99" \
  --output_csv "./data/cleaned_enterprise_panel.csv" \
  --report_path "./output/data_quality_report.txt"
```

## 输出内容

### 1. 清洗后数据集

CSV/Parquet 格式，直接可用于回归分析。

### 2. 质量报告

```
🧹 [数据质量报告] — 清洗前 → 清洗后

原始数据:
  - 样本量: 5,203 行
  - 时间范围: 2010 — 2023
  - 变量数: 18

缺失值处理:
  - 插值填充: roa (12处), lev (8处)
  - 均值填充: co_size_ln (5处)
  - 删除行: it_investment_g 缺失 3行（缺失率 < 1%）

异常值处理:
  - 缩尾处理: roa (1%/99%分位数), lev (1%/99%分位数)
  - 删除行: 资产负债率 > 1 的 7 条记录

去重处理:
  - firm_id+year 重复: 删除 23 行（保留首条）

清洗后数据:
  - 样本量: 5,173 行（减少 30 行）
  - 变量数: 18
  - 无完全重复行
  - 缺失值已处理完毕

✅ 清洗后数据已保存至 ./data/cleaned_enterprise_panel.csv
✅ 质量报告已保存至 ./output/data_quality_report.txt
```

## 错误处理

| 场景 | 触发条件 | 处理方式 |
|------|----------|----------|
| ID-时间重复 | 同一 firm_id 同 year 有多条记录 | 保留第一条并警告 |
| 严重缺失 | 某变量缺失率 > 50% | 报错，要求用户确认是否删除 |
| 时间格式混乱 | 无法解析年份 | 报错，要求手动确认时间格式 |
| ID类型异常 | firm_id 含字符串 | 警告，尝试转换为数值型 |

## 相关资源

- `references/data-quality-standards.md` — 数据质量标准与计量要求
- `references/missing-data-handling.md` — 缺失值处理学术规范
