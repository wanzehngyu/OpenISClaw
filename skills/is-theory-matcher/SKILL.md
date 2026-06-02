---
name: is-theory-matcher
description: 面向管理信息系统（IS）专业师生，当用户描述一个研究现象但不确定用哪种IS理论来解释时激活。技能通过语义匹配从15个核心IS理论库中推荐最匹配的理论，并生成完整的研究设计指引（假设、变量测量、实证策略），指导后续数据收集和建模过程。支持两种模式：（1）现象→理论推荐（推荐最适合解释现象的理论）；（2）理论→验证匹配（检验用户指定理论是否与现象匹配）。本技能为上游推荐层，不直接执行实证分析，具体建模由 panel-regression、iv-estimator、staggered-did 等子技能完成。
metadata: {
  "openclaw": {
    "emoji": "🔍",
    "requires": {
      "bins": ["python"],
      "os": ["linux", "darwin", "win32"]
    }
  }
}
---

# IS-Theory Matcher: IS 理论与研究设计推荐技能

## 概述

**你观察到一个现象，想知道用什么理论来解释？** 本技能正是为此设计。

用户只需描述自己想探究的现象或研究问题，技能会自动匹配最相关的 IS（信息系统）理论，并生成完整的研究设计指引——从理论框架到假设构建，从变量测量到实证策略，直至此前的实证建模。

```
用户: "我想研究某个政策对行业的影响是长期的还是短期的"
  │
  ▼
is-theory-matcher
  │  语义匹配 → Punctuated Equilibrium Theory（间断均衡）
  │
  ▼
研究设计生成
  │  研究假设 + 变量测量 + 数据要求 + 分析流程
  │
  ▼
与 panel-regression / staggered-did / iv-estimator 联动
  │
  ▼
实证结果 + 发表级表格（stargazer-exporter）
```

## 两种使用模式

### 模式一：现象 → 理论推荐（默认）

用户描述一个研究现象，技能推荐最匹配的理论并生成完整研究设计。

**典型触发词：** "我想研究..."、"某个现象可以用什么理论解释"、"帮我找理论框架"、"这个场景用什么IS理论"

### 模式二：理论 → 验证匹配

用户已确定理论，想验证该理论是否适合，或想了解在该理论下如何设计研究。

**典型触发词：** "用制度理论分析..."、"用网络效应理论"、"帮我用RBV框架"、"这个现象是否符合间断均衡"

## 支持的 IS 理论（15个）

| 理论 | 英文名 | 典型研究场景 | 匹配关键词示例 |
|------|--------|-------------|---------------|
| 间断均衡 | Punctuated Equilibrium | 政策冲击的突变效应、行业洗牌 | 政策影响、长期vs短期、突变、冲击 |
| 技术接受模型 | TAM | 新系统采纳阻力 | 技术接受、采纳意愿、有用性、易用性 |
| 计划行为理论 | TPB | 用户行为意向预测 | 行为意向、态度、规范、控制 |
| 技术接受统一理论 | UTAUT | 企业级技术采纳 | 绩效期望、努力期望、社会影响 |
| IS成功模型 | DeLone & McLean | 系统实施效果评估 | 系统成功、用户满意、信息质量 |
| 社会信息处理理论 | Social Info Processing | 虚拟团队沟通、远程办公 | 在线沟通、团队氛围、社会线索 |
| 临界量理论 | Critical Mass | 平台用户增长拐点 | 临界量、临界点、用户增长 |
| 知识基础理论 | Knowledge-Based | IT与知识整合、创新绩效 | 知识整合、知识转移、知识存量 |
| 资源基础观 | RBV | IT资源与竞争优势 | 异质资源、VRIN、不可模仿 |
| 动态能力理论 | Dynamic Capabilities | 数字化转型、敏捷性 | 感知能力、抓住机会、转型重构 |
| 正常化过程理论 | NPT | 系统持续使用、惯例化 | 正常化、持续使用、惯例嵌入 |
| 技术可供性理论 | Affordance Theory | 平台功能对行为的塑造 | 可供性、感知、行动实现 |
| 制度理论 | Institutional Theory | 监管压力、合法性、同构 | 制度压力、合规、模仿、同构 |
| 网络效应理论 | Network Effects | 平台价值与规模非线性关系 | 网络效应、梅特卡夫、锁定、赢家通吃 |
| 算法权力理论 | Algorithmic Power | 平台算法对商家/用户的影响 | 算法控制、算法透明度、算法歧视 |

