#!/usr/bin/env python3
"""
OpenISClaw Web UI — TensorBoard-Style Econometrics Dashboard
FastAPI server that serves the web interface and proxies API calls.

启动方式：
  cd is-econometrics-skills
  export OPENAI_API_KEY=sk-xxx
  python web-ui/server.py

访问： http://localhost:8000
"""

import os
import re
import json
import asyncio
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ─── 路径检测 ──────────────────────────────────────────────────────

DOCKER_SKILLS_BASE = "/app/skills"
DOCKER_UI_BASE = "/app/web-ui"

def detect_environment():
    """
    路径检测逻辑（优先级从高到低）：
    
    1. Docker 环境：使用容器固定路径
       （os.path.exists("/app/skills") 检测）
    
    2. 环境变量显式指定项目根：
       USER_PROJECT_ROOT    → 项目根目录
       OPENCLAW_SKILLS_BASE → skills 脚本目录
       USER_DATA_DIR         → 数据目录
       USER_OUTPUT_DIR       → 输出目录
    
    3. 以 cwd（启动时当前工作目录）为项目根：
       data_dir   = cwd/user_data
       output_dir = cwd/user_output
       skills_base = 在 cwd 的父目录链中搜索 is-econometrics-skills/skills
       （适用于：cd ~/myproject && python path/to/server.py）
    
    4. 默认行为（向后兼容）：
       skills 的父目录即为项目根
    """
    if os.path.exists(DOCKER_SKILLS_BASE):
        return {
            "skills_base": DOCKER_SKILLS_BASE,
            "data_dir": os.environ.get("USER_DATA_DIR", "/app/user_data"),
            "output_dir": os.environ.get("USER_OUTPUT_DIR", "/app/user_output"),
            "workspace_dir": os.environ.get("USER_WORKSPACE_DIR", "/app/user_workspace"),
            "project_root": "/app",
            "ui_base": DOCKER_UI_BASE,
        }

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 显式环境变量
    user_project_root = os.environ.get("USER_PROJECT_ROOT", "")
    user_data_dir = os.environ.get("USER_DATA_DIR", "")
    user_output_dir = os.environ.get("USER_OUTPUT_DIR", "")
    user_workspace_dir = os.environ.get("USER_WORKSPACE_DIR", "")
    skills_base_env = os.environ.get("OPENCLAW_SKILLS_BASE", "")

    if user_project_root:
        pr = os.path.abspath(user_project_root)
        return {
            "skills_base": skills_base_env or _find_skills_base(pr, script_dir),
            "data_dir": user_data_dir or os.path.join(pr, "user_data"),
            "output_dir": user_output_dir or os.path.join(pr, "user_output"),
            "workspace_dir": user_workspace_dir or os.path.join(pr, "user_workspace"),
            "project_root": pr,
            "ui_base": script_dir,
        }

    if user_data_dir or user_output_dir:
        pr = os.path.abspath(user_data_dir or user_output_dir)
        return {
            "skills_base": skills_base_env or _find_skills_base(pr, script_dir),
            "data_dir": os.path.abspath(user_data_dir) if user_data_dir else pr,
            "output_dir": os.path.abspath(user_output_dir) if user_output_dir else pr,
            "workspace_dir": user_workspace_dir or "/tmp/workspace",
            "project_root": pr,
            "ui_base": script_dir,
        }

    # 方案3：以 cwd 为项目根（用户友好默认行为）
    cwd = os.getcwd()
    skills_base = skills_base_env or _find_skills_base(cwd, script_dir)
    return {
        "skills_base": skills_base,
        "data_dir": os.path.join(cwd, "user_data"),
        "output_dir": os.path.join(cwd, "user_output"),
        "workspace_dir": os.path.join(cwd, "user_workspace"),
        "project_root": cwd,
        "ui_base": script_dir,
    }


