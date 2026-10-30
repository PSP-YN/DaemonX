# DAEMONX — Security & Privacy Architecture

## 1. Principles of Least Privilege & Local-First Processing
- **No Third-Party Telemetry**: DaemonX transmits zero metrics or tracking data to external servers.
- **Local OCR & CV Execution**: Tesseract 5.5 and OpenCV run entirely on the Fedora host CPU. Screenshots are processed locally without network egress.
- **Secure Antigravity Integration**: Communication between Antigravity Agent and DaemonX occurs strictly over local UNIX pipes via standard `stdio` JSON-RPC. No unauthenticated network ports are exposed to the local network.

## 2. Non-Destructive Safeguards
- **Reversible Quarantine Vault**: Files marked for cleanup are moved to `data/quarantine/<media_id>/` rather than deleted.
- **One-Click Restoration**: Any quarantined file can be restored back to its original location with full metadata preservation.
- **Instagram Safety Locks**: Automatic un-saving of Instagram reels is disabled by default. Un-saving requires:
  1. Record verification in SQLite.
  2. Confirmed matching on-screen UI state.
  3. Explicit parameter approval (`allow_unsave=True`).
- **Audit Logging**: Every cleanup, quarantine, restoration, and deletion event is permanently logged in the SQLite `audit_log` table.
