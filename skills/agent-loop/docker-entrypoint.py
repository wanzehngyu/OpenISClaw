#!/usr/bin/env python3
"""
Agent Loop — 交互式 Agent 入口
在 Docker 容器内运行，或直接在本地 Python 环境运行。
无需 OpenClaw，通过 LLM API 实现对话式分析体验。

本地运行：
  cd is-econometrics-skills
  pip install -r skills/agent-loop/requirements-agent.txt
  export OPENAI_API_KEY=sk-xxx
  python skills/agent-loop/docker-entrypoint.py

Docker 运行：
  cp .env.example .env  # 填入 OPENAI_API_KEY
  make chat
"""

import os
import re
import sys

# ─── 路径解析（Docker vs 原生）───────────────────────────────────────

# 在 Docker 内：/app/skills/agent-loop/docker-entrypoint.py
# 在本地：     skills/agent-loop/docker-entrypoint.py
DOCKER_SKILLS_BASE = "/app/skills"
LOCAL_SKILLS_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

def detect_environment():
    """检测运行环境，返回 (skills_base, data_dir, output_dir)"""
    if os.path.exists(DOCKER_SKILLS_BASE):
        # Docker 环境
        skills_base = DOCKER_SKILLS_BASE
        data_dir = os.path.join(skills_base, "..", "user_data")
        output_dir = os.path.join(skills_base, "..", "user_output")
        workspace_dir = os.path.join(skills_base, "..", "user_workspace")
    else:
        # 本地原生环境：skills/ 在项目根目录下
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skills_base = os.path.join(project_root, "skills")
        data_dir = os.path.join(project_root, "user_data")
        output_dir = os.path.join(project_root, "user_output")
        workspace_dir = os.path.join(project_root, "user_workspace")

    return skills_base, data_dir, output_dir, workspace_dir


SKILLS_BASE, USER_DATA_DIR, USER_OUTPUT_DIR, USER_WORKSPACE_DIR = detect_environment()

# 添加 skills/agent-loop 到 sys.path 以便导入 skills_registry
sys.path.insert(0, os.path.dirname(__file__))

from skills_registry import SKILLS, build_system_prompt

# ─── LLM 客户端 ─────────────────────────────────────────────────────

def get_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("MODEL", "gpt-4o")

    if not api_key:
        raise RuntimeError(
            "请设置环境变量 OPENAI_API_KEY：\n"
            "  export OPENAI_API_KEY=sk-xxx\n"
        )

    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=base_url), model
    except ImportError:
        raise RuntimeError("请安装 openai 库：pip install openai")


def call_llm(system_prompt: str, messages: list[dict], model: str = "gpt-4o"):
    client, model = get_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.3,
    )
    return response.choices[0].message.content

# ─── 路径规范化 ────────────────────────────────────────────────────

def resolve_path(arg: str) -> str:
    """将相对路径转换为对应运行环境下的正确路径"""
    # Docker 内：./user_data/ → /app/user_data/
    # 原生：   ./user_data/ → <project_root>/user_data/
    if arg.startswith("./user_data/"):
        return arg.replace("./user_data/", USER_DATA_DIR + "/")
    if arg.startswith("./user_output/"):
        return arg.replace("./user_output/", USER_OUTPUT_DIR + "/")
    if arg.startswith("./skills/"):
        return arg.replace("./skills/", SKILLS_BASE + "/")
    if arg.startswith("user_data/"):
        return arg.replace("user_data/", USER_DATA_DIR + "/")
    if arg.startswith("user_output/"):
        return arg.replace("user_output/", USER_OUTPUT_DIR + "/")
    return arg

# ─── 脚本执行 ──────────────────────────────────────────────────────

def execute_command(script_path: str, args: list[str]) -> tuple[str, int]:
    """执行 Python 脚本，返回 (stdout+stderr, returncode)"""
    cmd = ["python", script_path] + args
    result = __import__("subprocess").run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.stdout + result.stderr, result.returncode

# ─── 从 LLM 回复提取命令 ───────────────────────────────────────────

def extract_script_cmd(text: str) -> str | None:
    """从 LLM 回复中提取脚本调用命令"""
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    for block in code_blocks:
        if "python" in block and ("/app/skills/" in block or "/skills/" in block):
            return block.strip()
    for line in text.splitlines():
        if "python" in line and ("/app/skills/" in line or "/skills/" in line):
            return line.strip()
    return None

def parse_and_execute(script_cmd: str) -> tuple[str, int]:
    """解析并执行 LLM 给出的命令"""
    cmd = script_cmd.strip().strip("`").strip()
    if cmd.startswith("python "):
        cmd = cmd[7:].strip()

    parts = cmd.split(None, 1)
    script_path = None
    args = []

    if parts:
        first = parts[0]
        if first.startswith("/app/skills/") or first.startswith("/skills/") or first.startswith("skills/"):
            script_path = first
            args = parts[1].split() if len(parts) > 1 else []

    if not script_path:
        # 尝试从 SKILLS registry 匹配
        for key, skill in SKILLS.items():
            if key in cmd:
                script_path = skill["script"]
                remaining = cmd.split(key)[-1].strip() if key in cmd else cmd
                args = remaining.split() if remaining else []
                break

    # 路径规范化
    script_path = resolve_path(script_path) if script_path else script_path
    args = [resolve_path(a) for a in args]

    return execute_command(script_path, args)

# ─── 交互式循环 ───────────────────────────────────────────────────

SEPARATOR = "=" * 60

def run_chat():
    print(SEPARATOR)
    print("OpenISClaw Agent Loop（交互式）")
    print(f"  Skills:  {SKILLS_BASE}")
    print(f"  数据:    {USER_DATA_DIR}")
    print(f"  输出:    {USER_OUTPUT_DIR}")
    print(SEPARATOR)
    print("输入你的计量分析需求，中文或英文均可。")
    print("输入 quit 退出。\n")

    system_prompt = build_system_prompt()
    messages = []

    try:
        get_llm_client()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\n📩 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "q", "exit"):
            print("再见！")
            break

        messages.append({"role": "user", "content": user_input})
        print("\n🤖 思考中...")

        try:
            reply = call_llm(system_prompt, messages)
        except Exception as e:
            print(f"\n❌ LLM 调用失败: {e}")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": reply})

        script_cmd = extract_script_cmd(reply)

        if script_cmd:
            print(f"\n{SEPARATOR}")
            print("📋 推荐命令：")
            print(script_cmd)

            confirm = input("\n⏎ 是否执行此命令？(y/n, 直接回车执行) ").strip().lower()
            if confirm in ("", "y", "yes"):
                print("\n⚙️  执行中...")
                output, code = parse_and_execute(script_cmd)
                print(f"\n{SEPARATOR}")
                print("📊 执行结果：")
                print(output[:3000])
                if code != 0:
                    print(f"\n⚠️  脚本返回非零状态: {code}")
        else:
            print(f"\n{SEPARATOR}")
            print("🤖 OpenISClaw：")
            print(reply)


if __name__ == "__main__":
    run_chat()
