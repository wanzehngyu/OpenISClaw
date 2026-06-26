#!/usr/bin/env python3
"""
latex_writer.py
生成 LaTeX 论文的各个章节，自动插入引用占位符，
并将每个章节写入独立 .tex 文件供主文档 input。
支持分章节生成-编译-检查的迭代工作流。
"""

import argparse
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

# ─── 理论数据库 ───────────────────────────────────────────────────────────────
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
        "mechanism": "动态能力通过[感知-抓住-转换]机制影响企业行为和绩效",
        "key_refs": ["Teece2007", "Teece1997"],
    },
    "rbv": {
        "name_cn": "资源基础观",
        "name_en": "Resource-Based View",
        "scholars": "Barney (1991); Wernerfelt (1984); Peteraf (1993)",
        "core_claims": [
            "企业竞争优势来源于异质的、稀缺的、不可模仿的、不可替代的（VRIN）资源",
            "IT资源本身不直接创造价值，需通过与组织资源的整合来实现价值创造",
        ],
        "mechanism": "VRIN资源通过[资源异质性-不可模仿性]机制形成持续竞争优势",
        "key_refs": ["Barney1991", "Wernerfelt1984"],
    },
    "institutional": {
        "name_cn": "制度理论",
        "name_en": "Institutional Theory",
        "scholars": "DiMaggio & Powell (1983); Meyer & Rowan (1977); Scott (2001)",
        "core_claims": [
            "组织行为受制度环境的塑造，包括强制压力、模仿压力和规范压力",
            "合法性机制促使组织遵循制度环境中的规则和惯例",
        ],
        "mechanism": "制度压力通过[强制性-模仿性-规范性]同构机制影响组织行为",
        "key_refs": ["DiMaggio1983", "Meyer1977"],
    },
    "tam": {
        "name_cn": "技术接受模型",
        "name_en": "Technology Acceptance Model",
        "scholars": "Davis (1989); Venkatesh & Davis (2000)",
        "core_claims": [
            "用户对新技术的接受程度取决于感知有用性和感知易用性",
            "外部变量通过感知有用性和感知易用性间接影响使用行为",
        ],
        "mechanism": "感知有用性和感知易用性通过[态度-行为意愿-实际使用]路径影响技术采纳",
        "key_refs": ["Davis1989", "Venkatesh2000"],
    },
    "is_success": {
        "name_cn": "信息系统成功模型",
        "name_en": "D&M IS Success Model",
        "scholars": "DeLone & McLean (1992, 2003)",
        "core_claims": [
            "信息系统成功包含信息质量、系统质量、服务质量三个维度",
            "系统使用和用户满意度中介质量维度与净收益之间的关系",
        ],
        "mechanism": "IS质量通过[系统使用-用户满意度]中介路径产生净收益",
        "key_refs": ["Delone2003"],
    },
    "cognitive_load": {
        "name_cn": "认知负荷理论",
        "name_en": "Cognitive Load Theory",
        "scholars": "Sweller (1988, 2011); Mayer & Roxana (2019)",
        "core_claims": [
            "学习过程中的认知负荷包括内在负荷、外在负荷和相关负荷三类",
            "最优学习环境应最小化外在负荷，同时保持足够相关负荷来驱动图式建构",
        ],
        "mechanism": "认知负荷通过[内在负荷-外在负荷-相关负荷]交互影响学习效果",
        "key_refs": ["Sweller2011", "Mayer2019"],
    },
    "retrieval_practice": {
        "name_cn": "检索练习理论",
        "name_en": "Retrieval Practice Theory",
        "scholars": "Roediger & Karpicke (2006, 2008); Slamecka (1978)",
        "core_claims": [
            "从记忆中主动检索信息比被动重复更能巩固长期记忆",
            "检索练习的间隔和难度影响记忆巩固效果",
        ],
        "mechanism": "检索练习通过[努力提取-记忆巩固]机制提升长期保留率",
        "key_refs": ["Roediker2011", "Karpicke2008"],
    },
    "institutional_is": {
        "name_cn": "制度理论（IS情境）",
        "name_en": "Institutional Theory in IS",
        "scholars": "Ahuja et al. (2013); Dong et al. (2009)",
        "core_claims": [
            "技术扩散受制度环境的强制性、模仿性和规范性压力驱动",
            "组织对技术的合法性需求会影响其技术采纳决策",
        ],
        "mechanism": "制度压力通过[外部合法性-内部整合]张力影响技术采纳",
        "key_refs": ["Ahuja2013", "Dong2009"],
    },
}


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def clean_latex(text: str) -> str:
    """清理文本中的特殊字符，避免 LaTeX 解析错误。"""
    # 在 & % $ # _ { } 两侧加反斜杠（已转义的跳过）
    special = {
        '&': r'\&',
        '%': '\%',
        '$': r'\$',
        '#': '\#',
        '_': r'\_',
    }
    for char, escaped in special.items():
        text = text.replace(char, escaped)
    return text


