---
name: paper-writer
description: 面向已完成实证分析的 IS 研究者。激活条件：用户拥有数据、研究问题、理论框架和实证结果，希望生成符合期刊规范的完整学术论文。支持中文/英文，支持多模板（双栏 IEEEtran / 单栏等），采用分章节生成-编译-检查的迭代工作流。触发词："写论文"、"生成论文"、"学术论文"、"发表级论文"、"帮我写完整的实证论文"、"生成 LaTeX 论文"。
metadata: {
  "openclaw": {
    "emoji": "📝",
    "requires": {
      "bins": ["python", "xelatex"],
      "os": ["linux", "darwin", "win32"],
      "skills": ["is-theory-matcher", "is-econometrics"]
    }
  }
}
---

# Paper Writer: IS 实证论文写作技能

## 核心工作流：分章节生成 → 编译检查 → 整合输出

```
用户提供素材（研究问题 + 数据 + 理论 + 实证结果）
  │
  ├─ is-theory-matcher（可选）→ 推荐理论框架
  ├─ is-econometrics / panel-regression / iv-estimator / ...
  │    → 实证分析，输出回归结果 pickle / JSON
  └─ stargazer-exporter → 回归表格
        │
        ▼
paper-writer（本技能）
  │
  ├─ 步骤 1：生成 Introduction（写入 section_introduction.tex）
  ├─ 步骤 2：生成 Theoretical Foundations（写入 section_theory.tex）
  ├─ 步骤 3：生成 Hypotheses Development（写入 section_hypotheses.tex）
  ├─ 步骤 4：生成 Methodology（写入 section_methodology.tex）
  ├─ 步骤 5：生成 Empirical Results（写入 section_results.tex）
  ├─ 步骤 6：生成 Discussion（写入 section_discussion.tex）
  │    （每步生成后立即编译检查，发现问题当场修复）
  │
  ▼
整合所有章节 + 编译 → 最终 PDF
```

**关键原则：每生成完一节，立即写入 LaTeX 文件并编译检查，不要一次性生成全文再编译。**

---

## 技能架构

```
paper-writer/
├── SKILL.md（本文档）
├── scripts/
│   ├── outline_generator.py          # 大纲生成（可选快速预览）
│   ├── literature_fetcher.py         # 文献检索（调用 Tavily）
│   ├── latex_writer.py              # LaTeX 分章节生成（核心脚本）
│   └── latex_compiler.py            # LaTeX 编译检查工具
├── references/
│   ├── paper-structure-template.md  # 各章节写作规范与字数参考
│   └── is-journal-standards.md      # IS 期刊格式规范
└── templates/
    ├── ieee_dual_column/            # 模板 1：IEEEtran 双栏（默认）
    │   ├── main.tex                  # 主文档（含摘要、关键词、所有 \input{}）
    │   ├── refs.bib                  # BibTeX 参考文献文件
    │   └── sections/                 # 各章节 .tex 文件（由 latex_writer.py 生成）
    └── single_column/                # 模板 2：单栏（预留扩展）
        └── main.tex
```

---

## 输入素材

| 素材 | 必需 | 来源 | 说明 |
|------|------|------|------|
| 研究问题 | ✅ | 用户描述 | 描述研究现象/核心问题 |
| 数据描述 | ✅ | 用户描述 | 样本量、时间跨度、行业、数据来源 |
| 变量列表 | ✅ | 用户描述 | 因变量、自变量、控制变量 |
| 理论框架 | ✅ | 用户指定或 is-theory-matcher | 支持多理论（逗号分隔） |
| 实证结果 | 部分必需 | econometrics 技能输出 | JSON/pkl，含回归系数、SE、N、R² |
| 稳健性检验结果 | 部分必需 | econometrics 技能输出 | 同上 |
| 异质性分析结果 | 可选 | econometrics 技能输出 | 分组回归结果 |
| 假设 | 可选 | 用户指定或自动推导 | 含理论依据和变量对应 |
| 文献检索结果 | 可选 | literature_fetcher.py | 含引用 key |
| 论文语言 | 可选 | 用户指定 | cn（默认）/ en |
| 期刊模板 | 可选 | 用户指定 | ieee_dual_column（默认）/ single_column / future |

