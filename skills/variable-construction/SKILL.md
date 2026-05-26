---
name: variable-construction
description: 对面板数据进行变量构建与衍生计算。当用户提出"构建变量"、"生成新变量"、"计算增长率"、"行业调整"、"去中心化"、"标准化"、"虚拟变量"时激活。基于 pandas，提供变量计算、行业均值、时间差分、滞后项生成等常用变量构建方法，输出可直接对接 panel-regression。
metadata:
  {
    "openclaw": {
      "emoji": "🔧",
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
          "id": "pip-numpy",
          "kind": "pip",
          "package": "numpy",
          "label": "Install numpy"
        }
      ]
    }
  }
---

# Variable Construction: 变量构建技能

## 概述

实证研究中，原始变量往往需要经过二次加工才能进入回归模型。本技能提供常用变量构建方法的自动化实现，支持在数据清洗完成后直接调用。

## 核心功能

### 1. 增长率与变化量

```python
# 年同比增长率
df['roa_growth'] = df.groupby('firm_id')['roa'].pct_change(periods=1)

# 时间差分（t - t-1）
df['roa_diff'] = df.groupby('firm_id')['roa'].diff(1)

# 滞后项（t-1）
df['roa_lag1'] = df.groupby('firm_id')['roa'].shift(1)

# 超前项（t+1）
df['roa_lead1'] = df.groupby('firm_id')['roa'].shift(-1)
```

### 2. 行业均值与组内去中心化

```python
# 行业均值（按行业-年份）
df['industry_roa'] = df.groupby(['industry_code', 'year'])['roa'].transform('mean')

# 组内去中心化
df['roa_centered'] = df.groupby('firm_id')['roa'].transform(lambda x: x - x.mean())

# 行业调整后变量（减去行业均值）
df['roa_ind_adj'] = df['roa'] - df['industry_roa']
```

### 3. 虚拟变量

```python
# 二值虚拟变量（阈值可自定义）
df['big_firm'] = (df['co_size_ln'] > df['co_size_ln'].median()).astype(int)

# 分组虚拟变量（ tercile / quartile）
df['size_tercile'] = pd.qcut(df['co_size_ln'], q=3, labels=[1,2,3])

# 时间虚拟变量（年份固定效应底层变量）
df['year_dummy'] = df['year']
```

### 4. 交乘项

```python
# 标准化后交乘（减轻多重共线性）
df['it_x_size'] = (df['it_investment_g'] - df['it_investment_g'].mean()) / df['it_investment_g'].std() \\
                  * (df['co_size_ln'] - df['co_size_ln'].mean()) / df['co_size_ln'].std()
```

### 5. 滚动统计量

```python
# 过去3期滚动均值
df['roa_rolling3'] = df.groupby('firm_id')['roa'].transform(
    lambda x: x.shift(1).rolling(3, min_periods=1).mean()
)

# 滚动标准差（波动性）
df['roa_volatility'] = df.groupby('firm_id')['roa'].transform(
    lambda x: x.shift(1).rolling(3, min_periods=2).std()
)
```

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--data` | string | ✅ | 输入数据路径（.csv/.dta/.xlsx） |
| `--operations` | string | ✅ | 操作序列，格式：`原变量:操作:新变量名`（多个用 `\|` 分隔） |
| `--entity` | string | ✅ | 个体ID列名 |
| `--time` | string | ✅ | 时间ID列名 |
| `--output_csv` | string | ✅ | 输出 CSV 路径 |

## 操作语法说明

| 操作代码 | 含义 | 示例 |
|----------|------|------|
| `diff` | 一阶差分 | `roa:diff:roa_diff` |
| `pct_change` | 环比增长率 | `roa:pct_change:roa_growth` |
| `lag1` | 一阶滞后 | `roa:lag1:roa_lag1` |
| `lag2` | 二阶滞后 | `roa:lag2:roa_lag2` |
| `lead1` | 一阶超前 | `roa:lead1:roa_lead1` |
| `winsorize` | 缩尾 | `lev:winsorize:lev_win` |
| `demean` | 组内去中心化 | `roa:demean:roa_dm` |
| `industry_mean` | 行业均值 | `roa:industry_mean:industry_roa` |
| `industry_adj` | 行业调整 | `roa:industry_adj:roa_ind_adj` |
| `stdz` | 标准化 | `it_investment_g:stdz:it_std` |
| `winsor` | 缩尾（默认1%/99%）| `lev:winsor:lev_win` |

## 执行流程

```bash
python {baseDir}/scripts/build_variables.py \
  --data "./data/cleaned_enterprise_panel.csv" \
  --entity "firm_id" \
  --time "year" \
  --operations "roa:diff:roa_diff|roa:pct_change:roa_growth|it_investment_g:lag1:it_lag1|lev:winsor:lev_win|co_size_ln:industry_mean:ind_size" \
  --output_csv "./data/enterprise_panel_var.csv"
```

## 输出内容

```
🔧 [变量构建完成]

构建的变量:
  roa_diff         = d(roa)/dt          (一阶差分)
  roa_growth       = d(roa)/roa(t-1)     (环比增长率)
  it_lag1          = it_investment_g(t-1)  (一阶滞后)
  lev_win          = winsorize(lev, 1%, 99%) (缩尾)
  ind_size         = mean(co_size_ln by industry×year) (行业均值)

输出:
  变量数: 18 → 23（新增5个）
  路径: ./data/enterprise_panel_var.csv
```