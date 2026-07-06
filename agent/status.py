import json
import os
import pathlib

STATUS_FILE = pathlib.Path.cwd() / ".agent_status.json"
LOG_FILE = pathlib.Path.cwd() / ".agent_logs.txt"

def reset_status():
    if STATUS_FILE.exists():
        try:
            STATUS_FILE.unlink()
        except Exception:
            pass
    if LOG_FILE.exists():
        try:
            LOG_FILE.unlink()
        except Exception:
            pass
    update_status("idle", "Ready", done=False)

def update_status(phase, message, plan=None, task_plan=None, current_step=0, total_steps=0, error=None, done=False):
    status = {
        "phase": phase,
        "message": message,
        "current_step": current_step,
        "total_steps": total_steps,
        "error": error,
        "done": done
    }
    if plan:
        # plan is a Plan BaseModel
        status["plan"] = plan if isinstance(plan, dict) else plan.model_dump()
    if task_plan:
        # task_plan is a TaskPlan BaseModel
        status["task_plan"] = task_plan if isinstance(task_plan, dict) else task_plan.model_dump()
        
    # Read existing status to keep plan/task_plan if not provided
    if STATUS_FILE.exists() and (plan is None or task_plan is None):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                old_status = json.load(f)
                if plan is None and "plan" in old_status:
                    status["plan"] = old_status["plan"]
                if task_plan is None and "task_plan" in old_status:
                    status["task_plan"] = old_status["task_plan"]
        except Exception:
            pass

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    
    add_log(f"[{phase.upper()}] {message}")

def add_log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")
