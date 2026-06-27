#!/usr/bin/env python3
"""
批量为所有 skill 的 SKILL.md 添加标准化的 "安装与使用" section。

使用方法：
    python scripts/add-install-section.py [--dry-run] [--apply]

工作流程：
    1. 读取 skills/*/SKILL.md
    2. 从 metadata.openclaw.install 提取 pip 包列表（自动去重+过滤内置模块）
    3. 生成 "安装与使用" section
    4. 追加到 frontmatter 之后、## 概述 之前（替换旧的 "依赖安装确认" 等节）
"""

import os
import re
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SKILLS_DIR = PROJECT_ROOT / "skills"

# 已内置的 Python 模块，不需要 pip install
BUILTIN_MODULES = {"pickle", "pickle5", "pathlib", "os", "sys", "json", "re"}

# 各 skill 的脚本文件名（用于直接运行示例）
SKILL_SCRIPTS = {
    "agent-loop":         "docker-entrypoint.py",
    "data-cleaning":     "data_cleaning.py",
    "difference-in-discontinuities": "rdd_analysis.py",
    "economic-database":  "fetch_macro_data.py",
    "is-econometrics":   None,  # 纯协调层，无独立脚本
    "is-theory-matcher": "matcher.py",
    "iv-estimator":      "iv_regression.py",
    "markdown-to-paper": "converter.py",
    "panel-regression":  "panel_regression.py",
    "paper-writer":      "paper_writer.py",
    "propensity-score-matching": "psm_analysis.py",
    "regression-diagnostics-report": "generate_diagnostics_report.py",
    "regression-plotter": "plot_regression.py",
    "staggered-did":     "staggered_did_pipeline.py",
    "stargazer-exporter": "generate_table.py",
    "survival-analysis": "survival_analysis.py",
    "variable-construction": "build_variables.py",
    "word-template-filler": "filler.py",
}

# 核心依赖（所有 skill 默认需要的）
CORE_DEPS = ["pandas", "numpy", "scipy"]

# 手动补充某些 skill 缺少 metadata 的情况
SKILL_EXTRA_DEPS = {
    "is-econometrics":    ["linearmodels", "pyreadstat"],
    "is-theory-matcher":  [],  # 目前仅用标准库
    "agent-loop":         [],  # 运行时依赖已在 requirements-agent.txt
    "markdown-to-paper":  ["python-docx", "pyyaml"],
    "word-template-filler": ["python-docx", "lxml"],
    "paper-writer":       ["stargazer", "python-docx"],
    "regression-diagnostics-report": [],  # pandas + pickle(内置)
}


def extract_pip_packages(skill_md_content: str) -> list[str]:
    """从 SKILL.md 的 metadata.openclaw.install 中提取 pip 包列表（去重+过滤内置）"""
    packages = []
    install_match = re.search(r'"install"\s*:\s*\[(.*?)\]', skill_md_content, re.DOTALL)
    if install_match:
        install_block = install_match.group(1)
        pip_pattern = re.compile(r'"package"\s*:\s*"([^"]+)"')
        for m in pip_pattern.finditer(install_block):
            pkg = m.group(1).strip().lower()
            if pkg and pkg not in BUILTIN_MODULES:
                packages.append(pkg)

    # 去重，保持顺序
    seen = set()
    unique = []
    for p in packages:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def build_install_section(skill_name: str, pip_packages: list[str]) -> str:
    """构建标准化的安装与使用 section"""

    # 合并核心依赖 + skill 特定依赖
    extra = SKILL_EXTRA_DEPS.get(skill_name, [])
    all_deps_ordered = list(dict.fromkeys(CORE_DEPS + pip_packages + extra))

    if skill_name in SKILL_EXTRA_DEPS and not pip_packages and not extra:
        # 完全无依赖的 skill
        pip_cmd = "# 核心依赖已包含在项目 requirements 中"
    elif not all_deps_ordered:
        pip_cmd = "pip install pandas numpy scipy"
    else:
        pip_cmd = "pip install " + " ".join(all_deps_ordered)

    script_name = SKILL_SCRIPTS.get(skill_name)
    if script_name:
        script_line = f"python skills/{skill_name}/scripts/{script_name} --help"
    elif skill_name == "is-econometrics":
        script_line = "# 纯协调层，通过 agent-loop 或 OpenClaw 调用子技能"
    else:
        script_line = f"ls skills/{skill_name}/scripts/  # 查看可用脚本"

    lines = [
        "## 安装与使用",
        "",
        "本技能支持三种安装运行方式：",
        "",
        "### 方式一：有 OpenClaw（推荐）",
        "",
        "OpenClaw 用户直接通过命令安装：",
        "",
        "```bash",
        f"openclaw skill install {skill_name}",
        "```",
        "",
        "OpenClaw 会自动检测并安装所需 pip 依赖。",
        "",
        "### 方式二：纯 pip 安装（无 Docker / 无 OpenClaw）",
        "",
        "安装 pip 依赖后，直接运行脚本：",
        "",
        "```bash",
        f"# 安装依赖（核心计量包）",
        f"{pip_cmd}",
        "",
        f"# 运行脚本",
        f"{script_line}",
        "```",
        "",
        "### 方式三：Docker 免安装（无需本地 Python 环境）",
        "",
        "克隆项目后，用 Docker 运行 Agent Loop（自然语言交互）或 API Server：",
        "",
        "```bash",
        "git clone https://github.com/wanzehngyu/OpenISClaw.git",
        "cd OpenISClaw",
        "cp .env.example .env  # 编辑填入 OPENAI_API_KEY",
        "",
        "# 对话式 Agent Loop（自然语言 → 自动分析）",
        "make chat",
        "",
        "# HTTP API 服务",
        "make api-run",
        "# 访问 http://localhost:8000 查看所有技能并发起分析",
        "```",
        "",
        "详见 [项目 README](https://github.com/wanzehngyu/OpenISClaw) 。",
        "",
    ]

    return "\n".join(lines)


