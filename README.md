# NEXORA — AI-Powered Android Automation & Personal Knowledge Platform

Nexora is a production-grade, modular Android automation and personal knowledge intelligence platform controlled from Fedora Linux through Antigravity Agent.

Nexora combines **local deterministic execution** (ADB, Tesseract 5.5, OpenCV, SQLite FTS5) with **semantic AI reasoning** via Antigravity Agent using your existing Gemini subscription over the Model Context Protocol (MCP).

---

## 🚀 Quick Start

### 1. Prerequisites (Fedora Linux)
- Fedora Linux 40+ (Tested on Fedora 44 x86_64)
- Python 3.12+ (or `uv`)
- ADB (`android-tools`)
- Tesseract OCR (`tesseract`)

```bash
# Install system packages
sudo dnf install -y android-tools tesseract
```

### 2. Environment Verification
Run the system doctor to check ADB, hardware connectivity, and MCP registration:

```bash
./scripts/doctor.sh
```

### 3. Launch Local Dashboard
Start the local web dashboard:

```bash
./scripts/start.sh 8080
```
Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in your browser.

### 4. Run Test Suite
Execute the full automated test suite (27 comprehensive unit and integration tests):

```bash
./scripts/test.sh
```

---

## 📱 Hardware Configuration (Xiaomi Redmi 13 5G)

1. Connect the Xiaomi Redmi 13 5G via USB cable.
2. In **Settings -> About Phone**, tap **MIUI Version** or **OS Version** 7 times to enable Developer Options.
3. In **Additional Settings -> Developer Options**:
   - Enable **USB Debugging**.
   - Enable **USB Debugging (Security Settings)** (allows simulated touch and input).
4. On the phone, accept the host authorization prompt ("Always allow from this computer").
5. Verify hardware detection:
   ```bash
   adb devices -l
   ```

---

## 🤖 Antigravity Agent & IDE Integration

Nexora automatically registers itself into Antigravity MCP configuration files:
- Global / Agent config: `/home/psp/.gemini/config/mcp_config.json`
- IDE config: `/home/psp/.gemini/antigravity-ide/mcp_config.json`

### MCP Tools Available to Antigravity Agent
- **Device Tools**: `device_list`, `device_status`, `device_capture_screen`, `device_inspect_screen`, `device_launch_app`, `device_tap`, `device_swipe`, `device_scroll`, `device_press_back`, `device_input_text`.
- **Gallery Tools**: `gallery_inventory`, `gallery_get_metadata`, `gallery_extract_text`, `gallery_analyze_image`, `gallery_find_duplicates`, `gallery_search`.
- **Instagram Tools**: `instagram_open_saved`, `instagram_inspect_current_reel`, `instagram_extract_visible_content`, `instagram_get_reel_status`, `instagram_record_reel`, `instagram_verify_reel`, `instagram_unsave_verified`.
- **Knowledge Tools**: `knowledge_search`, `knowledge_get_record`, `knowledge_create_record`, `knowledge_update_record`, `knowledge_export`.
- **Task Tools**: `task_create`, `task_start`, `task_pause`, `task_resume`, `task_cancel`, `task_status`, `task_list`.
- **Cleanup Tools**: `cleanup_preview`, `cleanup_quarantine`, `cleanup_restore`, `cleanup_permanent_delete`.

---

## 🛡️ Safety & Privacy Architecture

- **Zero Cloud API Leakage**: No OpenAI, Claude, or third-party paid API keys required. Semantic reasoning is channeled exclusively through Antigravity Agent.
- **Reversible Quarantine**: Screenshots are NEVER deleted directly. Files are safely moved to `.data/quarantine/<media_id>` and can be restored with a single click.
- **Instagram Safe Mode**: Unsaving requires multi-step verification (`allow_unsave=True`, verified database persistence, confirmed on-screen identity). Unverified reels are never unsaved.
