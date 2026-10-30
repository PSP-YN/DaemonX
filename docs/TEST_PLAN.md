# DAEMONX — Automated Test & Verification Plan

## 1. Objectives & Scope
This test plan provides comprehensive verification for all DaemonX modules to ensure safety, reliability, performance, and deterministic behavior. It fulfills the 15 required acceptance criteria defined in the master specification.

---

## 2. Testing Framework & Strategy

1. **Unit & Integration Suite**:
   - `pytest` with `pytest-asyncio`.
   - Mock ADB backend (`MockAdbBackend`) enabling fast, deterministic CI execution without requiring a physical device.
   - Dual-mode test runner:
     - Default mode: Runs all unit, model, storage, perception, and mock device tests.
     - `--hardware` mode: Targets physical hardware (Xiaomi Redmi 13 5G) when connected via USB or wireless ADB.

2. **Test Categories**:
   - **`tests/test_device.py`**: ADB command generation, device discovery, connection state, error handling, coordinates mapping, touch/swipe/input execution.
   - **`tests/test_perception.py`**: UI hierarchy XML parsing, OCR text extraction, bounds normalization, CV screen comparison.
   - **`tests/test_storage.py`**: Database migrations, CRUD operations, FTS5 full-text search, export formatting.
   - **`tests/test_tasks.py`**: DAG execution, checkpointing, pause/resume, error recovery, duplicate prevention.
   - **`tests/test_gallery.py`**: Screenshot scanning, perceptual hashing, duplicate detection, metadata extraction.
   - **`tests/test_instagram.py`**: Saved reel parsing, taxonomy classification, verification rules, safe unsave safeguards.
   - **`tests/test_cleanup.py`**: Preview generation, quarantine isolation, file restoration, deletion safety guards.
   - **`tests/test_mcp.py`**: MCP tool registration, schema validation, tool invocation over stdio.

---

## 3. Acceptance Criteria Mapping (The 15 Acceptance Tests)

| Test ID | Name | Test Function / Target | Validation Criteria |
| :--- | :--- | :--- | :--- |
| **TEST 1** | Detect Redmi 13 5G over USB | `test_device_discovery` | Correctly parses `adb devices -l` and extracts device model & serial. |
| **TEST 2** | Disconnection & Reconnection | `test_connection_recovery` | Graceful failure handling on connection drop; auto-reconnects when available. |
| **TEST 3** | Screen Capture | `test_screen_capture` | Successfully captures screen bytes and decodes into valid RGB image. |
| **TEST 4** | Text & Element Extraction | `test_perception_extraction` | Extracts visible text strings, bounds, and interactive elements from UI dump. |
| **TEST 5** | Launch App & Foreground State | `test_launch_and_verify` | Launches target package and verifies `mCurrentFocus` / top activity. |
| **TEST 6** | MCP Tool Exposure | `test_mcp_tool_listing` | MCP server advertises all typed tools across device, gallery, instagram, etc. |
| **TEST 7** | Antigravity Agent MCP Connection | `test_mcp_client_handshake` | Client can initialize session and call tools via standard stdio JSON-RPC. |
| **TEST 8** | Gemini Agent Tool Dispatch | `test_agent_reasoning_flow` | Agent interprets screen structured JSON and invokes corresponding tool. |
| **TEST 9** | Screenshot Inventory | `test_gallery_inventory` | Discovers and hashes screenshots without modifying or moving original files. |
| **TEST 10** | Database Persistence | `test_storage_persistence` | Stores extracted OCR, entities, and metadata into normalized SQLite tables. |
| **TEST 11** | FTS5 Full-Text Search | `test_fts5_search` | Sub-millisecond text search matching exact and prefix queries. |
| **TEST 12** | Task Pause & Resume | `test_task_checkpoint_resume`| Simulates abort at step N; resuming starts at step N without re-running 1..N-1. |
| **TEST 13** | Instagram Saved Inventory | `test_instagram_inventory` | Inspects saved reel stream without performing unsaving or mutating UI. |
| **TEST 14** | Reel Information Extraction | `test_instagram_extraction` | Extracts creator, caption, tags, resources, and categorizes into taxonomy. |
| **TEST 15** | Safe Cleanup & Restoration | `test_cleanup_quarantine_restore`| Previews quarantine candidates, moves to quarantine vault, verifies restoration. |
