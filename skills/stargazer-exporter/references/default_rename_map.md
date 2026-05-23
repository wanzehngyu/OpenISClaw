# 默认变量重命名映射表

## 通用 IS 领域变量映射

以下映射表用于将原始数据库变量名转换为学术论文清晰标签。

### 企业特征变量

| 原变量名 | 学术标签（英文） | 学术标签（中文） |
|----------|-----------------|-----------------|
| `co_size_ln` / `ln_size` | Firm Size (log) | 企业规模（对数） |
| `co_size` / `size` | Firm Size | 企业规模 |
| `age` / `firm_age` | Firm Age | 企业年龄 |
| `tenure` / `ceo_tenure` | CEO Tenure | 首席执行官任期 |
| `lev` / `debt_ratio` | Leverage Ratio | 资产负债率 |
| `roa` | Return on Assets | 资产收益率 |
| `roe` | Return on Equity | 净资产收益率 |
| `tangibility` | Asset Tangibility | 资产有形性 |
| `cash` / `cash_ratio` | Cash Holdings | 现金持有量 |
| `sales_growth` | Sales Growth | 营业收入增长率 |
| `export` / `export_intensity` | Export Intensity | 出口强度 |
| `rd` / `rd_intensity` | R&D Intensity | 研发强度 |

### IT 与数字化变量

| 原变量名 | 学术标签（英文） | 学术标签（中文） |
|----------|-----------------|-----------------|
| `it_investment_g` | IT Investment (%) | IT 投资占比 |
| `it_spending` | IT Spending | IT 支出 |
| `it_investment` | IT Investment | IT 投资 |
| `digitalization` | Digitalization Level | 数字化水平 |
| `digital_transformation` | Digital Transformation | 数字化转型 |
| `ict_investment` | ICT Investment | 信息通信技术投资 |
| `e_business` | E-Business Adoption | 电子商务采用 |
| `cloud_adoption` | Cloud Adoption | 云采用 |
| `ai_adoption` | AI Adoption | 人工智能采用 |
| `erp_adoption` | ERP Adoption | ERP 系统采用 |
| `predicted_it` | IT Investment (IV) | IT 投资（工具变量预测值） |

### 治理与结构变量

| 原变量名 | 学术标签（英文） | 学术标签（中文） |
|----------|-----------------|-----------------|
| `board_size` | Board Size | 董事会规模 |
| `board_indep` / `indep_ratio` | Board Independence | 独立董事比例 |
| `duality` / `ceo_duality` | CEO Duality | CEO 两职合一 |
| `top10_share` / `top_holder` | Top 10 Shareholder | 前十大股东持股 |
| `state_own` | State Ownership | 国有持股 |
| `foreign_own` | Foreign Ownership | 外资持股 |
| `institution_own` | Institutional Ownership | 机构持股 |

### 行业与宏观变量

| 原变量名 | 学术标签（英文） | 学术标签（中文） |
|----------|-----------------|-----------------|
| `hhi` / `concentration` | Industry Concentration (HHI) | 行业集中度 |
| `competition` / `hhi_inv` | Competition Intensity | 竞争强度 |
| `gov_proc` / `ln_gov_proc` | Government Procurement (log) | 政府信息化采购（对数） |
| `digital_infra` | Digital Infrastructure | 数字基础设施 |
| `region_gdp` | Regional GDP (log) | 地区 GDP（对数） |
| `region_fdi` | Regional FDI (log) | 地区 FDI（对数） |

### 工具变量

| 原变量名 | 学术标签（英文） | 学术标签（中文） |
|----------|-----------------|-----------------|
| `iv_ln_gov_proc` | Government IT Procurement (IV) | 政府 IT 采购（工具变量） |
| `iv_digital_infra` | Digital Infrastructure (IV) | 数字基础设施（工具变量） |
| `iv_industry_digit` | Industry Digitization (IV) | 行业数字化（工具变量） |

## 自定义重命名

用户可通过 `--rename` 参数覆盖默认映射：

```bash
python generate_table.py \
  --rename "it_investment_g:IT投资,co_size_ln:企业规模,roa:企业绩效" \
  ...
```

格式：`old_name:new_label,old_name2:new_label2`

## 使用正则表达式处理模式变量

当变量名有规律但难以一一列举时，可在 SKILL.md 中添加正则处理逻辑：

```python
import re

def rename_var(var_name, rename_map):
    """Apply rename mapping with regex fallback."""
    # Direct match
    if var_name in rename_map:
        return rename_map[var_name]
    
    # Pattern-based rename
    patterns = [
        (r"^it_inv_(\d+)$", r"IT Investment (\1yr)"),
        (r"^roa_q(\d+)$", r"ROA Q\1"),
        (r"^ln_(.+)$", r"\1 (log)"),
    ]
    
    for pattern, replacement in patterns:
        new_name = re.sub(pattern, replacement, var_name)
        if new_name != var_name:
            return new_name
    
    return var_name  # No match, keep original
```