def tex_quote(text: str) -> str:
    """将双引号转换为 LaTeX 格式。"""
    return text.replace('"', '``').replace('"', "''")


def add_citations(text: str, theory_keys: list[str]) -> str:
    """
    在适当位置插入 \cite{} 命令。
    theory_keys: 理论库 key 列表，会被转换为 \cite{key1}\cite{key2} 格式。
    """
    if not theory_keys:
        return text
    # 去重保持顺序
    seen, unique = set(), []
    for k in theory_keys:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    cite_cmd = ''.join(f'\\cite{{{k}}}' for k in unique)
    # 在理论名称首次出现后插入引用
    # 简单策略：找到所有已知的理论名称，追加引用
    for key in unique:
        info = THEORY_DB.get(key, {})
        name_cn = info.get("name_cn", key)
        name_en = info.get("name_en", "")
        if name_cn in text:
            # 在理论名称后插入 \cite{}
            text = text.replace(name_cn, f"{name_cn} {cite_cmd}", 1)
            break
    return text


def section_header(level: int, title: str) -> str:
    """生成 LaTeX 章节标题。"""
    if level == 1:
        return f"\\section{{{title}}}\n"
    elif level == 2:
        return f"\\subsection{{{title}}}\n"
    elif level == 3:
        return f"\\subsubsection{{{title}}}\n"
    return title


# ─── 各章节生成函数 ────────────────────────────────────────────────────────────

def build_introduction(
    research_question: str,
    data_description: str,
    theory_keys: list[str],
    method: str,
    variables: list[str],
    regression_results: dict = None,
    literature_citations: list[str] = None,
) -> str:
    """生成引言章节（纯 LaTeX，无 \section 命令）。"""

    theory_names_cn = [THEORY_DB.get(k, {}).get("name_cn", k) for k in theory_keys]
    theory_text = "和".join(theory_names_cn) if theory_names_cn else "[理论名称]"
    theories_cited = ''.join(f'\\cite{{{k}}}' for k in theory_keys)

    # 引用列表（来自文献检索）
    lit_cite_block = ""
    if literature_citations:
        lit_cite_block = "\\leavevmode\\cite{" + "},\\cite{".join(literature_citations) + "}"

    # 研究贡献
    contributions = f"""本研究做出了以下理论贡献。第一，本研究运用{theory_text} {theories_cited}，系统检验了{research_question}这一现象，填补了[理论空白]。第二，本研究揭示了[机制名称]在{research_text_short(theory_text)}中的重要作用。第三，本研究为[中国制度情境/新技术情境]下{research_question}的实证研究提供了新的证据。"""

    text = f"""
本研究聚焦于以下核心问题：{clean_latex(research_question)}。

围绕这一研究问题，已有文献提供了重要的理论基础。{lit_cite_block or '随着研究深入，学者们从多个角度对[相关现象]展开了探讨。'}然而，现有研究在以下方面仍存在不足：[研究空白1]；[研究空白2]；[研究空白3]。

本研究运用{theory_text} {theories_cited}，基于{data_description or '实证数据集'}，对{research_question}进行系统检验。研究运用{method_map.get(method, method)}方法，考察{[v for v in variables][0] if variables else '[因变量]'}与{[v for v in variables][1] if len(variables) > 1 else '[自变量]'}之间的关系，以及[调节/中介变量]在其中发挥的作用。

{contributions}

本文结构如下：第二节介绍理论基础；第三节推导研究假设；第四节说明研究方法；第五节报告实证结果；第六节进行讨论与总结。
"""
    return text.strip() + "\n"


