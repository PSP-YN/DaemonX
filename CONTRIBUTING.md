# Contributing to DaemonX

Thank you for your interest in contributing to DaemonX! We welcome issues, pull requests, and discussions from the open-source community.

---

## 🛠️ Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PSP-YN/DaemonX.git
   cd DaemonX
   ```

2. **Set up Python Virtual Environment**:
   DaemonX requires Python 3.12+ on Linux (Fedora, Ubuntu, Arch, etc.).
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
   Or using `uv` (recommended):
   ```bash
   uv venv --python /usr/bin/python3.12 .venv
   uv pip install -e . --python .venv/bin/python
   ```

3. **Install System Dependencies**:
   - `android-tools` (provides `adb`)
   - `tesseract` (v5.0+ with English traineddata)
   ```bash
   # Fedora
   sudo dnf install -y android-tools tesseract
   # Ubuntu / Debian
   sudo apt install -y adb tesseract-ocr
   ```

4. **Verify Environment**:
   ```bash
   ./scripts/doctor.sh
   ```

---

## 🧪 Testing Guidelines

Before submitting any code changes, ensure all tests pass:

```bash
./scripts/test.sh
```

- When implementing new device actions, provide corresponding test cases in `tests/test_device.py`.
- If modifying perception or OCR logic, add fixtures in `tests/test_perception.py`.
- Ensure non-destructive safeguards (quarantine isolation, zero-deletion rules) remain 100% covered.

---

## 📜 Pull Request Process

1. Fork the repo and create a topic branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit your changes with descriptive, conventional commit messages:
   - `feat(...)`: New capability or tool
   - `fix(...)`: Bug fix
   - `docs(...)`: Documentation updates
   - `test(...)`: Test additions or refactoring
3. Run tests and static checks:
   ```bash
   ./scripts/test.sh
   ```
4. Push to your fork and submit a Pull Request targeting `main`.

---

## 🔒 Security Vulnerabilities

Please do not disclose security vulnerabilities publicly in GitHub Issues. Review our [Security Policy](SECURITY.md) for instructions on confidential disclosure.
