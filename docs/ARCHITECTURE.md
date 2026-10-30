# DAEMONX — System Architecture Specification

## 1. High-Level Architectural Overview

DaemonX is a modular, general-purpose AI-powered Android automation and personal knowledge intelligence platform. Designed to run on Fedora Linux and interface seamlessly with Antigravity Agent, DaemonX adheres to a **Local-First, Dual-Execution Engine** design:
1. **Deterministic Local Execution**: Device control, screen capture, accessibility node parsing, OCR, duplicate detection, SQLite knowledge extraction, and safe cleanup execute deterministically on Fedora without requiring AI cloud APIs.
2. **AI Reasoning via Antigravity Agent**: Semantic understanding, classification, actionable synthesis, and natural language instructions are processed directly through the Antigravity Agent using the user's active Gemini subscription via standard Model Context Protocol (MCP) tool calls.

```
+-------------------------------------------------------------+
|                      ANTIGRAVITY AGENT                      |
|           (Gemini 3.8 Flash / Pro via MCP Client)           |
+------------------------------+------------------------------+
                               |
                   [Standard MCP Stdio / JSON-RPC]
                               |
+------------------------------v------------------------------+
|                     DAEMONX MCP SERVER                       |
|                 (DaemonX Repository Root)                    |
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
+------v--------+     +--------v--------+     +--------v--------+
| Device Control|     | Screen Perception|     | Task Engine     |
| (ADB / Wireless)|   | (OCR/CV/XML)     |    | (Graphs/Recovery)|
+---------------+     +-----------------+     +-----------------+
       |                       |                       |
       +-----------------------+-----------------------+
                               |
+------------------------------v------------------------------+
|                     INTELLIGENCE MODULES                    |
|  * Screenshot & Gallery Intelligence  * Instagram Pipeline  |
|  * Knowledge Extraction & Enrichment   * Safe Cleanup Engine |
+------------------------------+------------------------------+
                               |
+------------------------------v------------------------------+
|                     STORAGE & DASHBOARD                     |
|  * SQLite 3.51 with FTS5 Full-Text Search                   |
|  * Local Dashboard (FastAPI + Vanilla Modern Web UI)         |
+-------------------------------------------------------------+
```

---

## 2. Core Subsystems and Component Breakdown

### 2.1 Device Control Engine (`daemonx.device`)
- **`DeviceController`**: Manages USB and Wireless ADB connections, authorization states, auto-reconnection, screen orientation detection, and lifecycle checks.
- **`InputDriver`**: Handles normalized coordinate transformations, taps, directional swipes, multi-point gestures, text input (with special character escaping), Back, Home, and App Switcher.
- **`AppManager`**: Launches applications by package/activity, queries foreground running tasks via `dumpsys window / activity`, and manages process state.
- **`FileTransfer`**: Safe push/pull operations with MD5 verification and error recovery.

### 2.2 Screen Perception Engine (`daemonx.perception`)
- **Multi-Modal Visual Hierarchy**:
  1. **Accessibility / UI Hierarchy (`uiautomator dump`)**: High-speed XML node parsing, extracting bounds, text, resource IDs, content descriptions, clickability, and scrollability.
  2. **Local OCR (`tesseract 5.5.3`)**: Bounding-box text detection, multilingual support, confidence thresholds.
  3. **Computer Vision (`OpenCV`)**: Edge detection, icon and button template matching, screen diffing, and state change verification.
- **`ScreenObserver`**: Combines XML nodes and OCR bounding boxes into unified `ScreenObservation` records with confidence scoring and semantic element selectors.

### 2.3 Task Orchestrator & State Engine (`daemonx.tasks`)
- **Directed Acyclic Graph (DAG) Engine**: Decomposes complex user workflows into granular, idempotent atomic steps.
- **Checkpoint & Persistence**: Every stage state is serialized to SQLite. If a USB cable disconnects or the host restarts, the task pauses cleanly and can be resumed with zero data duplication.
- **Adaptive Execution & Retries**: Circuit breakers and exponential backoff on transient UI glitches.

### 2.4 Screenshot & Gallery Intelligence (`daemonx.gallery`)
- Scans Android media stores (`/sdcard/DCIM/Screenshots`, `/sdcard/Pictures/Screenshots`).
- Perceptual hashing (`imagehash` pHash / dHash) and SHA-256 for duplicate detection.
- Entity extraction: URLs, emails, phone numbers, code snippets, dates, and technical keywords.
- Generates searchable records in SQLite FTS5.

### 2.5 Instagram Saved Reel Intelligence (`daemonx.instagram`)
- UI-driven safe extraction for saved reels without violating Instagram terms or invoking brittle reverse-engineered APIs.
- Captures: creator handle, caption, audio metadata, hashtags, displayed text/code, GitHub repository mentions, book titles, and AI tools.
- Strict multi-tag classification system across 22 taxonomy categories.
- Zero-deletion policy by default: unsaving requires strict multi-step verification and explicit confirmation.

### 2.6 Knowledge Database Engine (`daemonx.storage`)
- **Engine**: SQLite 3.51.2 with FTS5 virtual tables.
- **Schema**: Normalized schema covering `media_items`, `extracted_content`, `resources`, `categories`, `tags`, `media_tags`, `processing_jobs`, `cleanup_log`, and `audit_log`.
- **Search Capabilities**: Sub-millisecond full-text queries, exact phrase matching, category filters, and relation graphs.

### 2.7 Safe Cleanup & Quarantine Engine (`daemonx.cleanup`)
- **Quarantine vs. Deletion**: Files are NEVER deleted directly. Eligible processed files are moved to a reversible quarantine vault with an expiration window and one-click rollback.
- **Preview & Approvals**: Every cleanup action generates a verifiable JSON preview with checksums and status checks.

### 2.8 MCP Server (`daemonx.mcp`)
- Implements standard Model Context Protocol over `stdio`.
- Exposes typed tools across Device, Gallery, Instagram, Knowledge, Task, and Cleanup domains.
- Enforces strict parameter validation and security allowlists.

### 2.9 Modern Local Dashboard (`daemonx.dashboard`)
- Built with FastAPI backend and pure modern vanilla CSS/JS frontend (no external CDN dependencies required for offline stability).
- Live device screen stream, task execution graph, knowledge library explorer, and terminal log stream.
