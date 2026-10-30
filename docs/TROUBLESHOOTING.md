# DAEMONX — Troubleshooting Guide

## 1. Device Connection & ADB Issues

### Symptom: `adb devices` shows `unauthorized`
- **Cause**: The phone has not accepted the Fedora host's RSA debugging key.
- **Fix**:
  1. Unlock the Xiaomi Redmi 13 5G screen.
  2. A system prompt will appear: "Allow USB debugging?".
  3. Check "Always allow from this computer" and tap **OK**.
  4. Run `adb devices` to confirm state changes to `device`.

### Symptom: Device disconnected or not listed
- **Cause**: Loose USB cable, port sleep, or debugging disabled.
- **Fix**:
  1. Unplug and reconnect USB cable.
  2. Verify in Settings -> Additional Settings -> Developer Options that **USB Debugging** is toggled ON.
  3. Run `./scripts/doctor.sh` to diagnose host ADB bridge.

### Symptom: Tap or Swipe has no effect on phone
- **Cause**: Xiaomi HyperOS / MIUI requires a separate toggle for simulated touch input.
- **Fix**:
  1. Open **Settings -> Additional Settings -> Developer Options**.
  2. Enable **USB Debugging (Security settings)**. (Xiaomi requires a SIM card / Mi Account to toggle this security permission once).

---

## 2. MCP Integration Issues

### Symptom: Antigravity does not list `daemonx` tools
- **Cause**: MCP configuration needs reloading or path is incorrect.
- **Fix**:
  1. Run `./scripts/doctor.sh` to check registration.
  2. Re-register manually:
     ```bash
     .venv/bin/python -m daemonx.mcp.configurator
     ```
  3. In Antigravity IDE / Agent, restart the MCP connection or reload window.

---

## 3. OCR & Perception Issues

### Symptom: OCR returns empty or inaccurate text
- **Cause**: Text is too small, resolution too low, or non-Latin alphabet.
- **Fix**:
  1. Ensure Tesseract 5.5 is installed: `tesseract --version`.
  2. Capture full-resolution uncompressed screenshots (`1080x2460`).