def build_theoretical_foundations(
    theory_keys: list[str],
    research_question: str,
) -> str:
    """生成理论基础章节（纯 LaTeX，无 \section 命令）。"""

    blocks = []
    for key in theory_keys:
        info = THEORY_DB.get(key, {})
        name_cn = info.get("name_cn", key)
        name_en = info.get("name_en", "")
        scholars = info.get("scholars", "")
        claims = info.get("core_claims", [])
        mechanism = info.get("mechanism", "")
        refs = info.get("key_refs", [])

        claims_txt = "\n\n".join(f"\\begin{{enumerate}}\\item {clean_latex(c)} \\end{{enumerate}}"
                                  for c in claims) if claims else ""

        block = f"""
\\subsection{{{name_cn}}}

\\textit{{{name_en}}}

主要学者：{scholars}

\\textbf{{核心主张：}}

{claims_txt}

\\textbf{{理论机制：}}

{clean_latex(mechanism)}

关键文献：{''.join(f'\\\\cite{{{r}}}  ' for r in refs)}
"""
        blocks.append(block)

    # 综合分析框架
    combined = f"""
\\subsection{{理论整合与分析框架}}

综合以上理论，{research_question}这一现象可以从以下整合框架得到解释：[整合逻辑描述]。

\\textbf{{概念框架：}}

[理论变量关系图：理论 → 核心机制 → 研究变量]

"""
    blocks.append(combined)
    return "\n".join(blocks)


def build_hypotheses(
    theory_keys: list[str],
    hypotheses: list[dict],  # [{"id":"H1","content":"...","theory_key":"...","variables":[]}, ...]
    variables: list[str],
    research_question: str,
) -> str:
    """
    生成假设推导章节。
    每个假设须包含：假设内容 + 理论依据（从对应理论推导）+ 对应变量。
    """
    if not hypotheses:
        # 代为推导
        hypotheses = [
            {
                "id": "H1",
                "content": f"{variables[1] if len(variables)>1 else '[自变量]'}对{variables[0] if variables else '[因变量]'}有显著正向影响",
                "theory_key": theory_keys[0] if theory_keys else None,
                "variables": variables[:2],
            },
        ]

    blocks = []
    for h in hypotheses:
        h_id = h.get("id", "?")
        content = clean_latex(h.get("content", ""))
        theory_key = h.get("theory_key", theory_keys[0] if theory_keys else None)
        theory_info = THEORY_DB.get(theory_key, {})
        theory_name = theory_info.get("name_cn", theory_key or "?")
        mechanism = theory_info.get("mechanism", "")
        refs = theory_info.get("key_refs", [])

        derivation = f"""
基于{theory_name} {''.join(f'\\\\cite{{{r}}}' for r in refs)}的理论逻辑，{mechanism}，因此本研究预期{content}。"""

        block = f"""
\\subsection{{{h_id}: {content.split('有')[0] if '有' in content else content[:40]}}}

\\textbf{{假设内容：}} {content}

\\textbf{{理论依据：}} {derivation}

\\textbf{{对应变量：}}
\\begin{{itemize}}
\\item 因变量：{h.get('variables', variables)[0] if h.get('variables') else variables[0] if variables else '[因变量]'}
\\item 自变量：{h.get('variables', variables)[1] if len(h.get('variables', variables)) > 1 else variables[1] if len(variables) > 1 else '[自变量]'}
\\item 控制变量：{', '.join(h.get('variables', variables)[2:]) if len(h.get('variables', variables)) > 2 else '[控制变量]'}
\\end{{itemize}}
"""
        blocks.append(block)

    # 研究模型
    blocks.append("""
\subsection{研究模型}

基于上述假设，本研究建立如下概念模型：

\\begin{figure}[tbhp]
\\centering
\\includegraphics[width=0.48\\textwidth]{conceptual_model.png}
\\caption{Conceptual Framework}
\\label{fig:conceptual}
\\end{figure}

[概念模型说明：自变量/中介变量/调节变量/因变量之间的关系箭头]
""")

    return "\n".join(blocks)


