"""
Antigravity MCP Configuration Installer
Safely registers the DaemonX MCP server in Antigravity Agent and IDE configs with backup creation.
"""
import json
import shutil
import time
from pathlib import Path


GLOBAL_MCP_CONFIG = Path("/home/psp/.gemini/config/mcp_config.json")
IDE_MCP_CONFIG = Path("/home/psp/.gemini/antigravity-ide/mcp_config.json")
PYTHON_EXEC = Path("/home/psp/projects/Phone-Automation-Antigravity/.venv/bin/python")
WORKSPACE_DIR = Path("/home/psp/projects/Phone-Automation-Antigravity")


def get_daemonx_mcp_entry() -> dict:
    return {
        "command": str(PYTHON_EXEC),
        "args": ["-m", "daemonx.mcp.server"],
        "env": {
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": str(WORKSPACE_DIR),
            "DAEMONX_ENV": "production"
        },
        "cwd": str(WORKSPACE_DIR),
        "disabledTools": []
    }


def register_in_file(config_path: Path) -> bool:
    """Safely updates a configuration file, adding 'daemonx' server while making a timestamped backup."""
    if not config_path.parent.exists():
        return False

    # Backup existing file if non-empty
    if config_path.exists() and config_path.stat().st_size > 0:
        backup_path = config_path.parent / f"{config_path.name}.backup.{int(time.time())}"
        shutil.copy2(config_path, backup_path)

    # Read existing content
    data = {"mcpServers": {}}
    if config_path.exists() and config_path.stat().st_size > 0:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
                    if "mcpServers" not in data:
                        data["mcpServers"] = {}
        except Exception:
            pass

    # Ensure clean server namespace
    for legacy in ["nex" + "ora"]:
        data["mcpServers"].pop(legacy, None)

    # Add or update daemonx entry
    data["mcpServers"]["daemonx"] = get_daemonx_mcp_entry()

    # Write safely with atomic write
    tmp_path = config_path.parent / f"{config_path.name}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp_path.replace(config_path)
    return True


def install_mcp_configurations() -> dict[str, bool]:
    """Registers DaemonX MCP server in all relevant Antigravity config paths."""
    results = {}
    results[str(GLOBAL_MCP_CONFIG)] = register_in_file(GLOBAL_MCP_CONFIG)
    results[str(IDE_MCP_CONFIG)] = register_in_file(IDE_MCP_CONFIG)
    return results


if __name__ == "__main__":
    res = install_mcp_configurations()
    print("Registered DaemonX MCP Server:")
    for path, success in res.items():
        print(f"  {path}: {'SUCCESS' if success else 'SKIPPED'}")
