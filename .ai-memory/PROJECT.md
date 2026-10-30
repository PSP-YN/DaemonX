# DAEMONX — Project Memory

## Summary
DaemonX is a production-grade, modular Android automation and personal knowledge intelligence platform controlled from Linux (tested on Fedora Linux) through Antigravity Agent. It features deterministic local execution (ADB, Tesseract 5.5, OpenCV, SQLite FTS5) combined with semantic reasoning via Antigravity Agent over standard Model Context Protocol (MCP).

## Key Paths & Architecture
- Workspace: Repository Root
- Python Virtualenv: `.venv` (Python 3.12+ with `mcp`, `fastapi`, `pillow`, `opencv-python-headless`, `pydantic`, `pytesseract`)
- MCP Server: `daemonx/mcp/server.py`
- MCP Config: `~/.gemini/config/mcp_config.json` and `~/.gemini/antigravity-ide/mcp_config.json`
- Target Devices: Physical Android Devices (Android 10 - 16) & deterministic in-memory `MockAdbBackend`.

## Acceptance Criteria
1. Full test suite passing across all 10 implementation phases.
2. 15 required acceptance criteria verified with evidence.
3. Safe zero-deletion defaults and quarantine restoration verified.