## 技能架构

```
is-theory-matcher/
├── SKILL.md（本文档）
├── scripts/
│   ├── theory_db.json              # 15个IS理论的完整数据库
│   ├── matcher.py                  # 语义匹配引擎
│   └── research_design_generator.py # 研究设计生成器
└── references/
    └── theory-list.md              # 各理论详解与计量方法对照
```

## 工作流程

### Step 1：接收用户现象描述

用户输入研究现象或问题，技能解析关键词：

```
用户: "我想研究环保政策对制造业企业绩效的影响，是长期的还是短期的"
```

### Step 2：语义匹配（matcher.py）

`matcher.py` 对用户描述进行分词，与理论数据库的 `matching_keywords` 和 `key_concepts` 进行匹配评分：

```python
# 匹配示例
python skills/is-theory-matcher/scripts/matcher.py \
  --query "我想研究环保政策对制造业企业绩效的影响，是长期的还是短期的"
```

**输出示例：**
```
Top 1: Punctuated Equilibrium Theory（间断均衡）  匹配度: 87%
  理由: 现象涉及"政策影响"和"长期vs短期"的关键特征，
  间断均衡理论认为外部冲击会在长期稳定后触发突变，
  非常适合分析政策冲击对企业绩效的影响模式和持续性。

Top 2: Institutional Theory（制度理论）  匹配度: 72%
  理由: 制度理论关注监管压力对企业行为的合规效应，
  适合分析环保政策的强制性压力对企业绩效的影响。

Top 3: Dynamic Capabilities Theory（动态能力）  匹配度: 58%
```

### Step 3：生成研究设计（research_design_generator.py）

```python
# 研究设计生成示例
python skills/is-theory-matcher/scripts/research_design_generator.py \
  "punctuated_equilibrium" \
  "我想研究环保政策对制造业企业绩效的影响，是长期的还是短期的"
```

**输出内容：**

1. **研究问题**：基于间断均衡理论，重构用户现象为可检验的研究问题
2. **研究假设**（H1/H2/H3）：基于理论机制的因果假设
3. **变量测量建议**：因变量/自变量/中介变量/调节变量的具体测量方式
4. **数据要求**：数据类型、样本量、时间跨度、数据来源
5. **实证策略**：推荐使用的方法（对应具体子技能）
6. **分析流程**：Step-by-Step 的分析步骤

### Step 4：联动子技能执行实证分析

根据研究设计推荐的实证方法，联动对应子技能：

```
实证策略推荐 → 技能联动
  │
  ├─→ "事件研究法" + "断点回归RDD"
  │     → staggered-did / difference-in-discontinuities
  │
  ├─→ "双向固定效应面板回归"
  │     → panel-regression
  │
  ├─→ "工具变量回归"
  │     → iv-estimator
  │
  ├─→ "倾向得分匹配"
  │     → propensity-score-matching
  │
  └─→ "发表级表格"
        → stargazer-exporter
```

## 完整对话示例

### 示例一：用户有数据，想做实证研究

