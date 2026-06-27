#!/usr/bin/env python3
"""
OpenISClaw API Server — HTTP API for Econometric Skills
无需 Docker / OpenClaw，通过 LLM 自然语言驱动完成因果推断分析。

启动方式：
  cd is-econometrics-skills
  pip install -r skills/agent-loop/requirements-agent.txt
  export OPENAI_API_KEY=sk-xxx
  python skills/agent-loop/api-server.py

Docker 方式：
  make api-run

完整文档：参见项目根目录 PLAN1.md
"""

import os
import re
import sys
import argparse
import subprocess

# ─── 路径检测 ────────────────────────────────────────────────────

DOCKER_SKILLS_BASE = "/app/skills"

def detect_environment():
    if os.path.exists(DOCKER_SKILLS_BASE):
        skills_base = DOCKER_SKILLS_BASE
        project_root = os.path.join(skills_base, "..")
    else:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        skills_base = os.path.join(project_root, "skills")
    return {
        "skills_base": skills_base,
        "data_dir": os.path.join(project_root, "user_data"),
        "output_dir": os.path.join(project_root, "user_output"),
        "workspace_dir": os.path.join(project_root, "user_workspace"),
        "project_root": project_root,
    }

ENV = detect_environment()
sys.path.insert(0, os.path.dirname(__file__))

# ─── 依赖检查 ─────────────────────────────────────────────────────

REQUIRED_PYTHON_PACKAGES = [
    "fastapi",
    "uvicorn",
    "openai",
]

REQUIRED_CORE_SKILLS_PACKAGES = [
    "pandas",
    "numpy",
    "scipy",
    "linearmodels",
    "pyreadstat",
]

def check_dependencies() -> list[str]:
    """检查所有必需依赖，返回缺失列表。"""
    missing = []
    for pkg in REQUIRED_PYTHON_PACKAGES + REQUIRED_CORE_SKILLS_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    return missing


def print_dependency_report():
    """启动时打印依赖报告。"""
    missing = check_dependencies()
    print("\n" + "=" * 56)
    print("📦 依赖检查")
    print("=" * 56)
    if not missing:
        print("  ✅ 所有依赖已安装")
    else:
        print(f"  ⚠️  缺少 {len(missing)} 个包：")
        for pkg in missing:
            print(f"     - {pkg}")
        print()
        print("  修复命令：")
        print(f"    pip install {' '.join(missing)}")
        print("  或一行安装全部：")
        print("    pip install pandas numpy scipy linearmodels pyreadstat")
        print("    pip install openai fastapi uvicorn")
    print("=" * 56 + "\n")


# ─── FastAPI 依赖（延迟导入） ─────────────────────────────────────

def _load_fastapi():
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel, Field
        import uvicorn
        return FastAPI, HTTPException, CORSMiddleware, BaseModel, Field, uvicorn
    except ImportError:
        print(
            "❌ 缺少 FastAPI 相关依赖，请安装：\n"
            "   pip install fastapi uvicorn\n"
        )
        sys.exit(1)

FastAPI, HTTPException, CORSMiddleware, BaseModel, Field, uvicorn = _load_fastapi()

# ─── LLM 客户端 ────────────────────────────────────────────────────

def get_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "❌ 未设置 OPENAI_API_KEY\n"
            "   请先设置：export OPENAI_API_KEY=sk-xxx\n"
            "   详细说明见 PLAN1.md"
        )
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("MODEL", "gpt-4o")
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=base_url), model
    except ImportError:
        print("❌ 缺少 openai 包，请安装：pip install openai")
        sys.exit(1)


def call_llm(system_prompt: str, messages: list[dict]) -> str:
    client, model = get_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.3,
    )
    return response.choices[0].message.content


# ─── 路径解析 ─────────────────────────────────────────────────────

