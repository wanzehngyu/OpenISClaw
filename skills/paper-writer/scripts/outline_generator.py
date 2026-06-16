#!/usr/bin/env python3
"""
outline_generator.py
生成论文大纲——根据用户的研究问题、数据描述、理论框架，输出各章节标题和内容摘要。
"""

import argparse
import json
import sys
from pathlib import Path

def generate_outline(research_question: str, data_description: str, theory: str,
                     methods: str, hypotheses: str = "") -> str:
    """
    根据输入素材生成论文大纲。
    """

    # 理论映射
    theory_map = {
        "dynamic_capabilities": ("动态能力理论", "Teece (2007) 动态能力框架：感知-抓住-转换"),
        "rbv": ("资源基础观", "Barney (1991) VRIN 框架：价值-稀缺性-不可模仿性-不可替代性"),
        "institutional": ("制度理论", "DiMaggio & Powell (1983) 制度同构：强制同构/模仿同构/规范同构"),
        "tam": ("技术接受模型", "Davis (1989) TAM：感知有用性-感知易用性-使用态度-行为意向"),
        "utaut": ("技术接受统一理论", "Venkatesh et al. (2003) UTAUT：绩效期望-努力期望-社会影响-促进条件"),
        "punctuated_equilibrium": ("间断均衡理论", "Tichy & Uhlenbruck (1979) PET：稳定-断裂-重组-新的稳定"),
        "network_effects": ("网络效应理论", "Katz & Shapiro (1985)：直接网络效应-间接网络效应-梅特卡夫定律"),
        "deLone_mclean": ("IS成功模型", "DeLone & McLean (2003)：系统质量-信息质量-服务质量-使用-用户满意-净收益"),
        "affordance": ("技术可供性理论", "Gibson (1979)；Leonardi (2013) 可供性与组织变革"),
        "critical_mass": ("临界量理论", "Markus (1987)：临界量实现是平台成功的关键拐点"),
        "social_info_processing": ("社会信息处理理论", "Walz & Marcus (1973) SIPT：虚拟团队社会线索与沟通效果"),
        "knowledge_based": ("知识基础理论", "Conner & Prahalad (1996)：知识作为战略性资源的整合与转移"),
        "normalization_process": ("正常化过程理论", "May & Finch (2009) NPT：正常化-惯例化-融入常规"),
        "algorithmic_power": ("算法权力理论", "Kitchin (2017)：算法作为权力行使者的控制机制"),
        "tpb": ("计划行为理论", "Ajzen (1991) TPB：行为态度-主观规范-感知行为控制"),
    }

    theory_name, theory_framework = theory_map.get(theory, (theory, "待确认理论框架"))

    # 方法映射
    method_map = {
        "panel-regression": "双向固定效应（TWFE）面板回归",
        "iv-estimator": "两阶段最小二乘法（2SLS）工具变量回归",
        "staggered-did": "多时点双重差分（DID）",
        "difference-in-discontinuities": "断点回归（RDD）",
        "propensity-score-matching": "倾向得分匹配（PSM）",
        "survival-analysis": "Cox 比例风险模型",
    }

    method_name = method_map.get(methods, methods)

    # 解析假设
    hypothesis_items = []
    if hypotheses:
        for i, h in enumerate(hypotheses.split(";"), 1):
            h = h.strip()
            if h:
                hypothesis_items.append(f"  [H{i}] {h}")

    hypotheses_section = ""
    if hypothesis_items:
        hypotheses_section = "## 3. 研究假设（Hypotheses Development）\n"
        hypotheses_section += "### 3.1 假设推导\n"
        for h in hypothesis_items:
            hypotheses_section += f"{h}\n"
        hypotheses_section += "\n### 3.2 研究模型\n"
        hypotheses_section += f"基于 {theory_name}，本研究建立如下概念框架：\n"
        hypotheses_section += f"  {theory_framework}\n"
        hypotheses_section += f"  → 自变量 → 因变量（{method_name} 检验）\n"
    else:
        hypotheses_section = """## 3. 研究假设（Hypotheses Development）
### 3.1 假设推导
  [H1] （待基于研究问题和理论推导）
  [H2] （待基于研究问题和理论推导）
### 3.2 研究模型
  基于理论框架，推导自变量对因变量的预期影响路径。
"""

    outline = f"""# 论文大纲

> 自动生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
> 理论框架：{theory_name}
> 研究方法：{method_name}

---

## 1. 引言（Introduction）

### 1.1 研究背景与问题提出
- **现实背景**：从{research_question}的现实背景切入
- **研究问题**：本研究聚焦于{data_description}中的核心问题
- **研究问题表述**：（待用户确认）{research_question}

### 1.2 文献综述
- **检索策略**：以研究问题和核心变量为关键词，检索近 5 年 IS 顶刊文献
- **已有研究总结**：梳理现有研究的主要发现和结论
- **研究空白**：指出当前研究的不足和争议
- **文献列表**：（由 `literature_fetcher.py` 自动生成，约 8-15 篇）

### 1.3 研究目的与贡献
- **研究目的**：检验 {theory_name} 在 {research_question} 中的适用性
- **理论贡献**：
  - 贡献一：拓展 {theory_name} 对[具体现象]的解释
  - 贡献二：揭示[调节/中介机制]在理论框架中的作用
  - 贡献三：将 {theory_name} 置于[中国制度背景/新情境]下检验
- **实践贡献**：（待根据研究发现补充）

---

## 2. 理论基础（Theoretical Foundations）

### 2.1 {theory_name}概述
- **核心主张**：{theory_framework}
- **主要学者**：（根据理论补充）
- **适用本研究的原因**：为何该理论能够解释 {research_question}

### 2.2 理论机制与分析框架
- **机制分析**：{theory_name} 如何解释自变量对因变量的影响？
- **概念框架**：绘制理论变量关系图（文字描述版）

---

{hypotheses_section}

---

## 4. 研究方法（Methodology）

### 4.1 数据与样本
- **数据来源**：（待用户提供，如 CSMAR、Wind、企业年报等）
- **样本选择**：{data_description}
- **时间跨度**：（待用户提供）
- **样本量**：处理前 → 处理后最终样本量

### 4.2 变量测量
- **因变量**：（待用户提供变量名）
- **自变量**：（待用户提供变量名）
- **控制变量**：（待用户提供）
- **中介/调节变量**：（如有）

### 4.3 实证模型
- **模型选择**：{method_name}
- **模型设定理由**：为何选用该模型而非其他模型
- **固定效应设置**：个体固定效应 / 时间固定效应 / 双向固定效应
- **标准误聚类层级**：企业层面 / 行业层面

### 4.4 内生性与稳健性
- **内生性处理**：工具变量 / 滞后项 / DID 等
- **稳健性检验策略**：
  - [ ] 替换变量
  - [ ] 子样本检验
  - [ ] 缩尾处理变化
  - [ ] Bootstrap 标准误
  - [ ] 安慰剂检验

---

## 5. 实证结果与分析（Data Analysis and Results）

### 5.1 描述性统计
- **表格**：引用 `stargazer-exporter` 输出的描述性统计表
- **样本特征**：行业分布、时间分布、主要变量均值和标准差

### 5.2 主效应回归结果
- **表格**：引用 `stargazer-exporter` 输出的主效应回归表
- **H1 检验结果**：（待实证结果）
- **H2 检验结果**：（待实证结果）
- **模型质量**：R² within、F 统计量、VIF 诊断

### 5.3 稳健性检验
- **表格**：引用稳健性检验结果
- **各检验结果一致性**：逐一说明

### 5.4 异质性与机制分析（如有）
- **分组检验结果**：按企业规模/所有制/行业
- **中介/调节效应**：（如有）

---

## 6. 讨论（Discussion）

### 6.1 理论贡献
- **贡献一**：本研究对 {theory_name} 的[具体方面]做出了贡献
- **贡献二**：本研究揭示了[机制]在理论框架中的作用
- **贡献三**：（待根据研究结果补充）

### 6.2 实践贡献
- **对企业管理者的启示**：（待根据研究结果补充）
- **对政策制定者的启示**：（待根据研究结果补充）
- **中国情境的特殊性**：（如适用）

### 6.3 研究局限与未来研究方向
- **数据局限**：样本范围、时间跨度、变量测量
- **方法局限**：内生性处理、模型设定
- **未来研究方向**：基于局限提出 2-3 个有价值的研究方向

---

## 附录（如有）
- 附录A：描述性统计详细表
- 附录B：稳健性检验补充表
- 附录C：变量定义表

---

## 参考文献
（由 `literature_fetcher.py` 自动生成）

"""

    return outline


def main():
    parser = argparse.ArgumentParser(description="生成论文大纲")
    parser.add_argument("--research_question", required=True, help="用户的研究问题描述")
    parser.add_argument("--data_description", required=True, help="数据集描述")
    parser.add_argument("--theory", required=True, help="理论ID（如 dynamic_capabilities）")
    parser.add_argument("--methods", required=True, help="实证方法（如 panel-regression）")
    parser.add_argument("--hypotheses", default="", help="用户指定的假设（分号分隔）")
    parser.add_argument("--output", default="outline.md", help="输出文件路径")
    args = parser.parse_args()

    outline = generate_outline(
        research_question=args.research_question,
        data_description=args.data_description,
        theory=args.theory,
        methods=args.methods,
        hypotheses=args.hypotheses,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(outline)

    print(f"论文大纲已生成：{args.output}")
    print(f"章节数：6章 + 参考文献")
    print(f"理论框架：{args.theory}")


if __name__ == "__main__":
    main()