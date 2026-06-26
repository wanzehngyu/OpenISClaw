"""
Skills Registry — 技能注册表
记录所有可用脚本的路径、参数说明，供 Agent Loop 和 API Server 调用。

路径自动适配：
  Docker 环境（/app/skills/...）或本地环境（skills/...）
"""

import os

# ─── 路径检测（与 docker-entrypoint.py 保持一致）───────────────────

DOCKER_SKILLS_BASE = "/app/skills"

def get_skills_base():
    """返回 skills 目录的根路径"""
    if os.path.exists(DOCKER_SKILLS_BASE):
        return DOCKER_SKILLS_BASE
    # 本地：skills/agent-loop/skills_registry.py → 项目根目录
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "skills")

SKILLS_BASE = get_skills_base()

# ─── 辅助函数 ──────────────────────────────────────────────────────

def skill_path(relative: str) -> str:
    """将 skills/ 相对路径转换为对应环境下的绝对路径"""
    return os.path.join(SKILLS_BASE, relative)

# ─── 技能注册表 ─────────────────────────────────────────────────────

SKILLS = {
    "panel-regression": {
        "name": "面板回归（双向固定效应 TWFE）",
        "script": skill_path("panel-regression/scripts/panel_regression.py"),
        "description": "对面板数据进行双向固定效应回归，支持企业/行业层面聚类稳健标准误",
        "required_args": {
            "--data": "数据文件路径，支持 .csv/.dta/.xlsx",
            "--y": "因变量列名",
            "--x": "自变量（空格分隔，多个变量用引号包裹）",
            "--entity": "个体 ID 列名（如 firm_id）",
            "--time": "时间 ID 列名（如 year）",
        },
        "optional_args": {
            "--cluster": "聚类维度，可选 entity/time/multi",
            "--output_pickle": "结果 pickle 路径",
            "--output_csv": "结果 CSV 路径",
        },
        "example": (
            f'python {skill_path("panel-regression/scripts/panel_regression.py")} '
            '--data ./user_data/panel.csv --y roa '
            '--x "it_investment_g co_size_ln lev age" '
            '--entity firm_id --time year --cluster entity '
            '--output_pickle ./user_output/panel_results.pkl'
        ),
    },
    "iv-estimator": {
        "name": "工具变量回归（2SLS）",
        "script": skill_path("iv-estimator/scripts/iv_regression.py"),
        "description": "两阶段最小二乘法工具变量回归，诊断弱工具变量、内生性检验、过度识别检验",
        "required_args": {
            "--data": "数据文件路径",
            "--y": "因变量列名",
            "--exog": "外生控制变量（空格分隔）",
            "--endog": "内生解释变量列名",
            "--iv": "工具变量（空格分隔）",
        },
        "optional_args": {
            "--output_pickle": "结果 pickle 路径",
        },
        "example": (
            f'python {skill_path("iv-estimator/scripts/iv_regression.py")} '
            '--data ./user_data/panel.csv --y roa '
            '--exog "co_size_ln lev age" '
            '--endog it_investment_g '
            '--iv "ln_gov_proc digital_infrastructure" '
            '--output_pickle ./user_output/iv_results.pkl'
        ),
    },
    "staggered-did": {
        "name": "多时点双重差分（Callaway-Sant'Anna）",
        "script": skill_path("staggered-did/scripts/staggered_did_pipeline.py"),
        "description": "处理多期处理情况的 DID 估计量，支持事件研究法和平行趋势检验",
        "required_args": {
            "--data": "数据文件路径",
            "--y": "结果变量列名",
            "--t": "时间列名",
            "--id": "个体 ID 列名",
            "--g": "首次处理期列名（未处理为 0 或空）",
        },
        "optional_args": {
            "--cov": "协变量公式，如 ~ co_size_ln + lev + age",
            "--control_group": "对照组类型：notyettreated / nevertreated",
            "--est_method": "估计方法：dr（doubly robust）/ ipw",
            "--output_pickle": "结果 pickle 路径",
            "--plot_path": "事件研究图保存路径",
        },
        "example": (
            f'python {skill_path("staggered-did/scripts/staggered_did_pipeline.py")} '
            '--data ./user_data/did_panel.csv --y roa '
            '--t year --id firm_id --g first_adoption_year '
            '--cov "~ co_size_ln + lev + age" '
            '--control_group notyettreated --est_method dr '
            '--output_pickle ./user_output/did_results.pkl '
            '--plot_path ./user_output/event_study.png'
        ),
    },
    "stargazer-exporter": {
        "name": "学术表格导出",
        "script": skill_path("stargazer-exporter/scripts/generate_table.py"),
        "description": "将回归结果（pickle）导出为 LaTeX/HTML/Word 格式发表级三线表",
        "required_args": {
            "--pickles": "一个或多个 pickle 文件路径（空格分隔）",
            "--models": "模型名称（空格分隔，与 pickle 顺序对应）",
            "--title": "表格标题",
            "--output_dir": "输出目录",
        },
        "optional_args": {
            "--rename": "变量重命名，格式：原名:新名,原名:新名",
            "--formats": "输出格式，逗号分隔，如 latex,html,docx",
        },
        "example": (
            f'python {skill_path("stargazer-exporter/scripts/generate_table.py")} '
            '--pickles ./user_output/panel_results.pkl ./user_output/iv_results.pkl '
            '--models "双向固定效应" "工具变量回归" '
            '--rename "it_investment_g:IT投资,co_size_ln:企业规模,roa:企业绩效" '
            '--title "表1：数字化转型对企业绩效的影响" '
            '--output_dir ./user_output --formats latex,html,docx'
        ),
    },
    "data-cleaning": {
        "name": "面板数据清洗",
        "script": skill_path("data-cleaning/scripts/data_cleaning.py"),
        "description": "系统性清洗面板数据：缺失值处理、异常值检测、重复值剔除、变量类型转换",
        "required_args": {
            "--data": "数据文件路径",
        },
        "optional_args": {
            "--output": "清洗后数据保存路径",
            "--missing_strategy": "缺失值策略：drop/fill_forward/fill_mean/interpolate",
            "--outlier_method": "异常值方法：iqr/winsorize/zscore",
            "--winsor_pct": "Winsorize 截断比例，默认 0.01",
        },
        "example": (
            f'python {skill_path("data-cleaning/scripts/data_cleaning.py")} '
            '--data ./user_data/panel.csv '
            '--output ./user_output/panel_cleaned.csv '
            '--missing_strategy interpolate '
            '--outlier_method winsorize --winsor_pct 0.01'
        ),
    },
    "variable-construction": {
        "name": "变量构建",
        "script": skill_path("variable-construction/scripts/build_variables.py"),
        "description": "构建新变量：滞后项、增长率、行业均值、去中心化、交互项",
        "required_args": {
            "--data": "数据文件路径",
        },
        "optional_args": {
            "--output": "输出文件路径",
            "--lags": "滞后阶数，如 1,2,3",
            "--growth": "计算增长率的变量（逗号分隔）",
            "--demean": "需要去中心化的变量",
            "--interaction": "交互项，格式 var1*var2",
        },
        "example": (
            f'python {skill_path("variable-construction/scripts/build_variables.py")} '
            '--data ./user_data/panel.csv '
            '--output ./user_output/panel_with_vars.csv '
            '--lags 1,2,3 '
            '--growth "roa,it_investment_g" '
            '--demean roa '
            '--interaction "it_investment_g*co_size_ln"'
        ),
    },
    "regression-plotter": {
        "name": "回归系数森林图",
        "script": skill_path("regression-plotter/scripts/plot_regression.py"),
        "description": "生成学术级回归系数森林图，支持分组比较、置信区间标注",
        "required_args": {
            "--pickle": "回归结果 pickle 路径",
        },
        "optional_args": {
            "--output": "图片保存路径",
            "--title": "图表标题",
            "--rename": "变量重命名",
            "--vars": "仅显示指定变量",
        },
        "example": (
            f'python {skill_path("regression-plotter/scripts/plot_regression.py")} '
            '--pickle ./user_output/panel_results.pkl '
            '--output ./user_output/coef_plot.png '
            '--title "回归系数及其95%置信区间" '
            '--rename "it_investment_g:IT投资,co_size_ln:企业规模"'
        ),
    },
    "regression-diagnostics-report": {
        "name": "回归诊断报告",
        "script": skill_path("regression-diagnostics-report/scripts/generate_diagnostics_report.py"),
        "description": "生成完整回归诊断 Markdown 报告：共线性VIF、残差检验、异方差检验",
        "required_args": {
            "--pickle": "回归结果 pickle 路径",
        },
        "optional_args": {
            "--output": "报告保存路径（.md）",
        },
        "example": (
            f'python {skill_path("regression-diagnostics-report/scripts/generate_diagnostics_report.py")} '
            '--pickle ./user_output/panel_results.pkl '
            '--output ./user_output/diagnostics_report.md'
        ),
    },
    "difference-in-discontinuities": {
        "name": "断点回归（RDD）",
        "script": skill_path("difference-in-discontinuities/scripts/rdd_analysis.py"),
        "description": "模糊/清晰断点回归，估计阈值附近的因果效应",
        "required_args": {
            "--data": "数据文件路径",
            "--y": "结果变量",
            "--running": "驱动变量（分组变量）",
            "--threshold": "断点阈值",
        },
        "optional_args": {
            "--fuzzy": "模糊 RDD，指定内生处理变量",
            "--bandwidth": "带宽选择方式：cv / imse",
            "--output": "结果保存路径",
        },
        "example": (
            f'python {skill_path("difference-in-discontinuities/scripts/rdd_analysis.py")} '
            '--data ./user_data/rdd_data.csv '
            '--y roa --running score --threshold 0.5 '
            '--fuzzy treatment '
            '--bandwidth cv '
            '--output ./user_output/rdd_results.pkl'
        ),
    },
    "propensity-score-matching": {
        "name": "倾向得分匹配（PSM）",
        "script": skill_path("propensity-score-matching/scripts/psm_analysis.py"),
        "description": "计算倾向得分、进行一对一/一对多匹配、计算平均处理效应（ATT）",
        "required_args": {
            "--data": "数据文件路径",
            "--treatment": "处理变量列名（0/1）",
            "--features": "用于估计倾向得分的特征变量（空格分隔）",
        },
        "optional_args": {
            "--y": "结果变量（用于计算 ATT）",
            "--method": "匹配方法：nearest / radius / kernel",
            "--output": "结果保存路径",
        },
        "example": (
            f'python {skill_path("propensity-score-matching/scripts/psm_analysis.py")} '
            '--data ./user_data/psm_data.csv '
            '--treatment digital_transformation '
            '--features "co_size_ln lev age it_investment_g" '
            '--y roa --method nearest '
            '--output ./user_output/psm_results.pkl'
        ),
    },
    "survival-analysis": {
        "name": "生存分析（Cox 模型）",
        "script": skill_path("survival-analysis/scripts/survival_analysis.py"),
        "description": "Cox 比例风险模型、Kaplan-Meier 生存曲线、风险比（HR）报告",
        "required_args": {
            "--data": "数据文件路径",
            "--duration": "生存时间列名",
            "--event": "事件指示变量（0=截尾，1=事件发生）",
        },
        "optional_args": {
            "--covariates": "协变量（空格分隔）",
            "--output": "结果保存路径",
        },
        "example": (
            f'python {skill_path("survival-analysis/scripts/survival_analysis.py")} '
            '--data ./user_data/survival_data.csv '
            '--duration tenure --event failure '
            '--covariates "roa it_investment_g co_size_ln" '
            '--output ./user_output/survival_results.pkl'
        ),
    },
    "economic-database": {
        "name": "宏观经济数据库",
        "script": skill_path("economic-database/scripts/fetch_macro_data.py"),
        "description": "从世界银行、FRED 获取宏观数据：GDP、CPI、利率等",
        "required_args": {
            "--source": "数据源：worldbank / fred",
            "--series": "指标代码或序列名",
        },
        "optional_args": {
            "--country": "国家代码，如 CHN / USA",
            "--start_year": "起始年份",
            "--end_year": "结束年份",
            "--output": "输出 CSV 路径",
        },
        "example": (
            f'python {skill_path("economic-database/scripts/fetch_macro_data.py")} '
            '--source worldbank '
            '--series "NY.GDP.MKTP.CD,FP.CPI.TOTL.ZG" '
            '--country CHN --start_year 2010 --end_year 2023 '
            '--output ./user_output/macro_data.csv'
        ),
    },
    "paper-writer": {
        "name": "实证论文写作",
        "script": skill_path("paper-writer/scripts/paper_writer.py"),
        "description": "基于研究问题、理论框架和实证结果，生成完整六章学术论文",
        "required_args": {
            "--research_question": "研究问题描述",
            "--data_description": "数据描述",
            "--variables": "变量列表（逗号分隔）",
            "--theory": "理论框架名称",
        },
        "optional_args": {
            "--hypotheses": "研究假设（分号分隔）",
            "--method": "计量方法",
            "--pickle_results": "实证结果 pickle 路径",
            "--literature": "文献综述 markdown 路径",
            "--output": "论文输出路径（.md）",
        },
        "example": (
            f'python {skill_path("paper-writer/scripts/paper_writer.py")} '
            '--research_question "数字化转型对企业绩效的影响" '
            '--data_description "A股上市公司2010-2023年面板数据" '
            '--variables "roa,digital_transformation,firm_size,leverage,age" '
            '--theory dynamic_capabilities '
            '--hypotheses "H1:数字化转型对企业绩效有显著正向影响" '
            '--pickle_results ./user_output/panel_results.pkl '
            '--output ./user_output/paper.md'
        ),
    },
    "markdown-to-paper": {
        "name": "Markdown 转 Word/PDF",
        "script": skill_path("markdown-to-paper/scripts/converter.py"),
        "description": "将 Markdown 论文转换为 Word 或 LaTeX PDF，支持期刊格式模板",
        "required_args": {
            "--input": "输入 Markdown 文件路径",
            "--output": "输出文件路径（.docx 或 .tex）",
        },
        "optional_args": {
            "--template": "Word 模板路径或 LaTeX 模板路径",
        },
        "example": (
            f'python {skill_path("markdown-to-paper/scripts/converter.py")} '
            '--input ./user_output/paper.md '
            '--output ./user_output/paper.docx'
        ),
    },
    "word-template-filler": {
        "name": "Word 模板填充",
        "script": skill_path("word-template-filler/scripts/filler.py"),
        "description": "将 Markdown 内容按占位符填充到 Word 模板，保持格式样式",
        "required_args": {
            "--template": "Word 模板文件路径",
            "--content": "Markdown 内容文件路径",
        },
        "optional_args": {
            "--output": "输出文件路径",
        },
        "example": (
            f'python {skill_path("word-template-filler/scripts/filler.py")} '
            '--template ./examples/paper_template.docx '
            '--content ./user_output/paper.md '
            '--output ./user_output/paper_filled.docx'
        ),
    },
    "is-theory-matcher": {
        "name": "IS 理论推荐",
        "script": skill_path("is-theory-matcher/scripts/matcher.py"),
        "description": "根据研究现象推荐最匹配的 IS 理论框架，生成研究设计方案",
        "required_args": {
            "--query": "研究现象或问题描述",
        },
        "optional_args": {
            "--top_k": "返回候选理论数量，默认 3",
            "--output": "输出路径",
        },
        "example": (
            f'python {skill_path("is-theory-matcher/scripts/matcher.py")} '
            '--query "企业数字化转型对组织结构的影响" '
            '--top_k 3 '
            '--output ./user_output/theory_match.md'
        ),
    },
}