---

## 输出规格

- **最终格式**：PDF（通过 XeLaTeX 编译）
- **工作目录**：`{user_workspace}/paper_output/`
- **文件结构**：
  ```
  paper_output/
  ├── main.tex              # 主文档（template）
  ├── refs.bib              # BibTeX 文献
  ├── section_*.tex         # 各章节
  ├── table_*.tex           # 回归表格（如有）
  ├── fig*.png              # 图片（如有）
  └── paper.pdf             # 最终输出
  ```
- **语言**：默认中文；指定 `language=en` 时输出英文
- **模板**：IEEE Transactions on Education 风格（双栏）

---

## 论文结构（6 节标准结构）

```
1. Introduction                      引言
2. Theoretical Foundations           理论基础（理论深度阐述）
3. Hypotheses Development            假设推导（每个假设含理论依据）
4. Methodology                       研究方法
5. Empirical Results                实证结果
6. Discussion                       讨论（含 Conclusion 子节）
```

**Discussion 必须包含 Conclusion 子节（\subsection{Conclusion}），不是独立的 \section{Conclusion}。**

---

## 分章节写作流程（详细）

### 步骤 0：准备

1. 在 `{user_workspace}/paper_output/` 下创建工作目录
2. 确定：论文语言、模板类型、理论 key 列表、变量列表
3. 将模板 `templates/{template}/main.tex` 复制到工作目录
4. 更新 `main.tex` 中的标题、作者、摘要、关键词

### 步骤 1：Introduction

**目标**：生成引言，250-400 words

**必须包含**：
- 研究背景与研究问题的现实切入点
- 3-5 篇核心文献的 `\cite{}` 引用（用 `literature_fetcher.py` 检索）
- 明确的研究空白（Research Gap）描述
- 2-3 条理论贡献声明
- 本文结构说明

**LaTeX 写作规范**：
- 不要使用 `\section{Introduction}`（main.tex 已提供）
- 直接写段落内容，含 `\cite{}` 引用
- 使用 `\\cite{key1}\\cite{key2}` 格式引用多篇文献
- 末尾写 `本文结构如下：...`

**生成后**：写入 `section_introduction.tex` → 运行 `latex_compiler.py` 检查

### 步骤 2：Theoretical Foundations

**目标**：理论框架，400-600 words

**必须包含**：
- 每个理论的：名称（CN+EN）、主要学者、核心主张（3-5 条）
- 理论机制分析：该理论如何解释本研究问题
- 整合分析框架：多理论如何共同解释研究现象

**引用规范**：每个理论首次出现后加 `\cite{}`

**写作规范**：
- 不要将理论写成教科书概述，要紧扣本研究主题
- 每个理论单独一个小节（`\subsection{理论名称}`）

**生成后**：写入 `section_theory.tex` → 编译检查

### 步骤 3：Hypotheses Development

**目标**：假设推导，600-1000 words

**关键要求：每个假设必须包含三要素**
1. **假设内容**：清晰、可检验的假设陈述（H1、H2……）
2. **理论依据**：从理论核心主张和机制出发的完整推导，不是罗列
3. **对应变量**：假设中涉及的自变量、因变量、控制变量

**写作规范**：
- 每个假设一个小节（`\subsection{H1: ...}`）
- 假设推导的段落必须从理论出发，逻辑清晰，不允许直接给出假设而无推导过程
- 如果没有用户指定假设，根据理论 + 变量 + 研究问题自动推导

**假设数量**：通常 3-6 个主效应 + 调节/中介假设

**生成后**：写入 `section_hypotheses.tex` → 编译检查

### 步骤 4：Methodology

