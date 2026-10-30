# DAEMONX — User Manual & Operations Guide

## 1. Overview
DaemonX enables you to control your Android smartphone from Linux (tested on Fedora and Ubuntu) using natural language through Antigravity Agent, execute automated workflows, extract structured knowledge from screenshots and Instagram Saved Reels, and manage cleanups safely.

---

## 2. Operating Workflows

### Workflow A: Processing Screenshot Backlog
1. **Discover Screenshots**:
   In Antigravity Agent, instruct:
   > "Inventory all screenshots in `data/screenshots` and check for duplicates."
   Antigravity calls `gallery_inventory` and `gallery_find_duplicates`.
2. **Extract Knowledge**:
   > "Extract OCR text, GitHub repositories, books, and AI tools from all new screenshots."
   DaemonX runs local Tesseract 5.5 OCR and extracts entities into SQLite FTS5.
3. **Review & Quarantine**:
   > "Generate a cleanup preview for processed screenshots."
   DaemonX returns eligible files with hashes and storage confirmations. Files can be quarantined with `cleanup_quarantine`.

### Workflow B: Instagram Saved Reel Intelligence
1. **Open Collection**:
   > "Open my Instagram Saved collection on the connected device."
   Antigravity invokes `instagram_open_saved`.
2. **Extract Current Reel**:
   > "Inspect the reel currently displayed on screen."
   DaemonX reads creator `@handle`, caption, visible code/diagrams, and tags.
3. **Classify and Store**:
   Reel is automatically classified into the 22-category taxonomy and saved in SQLite.
4. **Safe Unsave**:
   Unsaving is executed ONLY when explicitly directed and verified.

---

## 3. Web Dashboard Features

Open `http://127.0.0.1:8080`:
- **Overview**: Real-time hardware telemetry (Model, Android OS, Resolution, DPI, Database metrics).
- **Live Screen**: Interactive canvas showing real-time device display. Clicking directly on the canvas injects touch events at exact device coordinates.
- **Knowledge Library**: Search bar querying the SQLite FTS5 full-text index with sub-millisecond response.
- **Task Engine**: View active, paused, or completed task pipelines.
- **Cleanup Vault**: Inspect quarantined files, generate previews, and perform one-click restorations.
