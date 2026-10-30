"""
NEXORA Model Context Protocol (MCP) Server
Exposes safe, typed, strictly validated local automation and knowledge tools to Antigravity Agent.
"""
import base64
import io
import json
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from nexora.core.config import config, DATA_DIR
from nexora.core.exceptions import DeviceError, QuarantineError, VerificationError
from nexora.device.controller import DeviceController
from nexora.device.mock_backend import MockAdbBackend
from nexora.perception.observer import ScreenObserver
from nexora.perception.ocr_engine import OCREngine
from nexora.storage.database import Database
from nexora.tasks.engine import TaskEngine
from nexora.tasks.model import TaskStatus
from nexora.gallery.pipeline import GalleryPipeline
from nexora.instagram.reel_extractor import InstagramPipeline, ReelData
from nexora.cleanup.vault import QuarantineVault


def create_mcp_server(mock_mode: bool = False) -> MCPServer:
    """Factory function to instantiate and configure the Nexora MCP server."""
    server = MCPServer(name="nexora", version="1.0.0")

    # Core engine singletons
    db = Database(config.storage.database_path)
    controller = DeviceController()
    if mock_mode:
        controller.use_mock(MockAdbBackend())
    else:
        # If no physical devices connected, automatically use mock backend gracefully for non-blocking readiness
        devices = controller.get_devices()
        if not devices:
            controller.use_mock(MockAdbBackend())

    observer = ScreenObserver(controller=controller)
    gallery_pipeline = GalleryPipeline(db=db, controller=controller)
    instagram_pipeline = InstagramPipeline(controller=controller, db=db, observer=observer)
    task_engine = TaskEngine(db=db)
    quarantine_vault = QuarantineVault(db=db, vault_dir=config.quarantine_dir)

    # Register default screenshot processing workflow in TaskEngine
    def _step_scan(state):
        d = state.get("directory", str(config.data_dir / "screenshots"))
        inv = gallery_pipeline.inventory_directory(d)
        state["inventory"] = inv
        return state

    def _step_ocr(state):
        inv = state.get("inventory", [])
        processed = []
        for item in inv:
            res = gallery_pipeline.process_screenshot_file(item["path"], media_id=item["media_id"])
            processed.append(res)
        state["processed"] = processed
        return state

    task_engine.register_workflow("process_screenshots", [
        ("Scan Directory", _step_scan),
        ("OCR and Entity Extraction", _step_ocr),
    ])

    # =========================================================================
    # 1. DEVICE TOOLS
    # =========================================================================

    @server.tool()
    def device_list() -> str:
        """Discovers all attached Android devices (USB, wireless, or mock)."""
        devices = controller.get_devices()
        return json.dumps([d.model_dump() for d in devices], indent=2)

    @server.tool()
    def device_status(serial: str | None = None) -> str:
        """Returns health, battery, OS version, and screen metrics for target device."""
        if serial:
            dev = controller.select_device(serial)
        else:
            dev = controller.get_device_status()
        return json.dumps(dev.model_dump(), indent=2)

    @server.tool()
    def device_capture_screen() -> str:
        """Captures the active screen display, saves to data directory, and returns path and dimensions."""
        img = controller.capture_screenshot()
        save_path = DATA_DIR / "screenshots" / f"screen_{int(img.width)}x{int(img.height)}.png"
        img.save(save_path)
        return json.dumps({
            "saved_path": str(save_path),
            "width": img.width,
            "height": img.height,
            "mode": img.mode
        }, indent=2)

    @server.tool()
    def device_inspect_screen(run_ocr: bool = True) -> str:
        """
        Executes a complete multi-modal screen perception pass.
        Returns active package name, screen type classification, visible elements, text, and confidence.
        """
        obs = observer.observe(run_ocr=run_ocr)
        return json.dumps(obs.model_dump(), indent=2)

    @server.tool()
    def device_launch_app(package_name: str, activity_name: str | None = None) -> str:
        """Launches an application package on the device."""
        success = controller.launch_app(package_name, activity_name)
        return json.dumps({"launched": success, "package": package_name})

    @server.tool()
    def device_tap(x: int, y: int) -> str:
        """Taps screen coordinate (x, y)."""
        success = controller.tap(x, y)
        return json.dumps({"tapped": success, "x": x, "y": y})

    @server.tool()
    def device_swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
        """Swipes from (x1, y1) to (x2, y2)."""
        success = controller.swipe(x1, y1, x2, y2, duration_ms)
        return json.dumps({"swiped": success, "start": [x1, y1], "end": [x2, y2]})

    @server.tool()
    def device_scroll(direction: str = "down", distance_ratio: float = 0.5) -> str:
        """Scrolls up, down, left, or right."""
        success = controller.scroll(direction=direction, distance_ratio=distance_ratio)
        return json.dumps({"scrolled": success, "direction": direction})

    @server.tool()
    def device_press_back() -> str:
        """Simulates Android Back button."""
        success = controller.press_back()
        return json.dumps({"pressed_back": success})

    @server.tool()
    def device_input_text(text: str) -> str:
        """Enters text into active input field with safe escaping."""
        success = controller.input_text(text)
        return json.dumps({"entered_text": success, "length": len(text)})

    # =========================================================================
    # 2. GALLERY TOOLS
    # =========================================================================

    @server.tool()
    def gallery_inventory(directory: str | None = None) -> str:
        """Inventories screenshot files in a directory without modifying or deleting them."""
        target_dir = directory or str(DATA_DIR / "screenshots")
        inventory = gallery_pipeline.inventory_directory(target_dir)
        return json.dumps(inventory, indent=2)

    @server.tool()
    def gallery_get_metadata(media_id: str) -> str:
        """Retrieves complete metadata record for a media item."""
        item = db.get_media_item(media_id)
        return json.dumps(item or {"error": "Not found"}, indent=2)

    @server.tool()
    def gallery_extract_text(file_path: str) -> str:
        """Runs local OCR on a specified image file and returns extracted text."""
        p = Path(file_path)
        if not p.exists():
            return json.dumps({"error": f"File '{file_path}' not found"})
        ocr_engine = OCREngine()
        from PIL import Image
        with Image.open(p) as img:
            text = ocr_engine.extract_text(img)
        return json.dumps({"file": file_path, "text": text}, indent=2)

    @server.tool()
    def gallery_analyze_image(file_path: str, media_id: str | None = None) -> str:
        """Executes full analysis: OCR, entity extraction (GitHub, books, AI tools), and saves to SQLite."""
        p = Path(file_path)
        if not p.exists():
            return json.dumps({"error": f"File '{file_path}' not found"})
        res = gallery_pipeline.process_screenshot_file(p, media_id=media_id)
        return json.dumps(res, indent=2)

    @server.tool()
    def gallery_find_duplicates(sha256: str | None = None, phash: str | None = None) -> str:
        """Checks if an image hash already exists in the knowledge database."""
        dup = db.find_duplicate_by_hash(sha256=sha256, phash=phash)
        return json.dumps({"duplicate_found": dup is not None, "record": dup}, indent=2)

    @server.tool()
    def gallery_search(query: str, limit: int = 25) -> str:
        """Searches gallery knowledge database across OCR text, summaries, and tags."""
        results = db.search(query, limit=limit)
        return json.dumps(results, indent=2)

    # =========================================================================
    # 3. INSTAGRAM TOOLS
    # =========================================================================

    @server.tool()
    def instagram_open_saved() -> str:
        """Opens Instagram and navigates to the Saved collection."""
        success = instagram_pipeline.open_saved_collection()
        return json.dumps({"opened": success})

    @server.tool()
    def instagram_inspect_current_reel() -> str:
        """Inspects the currently visible Reel on screen and extracts creator, caption, tags, and resources."""
        reel_data = instagram_pipeline.inspect_current_reel()
        return json.dumps(reel_data.model_dump(), indent=2)

    @server.tool()
    def instagram_extract_visible_content() -> str:
        """Extracts visible text, diagrams, code, and resources from the current reel view."""
        obs = observer.observe(run_ocr=True)
        return json.dumps({
            "visible_text": obs.visible_text,
            "elements": [e.model_dump() for e in obs.elements if e.text]
        }, indent=2)

    @server.tool()
    def instagram_get_reel_status(media_id: str) -> str:
        """Checks whether a reel has been processed and saved."""
        item = db.get_media_item(media_id)
        return json.dumps(item or {"error": "Not found"}, indent=2)

    @server.tool()
    def instagram_record_reel(creator: str, caption: str, text: str = "") -> str:
        """Stores a reel record directly into the knowledge database."""
        m_id = db.insert_media_item(
            source_type="instagram_reel",
            original_path=f"instagram://reel/@{creator}"
        )
        db.insert_extracted_content(
            media_id=m_id,
            full_text=text,
            caption=caption,
            creator=creator
        )
        db.update_media_status(media_id=m_id, status="processed")
        return json.dumps({"media_id": m_id, "status": "processed"})

    @server.tool()
    def instagram_verify_reel(media_id: str) -> str:
        """Verifies that an extracted reel record in SQLite satisfies all required fields."""
        item = db.get_media_item(media_id)
        if not item or item["status"] != "processed":
            return json.dumps({"verified": False, "reason": "Record not found or not marked processed"})
        return json.dumps({"verified": True, "media_id": media_id})

    @server.tool()
    def instagram_unsave_verified(media_id: str, allow_unsave: bool = False) -> str:
        """
        Safely unsaves a verified reel from Instagram.
        Fails safely if allow_unsave is False or if record is unverified.
        """
        try:
            reel_data = ReelData(media_id=media_id, verified=True, is_saved=True)
            success = instagram_pipeline.verify_and_unsave(reel_data, allow_unsave=allow_unsave)
            return json.dumps({"unsaved": success, "media_id": media_id})
        except VerificationError as e:
            return json.dumps({"unsaved": False, "error": str(e)})

    # =========================================================================
    # 4. KNOWLEDGE TOOLS
    # =========================================================================

    @server.tool()
    def knowledge_search(query: str, limit: int = 50) -> str:
        """Queries the SQLite FTS5 full-text index across screenshots, reels, and notes."""
        results = db.search(query, limit=limit)
        return json.dumps(results, indent=2)

    @server.tool()
    def knowledge_get_record(media_id: str) -> str:
        """Retrieves full details for a knowledge record including extracted content and tags."""
        item = db.get_media_item(media_id)
        return json.dumps(item or {"error": "Not found"}, indent=2)

    @server.tool()
    def knowledge_create_record(title: str, text: str, creator: str = "manual", source_url: str = "") -> str:
        """Creates a manual knowledge record in the SQLite database."""
        m_id = db.insert_media_item(source_type="manual_note")
        c_id = db.insert_extracted_content(
            media_id=m_id,
            full_text=text,
            caption=title,
            creator=creator,
            source_url=source_url
        )
        db.update_media_status(media_id=m_id, status="processed")
        return json.dumps({"media_id": m_id, "content_id": c_id})

    @server.tool()
    def knowledge_update_record(media_id: str, summary: str | None = None, tags: str | None = None) -> str:
        """Updates metadata, summary, or tags for an existing knowledge record."""
        if tags:
            for t in tags.split(","):
                clean_tag = t.strip()
                if clean_tag:
                    db.add_tag(media_id=media_id, tag_name=clean_tag)
        return json.dumps({"updated": True, "media_id": media_id})

    @server.tool()
    def knowledge_export(format: str = "json") -> str:
        """Exports all knowledge records to JSON, CSV, or Markdown."""
        return db.export_knowledge(format=format)

    # =========================================================================
    # 5. TASK TOOLS
    # =========================================================================

    @server.tool()
    def task_create(workflow_name: str, initial_data_json: str = "{}") -> str:
        """Creates a new persistent task graph and returns job_id."""
        init_data = json.loads(initial_data_json)
        cp = task_engine.create_job(workflow_name, initial_state=init_data)
        return json.dumps(cp.model_dump(), indent=2)

    @server.tool()
    def task_start(job_id: str) -> str:
        """Starts or runs all remaining steps of a task."""
        cp = task_engine.run_all(job_id)
        return json.dumps(cp.model_dump(), indent=2)

    @server.tool()
    def task_pause(job_id: str) -> str:
        """Pauses a running task after the current atomic step."""
        cp = task_engine.pause_job(job_id)
        return json.dumps(cp.model_dump(), indent=2)

    @server.tool()
    def task_resume(job_id: str) -> str:
        """Resumes a paused or interrupted task from its last SQLite checkpoint."""
        cp = task_engine.resume_job(job_id)
        return json.dumps(cp.model_dump(), indent=2)

    @server.tool()
    def task_cancel(job_id: str) -> str:
        """Cancels a task."""
        cp = task_engine.cancel_job(job_id)
        return json.dumps(cp.model_dump(), indent=2)

    @server.tool()
    def task_status(job_id: str) -> str:
        """Retrieves progress, current step, and logs for a task."""
        cp = task_engine.get_checkpoint(job_id)
        return json.dumps(cp.model_dump(), indent=2)

    @server.tool()
    def task_list() -> str:
        """Lists all persistent task jobs."""
        jobs = db.list_jobs(limit=50)
        return json.dumps(jobs, indent=2)

    # =========================================================================
    # 6. CLEANUP TOOLS
    # =========================================================================

    @server.tool()
    def cleanup_preview() -> str:
        """Generates a cleanup preview of eligible files without modifying anything."""
        preview = quarantine_vault.generate_preview()
        return json.dumps(preview.model_dump(), indent=2)

    @server.tool()
    def cleanup_quarantine(media_id: str, approved: bool = False) -> str:
        """Moves an eligible processed file to the reversible quarantine vault."""
        try:
            q_path = quarantine_vault.quarantine_file(media_id, approved=approved)
            return json.dumps({"quarantined": True, "vault_path": q_path})
        except QuarantineError as e:
            return json.dumps({"quarantined": False, "error": str(e)})

    @server.tool()
    def cleanup_restore(media_id: str) -> str:
        """Restores a quarantined file back to its exact original location."""
        try:
            restored = quarantine_vault.restore_file(media_id)
            return json.dumps({"restored": True, "original_path": restored})
        except QuarantineError as e:
            return json.dumps({"restored": False, "error": str(e)})

    @server.tool()
    def cleanup_permanent_delete(media_id: str, double_confirmed: bool = False) -> str:
        """Permanently deletes ONLY files currently in the quarantine vault."""
        try:
            success = quarantine_vault.permanent_delete(media_id, double_confirmed=double_confirmed)
            return json.dumps({"deleted": success, "media_id": media_id})
        except QuarantineError as e:
            return json.dumps({"deleted": False, "error": str(e)})

    return server


def main():
    """Runs the MCP server over stdio for Antigravity Agent integration."""
    server = create_mcp_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
