# OpenISClaw — IS-Econometrics Skills Docker Image
# 面向管理信息系统（IS）专业师生的因果推断与计量分析
# 用途：纯脚本执行（无需本地 OpenClaw），数据进、结果出

FROM python:3.11-slim

LABEL maintainer="万院士 <wan.zhengyu@gmail.com>"
LABEL description="IS-Econometrics Skills — 因果推断与计量分析 Docker 执行环境"

# ─── 系统依赖 ───────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ─── Python 依赖 ─────────────────────────────────────────────
# 核心计量
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scipy \
    statsmodels \
    linearmodels \
    pyreadstat \
    scikit-learn \
    matplotlib \
    seaborn \
    openpyxl \
    xlrd

# 多时点 DID（可选）
RUN pip install --no-cache-dir \
    moderndid \
    plotnine

# 表格导出（可选）
RUN pip install --no-cache-dir \
    stargazer \
    python-docx

# ─── 工作目录 ────────────────────────────────────────────────
WORKDIR /app

# 复制技能包
COPY skills/ ./skills/
COPY dist/ ./dist/
COPY examples/ ./examples/

# ─── 运行时目录 ──────────────────────────────────────────────
# 用户数据/输出挂载点（容器启动时映射）
RUN mkdir -p /app/user_workspace /app/user_data /app/user_output

WORKDIR /app/user_workspace

# 默认启动脚本（显示帮助）
ENTRYPOINT ["python"]
CMD ["-c", "print('OpenISClaw Docker 环境已就绪。\\n\\n用法示例：\\n\\n  docker compose run --rm is-econometrics python /app/skills/panel-regression/scripts/panel_regression.py \\\\\\n    --data /app/user_data/your_data.csv \\\\\\n    --y roa \\\\\\n    --x \"it_investment_g co_size_ln lev\" \\\\\\n    --entity firm_id \\\\\\n    --time year \\\\\\n    --output_pickle /app/user_output/results.pkl\\n\\n查看所有可用脚本：ls /app/skills/*/scripts/')"]