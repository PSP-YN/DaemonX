# NEXORA — Project Memory

## Summary
Nexora is a production-grade, modular Android automation and personal knowledge intelligence platform controlled from Fedora Linux through Antigravity Agent. It features deterministic local execution (ADB, Tesseract 5.5, OpenCV, SQLite FTS5) combined with semantic reasoning via Antigravity Agent over standard Model Context Protocol (MCP).

## Key Paths & Architecture
- Workspace: `/home/psp/projects/Phone-Automation-Antigravity`
- Python Virtualenv: `.venv` (Python 3.12.16 with `mcp`, `fastapi`, `pillow`, `opencv-python-headless`, `pydantic`, `pytesseract`)
- MCP Server: `nexora/mcp/server.py`
- MCP Config: `/home/psp/.gemini/config/mcp_config.json` and `/home/psp/.gemini/antigravity-ide/mcp_config.json`
- Target Device: Xiaomi Redmi 13 5G (Android 16); fallback Mock ADB & `small_phone` AVD.

## Acceptance Criteria
1. Full test suite passing across all 10 implementation phases.
2. 15 required acceptance criteria verified with evidence.
3. Safe zero-deletion defaults and quarantine restoration verified.