def resolve_path(arg: str) -> str:
    if arg.startswith("./user_data/"):
        return arg.replace("./user_data/", ENV["data_dir"] + "/")
    if arg.startswith("./user_output/"):
        return arg.replace("./user_output/", ENV["output_dir"] + "/")
    if arg.startswith("./skills/"):
        return arg.replace("./skills/", ENV["skills_base"] + "/")
    if arg.startswith("user_data/"):
        return arg.replace("user_data/", ENV["data_dir"] + "/")
    if arg.startswith("user_output/"):
        return arg.replace("user_output/", ENV["output_dir"] + "/")
    return arg


# ─── 脚本执行 ─────────────────────────────────────────────────────

def execute_script(script_path: str, args: list[str]) -> dict:
    if not os.path.exists(script_path):
        return {
            "stdout": "",
            "stderr": f"脚本不存在：{script_path}",
            "returncode": 1,
            "success": False,
        }
    cmd = ["python", script_path] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300,
        cwd=os.path.dirname(script_path) or None,
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "success": result.returncode == 0,
    }


def extract_script_cmd(text: str) -> str | None:
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    for block in code_blocks:
        if "python" in block and ("/app/skills/" in block or "/skills/" in block):
            return block.strip()
    for line in text.splitlines():
        if "python" in line and ("/app/skills/" in line or "/skills/" in line):
            return line.strip()
    return None


def resolve_cmd(script_cmd: str):
    from skills_registry import SKILLS
    cmd = script_cmd.strip().strip("`").strip()
    if cmd.startswith("python "):
        cmd = cmd[7:].strip()

    parts = cmd.split(None, 1)
    script_path, args = None, []

    if parts:
        first = parts[0]
        if first.startswith("/app/skills/") or first.startswith("/skills/") or first.startswith("skills/"):
            script_path = first
            args = parts[1].split() if len(parts) > 1 else []

    if not script_path:
        for key, skill in SKILLS.items():
            if key in cmd:
                script_path = skill["script"]
                remaining = cmd.split(key, 1)[-1].strip()
                args = remaining.split() if remaining else []
                break

    script_path = resolve_path(script_path) if script_path else script_path
    args = [resolve_path(a) for a in args]
    return script_path, args


