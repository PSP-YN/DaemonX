# DAEMONX — Reference Environment Specification
**Target Platform**: Linux (Tested on Fedora Linux 44 and Ubuntu 24.04 LTS)  
**Architecture**: x86_64 / aarch64  

---

## 1. Operating System & System Requirements

| Parameter | Recommended Specification | Notes |
| :--- | :--- | :--- |
| **OS** | Linux (Fedora 40+, Ubuntu 22.04+, Arch, Debian) | Tested on Fedora Linux |
| **Kernel** | Linux 6.x+ | Standard cgroups and USB subsystem support |
| **CPU Architecture** | x86_64 or aarch64 | AVX2 / SSE4.1 recommended for high-throughput OCR |
| **Storage** | 5GB+ free space | Required for SQLite database, temporary frames, and OCR data |

---

## 2. Runtimes & Core Dependencies

| Component | Minimum Version | Installation / Command | Role in DaemonX |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | `python3 --version` | Main runtime for core libraries and plugins |
| **uv Package Manager** | 0.5+ | `uv --version` | Fast, deterministic dependency resolution |
| **Java JDK** | OpenJDK 17+ | `java -version` | Required for Android SDK build and platform tools |
| **SQLite** | 3.40+ (FTS5 enabled) | Built-in | Full-text search and transactional persistence |
| **Tesseract OCR** | 5.0+ | `tesseract --version` | Local, offline OCR engine with bounding-box extraction |

---

## 3. Android SDK & ADB Infrastructure

| Component | Status / Path | Details |
| :--- | :--- | :--- |
| **ADB Executable** | System `adb` (`/usr/bin/adb` or `$ANDROID_HOME/platform-tools/adb`) | Android Debug Bridge version 1.0.41+ |
| **ANDROID_HOME / SDK** | `$HOME/Android/Sdk` or `/opt/android-sdk` | Platform-tools, build-tools, platforms, emulator |
| **Target Devices** | Android 10, 11, 12, 13, 14, 15, 16 | Supported over USB or Wireless ADB |
| **Emulators** | Android Virtual Devices (AVD) / Genymotion | Headless and GUI testing support |

---

## 4. Antigravity IDE & Agent Integration

| Component | Location | Status |
| :--- | :--- | :--- |
| **Antigravity Global Config** | `~/.gemini/config/mcp_config.json` | Registers `daemonx` MCP server over stdio |
| **Antigravity IDE Config** | `~/.gemini/antigravity-ide/mcp_config.json` | IDE tool integration |
| **Protocol** | Model Context Protocol (MCP 2.x) | Standard JSON-RPC over stdio |

---

## 5. Device Support & Execution Architecture

1. **Target Hardware**:
   - Any physical Android device running Android 10 through Android 16 (Google Pixel, Samsung Galaxy, Xiaomi, OnePlus, Motorola, etc.).
   - Standard Android Virtual Devices (AVD) or emulators.
2. **Connecting Devices**:
   - Connect phone via USB or Wireless ADB.
   - Enable **Developer Options** and toggle **USB Debugging** ON.
   - Accept the host computer's RSA authorization fingerprint.
3. **Dual-Backend Testing Strategy**:
   - `AdbBackend`: Real ADB calls executing commands against connected physical devices or emulators.
   - `MockAdbBackend`: In-memory deterministic mock device simulator providing simulated screens, dumpsys, accessibility hierarchies, screenshots, and failure injection for 100% test coverage in CI.
