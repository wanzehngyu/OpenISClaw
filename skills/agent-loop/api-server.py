#!/usr/bin/env python3
"""
API Server — FastAPI HTTP 服务
在 Docker 容器内运行，或直接在本地 Python 环境运行。
无需 OpenClaw，通过 HTTP API 提供完整分析流程。

本地运行：
  cd is-econometrics-skills
  pip install -r skills/agent-loop/requirements-agent.txt
  export OPENAI_API_KEY=sk-xxx
  python skills/agent-loop/api-server.py

Docker 运行：
  cp .env.example .env  # 填入 OPENAI_API_KEY
  make api-run
"""

import os
import sys
import re
import subprocess

# ─── 路径检测（与 docker-entrypoint.py 保持一致）───────────────────

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
from skills_registry import SKILLS

# ─── FastAPI 依赖 ─────────────────────────────────────────────────

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("缺少依赖，请运行：pip install -r skills/agent-loop/requirements-agent.txt")
    sys.exit(1)

# ─── LLM 客户端 ────────────────────────────────────────────────────

def get_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("MODEL", "gpt-4o")
    if not api_key:
        raise RuntimeError("请设置环境变量 OPENAI_API_KEY")
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url), model

def call_llm(system_prompt: str, messages: list[dict], model: str = "gpt-4o"):
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
    cmd = ["python", script_path] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
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

def resolve_cmd(script_cmd: str) -> tuple[str, list[str]]:
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
        for key, skill in SKILLS.items():
            if key in cmd:
                script_path = skill["script"]
                remaining = cmd.split(key)[-1].strip() if key in cmd else cmd
                args = remaining.split() if remaining else []
                break

    script_path = resolve_path(script_path) if script_path else script_path
    args = [resolve_path(a) for a in args]
    return script_path, args

# ─── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="OpenISClaw API",
    description=(
        "IS-Econometrics Skills HTTP API — 无需 Docker / OpenClaw 的因果推断分析服务。\n\n"
        f"Skills 目录: {ENV['skills_base']}\n"
        f"数据目录: {ENV['data_dir']}\n"
        f"输出目录: {ENV['output_dir']}"
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
    task: str = Field(..., description="分析任务描述（自然语言）")
    data_path: str | None = Field(None, description="数据文件路径（可选）")
    auto_execute: bool = Field(True, description="是否自动执行 LLM 推荐的脚本")

class AnalyzeResponse(BaseModel):
    reply: str
    script_command: str | None
    execution_result: dict | None

class SkillsListResponse(BaseModel):
    skills: list[dict]

class HealthResponse(BaseModel):
    status: str
    model: str | None
    skills_base: str

# ─── API 端点 ─────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    try:
        _, model = get_llm_client()
        return HealthResponse(status="ok", model=model, skills_base=ENV["skills_base"])
    except Exception as e:
        return HealthResponse(status=f"error: {e}", model=None, skills_base=ENV["skills_base"])

@app.get("/skills", response_model=SkillsListResponse)
def list_skills():
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
        ]
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
def execute(request: dict):
    skill_id = request.get("skill")
    args = request.get("args", [])
    if skill_id not in SKILLS:
        raise HTTPException(status_code=404, detail=f"未知技能: {skill_id}")
    skill = SKILLS[skill_id]
    resolved_args = [resolve_path(a) for a in args]
    result = execute_script(skill["script"], resolved_args)
    return result

# ─── 启动 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"🚀 OpenISClaw API Server")
    print(f"   Skills:  {ENV['skills_base']}")
    print(f"   数据:    {ENV['data_dir']}")
    print(f"   输出:    {ENV['output_dir']}")
    print(f"   启动于   http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
