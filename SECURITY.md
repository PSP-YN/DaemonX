# Security Policy

DaemonX takes the privacy and integrity of your personal device and data seriously. Because DaemonX interfaces directly with personal Android devices, privacy and defensive engineering are baked into the architecture by design.

---

## 🛡️ Supported Versions

We provide security updates and critical patches for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 1.0.x   | :white_check_mark: | Active |
| < 1.0   | :x:                | N/A    |

---

## 🔒 Security & Privacy Guarantees

1. **Local-First Processing**:
   - Device interactions, raw screen buffers, and OCR computations occur exclusively on your local host workstation.
   - Zero telemetry, tracking, or user data is transmitted to third-party services.
2. **Standard Local MCP Transport**:
   - Communication between Antigravity Agent and DaemonX occurs strictly via UNIX stdio pipes using the official Model Context Protocol (MCP).
   - No unauthenticated network services or public ports are exposed.
3. **Reversible Quarantine Architecture**:
   - Destructive operations are strictly decoupled from inspection and analysis.
   - Processed files are moved to an isolated quarantine vault (`data/quarantine/<media_id>/`) with an exact reverse mapping, rather than permanently deleted.
4. **Instagram Safe Mode**:
   - Unsaving is locked by default and requires explicit verified preconditions (`allow_unsave=True` and confirmed database persistence).
5. **Audit Logging**:
   - Every file transfer, quarantine, restoration, and deletion event is permanently recorded in the local SQLite `audit_log` table.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability or sensitive data handling flaw in DaemonX, please do **not** open a public issue.

Instead, please report the vulnerability confidentially:

- **Email**: [puttashankarprasadyn11@gmail.com](mailto:puttashankarprasadyn11@gmail.com)
- **Subject**: `[SECURITY] DaemonX Vulnerability Report`

Please include:
- A description of the issue and potential impact
- Detailed steps to reproduce or a proof of concept
- Your environment details (OS, Python version, device model)

We will acknowledge receipt within 48 hours and work with you to coordinate a safe resolution and release.
