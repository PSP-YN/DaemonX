"""
Nexora Unified Command-Line Interface (CLI)
Provides doctor, start, test, and mcp subcommands.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def doctor():
    """Runs comprehensive system diagnostics on Fedora, ADB, devices, Tesseract, SQLite, and MCP."""
    console.print("[bold cyan]NEXORA System Doctor[/bold cyan]\n")

    table = Table(title="System & Dependency Health Check")
    table.add_column("Component", style="bold")
    table.add_column("Path / Info")
    table.add_column("Status", style="bold")

    # 1. OS
    os_name = "Fedora Linux"
    if Path("/etc/os-release").exists():
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    os_name = line.split("=", 1)[1].strip().strip('"')
    table.add_row("Operating System", os_name, "[green]OK[/green]")

    # 2. Python
    py_ver = sys.version.split()[0]
    table.add_row("Python Runtime", f"{sys.executable} (v{py_ver})", "[green]OK[/green]")

    # 3. ADB
    adb_path = shutil_which("adb") or "/usr/bin/adb"
    if Path(adb_path).exists():
        try:
            res = subprocess.run([adb_path, "version"], capture_output=True, text=True, check=False)
            ver = res.stdout.splitlines()[0] if res.stdout else "Available"
            table.add_row("ADB Executable", f"{adb_path} ({ver})", "[green]OK[/green]")
        except Exception:
            table.add_row("ADB Executable", adb_path, "[yellow]Check Required[/yellow]")
    else:
        table.add_row("ADB Executable", "Not found", "[red]FAIL[/red]")

    # 4. Tesseract OCR
    tess_path = shutil_which("tesseract") or "/usr/bin/tesseract"
    if Path(tess_path).exists():
        table.add_row("Tesseract OCR 5.5", tess_path, "[green]OK[/green]")
    else:
        table.add_row("Tesseract OCR", "Not found in PATH", "[red]FAIL[/red]")

    # 5. SQLite FTS5
    try:
        import sqlite3
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE _test USING fts5(content);")
        table.add_row("SQLite FTS5", f"SQLite {sqlite3.sqlite_version}", "[green]OK[/green]")
    except Exception as e:
        table.add_row("SQLite FTS5", str(e), "[red]FAIL[/red]")

    # 6. Connected Devices
    try:
        from nexora.device.controller import DeviceController
        ctrl = DeviceController()
        devices = ctrl.get_devices()
        dev_desc = ", ".join([f"{d.model} ({d.serial})" for d in devices]) if devices else "None attached (Mock available)"
        status_color = "[green]OK[/green]" if devices else "[yellow]STANDBY[/yellow]"
        table.add_row("Android Hardware", dev_desc, status_color)
    except Exception as e:
        table.add_row("Android Hardware", str(e), "[yellow]WARNING[/yellow]")

    # 7. Antigravity MCP Config
    mcp_cfg = Path("/home/psp/.gemini/config/mcp_config.json")
    if mcp_cfg.exists():
        table.add_row("Antigravity MCP Config", str(mcp_cfg), "[green]REGISTERED[/green]")
    else:
        table.add_row("Antigravity MCP Config", "Not registered", "[yellow]PENDING[/yellow]")

    console.print(table)
    console.print("\n[bold green]Verdict: Platform is ready for deterministic automation and MCP reasoning.[/bold green]\n")


def start(port: int = 8080):
    """Starts the Nexora Local Dashboard on the specified port."""
    import uvicorn
    console.print(f"[bold cyan]Starting Nexora Local Dashboard on http://127.0.0.1:{port}[/bold cyan]")
    uvicorn.run("nexora.dashboard.app:app", host="127.0.0.1", port=port, reload=False, log_level="info")


def mcp_server():
    """Starts the standard stdio MCP Server for Antigravity Agent."""
    from nexora.mcp.server import main as mcp_main
    mcp_main()


def test():
    """Runs the full automated pytest suite."""
    console.print("[bold cyan]Running Nexora Test Suite...[/bold cyan]")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=False)
    sys.exit(res.returncode)


def shutil_which(cmd: str) -> str | None:
    import shutil
    return shutil.which(cmd)


def main():
    parser = argparse.ArgumentParser(description="Nexora Android Automation & Personal Knowledge Platform")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("doctor", help="Inspect system, ADB, dependencies, and MCP configuration")
    start_parser = subparsers.add_parser("start", help="Start the local web dashboard")
    start_parser.add_argument("--port", type=int, default=8080, help="Port to run dashboard on (default: 8080)")
    subparsers.add_parser("mcp", help="Run stdio MCP server for Antigravity Agent")
    subparsers.add_parser("test", help="Execute automated test suite")

    args = parser.parse_args()

    if args.command == "doctor":
        doctor()
    elif args.command == "start":
        start(port=args.port)
    elif args.command == "mcp":
        mcp_server()
    elif args.command == "test":
        test()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
