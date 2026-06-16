---
name: paper-writer
description: 面向已完成实证分析的 IS 研究者，当用户拥有数据、研究问题、理论框架和实证结果，希望将这些素材整合成完整学术论文时激活。技能根据用户指定的素材（实证结果 pickle、研究问题、理论推荐结果）自动生成符合 IS 期刊规范（类似 MIS Quarterly / ISR / JAIS）的完整论文，包含引言（文献综述）、理论基础、假设推导、方法论、实证结果与分析和讨论六大章节。讨论部分涵盖理论贡献、实践贡献与研究局限与未来方向。触发词："写论文"、"生成论文"、"学术论文"、"发表级论文"、"帮我写完整的实证论文"。
metadata: {
  "openclaw": {
    "emoji": "📝",
    "requires": {
      "bins": ["python"],
      "os": ["linux", "darwin", "win32"]
    }
  }
}
---

# Paper Writer: IS 实证论文写作技能

## 概述

用户在完成数据清洗、变量构建、实证分析后，手头有：实证结果（pickle/表格）、研究问题、理论框架（来自 is-theory-matcher 或自行指定）、假设（或需要技能代为推导），希望生成一篇完整的学术论文。

本技能将这些素材整合为符合 IS 顶级期刊规范的完整论文，输出格式为 Markdown，可直接粘贴至 Word/Overleaf。

```
用户上传数据 + 提出研究问题
  │
  ▼
is-theory-matcher（可选）→ 推荐理论框架
  │
  ▼
is-econometrics / panel-regression / iv-estimator / staggered-did
  │
  ▼
stargazer-exporter / regression-diagnostics-report
  │
  ▼
paper-writer（本技能）
  │  接收：研究问题 + 数据描述 + 实证结果 + 理论/假设
  │  ① 文献检索（Tavily）→ 引言文献综述
  │  ② 理论框架整理 → 理论基础
  │  ③ 假设推导/整理 → 研究假设
  │  ④ 方法论描述 → 方法章节
  │  ⑤ 结果解读 → 实证结果章节
  │  ⑥ 综合讨论 → 讨论章节
  │
  ▼
完整学术论文（Markdown）
```

## 技能架构

```
paper-writer/
├── SKILL.md（本文档）
├── scripts/
│   ├── outline_generator.py        # 论文大纲生成器
│   ├── literature_fetcher.py       # 文献检索（调用 Tavily）
│   └── paper_writer.py            # 论文各章节内容生成
└── references/
    ├── paper-structure-template.md # 论文结构模板与写作规范
    └── is-journal-standards.md     # IS 期刊格式规范（MIQ/ISR/JAIS）
```

## 输入素材（由用户或上游技能提供）

| 素材 | 来源 | 说明 |
|------|------|------|
| 研究问题 | 用户描述 | 用户的研究现象或问题描述 |
| 数据集描述 | 用户提供或 data-cleaning 输出 | 变量名、样本量、时间跨度、来源 |
| 实证结果 | `panel_regression.py` / `iv_regression.py` 等输出的 `.pkl` 文件 | 模型估计结果 |
| 回归表格 | `stargazer-exporter` 输出的 LaTeX/HTML/Word | 发表级表格 |
| 诊断报告 | `regression-diagnostics-report` 输出的 `.md` 文件 | VIF、F、显著性等 |
| 理论推荐结果 | `is-theory-matcher` 输出 | 匹配的理论及理由 |
| 指定理论 | 用户直接提供 | 如用户已明确理论，可直接使用 |
| 研究假设 | 用户指定或理论推导 | 用户已给假设则直接用；未给则由技能结合理论和数据推导 |

## 输出规格

- **格式**：Markdown（全文字数约 6000-10000 中文词，含完整三线表格式）
- **语言**：中文（用户未明确要求英文时默认中文；可指定英文）
- **期刊风格**：默认 IS 期刊规范（类似 MIS Quarterly / Information Systems Research / Journal of the AIS）
- **表格格式**：三线表（LaTeX/HTML/Word 来源表格直接插入）
- **文献列表**：引言文献综述部分附上检索到的真实文献（含 DOI）

## 论文结构