def build_methodology(
    data_description: str,
    variables: list[str],
    method: str,
    theory_keys: list[str],
    regression_results: dict = None,
) -> str:
    """生成研究方法章节。"""

    y_var = variables[0] if variables else "[因变量]"
    x_var = variables[1] if len(variables) > 1 else "[自变量]"
    ctrl_vars = variables[2:] if len(variables) > 2 else []

    method_text = {
        "panel-regression": ("双向固定效应（TWFE）面板回归", "双向固定效应模型（Two-Way Fixed Effects, TWFE）"),
        "iv-estimator": ("两阶段最小二乘法（2SLS）", "两阶段最小二乘法（Two-Stage Least Squares, 2SLS）"),
        "staggered-did": ("多时点双重差分（DID）", "多时点双重差分（Staggered Difference-in-Differences, Staggered DID）"),
        "difference-in-discontinuities": ("断点回归（RDD）", "断点回归设计（Regression Discontinuity Design, RDD）"),
        "propensity-score-matching": ("倾向得分匹配（PSM）", "倾向得分匹配（Propensity Score Matching, PSM）"),
        "survival-analysis": ("Cox 比例风险模型", "Cox 比例风险模型（Cox Proportional Hazards Model）"),
    }.get(method, (method, method))

    text = f"""
\\subsection{{数据与样本}}

{data_description or '[数据集描述，包括：数据来源、样本选择标准、时间跨度、最终样本量]'}

\\subsection{{变量测量}}

\\textbf{{因变量（Y）：}} {y_var}
\\begin{{itemize}}
\\item 测量方式：[具体测量方法]
\\item 数据来源：[数据来源]
\\end{{itemize}}

\\textbf{{自变量（X）：}} {x_var}
\\begin{{itemize}}
\\item 测量方式：[具体测量方法]
\\item 数据来源：[数据来源]
\\end{{itemize}}

\\textbf{{控制变量：}} {', '.join(ctrl_vars) if ctrl_vars else '[企业规模、资产负债率、企业年龄、行业竞争度等标准控制变量]'}
\\begin{{itemize}}
\\item {[', '.join(ctrl_vars)] if ctrl_vars else '企业规模(ln总资产)、资产负债率、企业年龄、行业竞争度、年度虚拟变量'}
\\end{{itemize}}

\\subsection{{实证模型}}

本研究采用{method_text[0]}，理由如下：{method_text[1]}能够有效处理[面板数据非观测异质性/内生性问题/因果识别问题]。

\\textbf{{模型设定：}}
\\begin{{equation}}
{y_var}_{{it}} = \\alpha + \\beta \\cdot {x_var}_{{it}} + \\gamma \\cdot Controls_{{it}} + \\mu_i + \\lambda_t + \\epsilon_{{it}}
\\end{{equation}}

其中：\\mu_i 为个体固定效应，\\lambda_t 为时间固定效应，\\epsilon_{{it}} 为误差项。

\\subsection{{稳健性与内生性处理}}

[内生性处理策略]

\\begin{{itemize}}
\\item 工具变量法（如适用）：[工具变量名称及选择依据]
\\item 平行趋势检验（如DID）：[检验方法与结果]
\\item 安慰剂检验：[检验设计]
\\end{{itemize}}
"""
    return text.strip() + "\n"


