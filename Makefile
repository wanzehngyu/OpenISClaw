# OpenISClaw — Makefile (Docker 纯脚本执行方式)
# 无需本地 OpenClaw，所有分析通过容器内 Python 脚本完成

.PHONY: help build up down shell logs skills-list example-panel example-iv example-did

DOCKER_IMG:=openisclaw/is-econometrics:latest

help:
	@echo "OpenISClaw Docker Makefile（纯脚本执行）"
	@echo ""
	@echo "  make build              构建 Docker 镜像"
	@echo "  make up                 启动容器（后台）"
	@echo "  make down               停止容器"
	@echo "  make shell              进入容器交互式 Python shell"
	@echo "  make logs               查看容器日志"
	@echo "  make skills-list        列出所有可用脚本"
	@echo "  make example-panel      运行面板回归示例"
	@echo "  make example-iv         运行工具变量示例"
	@echo "  make example-did        运行多时点 DID 示例"
	@echo ""
	@echo "  数据文件放入 ./user_data/，结果输出到 ./user_output/"

build:
	docker compose build

up:
	docker compose up -d
	@echo "容器已启动，运行 make shell 进入交互式环境"

down:
	docker compose down

shell:
	docker compose run --rm is-econometrics python

logs:
	docker compose logs -f

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