def process_skill(skill_dir: Path, dry_run: bool = False) -> tuple[bool, str]:
    """处理单个 skill 目录，返回 (是否修改, 信息)"""
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        return False, "SKILL.md not found"

    content = skill_md_path.read_text(encoding="utf-8")
    skill_name = skill_dir.name

    # 检查是否已有 "## 安装与使用" section
    if re.search(r"^## 安装与使用\s*$", content, re.MULTILINE):
        return False, "already has section"

    pip_packages = extract_pip_packages(content)
    install_section = build_install_section(skill_name, pip_packages)

    # 找到 frontmatter 结束位置（第二个 --- 之后）
    first_boundary = content.find("---")
    if first_boundary == -1:
        return False, "no frontmatter"
    second_boundary = content.find("---", first_boundary + 3)
    if second_boundary == -1:
        return False, "malformed frontmatter"

    body_start = second_boundary + 3  # skip second ---

    # 找第一个 ## 标题（插入点）
    first_h2 = re.search(r"\n## ", content[body_start:])
    if first_h2:
        insert_pos = body_start + first_h2.start()
    else:
        insert_pos = body_start

    new_content = (
        content[:insert_pos]
        + "\n"
        + install_section
        + "\n"
        + content[insert_pos:]
    )

    if dry_run:
        return False, (
            f"Would add section ({len(install_section)} chars)\n"
            f"  pip packages: {pip_packages}\n"
            f"  script: {SKILL_SCRIPTS.get(skill_name, 'N/A')}"
        )

    skill_md_path.write_text(new_content, encoding="utf-8")
    return True, f"Added section ({len(install_section)} chars)"


def main():
    parser = argparse.ArgumentParser(
        description="批量为 SKILL.md 添加标准化安装与使用 section"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="仅输出，不写入文件"
    )
    parser.add_argument(
        "--apply", action="store_true", help="实际写入文件（不加此参数则 dry-run）"
    )
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        print("Error: use --dry-run or --apply")
        sys.exit(1)

    if not SKILLS_DIR.exists():
        print(f"Error: {SKILLS_DIR} not found")
        sys.exit(1)

    modified = 0
    skipped = 0

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("."):
            continue

        changed, info = process_skill(skill_dir, dry_run=args.dry_run)
        if args.dry_run:
            if "already" not in info:
                print(f"[dry-run] {skill_dir.name}: {info}")
        else:
            if changed:
                print(f"✅ {skill_dir.name}: {info}")
                modified += 1
            else:
                print(f"⏭️  {skill_dir.name}: {info}")
                skipped += 1

    action = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{action}Modified: {modified}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