def build_results(
    regression_results: dict = None,
    variables: list[str] = None,
    hypotheses: list[dict] = None,
) -> str:
    """生成实证结果章节。"""

    y_var = variables[0] if variables else "[因变量]"
    x_var = variables[1] if len(variables) > 1 else "[自变量]"

    FTN = r"\footnotesize $^{{***}}p<0.01$, $^{{**}}p<0.05$, $^{{***}}p<0.1$; robust SEs in parentheses."
    text = f"""
\\subsection{{描述性统计}}

\\begin{{table}}[tbhp]
\\centering
\\caption{{Descriptive Statistics}}
\\label{{tab:descriptive}}
\\small
\\begin{{tabulary}}{{\\linewidth}}{{LCCCC}}
\\toprule
Variable & Mean & SD & Min & Max \\\\
\\midrule
{y_var} & [均值] & [标准差] & [最小值] & [最大值] \\\\
{x_var} & [均值] & [标准差] & [最小值] & [最大值] \\\\
\\bottomrule
\\end{{tabulary}}
\\end{{table}}

\\subsection{{主效应回归结果}}

\\begin{{table*}}[tbhp]
\\centering
\\caption{{Main Effects: {x_var} on {y_var}}}
\\label{{tab:main-effects}}
\\small
\\begin{{tabular}}{{p{{1.1in}}*{{4}}{{cr}}}}
\\toprule
 & \\multicol{{2}}{{c}}{{Model 1}} & \\multicol{{2}}{{c}}{{Model 2}} & \\multicol{{2}}{{c}}{{Model 3}} & \\multicol{{2}}{{c}}{{Model 4}} \\\\
\\cmidrule(lr){{2-3}}\\cmidrule(lr){{4-5}}\\cmidrule(lr){{6-7}}\\cmidrule(lr){{8-9}}
 & Coef. & SE & Coef. & SE & Coef. & SE & Coef. & SE \\\\
\\midrule
{x_var} & [系数] & [SE] & [系数] & [SE] & [系数] & [SE] & [系数] & [SE] \\\\
Controls & [Yes/No] & & [Yes/No] & & [Yes/No] & & [Yes/No] & \\\\
\\midrule
N & \\multicol{{2}}{{c}}{{[N]}} & \\multicol{{2}}{{c}}{{[N]}} & \\multicol{{2}}{{c}}{{[N]}} & \\multicol{{2}}{{c}}{{[N]}} \\\\
R$^{{2}}$ & \\multicol{{2}}{{c}}{{[R2]}} & \\multicol{{2}}{{c}}{{[R2]}} & \\multicol{{2}}{{c}}{{[R2]}} & \\multicol{{2}}{{c}}{{[R2]}} \\\\
\\bottomrule
\\end{{tabular}}
\\par\\vspace{{1ex}}
\{FTN}
\\end{{table*}}

[H1 检验结果说明]

\\subsection{{稳健性检验}}

[稳健性检验表格及说明]

\\subsection{{异质性与机制分析}}

[异质性分组回归及机制检验结果]
"""
    return text.strip() + "\n"


