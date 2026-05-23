# 多时点 DID 完整操作指南

## 1. Staggered DID 背景与问题

### 1.1 传统 TWFE 的问题

传统双向固定效应（TWFE）在交错处理（Staggered Adoption）下可能产生严重偏误：

$$\hat{\beta}_{TWFE} = \sum_g \sum_t w_{gt} \cdot ATT(g,t)$$

其中权重 $w_{gt}$ 可能为负，导致"负权重问题"：

- 早期处理组与晚期对照组相比时获得负权重
- 晚期处理组与早期处理组相比时获得负权重
- 当处理效应随时间变化时，这些负权重导致估计量严重偏离真实 ATT

### 1.2 Callaway-Sant'Anna 解决方案

使用"尚未采纳"组（Not-Yet-Treated）或"永不采纳"组（Never-Treated）作为纯净对照组：

$$ATT(g,t) = \mathbb{E}[Y_t^{(1)} - Y_t^{(0)} | G=g] - \mathbb{E}[Y_t^{(0)} | G=g] + \mathbb{E}[Y_t^{(0)} | C_t]$$

其中 $C_t$ 为对照组（尚未处理或永不处理）。

**双重稳健估计量（Doubly Robust）：**
- 方法 1：逆概率加权（IPW）
- 方法 2：回归调整（RA）
- 方法 3：双重稳健（DR）= IPW + RA 的结合

## 2. 数据结构要求

### 2.1 必需列

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | int | 个体唯一标识 |
| `t` | int | 时间标识（年/月份） |
| `g` | int | 首次处理时间（从未处理为 0） |
| `y` | float | 结果变量 |

### 2.2 判定规则

- `g = 0`：永不接受干预（Never-Treated）
- `g > 0`：在给定年份首次接受干预
- **Absorbing Treatment**：一旦处理，不再恢复未处理状态

```python
# 示例数据
df = pd.DataFrame({
    'firm_id': [1, 1, 1, 2, 2, 2, 3, 3, 3],
    'year': [2018, 2019, 2020, 2018, 2019, 2020, 2018, 2019, 2020],
    'first_adoption': [2019, 2019, 2019, 0, 0, 0, 2020, 2020, 2020],  # g
    'roa': [0.05, 0.06, 0.07, 0.04, 0.05, 0.05, 0.04, 0.05, 0.06]
})

# 判定处理状态
df['treated'] = (df['year'] >= df['first_adoption']) & (df['first_adoption'] > 0)
# firm_id=1: False, True, True
# firm_id=2: False, False, False
# firm_id=3: False, False, True
```

### 2.3 常见数据结构问题

| 问题 | 检测方法 | 解决方案 |
|------|----------|----------|
| 处理状态逆转 | 某企业先未处理后处理再未处理 | 数据清洗，确保 absorbing treatment |
| 对照组不足 | never-treated < 5% | 使用 not-yet-treated 作为对照 |
| 动态 Cohort 不平衡 | 不同群组样本量差异过大 | 分层分析，控制 cohort size |

## 3. 估计流程

### 3.1 主要函数

```python
import moderndid as did

# Step 1: 估计群组-时间 ATT
att_gt_result = did.att_gt(
    data=df,
    yname='y',           # 结果变量
    tname='t',           # 时间变量
    idname='id',         # 个体 ID
    gname='g',           # 首次处理年份（0=never-treated）
    xformla='~ x1 + x2', # 协变量（可选）
    est_method='dr',      # 'dr'（双重稳健）或 'ipw'（逆概率加权）
    control_group='notyettreated',  # 'notyettreated' 或 'nevertreated'
    boot=True,
    n_bootstrap=500
)

# Step 2: 聚合为事件研究
event_study = did.aggte(
    att_gt_result,
    type='dynamic',  # 'dynamic' = 事件研究法
    min_g=-5,        # 预处理期下限
    max_g=5          # 处理后上限
)
```

### 3.2 结果解读

| 属性 | 说明 |
|------|------|
| `att_gt_result.att` | 各群组-时间组合的 ATT |
| `att_gt_result.se` | 稳健标准误（bootstrap） |
| `event_study.overall_att` | 总体平均处理效应 |
| `event_study.overall_se` | 总体 ATT 标准误 |
| `event_study.dynamic_atts` | 事件研究系数（相对时间） |
| `event_study.dynamic_se` | 事件研究标准误 |