```
用户: 我有一个制造业上市公司2010-2023年的面板数据，想研究环保政策严格化对企业可持续发展的影响，是长期还是短期效应

助手: 好的，根据你的研究问题，我来帮你匹配最适合的理论框架并设计实证方案。

🔍 语义匹配结果：
  最匹配理论：Punctuated Equilibrium Theory（间断均衡）  匹配度 91%
  次匹配理论：Institutional Theory（制度理论）  匹配度 74%

📐 基于间断均衡理论的研究设计：

  研究问题：环保政策冲击是否触发制造业企业绩效的结构性断点？
           冲击后的恢复路径是什么？组织冗余资源如何调节恢复速度？

  研究假设：
  [H1] 环保政策趋严对企业绩效的负向影响在政策实施前后存在显著断点
  [H2] 政策冲击对企业绩效的影响在冲击后2-3年内逐渐衰减（短期效应）
  [H3] 组织冗余资源越丰富，企业从政策冲击中恢复的速度越快

  变量测量：
  因变量：ROA（总资产收益率）、TFP（全要素生产率）
  自变量：政策强度指数（环保处罚金额/合规成本）
  中介变量：战略调整频率、研发投入强度
  调节变量：组织冗余资源（现金比率、员工冗余度）
  控制变量：企业规模（ln总资产）、资产负债率、成立年限、行业竞争度

  数据要求：
  - 长面板数据，至少50家企业，时间跨度10年以上
  - 需要识别政策冲击的时间点（建议使用中央环保督察为外生冲击）
  - 数据来源：CSMAR（财务数据）+ 地方环保局处罚记录（手工整理）

  实证策略：
  1. 事件研究法：检验政策公告前后各期超额收益率（CAR）是否存在显著断点
  2. 断点回归（RDD）：以政策强度阈值为驱动变量，检验阈值处的局部处理效应
  3. 双向固定效应DID：处理组（高污染企业）vs 对照组（低污染企业），检验ATT的动态演变

  分析流程：
  Step 1: 事件研究法预检——确认平行趋势假设成立
  Step 2: RDD估计——识别政策阈值处的因果效应
  Step 3: TWFE-DID——估计政策冲击的平均处理效应及其时间衰减模式
  Step 4: 异质性分析——按企业规模/所有制/行业比较效应差异
  Step 5: 机制检验——中介效应检验（H2的衰减路径）
  Step 6: 稳健性——安慰剂检验、替换变量、子样本检验

  是否需要我调用 staggered-did 技能执行事件研究法分析？
```

### 示例二：用户只有想法，还没有数据

```
用户: 我观察到疫情期间很多传统企业加速了数字化转型，这个现象可以用什么理论来解释？

助手: 这是一个很有趣的观察！让我帮你从 IS 理论库中寻找最匹配的理论框架。

🔍 语义匹配结果：
  最匹配理论：Dynamic Capabilities Theory（动态能力）  匹配度 85%
  次匹配理论：Punctuated Equilibrium Theory（间断均衡）  匹配度 68%
  次匹配理论：Affordance Theory（技术可供性）  匹配度 61%

📐 推荐理论框架：动态能力理论

  核心主张：在快速变化的环境中，企业的持久竞争优势来自于
           感知环境变化、抓住机会、通过转换重构来更新组织的能力。

  疫情作为外部冲击，触发了企业的"动态能力"响应机制：
  - 感知（sensing）：感知到数字化机会和威胁
  - 抓住（seizing）：投资数字化工具和平台
  - 转换（transforming）：重组业务流程和组织架构

  研究假设建议：
  [H1] 环境动荡程度对数字化转型深度有显著正向影响
  [H2] 动态能力（感知/抓住/转换）在环境动荡与数字化转型之间起链式中介作用
  [H3] 数字化转型深度对企业短期（疫情期间）绩效有正向影响

  变量测量建议：
  - 环境动荡：行业营收增长率标准差、竞争对手数量变化率
  - 数字化转型：IT支出/总资产、数字化业务流程覆盖度（问卷）
  - 动态能力：Teece(2007)量表（感知/抓住/转换三个维度）
  - 企业绩效：ROA、营收增长率

  数据收集建议：
  - 推荐使用问卷调查（动态能力量表）+ 企业年报（数字化转型代理指标）
  - 样本：至少200家制造业或零售业企业
  - 建议采用分层抽样，覆盖不同行业和规模
  - 时间跨度：2019-2022年（疫情前后对照）

  实证策略：
  - 中介效应检验（三步法 + Bootstrap）：链式中介路径
  - 推荐使用结构方程模型（SEM）或多层线性模型（HLM）
  - 控制变量：企业规模、成立年限、所有制度、财务压力

  如果你后续收集到面板数据，可以联动 panel-regression 做量化检验。
```

### 示例三：用户指定理论

