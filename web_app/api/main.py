import asyncio
import os
import sys
import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScriptRequest(BaseModel):
    stage: str

# Global log buffer to store recent logs for new connections
log_buffer: List[str] = []
# Global set of connected clients
clients: List[WebSocket] = []

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts", "pipeline")

STAGE_MAP = {
    "1": "01_selection.py",
    "2": "02_curation.py",
    "3": "03_analysis.py",
    "4": "04_export.py"
}

async def broadcast_log(message: str):
    """Send log message to all connected clients."""
    print(message, end="") # Print to server stdout as well
    log_buffer.append(message)
    # Keep buffer size reasonable
    if len(log_buffer) > 1000:
        log_buffer.pop(0)
        
    for client in clients:
        try:
            await client.send_text(message)
        except:
            # Handle disconnected clients later
            pass

async def run_script(script_name: str):
    """Run a script and stream its output."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    await broadcast_log(f"\n\n\u001b[1;36m=== STARTING {script_name} ===\u001b[0m\n")
    
    # Use unbuffered output for python
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = BASE_DIR
    
    # Use the specific venv python interpreter as requested
    venv_python = os.path.join(BASE_DIR, "venv", "bin", "python")
    
    process = await asyncio.create_subprocess_exec(
        venv_python, script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=BASE_DIR, # Run from root
        env=env
    )

    if process.stdout:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await broadcast_log(line.decode())

    await process.wait()
    if process.returncode == 0:
        await broadcast_log(f"\n\u001b[1;32m=== FINISHED {script_name} (Success) ===\u001b[0m\n")
    else:
        await broadcast_log(f"\n\u001b[1;31m=== FINISHED {script_name} (Failed: {process.returncode}) ===\u001b[0m\n")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/run/{stage}")
async def run_stage(stage: str):
    if stage not in STAGE_MAP:
        return {"error": "Invalid stage"}
    
    script_name = STAGE_MAP[stage]
    # Fire and forget (run in background)
    asyncio.create_task(run_script(script_name))
    return {"status": "started", "script": script_name}

@app.post("/api/run-all")
async def run_all():
    async def run_sequence():
        for stage in ["1", "2", "3", "4"]:
            await run_script(STAGE_MAP[stage])
            
    asyncio.create_task(run_sequence())
    asyncio.create_task(run_sequence())
    return {"status": "started_sequence"}

# --- Config Management ---
@app.get("/api/config")
async def get_config():
    config_path = os.path.join(BASE_DIR, "config", "mobility.yaml")
    if os.path.exists(config_path):
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

class ConfigUpdate(BaseModel):
    sources: List[str]
    trust_list: List[str]
    block_list: List[str]

@app.post("/api/config")
async def update_config(data: ConfigUpdate):
    config_path = os.path.join(BASE_DIR, "config", "mobility.yaml")
    import yaml
    
    # Read existing to preserve comments/structure if possible? 
    # PyYAML safe_dump wipes comments. For now, simple dump is acceptable for this level of UI.
    # To preserve, we'd need round-trip parser like 'ruamel.yaml'. 
    # User just wants function.
    
    # Load current to preserve other fields like 'domain_name'
    current = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            current = yaml.safe_load(f) or {}
            
    current['sources'] = data.sources
    
    # Update reputation
    if 'reputation' not in current:
        current['reputation'] = {}
        
    current['reputation']['trust_list'] = data.trust_list
    current['reputation']['block_list'] = data.block_list
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(current, f, allow_unicode=True, default_flow_style=False)
        
    return {"status": "updated"}

# --- Curation ---
@app.get("/api/curation/candidates")
async def get_candidates():
    # Load latest Items from Stage 1
    # Check data/daily/YYYY-MM-DD/1_selected_ranked.json
    # Find latest date
    data_dir = os.path.join(BASE_DIR, "data", "daily")
    if not os.path.exists(data_dir):
        return []
    
    dates = sorted(os.listdir(data_dir), reverse=True)
    if not dates:
        return []
        
    latest_date = dates[0]
    file_path = os.path.join(data_dir, latest_date, "1_selected_ranked.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return {"date": latest_date, "items": json.load(f)}
            
    return {"date": latest_date, "items": []}

class CurationItem(BaseModel):
    id: str
    title: str
    content: str
    url: str
    source: str
    published_at: str

class CurationPayload(BaseModel):
    date: str
    items: List[dict] # Full object to save

@app.post("/api/curation/save")
async def save_curation(payload: CurationPayload):
    # Save to 2_curated.json
    target_dir = os.path.join(BASE_DIR, "data", "daily", payload.date)
    os.makedirs(target_dir, exist_ok=True)
    
    save_path = os.path.join(target_dir, "2_curated.json")
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(payload.items, f, indent=4, ensure_ascii=False)
        
    await broadcast_log(f"\n\u001b[1;32m=== Curation Saved ({len(payload.items)} items) ===\u001b[0m\n")
    
    # Trigger Auto-Training
    # We can run it as a script task
    await broadcast_log(f"\u001b[1;36m=== Triggering Auto-Training (Active Learning) ===\u001b[0m\n")
    
    # Run tools/train_irl.py
    script_path = os.path.join(BASE_DIR, "scripts", "tools", "train_irl.py")
    
    # Non-blocking run
    asyncio.create_task(run_custom_script(script_path))
    
    return {"status": "saved_and_training"}

async def run_custom_script(script_path):
    # Re-use run logic but for specific path
    venv_python = os.path.join(BASE_DIR, "venv", "bin", "python")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = BASE_DIR
    
    process = await asyncio.create_subprocess_exec(
        venv_python, script_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=BASE_DIR,
        env=env
    )
    
    if process.stdout:
        while True:
            line = await process.stdout.readline()
            if not line: break
            await broadcast_log(line.decode())
    await process.wait()

@app.websocket("/api/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        # Send history
        for log in log_buffer:
            await websocket.send_text(log)
            
        while True:
            # Just keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.get("/api/history")
async def get_history_list():
    data_dir = os.path.join(BASE_DIR, "data", "daily")
    if not os.path.exists(data_dir):
        return []
    dates = sorted(os.listdir(data_dir), reverse=True)
    return dates

@app.get("/api/results/{date_str}")
async def get_results(date_str: str):
    data_dir = os.path.join(BASE_DIR, "data", "daily")
    if not os.path.exists(data_dir):
        return {"error": "No data directory found"}
        
    dates = sorted(os.listdir(data_dir), reverse=True)
    if not dates:
        return {"error": "No daily data found"}
        
    if date_str == "latest":
        target_date = dates[0]
    else:
        target_date = date_str
        
    target_dir = os.path.join(data_dir, target_date)
    if not os.path.exists(target_dir):
         return {"error": f"No data found for {target_date}"}
    
    results = {
        "date": target_date,
        "selected": None,
        "analyzed": None,
        "report": None
    }
    
    # 1. Selected Items (Stage 1)
    sel_path = os.path.join(target_dir, "1_selected.json")
    if os.path.exists(sel_path):
        with open(sel_path, 'r', encoding='utf-8') as f:
            try: results["selected"] = json.load(f)
            except: pass
            
    # 3. Analyzed Items (Stage 3)
    ana_path = os.path.join(target_dir, "3_analyzed.json")
    if os.path.exists(ana_path):
        with open(ana_path, 'r', encoding='utf-8') as f:
             try: results["analyzed"] = json.load(f)
             except: pass

    # 4. Final Report (Stage 4)
    rep_path = os.path.join(target_dir, "4_report.md")
    if os.path.exists(rep_path):
        with open(rep_path, 'r', encoding='utf-8') as f:
            results["report"] = f.read()
            
    return results

# Serve the UI
# Ensure the directory exists
ui_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
if os.path.exists(ui_dir):
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
