#!/usr/bin/env python3
"""
paper_writer.py
整合所有素材（研究问题、数据描述、实证结果pickle、理论、假设），
生成完整的 IS 学术论文（Markdown 格式）。
"""

import argparse
import pickle
import sys
import os
from pathlib import Path
from datetime import datetime

# 尝试导入 pandas 和其他依赖
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# =============================================================================
# 理论数据库（与 is-theory-matcher 共享）
# =============================================================================
THEORY_DB = {
    "dynamic_capabilities": {
        "name_cn": "动态能力理论",
        "name_en": "Dynamic Capabilities Theory",
        "scholars": "Teece, D.J. (2007); Teece, Pisano & Shuen (1997)",
        "core_claims": [
            "企业的持久竞争优势来自于感知环境变化、抓住机会、通过转换重构来更新组织的能力",
            "动态能力包括感知能力（sensing）、抓住能力（seizing）和转换能力（transforming）",
            "动态能力是企业应对快速变化环境的关键",
        ],
        "hypothesis_templates": [
            "动态能力强的企业，其{自变量}对{因变量}的正向影响更为显著",
            "环境动荡程度正向调节{自变量}与{因变量}的关系",
        ],
        "key_papers": "Teece, D.J. (2007). Explicating Dynamic Capabilities. Strategic Management Journal.",
    },
    "rbv": {
        "name_cn": "资源基础观",
        "name_en": "Resource-Based View",
        "scholars": "Barney (1991); Wernerfelt (1984); Peteraf (1993)",
        "core_claims": [
            "企业竞争优势来源于其异质性的、稀缺的、不可模仿的、不可替代的（VRIN）资源",
            "IT资源本身不直接创造价值，需要通过与组织资源的整合来实现价值创造",
        ],
        "hypothesis_templates": [
            "具有异质性IT资源的企业，其{自变量}对{因变量}的影响更为显著",
        ],
        "key_papers": "Barney, J. (1991). Firm Resources and Sustained Competitive Advantage. Journal of Management.",
    },
    "institutional": {
        "name_cn": "制度理论",
        "name_en": "Institutional Theory",
        "scholars": "DiMaggio & Powell (1983); Meyer & Rowan (1977); Scott (2001)",
        "core_claims": [
            "组织行为受制度环境的塑造，包括强制压力、模仿压力和规范压力",
            "合法性机制促使组织遵循制度环境中的规则和惯例",
        ],
        "hypothesis_templates": [
            "制度压力越强，{自变量}对{因变量}的影响越显著",
            "政策监管对企业的{因变量}有显著正向影响",
        ],
        "key_papers": "DiMaggio, P.J. & Powell, W.W. (1983). The Iron Cage Revisited. American Sociological Review.",
    },
    "tam": {
        "name_cn": "技术接受模型",
        "name_en": "Technology Acceptance Model",
        "scholars": "Davis (1989); Venkatesh & Davis (2000)",
        "core_claims": [
            "用户对新技术的接受程度取决于感知有用性和感知易用性",
            "外部变量通过感知有用性和感知易用性间接影响使用行为",
        ],
        "hypothesis_templates": [
            "感知有用性正向影响用户对{技术/系统}的采纳意愿",
        ],
        "key_papers": "Davis, F.D. (1989). Perceived Usefulness, Perceived Ease of Use, and User Acceptance of IT. MIS Quarterly.",
    },
    "punctuated_equilibrium": {
        "name_cn": "间断均衡理论",
        "name_en": "Punctuated Equilibrium Theory",
        "scholars": "Tichy & Uhlenbruck (1979); Gersick (1991)",
        "core_claims": [
            "组织发展遵循稳定-断裂-重组-新的稳定的周期性路径",
            "外部冲击（政策、技术）会触发组织结构性断点",
            "组织在长期稳定后会因积累的矛盾而发生突变性变革",
        ],
        "hypothesis_templates": [
            "外部冲击（政策/技术）对{因变量}存在显著的结构性断点效应",
            "{自变量}对{因变量}的长期效应与短期效应存在显著差异",
        ],
        "key_papers": "Tichy, N.M. & Uhlenbruck, K. (1979). Punctuated Equilibrium Theory. Academy of Management Review.",
    },
    "network_effects": {
        "name_cn": "网络效应理论",
        "name_en": "Network Effects Theory",
        "scholars": "Katz & Shapiro (1985); Shapiro & Varian (1999); Eisenmann, Parker & Van Alstyne (2006)",
        "core_claims": [
            "平台价值随用户规模呈非线性增长（梅特卡夫定律）",
            "直接网络效应：同边用户之间的价值影响",
            "间接网络效应：跨边用户之间的价值影响（双边市场）",
        ],
        "hypothesis_templates": [
            "用户规模的平方项与平台价值呈显著正相关（梅特卡夫效应）",
            "卖家规模对买家采纳率有显著正向影响（跨边网络效应）",
        ],
        "key_papers": "Katz, M.L. & Shapiro, C. (1985). Network Externalities, Competition, and Compatibility. American Economic Review.",
    },
}


