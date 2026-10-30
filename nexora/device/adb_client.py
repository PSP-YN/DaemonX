"""
Low-Level ADB Subprocess Client with Strict Validation and Error Handling
"""
import subprocess
from pathlib import Path
from nexora.core.exceptions import DeviceError, DeviceConnectionError, DeviceNotFoundError


class AdbClient:
    def __init__(self, adb_path: str = "/usr/bin/adb", timeout_seconds: float = 15.0):
        self.adb_path = adb_path
        self.timeout_seconds = timeout_seconds

    def run_command(self, args: list[str], serial: str | None = None, timeout: float | None = None) -> tuple[int, str, str]:
        """
        Executes an ADB command with optional device targeting and timeout.
        Returns (exit_code, stdout, stderr).
        """
        cmd = [self.adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)

        t = timeout or self.timeout_seconds
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=t,
                check=False
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            raise DeviceError(f"ADB command timed out after {t}s: {' '.join(cmd)}")
        except FileNotFoundError:
            raise DeviceError(f"ADB executable not found at '{self.adb_path}'")
        except Exception as e:
            raise DeviceError(f"Failed to execute ADB command: {e}")

    def run_shell(self, shell_cmd: str, serial: str | None = None, timeout: float | None = None) -> str:
        """
        Executes an adb shell command and returns trimmed stdout.
        Raises DeviceError on non-zero return code or device disconnection.
        """
        code, stdout, stderr = self.run_command(["shell", shell_cmd], serial=serial, timeout=timeout)
        if code != 0:
            err = stderr.strip() or stdout.strip()
            if "device not found" in err or "device offline" in err or "no devices/emulators" in err:
                raise DeviceConnectionError(f"Device disconnected or offline: {err}")
            if "device unauthorized" in err:
                raise DeviceConnectionError(f"Device unauthorized. Please accept host RSA key: {err}")
            raise DeviceError(f"ADB shell command failed ({code}): {err}")
        return stdout.strip()

    def run_raw(self, args: list[str], serial: str | None = None, timeout: float | None = None) -> bytes:
        """
        Executes an ADB command capturing raw binary output (e.g. for screencap).
        """
        cmd = [self.adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)

        t = timeout or self.timeout_seconds
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                timeout=t,
                check=False
            )
            if res.returncode != 0:
                raise DeviceError(f"ADB raw command failed: {res.stderr.decode('utf-8', errors='ignore')}")
            return res.stdout
        except subprocess.TimeoutExpired:
            raise DeviceError(f"ADB raw command timed out after {t}s")
        except Exception as e:
            raise DeviceError(f"ADB raw command error: {e}")