# ─── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="OpenISClaw API",
    description=(
        "IS-Econometrics Skills — 无需 Docker / OpenClaw 的因果推断分析服务。\n\n"
        f"Skills 目录: {ENV['skills_base']}\n"
        f"数据目录:    {ENV['data_dir']}\n"
        f"输出目录:    {ENV['output_dir']}\n\n"
        "完整文档：项目根目录 PLAN1.md"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 请求/响应模型 ───────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    task: str = Field(..., description="分析任务（自然语言）")
    data_path: str | None = Field(None, description="数据文件路径")
    auto_execute: bool = Field(True, description="是否自动执行 LLM 推荐的脚本")

class AnalyzeResponse(BaseModel):
    reply: str
    script_command: str | None
    execution_result: dict | None

class ExecuteRequest(BaseModel):
    skill: str = Field(..., description="技能名称（如 panel-regression）")
    args: list[str] = Field(default_factory=list, description="脚本参数列表")

class SkillsListResponse(BaseModel):
    skills: list[dict]
    count: int

class HealthResponse(BaseModel):
    status: str
    model: str | None
    skills_base: str
    missing_deps: list[str] = Field(default_factory=list)


# ─── API 端点 ─────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    missing = check_dependencies()
    try:
        _, model = get_llm_client()
        status = "ok" if not missing else f"degraded ({len(missing)} deps missing)"
    except RuntimeError as e:
        status = f"error: {e}"
        model = None
    return HealthResponse(
        status=status,
        model=model,
        skills_base=ENV["skills_base"],
        missing_deps=missing,
    )


@app.get("/skills", response_model=SkillsListResponse)
def list_skills():
    from skills_registry import SKILLS
    return SkillsListResponse(
        skills=[
            {
                "id": key,
                "name": s["name"],
                "description": s["description"],
                "required_args": s["required_args"],
                "optional_args": s.get("optional_args", {}),
                "example": s["example"],
            }
            for key, s in SKILLS.items()
        ],
        count=len(SKILLS),
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    from skills_registry import build_system_prompt
    try:
        system_prompt = build_system_prompt()
        user_content = req.task
        if req.data_path:
            user_content += f"\n数据文件路径：{req.data_path}"

        messages = [{"role": "user", "content": user_content}]
        reply = call_llm(system_prompt, messages)
        script_cmd = extract_script_cmd(reply)

        execution_result = None
        if req.auto_execute and script_cmd:
            script_path, args = resolve_cmd(script_cmd)
            if script_path:
                execution_result = execute_script(script_path, args)

        return AnalyzeResponse(
            reply=reply,
            script_command=script_cmd,
            execution_result=execution_result,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute", response_model=dict)
def execute(req: ExecuteRequest):
    from skills_registry import SKILLS
    if req.skill not in SKILLS:
        raise HTTPException(
            status_code=404,
            detail=f"未知技能: {req.skill}，可用技能见 GET /skills",
        )
    skill = SKILLS[req.skill]
    resolved_args = [resolve_path(a) for a in req.args]
    result = execute_script(skill["script"], resolved_args)
    return result


# ─── 启动 ─────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════╗
║                  OpenISClaw API Server                   ║
║           因果推断与计量分析 · 无 OpenClaw/Docker         ║
╠══════════════════════════════════════════════════════════╣
║  服务地址:  http://0.0.0.0:{port}                        ║
║  Skills:    {skills_base}  ║
║  数据目录:  {data_dir}  ║
║  输出目录:  {output_dir}  ║
╠══════════════════════════════════════════════════════════╣
║  使用示例:                                               ║
║                                                          ║
║  查看技能:  curl http://localhost:{port}/skills          ║
║                                                          ║
║  自然语言分析任务:                                       ║
║  curl -X POST http://localhost:{port}/analyze \\          ║
║    -H 'Content-Type: application/json' \\                 ║
║    -d '{{\"task\": \"面板回归分析\", \"data_path\": \"./user_data/data.csv\"}}'  ║
║                                                          ║
║  直接执行脚本:                                           ║
║  curl -X POST http://localhost:{port}/execute \\          ║
║    -H 'Content-Type: application/json' \\                 ║
║    -d '{{\"skill\": \"panel-regression\", \"args\": [\"--data\", \"./user_data/data.csv\", \"--y\", \"roa\"]}}'  ║
║                                                          ║
║  详细文档:  参见项目根目录 PLAN1.md                       ║
╚══════════════════════════════════════════════════════════╝
"""


def main():
    parser = argparse.ArgumentParser(
        description="OpenISClaw API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python api-server.py                    # 默认 8000 端口\n"
            "  PORT=8080 python api-server.py           # 指定端口\n"
            "  python api-server.py --check             # 仅检查依赖\n"
        ),
    )
    parser.add_argument(
        "--check", action="store_true",
        help="仅检查依赖是否完整，不启动服务",
    )
    args = parser.parse_args()

    print_dependency_report()

    if args.check:
        missing = check_dependencies()
        if not missing:
            print("✅ 所有依赖已就绪，服务可以正常启动。")
            sys.exit(0)
        else:
            print(f"❌ 缺少 {len(missing)} 个依赖包，请先安装。")
            sys.exit(1)

    # 验证 skills 目录存在
    if not os.path.exists(ENV["skills_base"]):
        print(f"❌ Skills 目录不存在：{ENV['skills_base']}")
        print("   请确认已 clone 项目并位于正确目录。")
        sys.exit(1)

    port = int(os.environ.get("PORT", "8000"))
    print(BANNER.format(
        port=port,
        skills_base=ENV["skills_base"][:40],
        data_dir=ENV["data_dir"][:40],
        output_dir=ENV["output_dir"][:40],
    ))

    # 检查 API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  未设置 OPENAI_API_KEY，启动后调用 /analyze 会报错。")
        print("   设置命令：export OPENAI_API_KEY=sk-xxx\n")

    print(f"🚀 服务启动中... http://0.0.0.0:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