## 4. 平行趋势检验

### 4.1 视觉检验

事件研究图中预处理期（t < 0）的置信区间须包含 0：

```
      |
 ATT  |       ●------●
      |      /
  0   |-----/------------------> (干预时点 t=0)
      |    /
      |   ● 
      |
      +---------------------------
         t=-3  t=-2  t=-1  t=0  t=1  t=2
```

### 4.2 统计检验

```python
# 检验预处理期效应是否联合显著为 0
from scipy import stats

pre_periods = event_study.dynamic_atts[:negative_g_indices]
pre_se = event_study.dynamic_se[:negative_g_indices]

# 联合 F 检验
f_stat = sum(pre_periods ** 2 / pre_se ** 2) / len(pre_periods)
p_value = 1 - stats.f.cdf(f_stat, len(pre_periods), 1000)

if p_value > 0.05:
    print("✅ [平行趋势假设成立] 预处理期效应不显著（p = {:.3f}）".format(p_value))
else:
    print("❌ [平行趋势假设失败] 预处理期效应显著（p = {:.3f}）".format(p_value))
```

## 5. Goodman-Bacon 分解（可选诊断）

TWFE 偏误来源分解：

```python
# 安装 did 包中的 bacon decomposition
from did.bacon import Bacon

bacon_result = Bacon(
    data=df,
    yname='y',
    tname='t',
    idname='id',
    gname='g'
)

print(bacon_result.summary())
```

**分解结果解读：**

| 成分 | 权重 | 说明 |
|------|------|------|
| 早期处理组 vs 晚期对照组 | ~40% | 偏误主要来源 |
| 晚期处理组 vs 早期对照组 | ~30% | 权重可能为负 |
| 未处理组作为对照 | ~30% | 较纯净的估计 |

## 6. 输出解读模板

```
### [多时点 DID 因果推断报告]

【数据概况】
- 样本量: N = 4,832（企业×年份）
- 处理组企业数: 1,208
- 对照组企业数: 856（其中 never-treated: 234, not-yet-treated: 622）
- 处理年份分布: 2018(342), 2019(486), 2020(380)

【估计结果】
- 总体 ATT: 0.0382 (SE: 0.0127, 95% CI: [0.0134, 0.0630])
- 估计方法: Callaway-Sant'Anna 双重稳健估计量（DR）
- 对照组: Not-Yet-Treated

【事件研究法结果】
| 相对时间 | ATT | SE | 95% CI |
|----------|-----|----|--------|
| t = -3   | 0.012 | 0.018 | [-0.024, 0.048] |
| t = -2   | 0.008 | 0.015 | [-0.022, 0.038] |
| t = -1   | 0.004 | 0.012 | [-0.020, 0.028] |
| t = 0    | 0.031 | 0.013 | [0.006, 0.056]  |
| t = 1    | 0.042 | 0.014 | [0.015, 0.069]  |
| t = 2    | 0.051 | 0.016 | [0.020, 0.082]  |

【平行趋势检验】
✅ 预处理期（t=-3, t=-2, t=-1）置信区间均包含 0
✅ 联合 F 检验: p = 0.481 → 平行趋势假设成立

【学术结论】
事件研究法结果显示，数字化转型对企业绩效的处理效应在
干预后逐年递增（t=0: +3.1%, t=1: +4.2%, t=2: +5.1%），
且预处理期平行趋势假设满足。因果效应显著为正。
```

## 7. 局限性说明

| 局限性 | 说明 | 缓解措施 |
|--------|------|----------|
| SUTVA 假设 | 若处理组影响对照组，则违反 Stable Unit Treatment Value Assumption | 检查是否存在溢出效应 |
| 无未观测混淆 | 假设在控制协变量后，处理组与对照组可比较 | 使用双重稳健估计量降低偏误风险 |
| 动态处理效应 | 若效应在处理后持续变化，事件研究图难以完全捕捉 | 补充分组分析 |
| 对照组选择 | not-yet-treated vs never-treated 选择影响估计 | 进行敏感性分析 |