def build_discussion(
    theory_keys: list[str],
    research_question: str,
    hypotheses: list[dict] = None,
    variables: list = None,
) -> str:
    """生成讨论章节（含 Conclusion 子节）。"""

    theory_names = [THEORY_DB.get(k, {}).get("name_cn", k) for k in theory_keys]
    theory_text = "、".join(theory_names)

    text = f"""
\\subsection{{主要发现}}

本研究运用{research_question}作为研究情境，基于{theory_text}，得出以下主要发现：[发现1]；[发现2]。

\\subsection{{理论贡献}}

本研究的理论贡献如下。

\\textbf{{贡献一：}}本研究对{theory_text}的[具体方面]做出了贡献。研究发现[具体发现]，这一发现与理论预期[一致/不一致/拓展]，表明[机制]是解释[现象]的重要因素。

\\textbf{{贡献二：}}本研究揭示了[机制/调节因素]在{theory_text}中的重要作用。[基于异质性分析或稳健性检验，补充具体贡献]

\\subsection{{实践贡献}}

[对企业管理者的启示]

[对政策制定者的启示]

[中国制度情境的特殊性]

\\subsection{{研究局限与未来研究方向}}

\\textbf{{研究局限：}}
\\begin{{itemize}}
\\item 数据局限：[具体局限]
\\item 方法局限：[具体局限]
\\item 变量局限：[具体局限]
\\end{{itemize}}

\\textbf{{未来研究方向：}}
\\begin{{itemize}}
\\item 方向一：[具体方向]
\\item 方向二：[具体方向]
\\item 方向三：[具体方向]
\\end{{itemize}}

\\subsection{{Conclusion}}

本研究运用{theory_text}，系统检验了{research_question}，得出以下结论：[核心结论]。本研究的发现在理论上拓展了[理论名称]在[新情境]下的适用性，在实践上为[管理/政策]决策提供了实证依据。
"""
    return text.strip() + "\n"


# ─── 主函数 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LaTeX 论文分章节生成器")
    parser.add_argument("--output_dir", required=True, help="输出目录")
    parser.add_argument("--research_question", required=True, help="研究问题")
    parser.add_argument("--data_description", default="", help="数据描述")
    parser.add_argument("--variables", default="", help="变量列表（逗号分隔）")
    parser.add_argument("--theory_keys", default="", help="理论 key（逗号分隔）")
    parser.add_argument("--hypotheses_json", default="", help="假设 JSON 文件路径")
    parser.add_argument("--method", default="panel-regression", help="实证方法")
    parser.add_argument("--regression_json", default="", help="回归结果 JSON 文件")
    parser.add_argument("--literature_json", default="", help="文献检索结果 JSON")
    parser.add_argument("--section", choices=["all", "introduction", "theory", "hypotheses",
                                              "methodology", "results", "discussion"],
                        default="all", help="生成哪一节（默认 all）")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    variables = [v.strip() for v in args.variables.split(",") if v.strip()]
    theory_keys = [k.strip() for k in args.theory_keys.split(",") if k.strip()]

    # 读取假设
    hypotheses = []
    if args.hypotheses_json and os.path.exists(args.hypotheses_json):
        with open(args.hypotheses_json) as f:
            hypotheses = json.load(f)

    # 读取回归结果
    regression_results = None
    if args.regression_json and os.path.exists(args.regression_json):
        with open(args.regression_json) as f:
            regression_results = json.load(f)

    # 读取文献
    literature_citations = []
    if args.literature_json and os.path.exists(args.literature_json):
        with open(args.literature_json) as f:
            literature_citations = json.load(f).get("citations", [])

    sections = {}

    if args.section in ("all", "introduction"):
        sections["introduction"] = build_introduction(
            args.research_question, args.data_description,
            theory_keys, args.method, variables,
            regression_results, literature_citations,
        )

    if args.section in ("all", "theory"):
        sections["theory"] = build_theoretical_foundations(theory_keys, args.research_question)

    if args.section in ("all", "hypotheses"):
        sections["hypotheses"] = build_hypotheses(
            theory_keys, hypotheses, variables, args.research_question,
        )

    if args.section in ("all", "methodology"):
        sections["methodology"] = build_methodology(
            args.data_description, variables, args.method,
            theory_keys, regression_results,
        )

    if args.section in ("all", "results"):
        sections["results"] = build_results(regression_results, variables, hypotheses)

    if args.section in ("all", "discussion"):
        sections["discussion"] = build_discussion(
            theory_keys, args.research_question, hypotheses, variables,
        )

    # 写入各 section 文件
    for name, content in sections.items():
        out_path = os.path.join(args.output_dir, f"section_{name}.tex")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ section_{name}.tex ({len(content)} chars)")

    print(f"\n生成完成：{len(sections)} 节 → {args.output_dir}")


if __name__ == "__main__":
    sys.exit(main())