# =============================================================================
# 实证结果读取
# =============================================================================
def load_pickle_results(pickle_path: str) -> dict:
    """读取 pickle 格式的实证结果。"""
    if not PANDAS_AVAILABLE:
        return {"error": "pandas not installed, cannot read pickle files"}
    if not os.path.exists(pickle_path):
        return {"error": f"File not found: {pickle_path}"}
    try:
        with open(pickle_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# 论文各章节生成函数
# =============================================================================
def build_introduction(research_question: str, data_description: str, theory: str, methods: str,
                       literature_path: str = "") -> str:
    """生成引言章节。"""
    theory_info = THEORY_DB.get(theory, {})
    theory_name = theory_info.get("name_cn", theory)

    literature_section = ""
    if literature_path and os.path.exists(literature_path):
        with open(literature_path, "r", encoding="utf-8") as f:
            lit_content = f.read()
        # 提取文献综述部分（第二个标题之后的内容）
        if "### 1.2 文献综述" in lit_content:
            lit_start = lit_content.find("### 1.2 文献综述")
            lit_end = lit_content.find("\n---\n", lit_start)
            if lit_end == -1:
                lit_end = len(lit_content)
            literature_section = lit_content[lit_start:lit_end]
        else:
            literature_section = lit_content

    if not literature_section:
        literature_section = f"""### 1.2 文献综述

围绕"{research_question}"这一研究主题，现有文献主要从以下角度展开：

**主要研究发现：**
- 近年来，{theory_name}在信息系统（IS）领域的应用日益受到关注（请用户补充具体文献）
- [请用户补充相关文献综述内容，或运行 literature_fetcher.py 自动检索]

**研究空白：**
- 现有研究较少在[具体情境]下对[理论名称]进行实证检验
- [请用户补充研究空白描述]

**本研究的定位：**
本研究运用{theory}理论和{methods}方法，对{research_question}进行系统检验。
"""

    intro = f"""# 1. 引言

## 1.1 研究背景与问题提出

随着信息技术的快速发展和数字经济的深度渗透，企业面临日益复杂的外部环境。{research_question}已成为管理信息系统领域的重要研究议题。在这一背景下，{research_question}不仅关乎企业的战略选择，也涉及资源配置、组织变革等多层面的理论问题。

本研究聚焦于{data_description}中的核心关系，即：[请用户明确描述自变量和因变量之间的关系]。

## 1.2 文献综述

{literature_section}

## 1.3 研究目的与贡献

本研究旨在运用{theory}理论，通过{theory}方法，对{research_question}进行系统的实证检验。

**理论贡献：**
- 贡献一：拓展{theory}理论对[具体现象]的解释力，揭示[机制]在理论框架中的作用
- 贡献二：将{theory}理论置于[中国制度背景/新情境]下进行检验，拓展理论的外部效度
- 贡献三：提供[面板数据/新的工具变量/多时点DID]证据，丰富{theory}理论的实证研究

**实践贡献：**
- 为企业管理者在[具体情境]下的决策提供理论依据
- 为政策制定者提供[政策建议]的实证支持

**本文结构：** 第二节介绍理论基础；第三节推导研究假设；第四节说明研究方法；第五节报告实证结果；第六节进行讨论。

"""
    return intro


def build_theoretical_foundations(theory: str, research_question: str) -> str:
    """生成理论基础章节。"""
    theory_info = THEORY_DB.get(theory, {})
    if not theory_info:
        return f"""# 2. 理论基础

## 2.1 理论概述

（理论ID: {theory}）

## 2.2 理论机制与分析框架

（请用户补充理论机制分析）

"""

    theory_name_cn = theory_info["name_cn"]
    theory_name_en = theory_info["name_en"]
    scholars = theory_info["scholars"]
    core_claims = theory_info["core_claims"]
    key_papers = theory_info["key_papers"]

    claims_text = "\n".join([f"- {claim}" for claim in core_claims])

    tf = f"""# 2. 理论基础

## 2.1 {theory_name_cn}概述

**英文名称：** {theory_name_en}

**主要学者：** {scholars}

**核心主张：**
{claims_text}

**关键文献：**
{key_papers}

## 2.2 理论机制与分析框架

{theory}理论的核心机制在于[请根据研究问题和理论补充机制描述]。

具体到本研究，{research_question}这一现象可以从{theory}理论的角度得到解释：[请用户补充机制分析]。

"""
    return tf


def build_hypotheses(hypotheses: str, theory: str, research_question: str,
                     variables: str) -> str:
    """生成研究假设章节。"""
    theory_info = THEORY_DB.get(theory, {})
    theory_name = theory_info.get("name_cn", theory)

    var_list = variables.split(",") if variables else []

    if hypotheses:
        # 用户已提供假设，直接整理
        h_text = "## 3. 研究假设\n\n### 3.1 假设推导\n\n"
        for i, h in enumerate(hypotheses.split(";"), 1):
            h = h.strip()
            if h:
                h_text += f"[H{i}] {h}\n\n"
        h_text += "### 3.2 研究模型\n\n"
        h_text += f"基于 {theory_name}，本研究建立如下概念模型：\n"
        h_text += f"  自变量（{var_list[1] if len(var_list) > 1 else '待定'}）\n"
        h_text += f"    ↓  ({theory_name})\n"
        h_text += f"  因变量（{var_list[0] if var_list else '待定'}）\n"
        if len(var_list) > 2:
            h_text += f"  控制变量：{', '.join(var_list[2:])}\n"
        return h_text
    else:
        # 技能代为推导
        h_text = f"""## 3. 研究假设

### 3.1 假设推导

基于 {theory_name} 和研究问题 "{research_question}"，本研究提出以下假设：

**H1（主效应）：**
[基于{theory}理论的理论机制，推导{var_list[1] if len(var_list) > 1 else '自变量'}对{var_list[0] if var_list else '因变量'}的预期影响]

理论依据：{theory_name}认为[请补充理论依据]。

**H2（调节效应，可选）：**
[基于理论框架，分析{调节变量}在H1关系中的调节作用]

理论依据：[请补充调节效应的理论逻辑]。

### 3.2 研究模型

本研究以{var_list[0] if var_list else '因变量'}为因变量，以{var_list[1] if len(var_list) > 1 else '自变量'}为核心自变量，
同时控制{[var_list[2:] if len(var_list) > 2 else '企业规模、资产负债率、年龄等']}，
构建双向固定效应（TWFE）面板回归模型。
"""
        return h_text


def build_methodology(data_description: str, variables: str, method: str,
                       theory: str) -> str:
    """生成研究方法章节。"""
    method_map = {
        "panel-regression": ("双向固定效应（TWFE）面板回归", "双向固定效应模型（Two-Way Fixed Effects, TWFE）"),
        "iv-estimator": ("两阶段最小二乘法（2SLS）", "两阶段最小二乘法（Two-Stage Least Squares, 2SLS）"),
        "staggered-did": ("多时点双重差分（DID）", "多时点双重差分（Staggered Difference-in-Differences, Staggered DID）"),
        "difference-in-discontinuities": ("断点回归（RDD）", "断点回归设计（Regression Discontinuity Design, RDD）"),
        "propensity-score-matching": ("倾向得分匹配（PSM）", "倾向得分匹配（Propensity Score Matching, PSM）"),
        "survival-analysis": ("Cox 比例风险模型", "Cox 比例风险模型（Cox Proportional Hazards Model）"),
    }

    method_name, model_name = method_map.get(method, (method, method))

    var_list = variables.split(",") if variables else []

    methodology = f"""# 4. 研究方法

## 4.1 数据与样本

本研究的样本为{data_description}。

**数据来源：** [请用户补充具体数据来源，如 CSMAR、Wind、企业年报等]

**样本选择标准：** [请用户补充样本选择标准]

**时间跨度：** [请用户补充具体时间范围]

**样本量：** [原始样本量] → [剔除缺失值/异常值后] → [最终样本量]

## 4.2 变量测量

**因变量（Y）：** {var_list[0] if var_list else '[待用户提供]'}

**自变量（X）：** {var_list[1] if len(var_list) > 1 else '[待用户提供]'}

**控制变量：** {', '.join(var_list[2:]) if len(var_list) > 2 else '[企业规模(ln总资产)、资产负债率、企业年龄、行业竞争度等标准控制变量]'}

**中介/调节变量：** [如适用，请用户补充]

## 4.3 实证模型

本研究采用{model_name}，具体设定如下：

**模型设定理由：** {method_name}能够有效处理[面板数据的非观测异质性/内生性问题/因果识别问题]，
因此适用于本研究的研究问题和数据结构。

**固定效应设置：** 采用个体固定效应和时间固定效应（双向固定效应），以控制不随时间变化的个体异质性和共同时间趋势。

**标准误聚类：** 在企业层面聚类稳健标准误，以处理企业内部的序列相关性。

**模型基本形式：**
```
Y_it = α + β·X_it + γ·Controls_it + μ_i + λ_t + ε_it
```
其中：μ_i 为企业固定效应，λ_t 为年份固定效应，ε_it 为误差项。

## 4.4 内生性与稳健性处理

**内生性处理策略：**
- [若使用 IV] 工具变量：[工具变量名称]，选择依据：[理由]
- [若使用 DID] 处理组定义：[处理组定义]，控制组定义：[控制组定义]
- [其他方法]：[处理内生性的具体方式]

**稳健性检验策略：**
- [ ] 替换因变量/自变量
- [ ] 子样本检验（按行业/规模/地区）
- [ ] 缩尾处理变化（1%/99% → 5%/95%）
- [ ] Bootstrap 标准误估计
- [ ] 安慰剂检验（随机处理组/随机时间点）
- [ ] 滞后自变量（X_t-1）

"""
    return methodology


def build_results(pickle_results: str, diagnostics: str, method: str, theory: str,
                  variables: str, hypotheses: str) -> str:
    """生成实证结果章节。"""
    var_list = variables.split(",") if variables else []

    results = f"""# 5. 实证结果与分析

## 5.1 描述性统计

**表1：描述性统计**

| 变量 | 均值 | 标准差 | 最小值 | 最大值 |
|------|------|--------|--------|--------|
"""
    # 如果有pickle数据，尝试从中提取描述性统计
    if pickle_results and os.path.exists(pickle_results):
        results += "| （待从实证结果pickle中提取） | | | | |\n"
    else:
        results += f"| {var_list[0] if var_list else '因变量'} | — | — | — | — |\n"
        results += f"| {var_list[1] if len(var_list) > 1 else '自变量'} | — | — | — | — |\n"
        for v in var_list[2:]:
            results += f"| {v} | — | — | — | — |\n"

    results += """
注：*** p<0.01, ** p<0.05, * p<0.1；连续变量在1%和99%分位进行缩尾处理。

**样本基本特征：**
[请用户根据描述性统计表补充样本特征说明]
"""

    results += f"""

## 5.2 主效应回归结果

**表2：主效应回归结果**

| 变量 | M1（仅控制变量） | M2（+自变量） | M3（+固定效应） |
|------|----------------|--------------|----------------|
"""
    results += f"| {var_list[1] if len(var_list) > 1 else '自变量'} | — | — | — |\n"
    results += f"| R² within | — | — | — |\n"
    results += f"| N | — | — | — |\n"
    results += f"| 固定效应 | 否 | 否 | 是 |\n"

    results += """
注：*** p<0.01, ** p<0.05, * p<0.1；括号内为企业层面聚类稳健标准误。

**结果解读：**
- [请用户根据回归结果解读系数方向、显著性和经济含义]
- H1 检验结果：[支持/不支持]——[具体解读]

"""

    # 假设检验结果
    if hypotheses:
        results += "**假设检验汇总：**\n\n"
        for i, h in enumerate(hypotheses.split(";"), 1):
            h = h.strip()
            if h:
                results += f"- [H{i}] {h} → [检验结果：支持/不支持]\n"
        results += "\n"

    results += """## 5.3 稳健性检验

**表3：稳健性检验结果**

| 检验类型 | 自变量系数 | 标准误 | 显著性 |
|---------|-----------|--------|--------|
| 替换因变量 | — | — | — |
| 子样本检验 | — | — | — |
| 缩尾处理调整 | — | — | — |
| 工具变量法 | — | — | — |

**稳健性检验结果：** [请用户根据稳健性检验结果补充说明]

## 5.4 异质性与机制分析（如有）

[如研究包含异质性分析或中介效应检验，请用户补充]

"""

    return results


def build_discussion(theory: str, research_question: str, hypotheses: str,
                     variables: str) -> str:
    """生成讨论章节。"""
    theory_info = THEORY_DB.get(theory, {})
    theory_name = theory_info.get("name_cn", theory)

    var_list = variables.split(",") if variables else []

    discussion = f"""# 6. 讨论

## 6.1 理论贡献

本研究对{theory}理论做出了以下贡献：

**贡献一：拓展{theory}理论对{research_question}的解释力。**
本研究发现[具体发现]，这一发现与{theory}理论的预期[一致/不一致]，表明[理论机制]是解释[现象]的重要因素。
以往研究主要关注[已有研究主题]，但未充分考虑[本研究独特视角]，本研究填补了这一空白。

**贡献二：揭示了[机制/调节因素]在{theory}理论中的重要作用。**
[基于稳健性检验或异质性分析结果，补充具体贡献]

**贡献三：将{theory}理论置于中国制度背景下进行检验。**
中国制度环境具有独特性（政府-市场关系、产业政策、数字化转型战略），
本研究的发现拓展了{theory}理论的外部效度，为该理论在新兴市场情境下的适用性提供了新的证据。

## 6.2 实践贡献

**对企业管理者的启示：**
- 本研究表明[具体发现]，因此企业管理者在[具体情境]中应当[具体行动建议]。
- [基于{theory}理论，给出针对企业战略决策的具体建议]

**对政策制定者的启示：**
- 本研究发现[政策变量]对[企业行为/绩效]有显著影响，提示政策制定者在设计相关政策时应考虑[因素]。

**中国情境的特殊性：**
在中国独特的制度环境下，[具体制度因素]对[研究关系]具有调节作用，
这提示企业和政策制定者应充分重视中国制度背景的特殊性。

## 6.3 研究局限与未来研究方向

**研究局限：**
- **数据局限：** 本研究样本为[具体样本]，可能存在[选择偏差/外推局限]问题。
- **方法局限：** 尽管本研究采用{theory}方法，但仍可能存在[内生性问题/测量误差]。
- **变量局限：** [核心变量]的测量基于[数据来源]，可能未能完全捕捉[理论构念]。

**未来研究方向：**
- **方向一：** 在[不同样本/不同情境]下检验{theory}理论的适用性
- **方向二：** 引入[中介变量/调节变量]，进一步揭示{theory}理论的作用机制
- **方向三：** 采用[实验方法/案例研究]等补充研究设计，提供更丰富的因果证据

"""
    return discussion


def generate_full_paper(research_question: str, data_description: str,
                       variables: str, theory: str, hypotheses: str,
                       method: str, pickle_results: str = "",
                       diagnostics: str = "", literature: str = "",
                       language: str = "cn") -> str:
    """生成完整论文。"""

    date_str = datetime.now().strftime("%Y-%m-%d")

    paper = f"""---
title: （论文标题——待用户确定）
date: {date_str}
author: （作者信息——待用户填写）
---

# （论文标题——待用户确定）

**摘要：** （待用户撰写。摘要应包含：研究问题、理论背景、研究方法、主要发现、理论贡献，一段式，300-500字）

**关键词：** [关键词1]；[关键词2]；[关键词3]（3-5个）

---

"""
    paper += build_introduction(research_question, data_description, theory, method, literature)
    paper += build_theoretical_foundations(theory, research_question)
    paper += build_hypotheses(hypotheses, theory, research_question, variables)
    paper += build_methodology(data_description, variables, method, theory)
    paper += build_results(pickle_results, diagnostics, method, variables, theory, hypotheses)
    paper += build_discussion(theory, research_question, hypotheses, variables)

    paper += """
---

## 参考文献

（由 `literature_fetcher.py` 生成的文献列表将插入此处）

"""

    return paper


# =============================================================================
# 全局占位（用于在子函数中引用）
# =============================================================================
# =============================================================================
# 主函数
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="IS 实证论文写作")
    parser.add_argument("--research_question", required=True, help="用户的研究问题描述")
    parser.add_argument("--data_description", required=True, help="数据集描述")
    parser.add_argument("--variables", default="", help="变量列表（逗号分隔），格式：因变量,自变量,控制变量1,控制变量2,...")
    parser.add_argument("--theory", required=True, help="理论ID")
    parser.add_argument("--hypotheses", default="", help="用户指定的假设（分号分隔）")
    parser.add_argument("--method", required=True, help="实证方法（panel-regression / iv-estimator / staggered-did 等）")
    parser.add_argument("--pickle_results", default="", help="实证结果 pickle 文件路径")
    parser.add_argument("--diagnostics", default="", help="诊断报告 md 文件路径")
    parser.add_argument("--literature", default="", help="文献综述 md 文件路径（由 literature_fetcher.py 生成）")
    parser.add_argument("--language", default="cn", choices=["cn", "en"], help="论文语言")
    parser.add_argument("--output", default="paper.md", help="输出文件路径")
    args = parser.parse_args()

    # 设置全局变量
    data_description = args.data_description

    paper = generate_full_paper(
        research_question=args.research_question,
        data_description=args.data_description,
        variables=args.variables,
        theory=args.theory,
        hypotheses=args.hypotheses,
        method=args.method,
        pickle_results=args.pickle_results,
        diagnostics=args.diagnostics,
        literature=args.literature,
        language=args.language,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(paper)

    print(f"论文已生成：{args.output}")
    print(f"理论框架：{args.theory}")
    print(f"实证方法：{args.method}")
    print(f"变量数：{len(args.variables.split(',')) if args.variables else 0} 个")
    print("\n提示：生成内容包含占位符 [请用户补充]，请在使用前填充具体内容。")


if __name__ == "__main__":
    sys.exit(main())