```
1. 引言（Introduction）
   1.1 研究背景与问题提出
   1.2 文献综述（基于 Tavily 检索）
   1.3 研究目的与贡献

2. 理论基础（Theoretical Foundations）
   2.1 主要理论概述
   2.2 理论机制与分析框架

3. 研究假设（Hypotheses Development）
   3.1 假设推导（基于理论和研究问题）
   3.2 研究模型/概念框架

4. 研究方法（Methodology）
   4.1 数据与样本
   4.2 变量测量
   4.3 实证模型
   4.4 稳健性检验策略

5. 实证结果与分析（Data Analysis and Results）
   5.1 描述性统计
   5.2 主效应回归结果（引用 stargazer-exporter 输出表格）
   5.3 稳健性检验结果
   5.4 异质性分析（如有）

6. 讨论（Discussion）
   6.1 理论贡献（Theoretical Contributions）
   6.2 实践贡献（Practical Contributions）
   6.3 研究局限与未来研究方向（Limitations and Future Research）
```

## 各章节写作规范

### 引言（Introduction）

**1.1 研究背景与问题提出**（约 300-400 字）
- 从现实背景切入（政策/行业/技术变革）
- 指出这一背景下值得研究的核心问题
- 明确研究问题是什么

**1.2 文献综述**（约 600-800 字）
- 使用 `literature_fetcher.py` 基于"研究问题 + 数据变量"检索 IS 领域近 5 年核心期刊文献
- 检索策略：以研究问题和核心变量为关键词，检索 MIS Quarterly、ISR、JAIS、JMIS 等 IS 期刊
- 识别已有研究的主要发现、争议与空白（Research Gap）
- 附上检索到的文献列表（格式：作者, 年份, 期刊, 标题）

**1.3 研究目的与贡献**（约 300-400 字）
- 明确本研究的目的
- 逐条列出理论贡献（填补哪些空白）、方法贡献（如有）、实践贡献（如有）

### 理论基础（Theoretical Foundations）

**2.1 主要理论概述**（约 400-500 字）
- 介绍所用理论的核心主张、主要学者和发展脉络
- 结合用户数据/研究问题说明为何选用该理论

**2.2 理论机制与分析框架**（约 400-500 字）
- 阐明理论如何解释研究问题（机制分析）
- 绘制或描述概念框架（理论 → 假设 → 变量关系）

### 研究假设（Hypotheses Development）

**3.1 假设推导**（约 600-800 字）
- 若用户已提供假设：直接整理列出，并说明其理论依据
- 若用户未提供假设：根据研究问题 + 理论机制 + 数据变量，从理论推导至可检验的假设
- 每个假设 H1、H2…… 需包含：假设内容 + 理论依据 + 对应变量

**3.2 研究模型**（约 200-300 字）
- 描述概念模型或计量模型设定
- 说明因变量、自变量、控制变量

### 研究方法（Methodology）

**4.1 数据与样本**（约 300-400 字）
- 数据来源（如 CSMAR、Wind、企业年报等）
- 样本选择标准、时间跨度、企业数量
- 数据预处理说明（来自 data-cleaning 技能）

**4.2 变量测量**（约 400-500 字）
- 因变量：测量方式、数据来源
- 自变量：测量方式、数据来源
- 控制变量：测量方式、选择依据
- 如有中介/调节变量，说明测量方式

**4.3 实证模型**（约 300-400 字）
- 根据使用的技能说明模型：
  - `panel-regression`：双向固定效应模型，说明聚类方式
  - `iv-estimator`：两阶段最小二乘法（2SLS），说明工具变量选择依据
  - `staggered-did`：多时点 DID，说明处理组定义和控制组选择
  - `difference-in-discontinuities`：断点回归，说明驱动变量和阈值
  - 其他方法同理
- 说明为何选用该模型

**4.4 稳健性与内生性处理**（约 300-400 字）
- 列出将进行的稳健性检验策略（如替换变量、子样本、Bootstrap 等）
- 如使用了工具变量，说明工具变量的有效性（弱工具变量检验、Hansen J 检验等）
- 如使用了 DID，说明平行趋势假设的检验方式

### 实证结果与分析（Data Analysis and Results）

**5.1 描述性统计**（约 300-400 字）
- 引用 stargazer-exporter 输出的描述性统计表格
- 说明样本的基本特征（行业分布、时间分布等）

**5.2 主效应回归结果**（约 500-700 字）
- 引用 stargazer-exporter 输出的主效应表格
- 逐行解读系数的方向、显著性和经济含义
- 对应各假设 H1、H2…… 说明检验结果（支持/不支持）
- 结合诊断报告（VIF、F 统计量、R²）说明模型拟合质量