**目标**：方法章节，500-800 words

**必须包含**：
- 数据来源、样本选择标准、时间跨度、最终样本量
- 变量测量（因变量、自变量、控制变量，含数据来源）
- 实证模型设定（模型形式、为什么选该模型）
- 内生性/稳健性处理策略

**表格**：如有描述性统计，生成 `table_I.tex`

**生成后**：写入 `section_methodology.tex` → 编译检查

### 步骤 5：Empirical Results

**目标**：结果章节，600-1000 words

**必须包含**：
- 描述性统计表格（`table_I.tex`）及解读
- 主效应回归表格（`table_II.tex`）及逐行解读
- 假设检验结论（每个 H1、H2……的检验结果：支持/不支持）
- 稳健性检验结果（如有）
- 异质性分析结果（如有）

**表格规范**：
- 双栏表格用 `\begin{table*}` 跨栏
- 单栏表格用 `\begin{table}`
- 使用 `booktabs` 三线表格式
- 字号 `\footnotesize`，列宽用 `p{宽度}` 限制

**图片**：如有图片，用 `\includegraphics[width=0.48\textwidth]{}` 插入

**生成后**：写入 `section_results.tex` + `table_*.tex` → 编译检查

### 步骤 6：Discussion（含 Conclusion）

**目标**：讨论与总结，600-1000 words

**必须包含**：
- 主要发现概述
- **理论贡献**（2-3 条，表述为"对 XXX 理论的 XXX 方面做出贡献"）
- **实践贡献**（2-3 条，给出具体建议）
- **研究局限**（坦诚具体，不敷衍）
- **未来研究方向**（基于局限提出，有研究价值）
- **Conclusion 子节**（总结核心结论，1-2 段）

**写作规范**：
- Discussion 是独立 `\section{Discussion}`（main.tex 已提供）
- Conclusion 是其下的 `\subsection{Conclusion}`
- 不要创建独立的 `\section{Conclusion}`

### 步骤 7：整合与最终编译

所有章节检查无误后：
1. 运行 BibTeX 生成 `.bbl` 参考文献
2. XeLaTeX × 3 次编译，确保无错误
3. 检查 `\ref{}` 引用是否全部resolve
4. 确认无 undefined references、无 fatal errors

---

## 写作要求（不可忽略）

### 假设必须有理论推导
> 每个假设的推导段落必须从理论的核心主张出发，逻辑推演至可检验的假设。禁止直接罗列假设而无推导过程。

**示例结构**：
```
H1: GenAI 使用对技能保留有显著正向影响。

理论依据：检索练习理论认为[...]，而 GenAI 辅助学习会改变[...]，
基于此，本研究预期[...]。
```

### 参考文献必须在文中 `\cite{}` 引用
> BibTeX 只包含被 `\cite{}` 实际引用的条目。未在正文中引用的 ref.bib 条目不会出现在参考文献列表中。

**操作规范**：
- 在 literature_fetcher.py 检索后，将返回的 citation key 插入正文对应位置
- 在 Theoretical Foundations 每节理论后插入对应核心文献引用
- 在 Hypotheses Development 推导段落中插入理论引用

### 表格宽度不超过栏宽
> 双栏模板中，单栏表格宽度 ≤ `\columnwidth`（约 3.5in），双栏表格（`table*`）宽度 ≤ `\linewidth`（约 7in）。

**操作规范**：
- 列数较多时，使用 `\footnotesize` 字号
- 列宽用 `p{宽度}` 或 `tabulary` 固定
- 主效应表格推荐：8-9 列格式（变量列 + 多模型系数/SE），使用 `\multicol` 合并表头

### 图表宽度
> 图片宽度建议不超过 `0.48\textwidth`（单栏安全上限），表格内嵌图片同理。

---

## scripts 用法

### latex_writer.py（核心）

生成或更新某个章节的 .tex 文件：

