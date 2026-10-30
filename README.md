<div align="center">

# ⚡ DAEMONX
### Autonomous AI-Powered Android Automation & Personal Knowledge Intelligence Platform

[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](UNLICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Android 10 - 16](https://img.shields.io/badge/android-10_--_16-green.svg)](https://developer.android.com)
[![Tests: 27 Passed](https://img.shields.io/badge/tests-27%20passed-brightgreen.svg)](scripts/test.sh)
[![MCP Protocol](https://img.shields.io/badge/protocol-MCP%202.x-purple.svg)](https://modelcontextprotocol.io)
[![Fedora Linux](https://img.shields.io/badge/host-Fedora%20Linux-blue.svg)](https://fedoraproject.org)

**DaemonX** is a modular, production-grade Android automation and personal knowledge intelligence platform controlled from Linux (Fedora/Ubuntu/Arch) through **Antigravity Agent**. It fuses **deterministic local execution** (ADB, Tesseract 5.5 OCR, OpenCV, SQLite FTS5) with **semantic AI reasoning** via Antigravity Agent over the standard Model Context Protocol (MCP).

[Key Features](#-key-features) • [Device Support](#-device-support-matrix) • [Quick Start](#-quick-start) • [Architecture](#-system-architecture) • [MCP Tools](#-mcp-tool-registry) • [Dashboard](#-local-dashboard) • [Security](#-safety--quarantine-vault)

---

</div>

## 🌟 Key Features

- 📱 **Multi-Modal Android Perception**: Combines Accessibility XML trees (`uiautomator dump`), local Tesseract 5.5 OCR with bounding-box extraction, and OpenCV template matching and visual diffing.
- 🧠 **Antigravity Agent Semantic Reasoning**: Powered by your existing Antigravity Gemini subscription over standard `stdio` MCP. No external API keys, third-party subscriptions, or paid inference services required.
- 📸 **Screenshot Intelligence**: Recursively indexes screenshot backlogs, computes perceptual hashes (pHash/dHash) and SHA-256 for instant deduplication, and extracts GitHub repos, books, AI tools, emails, and code.
- 🎬 **Instagram Saved Reel Intelligence**: Inspects visible reels, extracts creator `@handles`, captions, hashtags, and code, and categorizes content across a standardized 22-category taxonomy without brittle unofficial APIs.
- 🔄 **Persistent Resumable Task Engine**: Directed step graphs persisted to SQLite. Automatically pauses upon disconnection and resumes from the exact checkpoint without re-running earlier steps.
- 🗄️ **SQLite FTS5 Knowledge Base**: Sub-millisecond full-text search across all extracted OCR, captions, and entities, with one-click exports to JSON, CSV, and Markdown.
- 🛡️ **Non-Destructive Quarantine Vault**: Files are never deleted directly. Eligible processed media is moved to a reversible quarantine vault with instant one-click restoration.
- 💻 **Real-Time Web Dashboard**: Fast, responsive, dark-mode single page app with interactive live device screen clicking, search console, task manager, and terminal telemetry.

---

## 📱 Device Support Matrix

DaemonX supports both physical Android hardware and headless emulators:

| Device Category | Verified Models / Versions | Connection Type | Capabilities Verified |
| :--- | :--- | :--- | :--- |
| **Physical Hardware** | **Android 10 - 16 Devices** (Google Pixel, Samsung Galaxy, Xiaomi, OnePlus, Motorola) | USB & Wireless ADB | High-res screen capture, touch injection, XML accessibility dumps, OCR, app lifecycle |
| **Android Versions** | **Android 16, 15, 14, 13, 12, 11, 10** | USB & Wireless ADB | Full OS compatibility, dumpsys window detection, input text, keyevents |
| **OEM Skins** | Stock Android (Pixel/AOSP), One UI, OxygenOS, HyperOS / MIUI, ColorOS | USB & Wireless ADB | Standard Android accessibility and ADB input handling |
| **Emulators** | Android Virtual Devices (AVD), Android Studio, Genymotion | Local Loopback (`emulator-5554`) | Automated test execution and headless CI |
| **Mock Simulator** | Built-in `MockAdbBackend` | In-Memory | 100% deterministic testing without physical hardware attached |

### Android Device Setup Note (Developer Options & ADB)
On any physical Android device:
1. Enable Developer Options: **Settings -> About Phone -> Tap Build Number (or OS Version) 7 times**.
2. In **Developer Options**:
   - Toggle **USB Debugging** to ON.
   - For OEM skins with enhanced security permissions (e.g. Xiaomi HyperOS/MIUI, ColorOS): toggle **USB Debugging (Security settings)** to ON to allow touch simulation.
3. Accept the computer's RSA fingerprint dialog ("Always allow from this computer").

---

## 🚀 Quick Start

### 1. System Requirements (Fedora Linux / Ubuntu)
```bash
# Fedora
sudo dnf install -y android-tools tesseract

# Ubuntu / Debian
sudo apt update && sudo apt install -y adb tesseract-ocr tesseract-ocr-eng
```

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/PSP-YN/DaemonX.git
cd DaemonX

# Set up Python virtual environment (Python 3.12+)
uv venv --python /usr/bin/python3.12 .venv
source .venv/bin/activate
uv pip install -e . --python .venv/bin/python
```

### 3. Run Self-Diagnostics
Verify your ADB bridge, attached devices, Tesseract 5.5, SQLite FTS5, and MCP registration:
```bash
./scripts/doctor.sh
```

### 4. Start the Local Web Dashboard
```bash
./scripts/start.sh 8080
```
Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in your browser.

### 5. Run the Test Suite
```bash
./scripts/test.sh
```

---

## 🏛️ System Architecture

```
+-------------------------------------------------------------+
|                      ANTIGRAVITY AGENT                      |
|           (Gemini 3.8 Flash / Pro via MCP Client)           |
+------------------------------+------------------------------+
                               |
                   [Standard MCP Stdio / JSON-RPC]
                               |
+------------------------------v------------------------------+
|                     DAEMONX MCP SERVER                      |
|                  (daemonx.mcp.server)                       |
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
+------v--------+     +--------v--------+     +--------v--------+
| Device Engine |     | Perception      |     | Task Engine     |
| (ADB Client)  |     | (OCR/CV/XML)    |     | (Checkpoints)   |
+---------------+     +-----------------+     +-----------------+
       |                       |                       |
       +-----------------------+-----------------------+
                               |
+------------------------------v------------------------------+
|                    INTELLIGENCE PIPELINES                   |
|  * Screenshot Scanner & pHash   * Instagram Reel Pipeline   |
|  * Entity & Knowledge Extractor  * Quarantine Vault         |
+------------------------------+------------------------------+
                               |
+------------------------------v------------------------------+
|                     STORAGE & DASHBOARD                     |
|  * SQLite 3.51 with FTS5 Full-Text Search                   |
|  * Local Web Dashboard (FastAPI + Vanilla CSS/JS)           |
+-------------------------------------------------------------+
```

---

## 🔌 MCP Tool Registry

DaemonX registers 32 typed tools in Antigravity configuration files (`~/.gemini/config/mcp_config.json` and `~/.gemini/antigravity-ide/mcp_config.json`):

| Domain | Available MCP Tools |
| :--- | :--- |
| **Device Control** | `device_list`, `device_status`, `device_capture_screen`, `device_inspect_screen`, `device_launch_app`, `device_tap`, `device_swipe`, `device_scroll`, `device_press_back`, `device_input_text` |
| **Gallery & OCR** | `gallery_inventory`, `gallery_get_metadata`, `gallery_extract_text`, `gallery_analyze_image`, `gallery_find_duplicates`, `gallery_search` |
| **Instagram Intelligence**| `instagram_open_saved`, `instagram_inspect_current_reel`, `instagram_extract_visible_content`, `instagram_get_reel_status`, `instagram_record_reel`, `instagram_verify_reel`, `instagram_unsave_verified` |
| **Knowledge Engine** | `knowledge_search`, `knowledge_get_record`, `knowledge_create_record`, `knowledge_update_record`, `knowledge_export` |
| **Task Engine** | `task_create`, `task_start`, `task_pause`, `task_resume`, `task_cancel`, `task_status`, `task_list` |
| **Safe Cleanup** | `cleanup_preview`, `cleanup_quarantine`, `cleanup_restore`, `cleanup_permanent_delete` |

---

## 🖥️ Local Dashboard

The built-in web dashboard provides full visibility into the platform:
- **Overview**: Hardware status, OS build, resolution, database statistics, and live telemetry.
- **Live Device**: Real-time display stream with interactive coordinate tapping and navigation keys (Home, Back, Scroll).
- **Knowledge Library**: Instant search across all indexed OCR text and entities with FTS5.
- **Task Engine**: Real-time monitoring of multi-step task execution and checkpoints.
- **Quarantine Vault**: Preview eligible cleanup candidates and restore quarantined files with one click.

---

## 🛡️ Safety & Quarantine Vault

DaemonX enforces strict safety rules:
1. **Zero-Deletion Default**: Running analysis or inventory never modifies or deletes any file.
2. **Reversible Quarantine**: Cleanup moves files to `data/quarantine/<media_id>/` with original paths logged in SQLite.
3. **One-Click Restoration**: Any quarantined file can be restored back to its exact original directory.
4. **Verified Instagram Unsaving**: Reels are unsaved only when verified records exist in SQLite and `allow_unsave=True` is explicitly passed.

---

## 🤝 Contributing & Community

Contributions are welcome! Please read:
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)

---

## 📄 License

This software is released into the public domain under the [Unlicense](UNLICENSE). You are free to copy, modify, publish, use, compile, sell, or distribute this software for any purpose.
