---
name: economic-database
description: 连接宏观经济数据库（世界银行WB、联储经济数据FRED、国家统计局CSMAR/国泰安、Wind）获取经济指标数据。当用户提出"下载宏观数据"、"获取GDP/CPI/利率数据"、"读取国泰安数据"、"世界银行指标"、"FRED数据"时激活。支持按国家/地区、时间范围、指标代码批量拉取数据，直接对接 panel-regression 和 iv-estimator 进行因果推断。
metadata:
  {
    "openclaw": {
      "emoji": "🌍",
      "requires": {
        "bins": ["python"],
        "os": ["linux", "darwin", "win32"]
      },
      "install": [
        {
          "id": "pip-wbdata",
          "kind": "pip",
          "package": "wbdata",
          "label": "Install wbdata (World Bank data)"
        },
        {
          "id": "pip-fred",
          "kind": "pip",
          "package": "fred",
          "label": "Install fred (FRED API client)"
        },
        {
          "id": "pip-pandas",
          "kind": "pip",
          "package": "pandas",
          "label": "Install pandas"
        },
        {
          "id": "pip-requests",
          "kind": "pip",
          "package": "requests",
          "label": "Install requests"
        }
      ]
    }
  }
---

# Economic Database: 宏观经济数据库连接技能

## 概述

本技能提供连接多个主流宏观经济数据库的统一接口，支持数据检索、清洗与合并，直接输出可导入计量模型的 CSV/DataFrame 格式。

## 支持的数据库

| 数据库 | 数据源 | 覆盖范围 | 获取方式 |
|--------|--------|----------|----------|
| **World Bank** | 世界银行公开数据 | 200+ 国家，1960至今，10000+ 指标 | API (wbdata) |
| **FRED** | 美联储圣路易斯分行 | 美国及全球宏观指标 | API (fred) |
| **CNBS/CSMAR** | 国泰安 | 中国A股上市公司财务数据 | 本地文件 / API |
| **Wind** | 万得 | 中国宏观及A股数据 | 本地文件 / API |

## 核心功能

- **多数据库联合查询**：一次请求横跨多个数据源
- **时间序列对齐**：自动对齐不同频率数据（月度→季度均值）
- **面板数据构建**：与用户上传的企业微观数据按年份/行业合并
- **缺失值处理**：线性插值、前向填充
- **序列化输出**：输出 pickle/DataFrame 供下游回归技能直接使用

## 数据库连接说明

### World Bank (wbdata)

```python
import wbdata
import pandas as pd

# 拉取中国GDP增速（NY.GDP.MKTP.KD.ZG）
data_date = pd.date_range(start='2010-01-01', end='2023-12-31', freq='YS')
wbdata.set_dataframe(indicator='NY.GDP.MKTP.KD.ZG', country='CN', date=data_date)
```

### FRED (fred)

```python
from fred import Fred
fred = Fred(api_key='YOUR_API_KEY')  # https://fred.stlouisfed.org/docs/api/api_key.html

# 拉取美国10年期国债收益率
data = fred.get_series('DGS10', observation_start='2010-01-01', observation_end='2023-12-31')
```

### CSMAR / 国泰安（中国A股）

```python
import pyreadstat
# 国泰安数据通常为 .dta 格式
df_csmar, meta = pyreadstat.read_dta('./data/csmar_financial.dta')
```

### Wind（需要本地客户端）

```python
# Wind数据通过本地Wind终端或PyWind读取
from WindPy import w
w.start()
data = w.edb("M0010119", "2010-01-01", "2023-12-31")  # CPI当月同比
```

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--db` | string | ✅ | 数据库名：`worldbank`、`fred`、`csmar`、`wind` |
| `--indicators` | string | ✅ | 指标代码，多个用空格分隔 |
| `--country` | string | ❌ | 国家/地区代码（World Bank专用，如 `CN`、`US`） |
| `--start` | string | ✅ | 开始时间 `YYYY-MM-DD` |
| `--end` | string | ✅ | 结束时间 `YYYY-MM-DD` |
| `--freq` | string | ❌ | 频率：`annual`（默认）、`quarterly`、`monthly` |
| `--merge_with` | string | ❌ | 用户已有面板数据的路径，用于宏微观合并 |
| `--output_csv` | string | ✅ | 输出 CSV 路径 |
| `--output_pickle` | string | ❌ | 输出 pickle 路径 |

## 执行流程

```bash
python {baseDir}/scripts/fetch_macro_data.py \
  --db "worldbank" \
  --indicators "NY.GDP.MKTP.KD.ZG FP.CPI.TOTL.ZG" \
  --country "CN" \
  --start "2010-01-01" \
  --end "2023-12-31" \
  --freq "annual" \
  --output_csv "./output/china_macro.csv"
```

### 标准输出格式

```
🌍 [宏观经济数据获取完成]
数据库: World Bank (CN)
时间范围: 2010 — 2023
指标:
  - NY.GDP.MKTP.KD.ZG: GDP增速 (%，年)
  - FP.CPI.TOTL.ZG: CPI通胀率 (%，年)
样本量: 14 行 × 3 列

✅ 数据已保存至 ./output/china_macro.csv
✅ 可通过 --merge_with 与企业微观数据合并后进行回归
```

## 宏微观数据合并

当用户已有微观面板数据时，自动按年份或行业代码合并宏观变量：

```bash
python {baseDir}/scripts/fetch_macro_data.py \
  --db "worldbank" \
  --indicators "NY.GDP.MKTP.KD.ZG" \
  --country "CN" \
  --start "2010-01-01" \
  --end "2023-12-31" \
  --merge_with "./data/enterprise_panel.dta" \
  --merge_key "year" \
  --output_csv "./output/enterprise_panel_with_macro.csv"
```

输出宏微观合并面板，字段包含：
- `year`：时间ID
- `gdp_growth`：GDP增速（来自World Bank）
- `cpi`：通胀率（来自World Bank）
- 原微观数据所有字段

## 错误处理

| 场景 | 触发条件 | 处理方式 |
|------|----------|----------|
| API 连接失败 | 网络不通或API限制 | 尝试备用数据源或从缓存读取 |
| 指标代码无效 | World Bank指标代码错误 | 列出可用指标供用户选择 |
| 时间范围超限 | FRED数据最早只能到1970 | 自动截断并警告 |
| 频率不匹配 | 月度数据与年度回归混用 | 自动聚合并警告用户 |

## 相关资源

- `references/worldbank-indicator-codes.md` — 常用World Bank指标代码速查表
- `references/fred-common-series.md` — FRED常用数据系列速查表
- `references/csmar-table-schema.md` — CSMAR数据库表结构说明

## 依赖安装确认

```bash
python -c "import wbdata; print('wbdata OK')"
python -c "from fred import Fred; print('fred OK')"
python -c "import pandas; print('pandas OK')"
python -c "import requests; print('requests OK')"
```