**5.3 稳健性检验**（约 400-500 字）
- 引用稳健性检验表格
- 逐一说明各稳健性检验结果是否与主效应一致

**5.4 异质性与机制分析**（如有，约 300-500 字）
- 分组回归结果（企业规模、所有制、行业等）
- 中介效应或调节效应检验结果（如有）

### 讨论（Discussion）

**6.1 理论贡献**（约 400-600 字）
- 本研究对理论的核心拓展或修正（基于假设检验结果）
- 与既有文献对话：哪些发现支持/挑战/拓展了已有理论
- 明确列出 2-3 条理论贡献

**6.2 实践贡献**（约 400-600 字）
- 基于研究发现，对企业管理者、政策制定者、行业从业者的实践启示
- 结合中国情境下的特殊制度背景（如有）

**6.3 研究局限与未来研究方向**（约 300-400 字）
- 坦诚说明数据、方法和样本的局限性
- 基于局限性提出 2-3 个有价值的未来研究方向

## scripts 用法

### outline_generator.py

接收用户素材，生成论文大纲（各章节标题和内容摘要）：

```bash
python skills/paper-writer/scripts/outline_generator.py \
  --research_question "研究数字化转型对企业绩效的影响" \
  --data_description "A股上市公司2010-2023年面板数据，包含ROA、数字化转型指标" \
  --theory "dynamic_capabilities" \
  --methods "panel-regression" \
  --output "outline.md"
```

### literature_fetcher.py

基于研究问题和关键词，检索 IS 领域文献并生成文献综述草稿：

```bash
python skills/paper-writer/scripts/literature_fetcher.py \
  --query "数字化转型 企业绩效 动态能力" \
  --topic "digital transformation firm performance dynamic capabilities" \
  --top_k 15 \
  --output "literature_review.md"
```

### paper_writer.py

整合所有素材，生成完整论文：

```bash
python skills/paper-writer/scripts/paper_writer.py \
  --research_question "研究数字化转型对企业绩效的影响" \
  --data_description "A股上市公司2010-2023年面板数据" \
  --variables "roa,digital_transformation,firm_size,leverage,age" \
  --theory "dynamic_capabilities" \
  --hypotheses "H1:数字化转型对企业绩效有显著正向影响;H2:组织冗余正向调节上述关系" \
  --method "panel-regression" \
  --pickle_results "./output/panel_results.pkl" \
  --diagnostics "./output/diagnostics.md" \
  --literature "./output/literature_review.md" \
  --language "cn" \
  --output "paper.md"
```

## 与其他技能的联动关系

| 上游技能 | 输出内容 | 本技能接收方式 |
|---------|---------|--------------|
| `is-theory-matcher` | 推荐理论名称及理由 | 通过用户转述或直接传递 |
| `is-econometrics` | 主控协调 | 本技能作为末端技能，接收汇总结果 |
| `panel-regression` | `.pkl` 回归结果 | 通过 `--pickle_results` 参数传入 |
| `iv-estimator` | `.pkl` 回归结果 + 诊断报告 | 通过 `--pickle_results` + `--diagnostics` 传入 |
| `staggered-did` | `.pkl` DID 结果 + 事件研究图 | 通过 `--pickle_results` + `--plot` 传入 |
| `stargazer-exporter` | LaTeX/HTML/Word 表格 | 直接插入论文对应位置 |
| `regression-diagnostics-report` | `.md` 诊断报告 | 通过 `--diagnostics` 参数传入 |
| `data-cleaning` | 清洗后数据集 | 通过数据集描述传给论文方法章节 |

## 限制与边界

1. **本技能生成论文草稿**，最终投稿前需研究者自行审阅和润色
2. **文献检索依赖 Tavily API**，检索结果为近 5 年内可检索到的文献，可能遗漏重要历史文献
3. **假设推导依赖 is-theory-matcher 的理论推荐结果**，若理论匹配质量不高，假设推导可能需调整
4. **实证结果的解读需结合具体情境**，技能基于统计显著性进行判断，研究者需确认经济含义合理性
5. **表格直接复用 stargazer-exporter 输出**，确保上游技能已正确配置输出路径
6. **中文论文默认遵循中文学术规范**，英文论文默认遵循 APA 格式

## 学术引用

若在学术研究中使用本技能生成论文草稿，建议引用：

> 万院士 (2026). Paper Writer: IS 实证论文写作技能. GitHub Repository.