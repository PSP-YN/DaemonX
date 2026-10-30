"""
FastAPI Backend Server for DaemonX Local Dashboard
"""
import io
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from daemonx.core.config import config, DATA_DIR
from daemonx.device.controller import DeviceController
from daemonx.device.mock_backend import MockAdbBackend
from daemonx.storage.database import Database
from daemonx.tasks.engine import TaskEngine
from daemonx.cleanup.vault import QuarantineVault
from daemonx.skills.registry import SkillRegistry


STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(title="DaemonX Local Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine Singletons
db = Database(config.storage.database_path)
controller = DeviceController()
if not controller.get_devices():
    controller.use_mock(MockAdbBackend())

task_engine = TaskEngine(db=db)
quarantine_vault = QuarantineVault(db=db, vault_dir=config.quarantine_dir)
skill_registry = SkillRegistry()


class TapRequest(BaseModel):
    x: int
    y: int


class SwipeRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    duration_ms: int = 300


class KeyRequest(BaseModel):
    key: str  # 'back', 'home'


class TaskCreateRequest(BaseModel):
    workflow_name: str
    initial_data: dict[str, Any] = {}


class QuarantineRequest(BaseModel):
    media_id: str
    approved: bool = True


@app.get("/api/status")
def get_status():
    devices = controller.get_devices()
    active_dev = controller.get_device_status() if devices else None

    with db.get_connection() as conn:
        media_count = conn.execute("SELECT COUNT(*) as cnt FROM media_items").fetchone()["cnt"]
        processed_count = conn.execute("SELECT COUNT(*) as cnt FROM media_items WHERE status = 'processed'").fetchone()["cnt"]
        resource_count = conn.execute("SELECT COUNT(*) as cnt FROM resources").fetchone()["cnt"]
        job_count = conn.execute("SELECT COUNT(*) as cnt FROM processing_jobs").fetchone()["cnt"]

    return {
        "status": "online",
        "device": active_dev.model_dump() if active_dev else None,
        "device_count": len(devices),
        "database": {
            "total_media": media_count,
            "processed_media": processed_count,
            "resources": resource_count,
            "total_jobs": job_count
        }
    }


@app.get("/api/devices")
def get_devices():
    return [d.model_dump() for d in controller.get_devices()]


@app.get("/api/screen")
def get_screen():
    img = controller.capture_screenshot()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/action/tap")
def action_tap(req: TapRequest):
    success = controller.tap(req.x, req.y)
    return {"success": success, "x": req.x, "y": req.y}


@app.post("/api/action/swipe")
def action_swipe(req: SwipeRequest):
    success = controller.swipe(req.x1, req.y1, req.x2, req.y2, req.duration_ms)
    return {"success": success}


@app.post("/api/action/key")
def action_key(req: KeyRequest):
    if req.key.lower() == "back":
        success = controller.press_back()
    elif req.key.lower() == "home":
        success = controller.press_home()
    else:
        raise HTTPException(status_code=400, detail="Invalid key")
    return {"success": success, "key": req.key}


@app.get("/api/search")
def search(q: str = "", limit: int = 50):
    if not q:
        return []
    return db.search(q, limit=limit)


@app.get("/api/jobs")
def get_jobs():
    return db.list_jobs(limit=50)


@app.get("/api/cleanup/preview")
def get_cleanup_preview():
    return quarantine_vault.generate_preview().model_dump()


@app.post("/api/cleanup/quarantine")
def post_quarantine(req: QuarantineRequest):
    path = quarantine_vault.quarantine_file(req.media_id, approved=req.approved)
    return {"quarantined": True, "vault_path": path}


@app.post("/api/cleanup/restore")
def post_restore(req: QuarantineRequest):
    orig = quarantine_vault.restore_file(req.media_id)
    return {"restored": True, "original_path": orig}


@app.get("/api/skills")
def get_skills():
    return [s.model_dump() for s in skill_registry.list_skills()]


@app.get("/api/export")
def export(format: str = "json"):
    content = db.export_knowledge(format=format)
    media_type = "application/json" if format == "json" else "text/plain"
    return Response(content=content, media_type=media_type)


# Mount static assets
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