def _find_skills_base(start_path, script_dir):
    """
    从 start_path 向上搜索 is-econometrics-skills/skills 目录。
    同时检查父目录链的兄弟目录（如 start_path/../clawd/is-econometrics-skills/skills）。
    """
    p = os.path.abspath(start_path)
    visited = set()
    for _ in range(20):
        candidate = os.path.join(p, "is-econometrics-skills", "skills")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(p)
        if parent == p or p in visited:
            break
        visited.add(p)
        p = parent
    # 没找到则搜索脚本所在目录的父目录链（向后兼容）
    p = os.path.abspath(os.path.dirname(script_dir))
    visited.clear()
    for _ in range(20):
        # 检查当前 p 下是否有 is-econometrics-skills/skills
        candidate = os.path.join(p, "is-econometrics-skills", "skills")
        if os.path.isdir(candidate):
            return candidate
        # 也检查 p 的兄弟目录 clawd（因为 skills 常在 clawd/ 下）
        clawd_candidate = os.path.join(p, "clawd", "is-econometrics-skills", "skills")
        if os.path.isdir(clawd_candidate):
            return clawd_candidate
        parent = os.path.dirname(p)
        if parent == p or p in visited:
            break
        visited.add(p)
        p = parent
    return os.path.join(os.path.dirname(os.path.dirname(script_dir)), "skills")

ENV = detect_environment()
sys_path = os.path.join(ENV["skills_base"], "agent-loop")
if os.path.exists(sys_path):
    import sys
    sys.path.insert(0, sys_path)

# ─── FastAPI App ────────────────────────────────────────────────────

app = FastAPI(
    title="OpenISClaw Web UI",
    description="IS-Econometrics Skills — TensorBoard-Style Dashboard",
    version="1.0.0",
)

# ─── 静态文件挂载 ───────────────────────────────────────────────────

ui_base = ENV["ui_base"]
static_dir = os.path.join(ui_base, "static")
templates_dir = os.path.join(ui_base, "templates")

if os.path.exists(static_dir):
    from starlette.middleware.base import BaseHTTPMiddleware
    @app.middleware("http")
    async def no_cache(request, call_next):
        resp = await call_next(request)
        if request.url.path.startswith(("/static/", "/")):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
        return resp
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ─── 依赖检查 ───────────────────────────────────────────────────────

def check_dependencies():
    missing = []
    for pkg in ["fastapi", "uvicorn", "pandas", "linearmodels"]:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    return missing


# ─── 数据文件工具 ────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {".csv", ".dta", ".xlsx", ".xls"}


def list_datasets() -> list[dict]:
    """列出 user_data 目录下的所有可用数据集。"""
    data_dir = ENV["data_dir"]
    os.makedirs(data_dir, exist_ok=True)
    datasets = []
    for fname in sorted(os.listdir(data_dir)):
        fpath = os.path.join(data_dir, fname)
        if os.path.isfile(fpath):
            ext = os.path.splitext(fname)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                stat = os.stat(fpath)
                datasets.append({
                    "name": fname,
                    "path": fname,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": ext[1:],  # csv, dta, xlsx
                })
    return datasets


