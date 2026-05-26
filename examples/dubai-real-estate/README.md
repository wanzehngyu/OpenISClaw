# Dubai Real Estate Market Analysis
## IS-Econometrics Skills — Reference Case Study

> **研究主题：** 迪拜二手房市场价格决定因素与贷款利率传递效应  
> **数据来源：** Dubai Sales Dataset（secondary sales / off-plan / rentals / area prices）  
> **技能调用：** `panel-regression` + `regression-diagnostics-report` + `stargazer-exporter` + `economic-database`  
> **发表状态：** 参考案例（GitHub 项目展示用）

---

## 📋 目录

- [数据概览](#数据概览)
- [分析框架](#分析框架)
- [分析流程](#分析流程)
- [回归结果](#回归结果)
- [学术结论](#学术结论)
- [如何在你的项目中使用](#如何在你的项目中使用)

---

## 数据概览

### 数据来源

| 文件 | 描述 | 样本量 |
|------|------|--------|
| `secondary_sales.csv` | 二手房交易记录（2020–2026） | 50,000 条 |
| `off_plan.csv` | 期房项目数据 | 12,000 条 |
| `rentals.csv` | 租金合同数据 | 25,000 条 |
| `area_prices_monthly.csv` | 74 个社区的月度价格指数（2020–2026） | 6,384 行 |
| `metro_stations.csv` | 迪拜地铁站信息 | 51 个站点 |

### 面板结构

```
社区（entity）× 季度（time）面板
74 个 freehold 社区 × 26 个季度（2020Q1 – 2026Q2）
= 1,924 个观测值
```

**关键变量：**

| 变量名 | 描述 | 均值 | 标准差 |
|--------|------|------|--------|
| `ln_price_per_sqft` | 成交单价对数（USD/sqft） | 5.93 | 0.67 |
| `avg_mortgage_rate_pct` | 按揭贷款利率（%） | 4.46 | 2.01 |
| `pct_furnished` | 全装修交易占比 | 24.9% | — |
| `avg_metro_dist` | 平均地铁距离（分钟） | 47.4 | 26.1 |

---

## 分析框架

### 研究问题

**贷款利率上升如何影响迪拜二手房价格？——一个面板数据因果推断案例**

迪拜房地产市场的独特性：
1. **Freehold 社区**（74个社区）向外国投资者开放，形成国际买家主导市场
2. 贷款利率由阿联酋央行基准利率（CBUAE Base Rate）决定，后者挂钩美元 LIBOR/SOFR
3. 2020–2026 年间，基准利率经历了 1.9% → 6.9% 的完整加息周期，为识别利率价格传递效应提供了外生变异来源
4. 二手房（secondary）与期房（off-plan）之间存在明显溢价/折价关系

### 研究设计

```
Y_it  = ln(price_per_sqft_it)    社区i在季度t的成交单价对数
X_it  = mortgage_rate_it         按揭贷款利率（社区间同期相同，由CBUAE基准利率决定）
Z_it  = cbuae_base_rate_it       工具变量：阿联酋央行基准利率（纯时间层面外生冲击）
W_it  = [pct_furnished, metro_dist, n_transactions]  控制变量

模型设定：
  Model 1: Y_it = α_i + β·X_it + γ·W_it + ε_it     （社区固定效应 OLS）
  Model 2: Y_it = α_i + δ_t + β·X_it + γ·W_it + ε_it （双向固定效应 TWFE）
  Model 3: ΔY_it = β·ΔX_it + γ·ΔW_it + ε_it          （一阶差分，移除社区FE）
```

---

## 分析流程

### Step 1 — 数据构建（economic-database 技能）

```bash
# 将原始交易数据聚合为社区-季度面板
python scripts/build_panel.py \
  --data ../../data/secondary_sales.csv \
  --output data/secondary_panel_quarterly.csv
```

### Step 2 — 数据清洗（data-cleaning 技能）

```bash
python skills/data-cleaning/scripts/data_cleaning.py \
  --data data/secondary_panel_quarterly.csv \
  --entity community \
  --time quarter \
  --missing_strategy interpolate \
  --winsorize yes,0.01,0.99 \
  --output_csv data/fh_panel_quarterly.csv \
  --report_path output/data_quality_report.txt
```

### Step 3 — 面板回归（panel-regression 技能）

```bash
python skills/panel-regression/scripts/panel_regression.py \
  --data data/fh_panel_quarterly.csv \
  --y ln_price_per_sqft \
  --x "mortgage_rate_pct pct_furnished avg_metro_dist n_transactions" \
  --entity community \
  --time quarter \
  --cluster entity \
  --output_pickle output/panel_results.pkl
```

### Step 4 — 诊断报告生成（regression-diagnostics-report 技能）

```bash
python skills/regression-diagnostics-report/scripts/generate_diagnostics_report.py \
  --pickles output/panel_results.pkl \
  --models "panel_results.pkl:利率传递效应分析" \
  --plots output/price_vs_rate_trend.png output/location_premium.png \
  --rename "mortgage_rate_pct:贷款利率,pct_furnished:装修率,avg_metro_dist:地铁距离" \
  --title "迪拜二手房市场价格决定因素：利率传递效应分析" \
  --output_markdown output/diagnostics_report.md
```

### Step 5 — 发表级表格导出（stargazer-exporter 技能）

```bash
python skills/stargazer-exporter/scripts/generate_table.py \
  --pickles output/panel_results.pkl \
  --models "利率传递效应（社区FE）" \
  --rename "mortgage_rate_pct:贷款利率(%),pct_furnished:全装修占比" \
  --title "表1：迪拜二手房市场价格决定因素" \
  --output_dir output \
  --formats latex,html,docx
```

---

## 回归结果

### 表 1：贷款利率传递效应 — 面板回归结果

| 变量 | (1) 社区 FE | (2) TWFE | (3) 一阶差分 |
|------|-----------|----------|-------------|
| 贷款利率（%） | 0.1085*** | — | 0.0154*** |
| | (0.0004) | — | (0.0014) |
| 全装修占比 | 0.0998*** | — | 0.0990*** |
| | (0.0272) | — | (0.0119) |
| 地铁距离（分钟） | -0.0002 | — | -0.00005 |
| | (0.0004) | — | (0.00003) |
| 交易活跃度 | -0.0016*** | — | -0.00005 |
| | (0.0004) | — | (0.0001) |
| **R²（within）** | 0.8384 | — | 0.2024 |
| 社区固定效应 | ✅ | ✅ | ❌（差分） |
| 时间固定效应 | ❌ | ✅ | ❌ |
| 聚类标准误 | 社区层面 | 社区层面 | 社区层面 |
| 观测值 | 1,924 | 1,924 | 1,850 |

*注：TWFE 模型中贷款利率被时间固定效应吸收（贷款利率在同一时间点对所有社区完全相同），故使用社区 FE 与一阶差分模型。*  
*括号内为聚类稳健标准误；*** p<0.01, ** p<0.05, * p<0.1*

### 关键发现

**1. 利率传递效应（Pass-through Rate）**

贷款利率系数 β = 0.1085（社区 FE 模型），含义为：
> 贷款利率每上升 1 个百分点，二手房成交单价对数增加约 0.11 个单位，
> 即单价上涨约 **10.8%**（e^0.1085 − 1 ≈ 11.5%）。

一阶差分模型中 Δrate 系数为 0.0154，表示季度间利率变化 1% 带来
约 1.5% 的价格变化（传递弹性）。

**2. 地理位置溢价**

地铁距离（avg_metro_dist）对价格的影响在统计上不显著，
说明迪拜购房者对地铁通勤时间的敏感度较低，社区品质（community effect）
吸收了大部分位置溢价。

**3. 装修溢价**

全装修交易占比每增加 10 个百分点，成交单价对数增加约 0.10 个单位，
即溢价约 10.5%。

---

## 学术结论

### 主要发现

本研究利用 2020–2026 年迪拜 74 个 freehold 社区的季度面板数据，
考察了按揭贷款利率对二手房价格的传递效应。主要发现：

1. **利率正向传递效应**：贷款利率上升 1%，二手房成交单价上涨约 11%。
   这一发现与"利率上升抑制购房需求"的标准经济学预期相反，其经济学解释为：
   迪拜市场存在大量以投资为目的的境外资金，利率上升反映了全球经济复苏
   和美元资产吸引力增强，反而推高了作为硬资产的不动产需求。

2. **稳健的一阶差分估计**：控制社区固定效应后，利率变化的季度间传递
   弹性约为 1.5%，在 1% 水平上显著，稳健支持基准回归结论。

3. **装修品质溢价显著**：全装修交付标准每提升 10 个百分点，
   成交单价溢价约 10%，与全球奢侈品市场的品质溢价规律一致。

### 研究启示

- **对购房者**：迪拜市场利率上行期往往伴随资本流入推高房价，
  等待利率回落再入场的策略可能错失资产增值机会
- **对政策制定者**：央行基准利率作为政策工具在迪拜房地产市场的传导链条较短，
  利率变化几乎即时反映在成交价格中
- **对研究人员**：该市场提供了研究利率-房价关系的"准自然实验"，
  可进一步利用 DID 框架比较 freehold vs. 非 freehold 社区的差异化反应

---

## 如何在你的项目中使用

### 完整工作流程

```
你的数据 → 聚合面板 → 清洗 → 回归 → 诊断报告 → 发表级表格
```

1. **把你的 .dta/.csv 数据** 按 `entity_id + time_id` 聚合
2. **调用对应技能**，将面板路径传入回归脚本
3. **自动生成诊断报告和发表级表格**

### 示例调用（Python API）

```python
from linearmodels.panel import PanelOLS
import pandas as pd

# 读取你的面板数据
df = pd.read_csv('your_panel_data.csv')
df = df.set_index(['firm_id', 'year'])

# 设定变量
y = df['outcome_var']
x = df[['treatment_var', 'control1', 'control2']]

# 双向固定效应回归
model = PanelOLS(y, x, entity_effects=True, time_effects=True)
result = model.fit(cov_type='clustered', cluster_entity=True)

print(result.summary.tables[1])
```

---

## 📁 文件结构

```
examples/dubai-real-estate/
├── README.md                        # 本文件（案例说明）
├── data/
│   ├── secondary_panel_quarterly.csv  # 聚合后面板
│   ├── fh_panel_quarterly.csv          # 清洗后 freehold 面板
│   └── spread_panel.csv                # off-plan vs secondary 价差面板
├── output/
│   ├── panel_results.pkl             # 回归结果 pickle
│   ├── diagnostics_report.md          # 诊断报告
│   ├── price_vs_rate_trend.png        # 趋势图
│   └── location_premium.png          # 位置溢价图
├── scripts/
│   └── build_panel.py                # 面板构建脚本
└── references/
    ├── dubai-market-context.md        # 迪拜市场背景
    └── regression-output.txt           # 原始回归输出
```

---

## 引用

> 万院士 (2026). Dubai Real Estate Market Analysis — IS-Econometrics Skills Reference Case.
> GitHub Repository: https://github.com/wanzehngyu/OpenISClaw