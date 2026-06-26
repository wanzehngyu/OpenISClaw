# OpenISClaw — Makefile
# 支持三种模式：
#   1. 纯脚本执行（原有，无需 OpenClaw）
#   2. 对话式 Agent Loop（方案二）
#   3. HTTP API Server（方案三）
#
# ══════════════════════════════════════════════════════

.DPHONY: help build up down shell logs skills-list \
         example-panel example-iv example-did \
         chat api api-run

DOCKER_IMG := openisclaw/is-econometrics:latest

# ── 帮助 ─────────────────────────────────────────────────

help:
	@echo "OpenISClaw Makefile"
	@echo ""
	@echo "【构建】"
	@echo "  make build              构建 Docker 镜像"
	@echo ""
	@echo "【纯脚本执行】（无需 OpenClaw / 无 LLM）"
	@echo "  make skills-list        列出所有可用分析脚本"
	@echo "  make example-panel      面板回归示例"
	@echo "  make example-iv         工具变量回归示例"
	@echo "  make example-did        多时点 DID 示例"
	@echo ""
	@echo "【对话式 Agent Loop】（方案二，需要 OPENAI_API_KEY）"
	@echo "  make chat               启动交互式对话（自然语言 → 自动执行分析）"
	@echo ""
	@echo "【HTTP API Server】（方案三，需要 OPENAI_API_KEY）"
	@echo "  make api                启动 API 服务（前台）"
	@echo "  make api-run            启动 API 服务（后台）"
	@echo "  curl http://localhost:8000/skills    查看所有技能"
	@echo "  curl -X POST http://localhost:8000/analyze   发送分析任务"
	@echo ""
	@echo "【交互式环境】"
	@echo "  make shell              进入容器交互式 Python 环境"
	@echo ""
	@echo "【数据目录】"
	@echo "  数据文件放入 ./user_data/，结果输出到 ./user_output/"
	@echo ""
	@echo "【环境变量】（写入 .env 文件）"
	@echo "  OPENAI_API_KEY=sk-xxx   LLM API Key（chat / api 模式必需）"
	@echo "  MODEL=gpt-4o            模型名称（默认 gpt-4o）"
	@echo "  OPENAI_BASE_URL=...     API Base URL（可选）"

# ── 构建 ─────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up -d
	@echo "容器已启动。运行 make shell 进入交互式环境"

down:
	docker compose down

shell:
	docker compose run --rm is-econometrics-shell

logs:
	docker compose logs -f

# ── 纯脚本执行 ───────────────────────────────────────────

skills-list:
	@echo "=== 可用分析脚本 ==="
	@find ./skills -name "*.py" -path "*/scripts/*" | sort
	@echo ""
	@echo "=== 用法示例 ==="
	@echo "docker compose run --rm is-econometrics \\"
	@echo "  python /app/skills/panel-regression/scripts/panel_regression.py \\"
	@echo "  --data /app/user_data/your_data.csv \\"
	@echo "  --y roa \\"
	@echo "  --x 'it_investment_g co_size_ln lev' \\"
	@echo "  --entity firm_id \\"
	@echo "  --time year \\"
	@echo "  --output_pickle /app/user_output/results.pkl"

example-panel:
	@echo "面板回归示例："
	@docker compose run --rm is-econometrics \
		python skills/panel-regression/scripts/panel_regression.py \
		--data examples/dubai-real-estate/data/fh_panel_quarterly.csv \
		--y ln_price_per_sqft \
		--x "mortgage_rate_pct pct_furnished avg_metro_dist n_transactions" \
		--entity community \
		--time quarter \
		--cluster entity \
		--output_pickle user_output/panel_results.pkl

example-iv:
	@echo "工具变量回归示例："
	@docker compose run --rm is-econometrics \
		python skills/iv-estimator/scripts/iv_regression.py \
		--data examples/dubai-real-estate/data/fh_panel_quarterly.csv \
		--y ln_price_per_sqft \
		--exog "pct_furnished avg_metro_dist n_transactions" \
		--endog "mortgage_rate_pct" \
		--iv "cbuae_base_rate" \
		--output_pickle user_output/iv_results.pkl

example-did:
	@echo "多时点 DID 示例："
	@docker compose run --rm is-econometrics \
		python skills/staggered-did/scripts/staggered_did_pipeline.py \
		--data examples/dubai-real-estate/data/fh_panel_quarterly.csv \
		--y ln_price_per_sqft \
		--t quarter \
		--id community \
		--g first_treatment_quarter \
		--output_pickle user_output/did_results.pkl

# ── 对话式 Agent Loop（方案二）───────────────────────────

chat: .check-env
	@echo "启动对话式 Agent Loop..."
	@echo "输入 quit 退出\n"
	@docker compose run --rm is-econometrics-chat

# ── HTTP API Server（方案三）──────────────────────────────

api: .check-env
	@docker compose up api

api-run: .check-env
	@docker compose up -d api
	@echo "API 服务已后台启动：http://localhost:8000"
	@echo "技能列表：curl http://localhost:8000/skills"

# ── 环境变量检查 ─────────────────────────────────────────

.check-env:
	@if [ -z "$$OPENAI_API_KEY" ] && ! grep -q "OPENAI_API_KEY" .env 2>/dev/null; then \
		echo "❌ 错误：请先设置 OPENAI_API_KEY"; \
		echo ""; \
		echo "方式一（当前 shell）："; \
		echo "  export OPENAI_API_KEY=sk-xxx"; \
		echo ""; \
		echo "方式二（永久保存，创建 .env 文件）："; \
		echo "  echo 'OPENAI_API_KEY=sk-xxx' > .env"; \
		echo "  echo 'MODEL=gpt-4o' >> .env"; \
		echo ""; \
		echo "支持的模型：gpt-4o, gpt-4o-mini, gpt-4-turbo, claude-3-opus 等"; \
		echo "（Claude 系列需设置 ANTHROPIC_API_KEY）"; \
		exit 1; \
	fi