def preview_dataset(name: str, rows: int = 100) -> dict:
    """读取数据集前 N 行，返回列信息 + 预览。"""
    data_dir = ENV["data_dir"]
    fpath = os.path.join(data_dir, name)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail=f"文件不存在: {name}")

    try:
        import pandas as pd
        ext = os.path.splitext(name)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(fpath, nrows=rows)
        elif ext == ".dta":
            df = pd.read_stata(fpath, nrows=rows)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(fpath, nrows=rows)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            columns.append({
                "name": col,
                "dtype": dtype,
                "type": "numeric" if df[col].dtype.kind in "fiuc" else "string",
                "missing": int(df[col].isna().sum()),
                "missing_pct": round(df[col].isna().mean() * 100, 1),
                "nunique": int(df[col].nunique()),
            })

        preview_rows = []
        for _, row in df.head(rows).iterrows():
            preview_rows.append([str(v) if v is not None else "" for v in row.tolist()])

        summary = {}
        for col in df.select_dtypes(include="number").columns:
            summary[col] = {
                "mean": round(float(df[col].mean()), 4) if not df[col].isna().all() else None,
                "std": round(float(df[col].std()), 4) if not df[col].isna().all() else None,
                "min": round(float(df[col].min()), 4) if not df[col].isna().all() else None,
                "max": round(float(df[col].max()), 4) if not df[col].isna().all() else None,
            }

        return {
            "name": name,
            "rows": len(df),
            "total_rows": int(len(pd.read_csv(fpath) if ext == ".csv" else df)),
            "columns": columns,
            "preview": preview_rows,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 结果管理 ────────────────────────────────────────────────────────

def list_results() -> list[dict]:
    """列出 user_output 目录下的所有结果文件。"""
    output_dir = ENV["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    results = []
    for fname in sorted(os.listdir(output_dir)):
        fpath = os.path.join(output_dir, fname)
        if os.path.isfile(fpath):
            ext = os.path.splitext(fname)[1].lower()
            ftype = "table" if ext in (".tex", ".html", ".docx") else \
                    "plot" if ext in (".png", ".jpg", ".pdf") else \
                    "data" if ext in (".pkl", ".csv") else "other"
            stat = os.stat(fpath)
            results.append({
                "id": fname,
                "name": fname,
                "type": ftype,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return results


# ─── 脚本执行 ───────────────────────────────────────────────────────

def execute_script(skill: str, args: list[str]) -> dict:
    """通过 skills_registry 执行技能脚本。"""
    skills_base = ENV["skills_base"]

    registry_path = os.path.join(skills_base, "agent-loop", "skills_registry.py")
    if not os.path.exists(registry_path):
        return {"success": False, "stderr": f"skills_registry.py not found at {registry_path}"}

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("skills_registry", registry_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        SKILLS = mod.SKILLS
    except Exception as e:
        return {"success": False, "stderr": f"Failed to load skills_registry: {e}"}

    if skill not in SKILLS:
        return {"success": False, "stderr": f"未知技能: {skill}，可用技能: {list(SKILLS.keys())}"}

    script_path = SKILLS[skill]["script"]
    if not os.path.isabs(script_path):
        script_path = os.path.join(skills_base, script_path.lstrip("/"))

    def resolve(arg: str) -> str:
        for prefix, base in [
            ("./user_data/", ENV["data_dir"]),
            ("./user_output/", ENV["output_dir"]),
            ("user_data/", ENV["data_dir"]),
            ("user_output/", ENV["output_dir"]),
        ]:
            if arg.startswith(prefix):
                return arg.replace(prefix, base + "/")
        return arg

    resolved_args = [resolve(a) for a in args]
    cmd = ["python3", script_path] + resolved_args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(script_path) or None,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stderr": "脚本执行超时（5分钟）"}
    except Exception as e:
        return {"success": False, "stderr": str(e)}


# ─── OpenClaw Gateway 集成 ─────────────────────────────────────────────

def check_openclaw() -> dict:
    """检测 OpenClaw CLI 是否可用及运行状态。"""
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "status", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            try:
                import json as _json
                status = _json.loads(result.stdout)
                return {
                    "available": True,
                    "running": status.get("running", False),
                    "port": status.get("port"),
                    "url": f"http://127.0.0.1:{status.get('port', 18789)}",
                }
            except Exception:
                return {"available": True, "running": True, "port": 18789}
    except Exception:
        pass
    return {"available": False, "running": False, "port": None}

OPENCLAW_STATUS = check_openclaw()

def chat_via_openclaw(task: str, session_id: str, data_path: Optional[str] = None,
                      agent_id: Optional[str] = None, timeout: int = 120) -> dict:
    """
    通过 openclaw agent --local 调用 OpenClaw Gateway。
    
    优点：
      - API Key 由 OpenClaw 统一管理，不泄露给 web-ui
      - 支持 OpenClaw 的所有渠道（飞书/iMessage）投递
      - 复用 OpenClaw 配置的模型（MiniMax / GPT-4o 等）
      - session_id 支持保持对话上下文
    """
    full_task = task
    if data_path:
        full_task += f"\n\n数据文件路径：{data_path}"

    project_root = ENV["project_root"]
    skills_base = ENV["skills_base"]
    full_task += (
        f"\n\n【项目环境】"
        f"\nSkills 目录：{skills_base}"
        f"\n数据目录：{ENV['data_dir']}"
        f"\n输出目录：{ENV['output_dir']}"
        f"\n工作目录：{project_root}"
        f"\n请基于以上路径执行计量分析技能脚本。"
    )

    cmd = [
        "openclaw", "agent",
        "--session-id", session_id,
        "--message", full_task,
        "--local",       # embedded 模式，不走 Gateway channel 路由
        "--json",
        "--timeout", str(timeout),
    ]
    if agent_id:
        cmd.extend(["--agent", agent_id])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout + 10,
            cwd=project_root,
        )
        if result.returncode != 0:
            return {"reply": "", "error": result.stderr or f"openclaw agent 返回码 {result.returncode}",
                    "script_command": None, "model": None}

        import json as _json
        data = _json.loads(result.stdout)

        payloads = data.get("payloads", [])
        reply = payloads[0]["text"] if payloads else ""

        script_cmd = None
        for block in re.findall(r"```(?:python)?\n(.*?)```", reply, re.DOTALL):
            if "python" in block and ("skills/" in block or "/app/skills/" in block):
                script_cmd = block.strip()
                break

        meta = data.get("meta", {})
        agent_meta = meta.get("agentMeta", {})
        execution = meta.get("executionTrace", {})

        return {
            "reply": reply,
            "script_command": script_cmd,
            "model": agent_meta.get("model"),
            "provider": agent_meta.get("provider"),
            "usage": agent_meta.get("usage"),
            "session_id": session_id,
            "runner": execution.get("runner"),
        }
    except subprocess.TimeoutExpired:
        return {"reply": "", "error": "OpenClaw Agent 执行超时",
                "script_command": None, "model": None}
    except _json.JSONDecodeError as e:
        return {"reply": "", "error": f"OpenClaw 返回 JSON 解析失败: {e}\n{result.stdout[:500]}",
                "script_command": None, "model": None}
    except Exception as e:
        return {"reply": "", "error": str(e), "script_command": None, "model": None}

# ─── Direct LLM 模式（无 OpenClaw 时备用） ─────────────────────────────────

def get_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("MODEL", "gpt-4o")
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=base_url), model
    except ImportError:
        raise RuntimeError("openai package not installed")


def build_system_prompt() -> str:
    skills_base = ENV["skills_base"]
    registry_path = os.path.join(skills_base, "agent-loop", "skills_registry.py")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("skills_registry", registry_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build_system_prompt()
    except Exception:
        return "You are an econometrics assistant. Help users with causal inference analysis."


def chat_with_llm_direct(task: str, data_path: Optional[str] = None) -> dict:
    """直连 LLM API（OpenAI/兼容接口），无 OpenClaw 时使用。"""
    try:
        system_prompt = build_system_prompt()
        client, model = get_llm_client()
        user_content = task
        if data_path:
            user_content += f"\n数据文件路径：{data_path}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        reply = response.choices[0].message.content

        script_cmd = None
        for block in re.findall(r"```(?:python)?\n(.*?)```", reply, re.DOTALL):
            if "python" in block and ("skills/" in block or "/app/skills/" in block):
                script_cmd = block.strip()
                break

        return {"reply": reply, "script_command": script_cmd, "model": model}
    except Exception as e:
        return {"reply": "", "error": str(e), "script_command": None, "model": None}


def chat_with_llm(task: str, session_id: Optional[str] = None,
                   data_path: Optional[str] = None, prefer_openclaw: bool = True) -> dict:
    """
    聊天入口。优先使用 OpenClaw Gateway（若可用），
    否则回退到直连 LLM API。
    """
    if prefer_openclaw and OPENCLAW_STATUS["available"]:
        sid = session_id or f"webui-{os.getpid()}"
        result = chat_via_openclaw(task, session_id=sid, data_path=data_path)
        if not result.get("error"):
            return result
        import sys
        print(f"⚠️ OpenClaw 调用失败，回退到直连模式: {result.get('error')}", file=sys.stderr)

    return chat_with_llm_direct(task, data_path)


# ─── Pydantic 模型 ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    task: str = Field(..., description="分析任务（自然语言）")
    data_path: Optional[str] = Field(None, description="数据文件路径")
    auto_execute: bool = Field(True, description="是否自动执行")
    session_id: Optional[str] = Field(None, description="会话ID（用于 OpenClaw 保持上下文）")
    prefer_openclaw: bool = Field(True, description="优先使用 OpenClaw Gateway（若可用）")


class RunRequest(BaseModel):
    skill: str = Field(..., description="技能名称")
    args: list[str] = Field(default_factory=list, description="脚本参数")


# ─── API 端点 ──────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回 Web UI 主页。"""
    tpl = os.path.join(templates_dir, "index.html")
    if os.path.exists(tpl):
        with open(tpl, encoding="utf-8") as f:
            return f.read()
    return """
    <html><head><title>OpenISClaw Web UI</title>
    <meta charset="utf-8">
    <style>
        body { font-family: system-ui; background: #0f172a; color: #f1f5f9; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .container { text-align: center; max-width: 600px; padding: 40px; }
        h1 { color: #3b82f6; font-size: 2rem; }
        p { color: #94a3b8; }
        code { background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #e879f9; }
    </style>
    <div class="container">
        <h1>🤖 OpenISClaw Web UI</h1>
        <p>Web UI 文件未找到。请确保模板文件存在于 <code>templates/index.html</code></p>
        <p>或者直接通过 API 访问：<code>GET /api/datasets</code></p>
    </div>
    </html>
    """


@app.get("/api/datasets")
async def api_list_datasets():
    return JSONResponse(list_datasets())


@app.post("/api/datasets/upload")
async def api_upload_dataset(file: UploadFile):
    data_dir = ENV["data_dir"]
    os.makedirs(data_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {ext}，支持: {ALLOWED_EXTENSIONS}")

    save_path = os.path.join(data_dir, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return JSONResponse({"success": True, "filename": file.filename, "size": os.stat(save_path).st_size})


@app.get("/api/datasets/{name}/preview")
async def api_preview_dataset(name: str, rows: int = 100):
    return JSONResponse(preview_dataset(name, rows))


@app.get("/api/results")
async def api_list_results():
    return JSONResponse(list_results())


@app.get("/api/results/{filename}")
async def api_get_result(filename: str):
    output_dir = ENV["output_dir"]
    fpath = os.path.join(output_dir, filename)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Result file not found")
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".tex", ".html", ".md"):
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        return JSONResponse({"filename": filename, "content": content, "type": ext[1:]})
    elif ext in (".png", ".jpg", ".jpeg", ".pdf"):
        return JSONResponse({"filename": filename, "url": f"/api/results/{filename}/file", "type": ext[1:]})
    else:
        with open(fpath, encoding="utf-8", errors="replace") as f:
            content = f.read()
        return JSONResponse({"filename": filename, "content": content, "type": "text"})


@app.get("/api/results/{filename}/file")
async def api_result_file(filename: str):
    output_dir = ENV["output_dir"]
    fpath = os.path.join(output_dir, filename)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="File not found")
    ext = os.path.splitext(filename)[1].lower()
    media = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "pdf": "application/pdf"}
    return FileResponse(fpath, media_type=media.get(ext, "application/octet-stream"))


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    result = chat_with_llm(
        req.task,
        session_id=req.session_id,
        data_path=req.data_path,
        prefer_openclaw=req.prefer_openclaw,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    script_cmd = result.get("script_command")
    execution_result = None
    if req.auto_execute and script_cmd:
        code_blocks = re.findall(r"```python\n(.*?)```", script_cmd, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r"```\n(.*?)```", script_cmd, re.DOTALL)
        if code_blocks:
            lines = code_blocks[0].strip().splitlines()
            if lines and lines[0].startswith("python"):
                args_str = lines[0][6:].strip()
                parts = args_str.split()
                script_path = parts[0] if parts else None
                args = parts[1:] if len(parts) > 1 else []
                if script_path:
                    def resolve(arg: str) -> str:
                        for prefix, base in [
                            ("./user_data/", ENV["data_dir"]),
                            ("./user_output/", ENV["output_dir"]),
                            ("user_data/", ENV["data_dir"]),
                            ("user_output/", ENV["output_dir"]),
                        ]:
                            if arg.startswith(prefix):
                                return arg.replace(prefix, base + "/")
                        return arg
                    execution_result = execute_script(script_path, [resolve(a) for a in args])

    return JSONResponse({
        "reply": result["reply"],
        "script_command": script_cmd,
        "execution_result": execution_result,
        "model": result.get("model"),
        "provider": result.get("provider"),
        "session_id": result.get("session_id"),
        "runner": result.get("runner"),
        "openclaw_available": OPENCLAW_STATUS["available"],
    })


@app.post("/api/run")
async def api_run(req: RunRequest):
    result = execute_script(req.skill, req.args)
    return JSONResponse(result)


@app.get("/api/skills")
async def api_list_skills():
    skills_base = ENV["skills_base"]
    registry_path = os.path.join(skills_base, "agent-loop", "skills_registry.py")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("skills_registry", registry_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return JSONResponse([
            {
                "id": key,
                "name": s["name"],
                "description": s["description"],
                "required_args": s.get("required_args", []),
                "example": s.get("example", ""),
            }
            for key, s in mod.SKILLS.items()
        ])
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/health")
async def api_health():
    missing = check_dependencies()
    oc = OPENCLAW_STATUS
    if oc["available"]:
        status = "ok (OpenClaw)" if not missing else f"degraded ({len(missing)} deps missing)"
        health_model = "via OpenClaw Gateway"
    else:
        try:
            _, model = get_llm_client()
            status = "ok" if not missing else f"degraded ({len(missing)} deps missing)"
            health_model = model
        except Exception as e:
            status = f"error: {e}"
            health_model = None
    return JSONResponse({
        "status": status,
        "model": health_model,
        "missing_deps": missing,
        "openclaw": {
            "available": oc["available"],
            "running": oc["running"],
            "port": oc["port"],
        },
        "data_dir": ENV["data_dir"],
        "output_dir": ENV["output_dir"],
        "skills_base": ENV["skills_base"],
    })


# ─── WebSocket 聊天（流式） ─────────────────────────────────────────

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            task = data.get("task", "")
            data_path = data.get("data_path")
            auto_execute = data.get("auto_execute", True)

            # 流式 LLM 响应
            try:
                system_prompt = build_system_prompt()
                client, model = get_llm_client()
                user_content = task
                if data_path:
                    user_content += f"\n数据文件路径：{data_path}"

                await websocket.send_json({"type": "status", "content": "正在连接 LLM..."})

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.3,
                    stream=True,
                )

                full_reply = ""
                for chunk in response:
                    delta = chunk.choices[0].delta.content or ""
                    full_reply += delta
                    await websocket.send_json({"type": "chunk", "content": delta})

                await websocket.send_json({"type": "done", "content": full_reply, "model": model})

            except Exception as e:
                await websocket.send_json({"type": "error", "content": str(e)})

    except WebSocketDisconnect:
        pass


# ─── 启动 ─────────────────────────────────────────────────────────

BANNER = """
╔════════════════════════════════════════════════════════════╗
║           OpenISClaw Web UI — TensorBoard 风格            ║
║            因果推断与计量分析 · 本地 Web 工作台            ║
╠════════════════════════════════════════════════════════════╣
║  访问地址:  http://localhost:{port}                         ║
║  数据目录:  {data_dir}       ║
║  输出目录:  {output_dir}     ║
║  Skills:    {skills_base}  ║
╠════════════════════════════════════════════════════════════╣
║  🤖 LLM 模式: {llm_mode:<50} ║
╚════════════════════════════════════════════════════════════╝
"""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OpenISClaw Web UI Server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    oc = OPENCLAW_STATUS
    if oc["available"]:
        llm_mode = f"OpenClaw Gateway (127.0.0.1:{oc['port']}) ✅"
    else:
        llm_mode = "Direct API (OPENAI_API_KEY required) ⚠️"

    print(BANNER.format(
        port=args.port,
        data_dir=ENV["data_dir"][:40],
        output_dir=ENV["output_dir"][:40],
        skills_base=ENV["skills_base"][:40],
        llm_mode=llm_mode,
    ))

    missing = check_dependencies()
    if missing:
        print(f"⚠️  缺少依赖: {missing}")
        print(f"   安装: pip install {' '.join(missing)}\n")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