```bash
python skills/paper-writer/scripts/latex_writer.py \
  --output_dir ./paper_output \
  --research_question "研究 GenAI 使用对大学生学业成绩和心理健康的影响" \
  --data_description "50,000名大学生样本，五个学科类别，三种制度政策环境" \
  --variables "GPA,Weekly_GenAI_Hours,Tool_Diversity,Pre_GPA,Trad_Study_Hours" \
  --theory_keys "is_success,institutional,cognitive_load" \
  --method panel-regression \
  --section introduction       # 或 all / theory / hypotheses / methodology / results / discussion
```

### latex_compiler.py

编译并检查 LaTeX 文件：

```bash
python skills/paper-writer/scripts/latex_compiler.py \
  --dir ./paper_output \
  --template ieee_dual_column
```

输出：PDF 文件 + 编译错误报告 + overfull/underfull 警告统计

### outline_generator.py（快速预览）

生成论文大纲（用于和用户确认结构后再开始写）：

```bash
python skills/paper-writer/scripts/outline_generator.py \
  --research_question "研究 GenAI 使用对大学生学业成绩的影响" \
  --data_description "50,000名大学生，5个学科" \
  --theory "is_success,institutional" \
  --method panel-regression \
  --output outline.md
```

### literature_fetcher.py

检索文献并生成引用 key：

```bash
python skills/paper-writer/scripts/literature_fetcher.py \
  --query "GenAI higher education academic performance skill retention mental health" \
  --topic "generative AI education learning outcomes" \
  --top_k 15 \
  --output literature.json
```

---

## 与其他技能的联动

| 上游技能 | 输出 | 本技能接收 |
|---------|------|----------|
| `is-theory-matcher` | 理论名称 + 理由 | `--theory_keys` 参数 |
| `is-econometrics` | 回归结果 JSON | `--regression_json` |
| `panel-regression` | 回归结果 JSON + 诊断报告 | `--regression_json` + `--diagnostics` |
| `iv-estimator` | IV 回归结果 | `--regression_json` |
| `staggered-did` | DID 结果 | `--regression_json` |
| `stargazer-exporter` | LaTeX 表格 | 插入 `table_*.tex` |
| `regression-diagnostics-report` | 诊断报告 | `--diagnostics` |
| `literature_fetcher` | 文献 JSON | `--literature_json` |

---

## 模板扩展指南

新增模板（如 single_column）的步骤：

1. 在 `templates/` 下创建 `single_column/` 目录
2. 编写 `main.tex`（替换双栏 preamble 为单栏格式，如 `\documentclass[11pt]{article}`）
3. 在 `main.tex` 中保留相同的 `\input{section_*.tex}` 指令
4. 在 SKILL.md 的 `--template` 参数说明中新增该模板

模板应遵循：
- `\input{section_*.tex}` 保持不变（章节内容格式与模板无关）
- 唯一差异：文档类、字体、栏宽、摘要格式
- `\bibliographystyle{IEEEtran}` 保持一致

---

## 限制与边界

1. **假设推导依赖理论库**：若用户理论不在内置 `THEORY_DB` 中，假设推导质量可能受限，请先调用 `is-theory-matcher` 获取推荐
2. **文献检索依赖 Tavily API**：结果受 API 可用性和检索质量影响，建议用户手动补充遗漏的重要文献
3. **表格需手动填充数据**：`latex_writer.py` 生成表格骨架，回归系数的具体数值需由用户或 econometrics 技能提供
4. **PDF 编译依赖 XeLaTeX**：确保系统已安装 TeX Live / MacTeX，且 `xelatex` 命令可用
5. **中文论文字体**：XeLaTeX 编译中文需系统安装中文字体（如 `ctex` 宏包或系统宋体/黑体）
6. **最终审稿**：本技能生成论文草稿，投稿前需研究者自行审阅、润色和格式调整

---

## 学术引用

> 万院士 (2026). Paper Writer: IS 实证论文写作技能 (v2.0). GitHub Repository.
