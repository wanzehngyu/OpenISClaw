"""
Research Design Generator - 从理论生成完整研究设计指引
给定一个 IS 理论和用户描述的现象，生成结构化研究设计
"""

import json
from typing import Dict, Optional

# 加载理论数据库
THEORY_DB_PATH = __file__.replace("research_design_generator.py", "theory_db.json")


def load_theory_db() -> Dict:
    with open(THEORY_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 研究设计模板
# ============================================================

METHOD_SKILL_MAP = {
    "事件研究法": {
        "skill": "staggered-did",
        "script": "staggered_did_pipeline.py",
        "note": "用于检验政策/事件发布前后的短期市场反应",
        "example": "--est_method cs --control_group notyettreated"
    },
    "断点回归RDD": {
        "skill": "difference-in-discontinuities",
        "script": "rdd_analysis.py",
        "note": "适用于政策阈值附近的因果效应估计",
        "example": "--running_var score --cutoff 0.5 --bandwidth 0.1"
    },
    "双重差分DID": {
        "skill": "staggered-did",
        "script": "staggered_did_pipeline.py",
        "note": "适用于处理组vs对照组在干预前后的比较",
        "example": "--est_method dr --control_group notyettreated"
    },
    "面板回归": {
        "skill": "panel-regression",
        "script": "panel_regression.py",
        "note": "双向固定效应回归，控制不可观测的个体/时间异质性",
        "example": "--entity firm_id --time year --cluster entity"
    },
    "工具变量回归": {
        "skill": "iv-estimator",
        "script": "iv_regression.py",
        "note": "处理内生性问题，需要排他性工具变量",
        "example": "--endog treatment --iv instrument"
    },
    "倾向得分匹配PSM": {
        "skill": "propensity-score-matching",
        "script": "psm_analysis.py",
        "note": "处理选择偏差，构建反事实对照组",
        "example": "--treatment treated --covariates age size lev"
    },
    "生存分析": {
        "skill": "survival-analysis",
        "script": "survival_analysis.py",
        "note": "分析事件发生的时间依赖性，如企业存活、用户流失",
        "example": "--duration tenure --event churn --covariates age tenure"
    },
    "结构方程模型SEM": {
        "skill": "is-econometrics",
        "script": "（建议使用 R lavaan 或 Python semopy）",
        "note": "检验复杂中介/调节路径",
        "example": "需手动建模"
    },
    "多层线性模型HLM": {
        "skill": "is-econometrics",
        "script": "（建议使用 R lme4 或 Python statsmodels）",
        "note": "处理嵌套数据结构（个体嵌套于组织）",
        "example": "需手动建模"
    }
}


def generate_research_design(theory_id: str, user_phenomenon: str) -> Dict:
    """
    给定理论ID和用户描述的现象，生成完整研究设计指引

    Parameters
    ----------
    theory_id : str
        理论ID（如 "punctuated_equilibrium"）
    user_phenomenon : str
        用户描述的研究现象

    Returns
    -------
    Dict
        完整研究设计，包含：
        - theory_info: 理论基本信息
        - research_question: 重构后的研究问题
        - hypotheses: 理论驱动的假设列表
        - variable_measurement: 变量测量建议
        - data_requirements: 数据要求
        - empirical_strategy: 推荐实证方法
        - analysis_pipeline: 分析流程
        - references: 参考文献
    """
    db = load_theory_db()
    theory = None
    for t in db["theories"]:
        if t["id"] == theory_id:
            theory = t
            break

    if theory is None:
        raise ValueError(f"未找到理论ID: {theory_id}，可用: {[t['id'] for t in db['theories']]}")

    # 构建研究问题
    research_question = _generate_research_question(theory, user_phenomenon)

    # 构建假设
    hypotheses = _generate_hypotheses(theory, user_phenomenon)

    # 变量测量
    variable_measurement = _generate_variable_measurement(theory)

    # 数据要求
    data_requirements = _generate_data_requirements(theory)

    # 实证策略
    empirical_strategy = _generate_empirical_strategy(theory)

    # 分析流程
    analysis_pipeline = _generate_analysis_pipeline(theory)

    return {
        "theory_info": {
            "id": theory["id"],
            "name_en": theory["name_en"],
            "name_zh": theory["name_zh"],
            "core_claim": theory["core_claim"]
        },
        "user_phenomenon": user_phenomenon,
        "research_question": research_question,
        "hypotheses": hypotheses,
        "variable_measurement": variable_measurement,
        "data_requirements": data_requirements,
        "empirical_strategy": empirical_strategy,
        "analysis_pipeline": analysis_pipeline,
        "theory_phenomena": theory.get("typical_phenomena", [])
    }


def _generate_research_question(theory: Dict, phenomenon: str) -> str:
    """根据理论框架重构用户现象为研究问题"""
    template = (
        f"基于{theory['name_zh']}（{theory['name_en']}），"
        f"本研究旨在探讨：{phenomenon}。"
        f"具体而言，本研究试图回答："
        f"{theory['core_claim']}这一理论机制在以下情境中如何作用？"
        f"——{phenomenon}。"
    )
    return template


def _generate_hypotheses(theory: Dict, phenomenon: str) -> list:
    """基于理论的核心机制生成假设"""
    theory_id = theory["id"]
    hypotheses = []

    if theory_id == "punctuated_equilibrium":
        hypotheses = [
            {
                "label": "H1",
                "statement": "政策/技术冲击的强度与组织变革幅度呈正相关关系，冲击越强，组织变革越剧烈。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "间断均衡效应：组织在冲击前后存在显著的结构性断点，表现为关键指标的突变。",
                "direction": "discontinuous"
            },
            {
                "label": "H3",
                "statement": "冲击后组织绩效的恢复速度与组织冗余资源呈正相关。",
                "direction": "positive",
                "moderator": "组织冗余资源"
            }
        ]

    elif theory_id == "tam":
        hypotheses = [
            {
                "label": "H1",
                "statement": "感知有用性对用户使用意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "感知易用性对感知有用性有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "感知易用性对用户使用态度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H4",
                "statement": "外部变量（系统质量、社会影响）通过感知有用性和易用性间接影响使用行为。",
                "direction": "indirect"
            }
        ]

    elif theory_id == "tpb":
        hypotheses = [
            {
                "label": "H1",
                "statement": "行为态度对行为意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "主观规范对行为意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "感知行为控制对行为意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H4",
                "statement": "行为意向对实际行为有显著正向影响。",
                "direction": "positive"
            }
        ]

    elif theory_id == "utaut":
        hypotheses = [
            {
                "label": "H1",
                "statement": "绩效期望对用户使用意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "努力期望对用户使用意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "社会影响对用户使用意向有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H4",
                "statement": "促进条件对实际使用行为有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H5",
                "statement": "年龄、经验、性别等控制变量调节上述关系。",
                "direction": "moderating"
            }
        ]

    elif theory_id == "delone_mclean":
        hypotheses = [
            {
                "label": "H1",
                "statement": "系统质量对用户满意度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "信息质量对用户满意度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "服务质量对用户满意度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H4",
                "statement": "用户满意度对使用意向/实际使用有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H5",
                "statement": "使用意向对净收益有显著正向影响，形成正向反馈循环。",
                "direction": "positive"
            }
        ]

    elif theory_id == "social_information_processing":
        hypotheses = [
            {
                "label": "H1",
                "statement": "组织沟通氛围对员工工作满意度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "社会线索的丰富度调节在线沟通对团队绩效的影响。",
                "direction": "moderating"
            },
            {
                "label": "H3",
                "statement": "团队沟通频率对知识分享行为有显著正向影响。",
                "direction": "positive"
            }
        ]

    elif theory_id == "critical_mass":
        hypotheses = [
            {
                "label": "H1",
                "statement": "平台用户规模达到临界量后，使用价值显著提升（网络效应临界点）。",
                "direction": "nonlinear"
            },
            {
                "label": "H2",
                "statement": "早期用户密度对后续用户采纳速度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "临界量达成后，平台增长呈S型曲线加速特征。",
                "direction": "s-curve"
            }
        ]

    elif theory_id == "knowledge_based":
        hypotheses = [
            {
                "label": "H1",
                "statement": "知识整合能力对企业创新绩效有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "知识转移效率是企业竞争优势的重要来源。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "组织学习在知识存量与创新绩效之间起中介作用。",
                "direction": "mediating"
            }
        ]

    elif theory_id == "rbv":
        hypotheses = [
            {
                "label": "H1",
                "statement": "异质性IT资源（难以模仿、不可替代）与企业竞争优势呈正相关。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "IT资源与组织能力的协同对企业绩效有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "环境动态性调节IT资源与竞争优势的关系（动态环境下IT价值更高）。",
                "direction": "moderating"
            }
        ]

    elif theory_id == "dynamic_capabilities":
        hypotheses = [
            {
                "label": "H1",
                "statement": "感知能力（感知环境变化）在数字化转型与企业绩效之间起正向中介作用。",
                "direction": "mediating"
            },
            {
                "label": "H2",
                "statement": "抓住能力（把握机会）在环境动荡与战略调整之间起正向中介作用。",
                "direction": "mediating"
            },
            {
                "label": "H3",
                "statement": "转型能力（整合重构）在战略调整与企业绩效之间起正向中介作用。",
                "direction": "mediating"
            },
            {
                "label": "H4",
                "statement": "环境动态性正向调节动态能力对企业绩效的影响。",
                "direction": "moderating"
            }
        ]

    elif theory_id == "normalization_process":
        hypotheses = [
            {
                "label": "H1",
                "statement": "技术嵌入程度（coherence）与技术持续使用率呈正相关。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "技能认知（cognitive participation）在培训投入与系统使用率之间起中介作用。",
                "direction": "mediating"
            },
            {
                "label": "H3",
                "statement": "行动启动（activation）正向调节技术熟悉度对使用深度的作用。",
                "direction": "moderating"
            },
            {
                "label": "H4",
                "statement": "正常化（normalization）是技术产生持续业务价值的关键阶段。",
                "direction": "positive"
            }
        ]

    elif theory_id == "affordance":
        hypotheses = [
            {
                "label": "H1",
                "statement": "技术可供性（affordance）的感知强度与用户采用速度呈正相关。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "组织对技术可供性的利用程度（affordance actualization）与组织绩效改善呈正相关。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "可供性感知在技术特征与用户满意度之间起中介作用。",
                "direction": "mediating"
            },
            {
                "label": "H4",
                "statement": "组织资源禀赋正向调节技术可供性与组织变革的关系。",
                "direction": "moderating"
            }
        ]

    elif theory_id == "institutional":
        hypotheses = [
            {
                "label": "H1",
                "statement": "强制压力（监管政策）对企业合规行为有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "模仿压力（同行业标杆企业行为）对技术采纳有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "规范压力（专业标准）对企业数字化转型深度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H4",
                "statement": "制度压力对企业绩效的影响呈倒U型（适度压力最优）。",
                "direction": "inverted_u"
            }
        ]

    elif theory_id == "network_effects":
        hypotheses = [
            {
                "label": "H1",
                "statement": "平台用户规模的平方（梅特卡夫效应）与平台价值呈正相关。",
                "direction": "nonlinear"
            },
            {
                "label": "H2",
                "statement": "跨边网络效应：一边用户规模对另一边用户采纳有正向影响。",
                "direction": "positive"
            },
            {
                "label": "H3",
                "statement": "用户锁定程度正向调节用户规模对平台黏性的影响。",
                "direction": "moderating"
            },
            {
                "label": "H4",
                "statement": "网络效应强度与市场集中度呈正相关。",
                "direction": "positive"
            }
        ]

    elif theory_id == "algorithmic_power":
        hypotheses = [
            {
                "label": "H1",
                "statement": "算法透明度对平台用户信任度有显著正向影响。",
                "direction": "positive"
            },
            {
                "label": "H2",
                "statement": "算法控制感（perceived algorithmic control）负向影响用户留存意愿。",
                "direction": "negative"
            },
            {
                "label": "H3",
                "statement": "算法偏见程度对特定用户群体（如中小商家）的绩效有负向影响。",
                "direction": "negative"
            },
            {
                "label": "H4",
                "statement": "监管强度调节算法权力对企业创新的影响（强监管下负向效应减弱）。",
                "direction": "moderating"
            }
        ]

    # 如果没有特定模板，使用通用模板
    if not hypotheses:
        hypotheses = [
            {
                "label": "H1",
                "statement": f"基于{theory['name_zh']}，{theory['core_claim']}，本研究假设核心机制变量对结果有显著影响。",
                "direction": "positive"
            }
        ]

    return hypotheses


def _generate_variable_measurement(theory: Dict) -> Dict:
    """生成变量测量建议"""
    hints = theory.get("variables_hints", {})
    measurement = {
        "dependent": {},
        "independent": {},
        "mediators": {},
        "moderators": {}
    }

    # 因变量测量建议
    dep_map = {
        "组织绩效波动": ("财务指标变异系数", "ROA标准差/均值", "季度或年度"),
        "市场份额突变": ("市场份额变化率", "HHI指数变化", "年度或季度"),
        "战略调整频率": ("战略决策数量", "并购/重组事件数", "年度"),
        "系统使用率": ("登录频次", "功能使用覆盖率", "月度或周度"),
        "使用意向": ("问卷量表（7点李克特）", "Likert量表", "截面调查"),
        "用户满意度": ("NPS分数", "CSAT量表", "截面调查"),
        "组织结构变化率": ("组织架构调整次数", "部门合并/拆分事件", "年度"),
        "知识分享行为": ("知识流转量", "知识库贡献次数", "月度"),
        "企业创新绩效": ("专利申请数量", "新产品收入占比", "年度"),
        "平台用户数": ("MAU/DAU", "注册用户总数", "日度或月度"),
        "用户留存率": ("Cohort留存率", "流失率", "月度"),
        "合规水平": ("合规评分", "违规次数", "季度或年度"),
        "信任度": ("问卷量表", "Likert量表", "截面调查"),
        "企业绩效": ("ROA/ROE/TFP", "财务指标", "年度"),
    }
    for i, hint in enumerate(hints.get("dependent", [])):
        measurement["dependent"][hint] = {
            "measure": dep_map.get(hint, ("需根据具体构念设计", "专家访谈/问卷", ""))[0],
            "data_source": dep_map.get(hint, ("需根据具体构念设计", "专家访谈/问卷", ""))[1] if hint in dep_map else "专家访谈/问卷/二手数据",
            "period": dep_map.get(hint, ("", "", ""))[2] if hint in dep_map else "视研究设计定"
        }

    # 自变量测量建议
    ind_map = {
        "环境动荡程度": ("行业年均增长率标准差", "营收增长率波动", "年度"),
        "技术冲击强度": ("技术替代率", "研发支出占比", "年度"),
        "政策变化幅度": ("监管政策数量变化", "合规要求增加比例", "年度或季度"),
        "感知有用性": ("问卷量表（Davis, 1989）", "TAM量表", "截面"),
        "感知易用性": ("问卷量表（Davis, 1989）", "TAM量表", "截面"),
        "IT投资强度": ("IT支出/总资产", "软件投资占比", "年度"),
        "知识存量": ("专利存量", "知识库规模", "年度"),
        "动态能力": ("问卷量表（Teece, 2007）", "动态能力量表", "截面"),
        "制度压力": ("行业平均IT投资", "监管合规成本", "年度"),
        "用户规模": ("MAU或总用户数", "平台注册量", "日度或月度"),
    }
    for hint in hints.get("independent", []):
        measurement["independent"][hint] = {
            "measure": ind_map.get(hint, ("需根据具体构念设计", "", ""))[0] if hint in ind_map else "需根据具体构念设计",
            "data_source": ind_map.get(hint, ("", "二手数据", ""))[1] if hint in ind_map else "二手数据/问卷",
            "period": ind_map.get(hint, ("", "", ""))[2] if hint in ind_map else "视研究设计定"
        }

    for hint in hints.get("mediators", []):
        measurement["mediators"][hint] = {
            "measure": "需设计量表或代理指标",
            "data_source": "问卷调查/专家访谈/二手数据",
            "period": "截面或面板"
        }

    for hint in hints.get("moderators", []):
        measurement["moderators"][hint] = {
            "measure": "需根据具体构念设计",
            "data_source": "二手数据/问卷",
            "period": "截面或面板"
        }

    return measurement


def _generate_data_requirements(theory: Dict) -> Dict:
    """生成数据收集要求"""
    theory_id = theory["id"]

    # 不同理论对数据有不同要求
    req_templates = {
        "punctuated_equilibrium": {
            "data_type": "长面板数据，含政策/冲击前后对照",
            "min_sample": "至少50个观测单位（如企业），时间跨度至少10年",
            "key_variables": "绩效指标（ROA/营收增长率）、组织结构变量、冲击事件时间点",
            "recommended_sources": "CSMAR、Wind、上市公司年报",
            "time_structure": "年度数据，需要冲击前后对称或近似对称窗口"
        },
        "tam": {
            "data_type": "截面调查数据或行为追踪数据",
            "min_sample": "至少200个用户样本（结构方程模型要求）",
            "key_variables": "感知有用性、易用性、使用态度、使用意向、实际使用",
            "recommended_sources": "问卷调查+系统日志",
            "time_structure": "截面或短面板（追踪调查"
        },
        "network_effects": {
            "data_type": "平台双边数据，含用户规模和交易记录",
            "min_sample": "至少1000个用户，跨多个平台比较更佳",
            "key_variables": "用户规模、平台价值指标（GMV/成交量）、用户黏性",
            "recommended_sources": "平台后台数据、第三方数据平台",
            "time_structure": "日度或周度面板，观察网络效应动态"
        },
        "algorithmic_power": {
            "data_type": "平台商家或用户面板数据",
            "min_sample": "至少100个商家/用户，跨平台比较更佳",
            "key_variables": "算法评分/排名、曝光量、交易额、用户评分",
            "recommended_sources": "平台API、网页爬取（需合规）、商家调查",
            "time_structure": "日度或周度面板"
        }
    }

    default_req = {
        "data_type": "根据研究设计，可能是截面/面板/时间序列",
        "min_sample": "因分析方法而异，建议 N ≥ 100（回归）/ N ≥ 200（SEM）",
        "key_variables": "因理论而异，参见上方变量测量建议",
        "recommended_sources": "问卷调查、公开数据库（CSMAR/Wind/FRED）、企业年报",
        "time_structure": "截面或面板，视理论机制定"
    }

    return req_templates.get(theory_id, default_req)


def _generate_empirical_strategy(theory: Dict) -> Dict:
    """生成实证策略"""
    methods = theory.get("recommended_methods", [])
    strategy = {
        "primary_method": methods[0] if methods else "面板回归",
        "skill_mapping": [],
        "justification": ""
    }

    for method in methods:
        if method in METHOD_SKILL_MAP:
            skill_info = METHOD_SKILL_MAP[method]
            strategy["skill_mapping"].append({
                "method": method,
                "skill": skill_info["skill"],
                "script": skill_info["script"],
                "usage_example": skill_info["example"]
            })

    # 填充默认方法
    if not strategy["skill_mapping"]:
        strategy["skill_mapping"].append({
            "method": "面板回归",
            "skill": "panel-regression",
            "script": "panel_regression.py",
            "usage_example": "--entity firm_id --time year --cluster entity"
        })

    # 为间断均衡生成特殊策略
    if theory["id"] == "punctuated_equilibrium":
        strategy["justification"] = (
            "间断均衡的核心是检测结构性断点，建议采用事件研究法（event study）检验冲击前后"
            "关键指标是否存在显著断点，并结合断点回归（RDD）分析阈值效应。"
        )
    elif theory["id"] == "network_effects":
        strategy["justification"] = (
            "网络效应体现为规模的价值非线性，建议对用户规模取平方项检验梅特卡夫效应，"
            "并使用动态面板GMM估计处理内生性问题。"
        )
    else:
        strategy["justification"] = f"基于{ theory['name_zh'] }的理论逻辑，{methods[0] if methods else '面板回归'}是最适合的实证方法。"

    return strategy


def _generate_analysis_pipeline(theory: Dict) -> list:
    """生成分析流程"""
    theory_id = theory["id"]

    # 通用流程模板
    generic_pipeline = [
        {"step": 1, "action": "描述性统计与相关性分析", "output": "数据质量报告"},
        {"step": 2, "action": "多重共线性检验（VIF）", "output": "VIF < 10 为可接受"},
        {"step": 3, "action": "固定效应模型估计", "output": "基准回归结果"},
        {"step": 4, "action": "稳健性检验（替换变量/子样本/Bootstrap SE）", "output": "稳健性证据"},
        {"step": 5, "action": "异质性分析（按行业/规模/地区分组）", "output": "异质性证据"}
    ]

    pipelines = {
        "punctuated_equilibrium": [
            {"step": 1, "action": "识别冲击事件点，构建事件时间变量（relative time）", "output": "事件时间序列"},
            {"step": 2, "action": "事件研究法回归：检验冲击前后各期的系数显著性", "output": "事件研究图（平行趋势预检）"},
            {"step": 3, "action": "断点回归（RDD）：以冲击强度为驱动变量，检验断点处效应", "output": "RDD估计量与置信区间"},
            {"step": 4, "action": "双向固定效应DID：处理组vs对照组前后对比", "output": "ATT估计与聚类稳健SE"},
            {"step": 5, "action": "异质性分析：按组织年龄/规模/行业比较间断效应强度", "output": "异质性证据"},
            {"step": 6, "action": "安慰剂检验：随机化冲击时间点，检验效应是否消失", "output": "因果效应可信度"}
        ],
        "network_effects": [
            {"step": 1, "action": "描述性统计：用户规模分布、平台价值指标", "output": "基础统计报告"},
            {"step": 2, "action": "非线性检验：加入用户规模的平方项，检验梅特卡夫效应", "output": "规模二次项系数"},
            {"step": 3, "action": "动态面板GMM：处理用户规模与平台价值的内生性", "output": "GMM估计结果"},
            {"step": 4, "action": "双边网络效应：检验一边规模对另一边用户采纳的影响", "output": "交叉弹性估计"},
            {"step": 5, "action": "锁定效应检验：用户转换成本对留存率的影响", "output": "锁定效应系数"},
            {"step": 6, "action": "跨平台比较：不同平台网络效应强度差异", "output": "平台异质性证据"}
        ],
        "institutional": [
            {"step": 1, "action": "制度压力测量：行业IT投资均值/监管合规成本", "output": "制度压力指标"},
            {"step": 2, "action": "多重固定效应面板回归：控制个体/行业/年份异质性", "output": "基准回归结果"},
            {"step": 3, "action": "调节效应检验：制度压力×技术投资的交互项", "output": "调节效应系数"},
            {"step": 4, "action": "工具变量法：使用外生制度工具变量处理内生性", "output": "IV估计结果"},
            {"step": 5, "action": "倒U型检验：加入制度压力的二次项", "output": "非线性效应证据"},
            {"step": 6, "action": "机制检验：中介效应（通过合法性/模仿压力）", "output": "中介效应路径"}
        ]
    }

    return pipelines.get(theory_id, generic_pipeline)


# ============================================================
# 命令行接口
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python research_design_generator.py <theory_id> <用户现象描述>")
        print("\n可用 theory_id:")
        db = load_theory_db()
        for t in db["theories"]:
            print(f"  - {t['id']}: {t['name_zh']}")
        sys.exit(1)

    theory_id = sys.argv[1]
    phenomenon = sys.argv[2]

    result = generate_research_design(theory_id, phenomenon)

    print(f"\n{'='*60}")
    print(f"理论: {result['theory_info']['name_zh']} ({result['theory_info']['name_en']})")
    print(f"{'='*60}")
    print(f"\n📌 用户现象: {result['user_phenomenon']}")
    print(f"\n📖 研究问题:\n{result['research_question']}")
    print(f"\n💡 核心主张: {result['theory_info']['core_claim']}")
    print(f"\n📋 典型现象: {', '.join(result['theory_phenomena'])}")

    print(f"\n{'='*60}")
    print("假设 (Hypotheses)")
    print(f"{'='*60}")
    for h in result["hypotheses"]:
        print(f"  [{h['label']}] {h['statement']} (方向: {h['direction']})")

    print(f"\n{'='*60}")
    print("变量测量建议 (Variable Measurement)")
    print(f"{'='*60}")
    for var_type, vars_list in result["variable_measurement"].items():
        if vars_list:
            print(f"\n  {var_type}:")
            for name, info in vars_list.items():
                print(f"    • {name}")
                print(f"      测量: {info['measure']}")
                print(f"      数据源: {info['data_source']}")

    print(f"\n{'='*60}")
    print("数据要求 (Data Requirements)")
    print(f"{'='*60}")
    for k, v in result["data_requirements"].items():
        print(f"  {k}: {v}")

    print(f"\n{'='*60}")
    print("实证策略 (Empirical Strategy)")
    print(f"{'='*60}")
    print(f"  主方法: {result['empirical_strategy']['primary_method']}")
    print(f"  理由: {result['empirical_strategy']['justification']}")
    for m in result['empirical_strategy']['skill_mapping']:
        print(f"\n  → 推荐技能: {m['skill']}")
        print(f"    脚本: {m['script']}")
        print(f"    用法示例: python skills/{m['skill']}/scripts/{m['script']} {m['usage_example']}")

    print(f"\n{'='*60}")
    print("分析流程 (Analysis Pipeline)")
    print(f"{'='*60}")
    for step in result["analysis_pipeline"]:
        print(f"  Step {step['step']}: {step['action']}")
        print(f"           预期输出: {step['output']}")
