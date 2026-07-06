import json
import os
import pathlib
import threading
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph import run_agent
from agent.status import reset_status

# Ensure directories exist
PROJECT_ROOT = pathlib.Path("generated_project")
PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Lovable Clone Server")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generation_thread = None
current_prompt = None

class GenerateRequest(BaseModel):
    prompt: str

@app.post("/api/generate")
def generate_app(req: GenerateRequest):
    global generation_thread, current_prompt
    prompt = req.prompt
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    if generation_thread and generation_thread.is_alive():
        raise HTTPException(status_code=400, detail="A generation is already in progress.")
    
    current_prompt = prompt
    
    # Initialize project root fresh on a new prompt
    if not PROJECT_ROOT.exists():
        PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    
    def bg_run():
        try:
            run_agent(prompt)
        except Exception as e:
            print(f"Error in bg_run agent: {e}")
            
    generation_thread = threading.Thread(target=bg_run, daemon=True)
    generation_thread.start()
    return {"status": "success", "message": "Generation started."}

@app.get("/api/status")
def get_status():
    status_path = pathlib.Path(".agent_status.json")
    logs_path = pathlib.Path(".agent_logs.txt")
    
    status_data = {"phase": "idle", "message": "Ready", "done": False}
    if status_path.exists():
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                status_data = json.load(f)
        except Exception:
            pass
            
    logs = ""
    if logs_path.exists():
        try:
            with open(logs_path, "r", encoding="utf-8") as f:
                logs = f.read()
        except Exception:
            pass
            
    is_running = generation_thread is not None and generation_thread.is_alive()
    status_data["is_running"] = is_running
    status_data["logs"] = logs
    status_data["current_prompt"] = current_prompt
    return status_data

@app.get("/api/files")
def get_files():
    if not PROJECT_ROOT.exists():
        return []
        
    def get_tree(p: pathlib.Path):
        result = []
        for item in p.iterdir():
            if item.name in [".git", "__pycache__", "node_modules", ".venv"]:
                continue
            rel_path = str(item.relative_to(PROJECT_ROOT)).replace("\\", "/")
            if item.is_dir():
                result.append({
                    "name": item.name,
                    "type": "directory",
                    "path": rel_path,
                    "children": get_tree(item)
                })
            else:
                result.append({
                    "name": item.name,
                    "type": "file",
                    "path": rel_path
                })
        result.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
        return result
        
    return get_tree(PROJECT_ROOT)

@app.get("/api/file")
def get_file_content(path: str):
    base = PROJECT_ROOT.resolve()
    target = (base / path).resolve()
    
    # Safety checks
    if base not in target.parents and base != target:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SaveFileRequest(BaseModel):
    path: str
    content: str

@app.post("/api/save-file")
def save_file(req: SaveFileRequest):
    base = PROJECT_ROOT.resolve()
    target = (base / req.path).resolve()
    
    if base not in target.parents and base != target:
        raise HTTPException(status_code=403, detail="Access denied")
        
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "message": f"Saved {req.path}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serving UI
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    ui_path = pathlib.Path("dashboard_assets/index.html")
    if not ui_path.exists():
        return """
        <html>
            <body style="font-family: sans-serif; background: #0f0c1b; color: white; display: flex; align-items: center; justify-content: center; height: 100vh;">
                <div>
                    <h1>Lovable Clone Server is Running</h1>
                    <p>Dashboard UI template not found at <code>dashboard_assets/index.html</code> yet.</p>
                </div>
            </body>
        </html>
        """
    with open(ui_path, "r", encoding="utf-8") as f:
        return f.read()

# Register the preview static files AFTER API endpoints to avoid conflict, mount it at /preview
app.mount("/preview", StaticFiles(directory="generated_project", html=True), name="preview")