SYSTEM_PROMPT_TEMPLATE = """你是一个面向管理信息系统（IS）专业师生的因果推断与计量分析助手。

## 可用技能

以下是所有可用技能（每个技能对应一个 Python 脚本）：

{skills_text}

## 使用规则

1. 当用户提供分析需求时，从中选择最匹配的技能
2. 只需构建命令，无需实际执行（由调用方执行）
3. 如果用户的需求不明确，先追问关键参数（数据路径、因变量、自变量等）
4. 如果需要多步分析（如先回归再输出表格），按顺序列出所有命令
5. 回答用中文，保持简洁专业

## 输出格式

选择技能后，给出：
- 选中的技能名称和功能说明
- 推荐的脚本调用命令（包含完整参数）
- 简要解释每个参数的含义

现在开始！"""

def build_system_prompt() -> str:
    """构建供 LLM 使用的 system prompt"""
    lines = []
    for key, skill in SKILLS.items():
        required = "  ".join(f"{k} {v}" for k, v in skill["required_args"].items())
        optional = "  ".join(f"{k} {v}" for k, v in skill.get("optional_args", {}).items())
        lines.append(
            f"- **{skill['name']}** (`{key}`)\n"
            f"  说明：{skill['description']}\n"
            f"  必选参数：{required}\n"
            f"  可选参数：{optional}\n"
            f"  示例：{skill['example']}"
        )
    skills_text = "\n".join(lines)
    return SYSTEM_PROMPT_TEMPLATE.format(skills_text=skills_text)
