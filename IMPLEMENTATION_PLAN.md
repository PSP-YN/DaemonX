# NEXORA — Phased Implementation Plan

This implementation plan defines the phased rollout of Nexora across 10 sequential phases, adhering strictly to the specifications.

---

## Phase Breakdown

### Phase 0: Environment Audit & System Blueprint (Completed)
- Inspect host Fedora 44, Python 3.12/3.14, OpenJDK 17, ADB, Tesseract 5.5, SQLite FTS5.
- Audit Antigravity IDE and standalone Agent MCP configurations.
- Verify connected devices and setup fallback Mock ADB and AVD test harness.
- Deliver `ENVIRONMENT_AUDIT.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_PLAN.md`, `TEST_PLAN.md`.

### Phase 1: ADB Device Connection & Low-Level Device Control
- **Components**:
  - `nexora/device/adb_client.py`: High-performance ADB subprocessing with timeout, exit code validation, and device targeting (`-s <serial>`).
  - `nexora/device/controller.py`: `DeviceController` class implementing discovery, USB/wireless connectivity, touch input, coordinate mapping, app management, and file transfer.
  - `nexora/device/mock_backend.py`: High-fidelity mock ADB simulator for reproducible headless unit and integration testing.
- **Verification**: Device discovery, command execution, error recovery when device drops.

### Phase 2: Screenshot Capture, OCR & UI Perception Engine
- **Components**:
  - `nexora/perception/screen_capture.py`: Raw framebuffer and `screencap -p` stream decoding into PIL/NumPy images.
  - `nexora/perception/ocr_engine.py`: Tesseract 5.5 wrapper extracting word bounds, text strings, and confidence metrics.
  - `nexora/perception/ui_hierarchy.py`: `uiautomator dump` XML parser extracting semantic hierarchy trees and bounding boxes.
  - `nexora/perception/cv_matcher.py`: OpenCV template matching, color difference, and visual change detection.
  - `nexora/perception/observer.py`: Unified `ScreenObserver` combining XML, OCR, and CV into structured `ScreenObservation`.
- **Verification**: Parsing sample Android screens, extracting structured JSON element lists, sub-second OCR throughput.

### Phase 3: MCP Server & Antigravity Agent Integration
- **Components**:
  - `nexora/mcp/server.py`: Standard stdio MCP Server exposing typed tools.
  - `nexora/mcp/tools_device.py`: `device_list`, `device_status`, `device_capture_screen`, `device_tap`, etc.
  - `nexora/mcp/tools_gallery.py`: `gallery_inventory`, `gallery_analyze_image`, etc.
  - `nexora/mcp/tools_instagram.py`: `instagram_open_saved`, `instagram_inspect_current_reel`, etc.
  - `nexora/mcp/tools_knowledge.py`: `knowledge_search`, `knowledge_create_record`, etc.
  - `nexora/mcp/tools_task.py`: `task_create`, `task_status`, etc.
  - `nexora/mcp/tools_cleanup.py`: `cleanup_preview`, `cleanup_quarantine`, etc.
  - Automatic registration in `/home/psp/.gemini/config/mcp_config.json` and IDE config.
- **Verification**: MCP protocol test suite (tool listing, schema validation, simulated tool calls).

### Phase 4: Task Engine, Checkpoints & Recovery
- **Components**:
  - `nexora/tasks/model.py`: Task, Step, State, and Checkpoint schemas.
  - `nexora/tasks/engine.py`: Persistent task executor with SQLite state storage, retry logic, error classification, and cancellation.
  - `nexora/tasks/recovery.py`: Automatic recovery after process restart or connection drop.
- **Verification**: Execution of multi-step graphs, simulated disconnection midway, successful resume without duplicate work.

### Phase 5: SQLite Knowledge Database & FTS5 Search
- **Components**:
  - `nexora/storage/schema.py`: Database DDL for normalized tables and FTS5 virtual tables.
  - `nexora/storage/database.py`: Thread-safe database connection pool, migrations, CRUD operations.
  - `nexora/storage/search.py`: High-speed full-text search, filtering by tags, dates, authors, and categories.
  - `nexora/storage/export.py`: Export to JSON, CSV, and Markdown.
- **Verification**: Schema initialization, insert benchmarking, FTS5 query correctness, export tests.

### Phase 6: Screenshot Inventory & Entity Intelligence
- **Components**:
  - `nexora/gallery/scanner.py`: Recursive Android filesystem scanner for screenshot discovery.
  - `nexora/gallery/hasher.py`: Perceptual hashing (pHash/dHash) and SHA-256 duplicate detection.
  - `nexora/gallery/extractor.py`: Regex and NER entity extraction (URLs, emails, phone numbers, code snippets).
  - `nexora/gallery/pipeline.py`: End-to-end processing pipeline orchestrating scan -> OCR -> entity extraction -> DB record.
- **Verification**: Processing sample test screenshots, zero data loss, duplicate deduplication.

### Phase 7: Instagram Saved Reel Intelligence
- **Components**:
  - `nexora/instagram/navigator.py`: Safe UI navigation to Saved collections and Reels viewer.
  - `nexora/instagram/extractor.py`: Extracting creator, caption, hashtags, displayed text, and audio info.
  - `nexora/instagram/classifier.py`: 22-category taxonomy classification and tag assignment.
  - `nexora/instagram/verifier.py`: Verification checks before unsaving.
- **Verification**: UI parsing of Instagram Reel view, extraction validation, rejection of unverified deletions.

### Phase 8: Resource, GitHub, Claude Skill & Book Extraction
- **Components**:
  - `nexora/knowledge/enrichment.py`: Extraction of GitHub repo URLs, owner/repo parsing, Claude skills, and book details.
  - Dedicated storage tables linking resources to media items.
- **Verification**: Correct parsing of markdown/OCR snippets containing repo URLs and books.

### Phase 9: Safe Cleanup & Quarantine Engine
- **Components**:
  - `nexora/cleanup/vault.py`: Quarantine directory management on host with reverse mapping.
  - `nexora/cleanup/preview.py`: Generating structured cleanup previews with checksums and status checks.
  - `nexora/cleanup/executor.py`: Safe move-to-quarantine and one-click restoration.
- **Verification**: Preview generation, quarantine isolation, file restoration test, prevention of unverified deletions.

### Phase 10: Modern Local Dashboard & Startup Tooling
- **Components**:
  - `nexora/dashboard/app.py`: FastAPI server serving REST APIs and static dashboard UI.
  - `nexora/dashboard/static/`: Vanilla HTML5/CSS3/JavaScript single-page app with live device preview, task runner, and library search.
  - `scripts/start.sh`, `scripts/doctor.sh`, `scripts/test.sh`.
- **Verification**: End-to-end execution, doctor self-diagnosis, complete test suite passing.