```
用户: 我想用网络效应理论分析某个双边平台的用户增长策略

助手: 好的，让我为你构建基于网络效应理论的研究设计。

📐 网络效应理论（Network Effects Theory）研究设计

  核心主张：平台价值随用户规模呈非线性增长（梅特卡夫效应），
           直接和间接网络效应导致赢家通吃。

  研究假设：
  [H1] 平台用户规模的平方项与平台价值（GMV）呈显著正相关（梅特卡夫效应）
  [H2] 卖家规模对买家采纳率有显著正向影响（跨边网络效应）
  [H3] 用户锁定程度正向调节用户规模对平台黏性的影响

  变量测量：
  - 因变量：平台价值（DAU/MAU、GMV、用户留存率）
  - 自变量：用户规模（MAU）、用户规模平方（MAU²）
  - 调节变量：转换成本、平台依赖度
  - 控制变量：平台成立年限、融资阶段、市场渗透率

  实证策略：
  1. 非线性检验：加入 MAU² 项，用 OLS 或 FE 估计
  2. 动态面板GMM：处理用户规模与平台价值的内生性
  3. 联立方程：卖家规模 ↔ 买家规模（跨边效应）

  推荐技能：panel-regression（非线性检验）+ iv-estimator（GMM）
```

## matcher.py 命令行用法

```bash
# 基本用法（返回Top-3匹配）
python skills/is-theory-matcher/scripts/matcher.py \
  --query "你的研究现象描述"

# 返回Top-5匹配
python skills/is-theory-matcher/scripts/matcher.py \
  --query "你的研究现象描述" \
  --top_k 5

# 输出完整匹配报告
python skills/is-theory-matcher/scripts/matcher.py \
  --query "你的研究现象描述" \
  --verbose
```

## research_design_generator.py 命令行用法

```bash
# 生成研究设计
python skills/is-theory-matcher/scripts/research_design_generator.py \
  "punctuated_equilibrium" \
  "我想研究环保政策对制造业企业绩效的影响"

# 可用 theory_id（从 matcher.py 输出获取）
# 全部可用理论ID：
#   punctuated_equilibrium, tam, tpb, utaut,
#   delone_mclean, social_information_processing,
#   critical_mass, knowledge_based, rbv,
#   dynamic_capabilities, normalization_process,
#   affordance, institutional, network_effects,
#   algorithmic_power
```

## 与其他技能的联动关系

| 推荐方法 | 联动技能 | 脚本 |
|---------|---------|------|
| 双向固定效应回归 | `panel-regression` | `panel_regression.py` |
| 工具变量回归 | `iv-estimator` | `iv_regression.py` |
| 多时点DID / 事件研究 | `staggered-did` | `staggered_did_pipeline.py` |
| 断点回归RDD | `difference-in-discontinuities` | `rdd_analysis.py` |
| 倾向得分匹配 | `propensity-score-matching` | `psm_analysis.py` |
| 生存分析 | `survival-analysis` | `survival_analysis.py` |
| 学术表格输出 | `stargazer-exporter` | `generate_table.py` |

联动由 `is-econometrics` 主控技能统一调度，本技能作为上游理论推荐层。

## 限制与边界

1. **本技能只做理论推荐和设计指引**，不直接执行实证回归分析
2. **理论数据库基于 TheorizeIt IS Wiki**，覆盖主流IS理论，无法穷尽所有理论
3. **匹配结果仅作为参考**，研究者应结合文献和专业知识判断
4. **变量测量仅为建议**，实际测量需根据具体情境和数据可得性调整
5. **实证方法的推荐假设用户已有或可获得相应数据**，若数据不可得，技能会说明数据要求

## 学术引用

若在学术研究中使用本技能进行理论筛选和设计，建议引用：

> 万院士 (2026). IS-Theory Matcher: 面向信息系统研究的理论与实证设计推荐技能. GitHub Repository.

相关理论文献：
- Tichy, N. M., & Uhlenbruck, K. (1979). "Punctuated Equilibrium Theory." Academy of Management Review.
- Davis, F. D. (1989). "Perceived Usefulness, Perceived Ease of Use, and User Acceptance of Information Technology." MIS Quarterly.
- Venkatesh, V., et al. (2003). "UTAUT." MIS Quarterly.
- DeLone, W. H., & McLean, E. R. (2003). "The DeLone and McLean Model of Information Systems Success." JMIS.
- Teece, D. J. (2007). "Explicating Dynamic Capabilities." Strategic Management Journal.
