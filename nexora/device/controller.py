"""
Device Controller for Android Devices (Hardware & Mock Backends)
"""
import re
import time
from pathlib import Path
from PIL import Image
import io

from nexora.core.exceptions import DeviceError, DeviceNotFoundError, DeviceConnectionError
from nexora.core.types import DeviceInfo, DeviceState, ConnectionType
from nexora.device.adb_client import AdbClient
from nexora.device.mock_backend import MockAdbBackend


class DeviceController:
    def __init__(self, serial: str | None = None, adb_client: AdbClient | None = None, mock_backend: MockAdbBackend | None = None):
        self.serial = serial
        self.adb = adb_client or AdbClient()
        self.mock = mock_backend
        self._cached_info: DeviceInfo | None = None

    def use_mock(self, mock_backend: MockAdbBackend | None = None):
        """Switches controller to headless mock backend."""
        self.mock = mock_backend or MockAdbBackend()
        self.serial = self.mock.serial

    def get_devices(self) -> list[DeviceInfo]:
        """Discovers all attached USB, wireless, or mock devices."""
        if self.mock:
            return self.mock.get_devices()

        code, stdout, stderr = self.adb.run_command(["devices", "-l"])
        if code != 0:
            raise DeviceError(f"Failed to query adb devices: {stderr}")

        devices = []
        for line in stdout.strip().splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            serial = parts[0]
            state_str = parts[1]

            state = DeviceState.ONLINE if state_str == "device" else (
                DeviceState.UNAUTHORIZED if state_str == "unauthorized" else DeviceState.OFFLINE
            )

            model = "Unknown"
            product = "Unknown"
            for part in parts[2:]:
                if part.startswith("model:"):
                    model = part.split(":", 1)[1]
                elif part.startswith("product:"):
                    product = part.split(":", 1)[1]

            conn_type = ConnectionType.WIRELESS if ":" in serial else ConnectionType.USB

            devices.append(
                DeviceInfo(
                    serial=serial,
                    state=state,
                    model=model,
                    product=product,
                    connection_type=conn_type
                )
            )
        return devices

    def select_device(self, serial: str | None = None) -> DeviceInfo:
        """Selects target device or picks first online device."""
        devices = self.get_devices()
        if not devices:
            raise DeviceNotFoundError("No Android devices or emulators detected via ADB.")

        if serial:
            for dev in devices:
                if dev.serial == serial:
                    self.serial = serial
                    return self._populate_device_metadata(dev)
            raise DeviceNotFoundError(f"Device with serial '{serial}' not found in active devices.")

        # Default to first online device or first device
        online = [d for d in devices if d.state == DeviceState.ONLINE]
        target = online[0] if online else devices[0]
        self.serial = target.serial
        return self._populate_device_metadata(target)

    def _populate_device_metadata(self, dev: DeviceInfo) -> DeviceInfo:
        if self.mock:
            self._cached_info = dev
            return dev

        if dev.state != DeviceState.ONLINE:
            self._cached_info = dev
            return dev

        try:
            # Query Android OS & hardware metrics
            dev.android_version = self.adb.run_shell("getprop ro.build.version.release", serial=self.serial)
            sdk_str = self.adb.run_shell("getprop ro.build.version.sdk", serial=self.serial)
            dev.sdk_version = int(sdk_str) if sdk_str.isdigit() else 0
            dev.model = self.adb.run_shell("getprop ro.product.model", serial=self.serial)

            # Query dimensions and density
            wm_size = self.adb.run_shell("wm size", serial=self.serial)
            match_size = re.search(r"(\d+)x(\d+)", wm_size)
            if match_size:
                dev.width, dev.height = int(match_size.group(1)), int(match_size.group(2))

            wm_density = self.adb.run_shell("wm density", serial=self.serial)
            match_density = re.search(r"(\d+)", wm_density)
            if match_density:
                dev.density = int(match_density.group(1))

        except Exception:
            pass  # Retain defaults if query fails

        self._cached_info = dev
        return dev

    def get_device_status(self) -> DeviceInfo:
        """Returns health and status of the currently selected device."""
        if not self.serial:
            return self.select_device()
        devices = self.get_devices()
        for dev in devices:
            if dev.serial == self.serial:
                return self._populate_device_metadata(dev)
        raise DeviceConnectionError(f"Selected device '{self.serial}' is no longer connected.")

    def connect_usb(self) -> DeviceInfo:
        """Connects and binds to primary USB device."""
        devices = self.get_devices()
        usb_devices = [d for d in devices if d.connection_type == ConnectionType.USB]
        if not usb_devices and not self.mock:
            raise DeviceNotFoundError("No USB-connected Android device found.")
        target = usb_devices[0] if usb_devices else devices[0]
        self.serial = target.serial
        return self._populate_device_metadata(target)

    def connect_wireless(self, address: str, port: int) -> DeviceInfo:
        """Connects to device over wireless ADB."""
        if self.mock:
            return self.mock.get_devices()[0]
        endpoint = f"{address}:{port}"
        code, stdout, stderr = self.adb.run_command(["connect", endpoint])
        if code != 0 or "connected to" not in stdout.lower():
            raise DeviceConnectionError(f"Failed to connect wirelessly to {endpoint}: {stdout} {stderr}")
        self.serial = endpoint
        return self.get_device_status()

    def capture_screenshot(self) -> Image.Image:
        """Captures device display and returns PIL Image."""
        if self.mock:
            raw_bytes = self.mock.capture_screenshot_bytes()
        else:
            if not self.serial:
                self.select_device()
            raw_bytes = self.adb.run_raw(["exec-out", "screencap", "-p"], serial=self.serial)

        try:
            return Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        except Exception as e:
            raise DeviceError(f"Failed to decode captured screenshot: {e}")

    def launch_app(self, package_name: str, activity_name: str | None = None) -> bool:
        """Launches application package."""
        if self.mock:
            self.mock.run_shell(f"monkey -p {package_name} 1")
            return True

        if not self.serial:
            self.select_device()

        if activity_name:
            cmd = f"am start -n {package_name}/{activity_name}"
        else:
            cmd = f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"

        out = self.adb.run_shell(cmd, serial=self.serial)
        time.sleep(1.0)  # Adaptive settle window
        return True

    def get_foreground_app(self) -> str:
        """Queries current active foreground window / package."""
        if self.mock:
            return self.mock.foreground_app

        if not self.serial:
            self.select_device()

        out = self.adb.run_shell("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'", serial=self.serial)
        match = re.search(r"([a-zA-Z0-9_\.]+(?:/[a-zA-Z0-9_\.]+))", out)
        if match:
            return match.group(1).split("/")[0]
        return "Unknown"

    def tap(self, x: int, y: int) -> bool:
        """Taps screen coordinate (x, y)."""
        if self.mock:
            self.mock.run_shell(f"input tap {x} {y}")
            return True

        if not self.serial:
            self.select_device()
        self.adb.run_shell(f"input tap {x} {y}", serial=self.serial)
        return True

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Swipes smoothly from (x1, y1) to (x2, y2)."""
        if self.mock:
            self.mock.run_shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
            return True

        if not self.serial:
            self.select_device()
        self.adb.run_shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}", serial=self.serial)
        return True

    def scroll(self, direction: str = "down", distance_ratio: float = 0.5) -> bool:
        """Scrolls up, down, left, or right based on screen dimensions."""
        info = self.get_device_status()
        w, h = info.width, info.height
        cx = w // 2
        cy = h // 2
        dy = int(h * distance_ratio * 0.5)

        if direction.lower() == "down":
            return self.swipe(cx, cy + dy, cx, cy - dy, duration_ms=300)
        elif direction.lower() == "up":
            return self.swipe(cx, cy - dy, cx, cy + dy, duration_ms=300)
        elif direction.lower() == "left":
            dx = int(w * distance_ratio * 0.5)
            return self.swipe(cx + dx, cy, cx - dx, cy, duration_ms=300)
        elif direction.lower() == "right":
            dx = int(w * distance_ratio * 0.5)
            return self.swipe(cx - dx, cy, cx + dx, cy, duration_ms=300)
        else:
            raise ValueError(f"Unknown direction '{direction}'")

    def press_back(self) -> bool:
        """Emulates Android Back button."""
        if self.mock:
            self.mock.run_shell("input keyevent 4")
            return True

        if not self.serial:
            self.select_device()
        self.adb.run_shell("input keyevent 4", serial=self.serial)
        return True

    def press_home(self) -> bool:
        """Emulates Android Home button."""
        if self.mock:
            self.mock.run_shell("input keyevent 3")
            return True

        if not self.serial:
            self.select_device()
        self.adb.run_shell("input keyevent 3", serial=self.serial)
        return True

    def input_text(self, text: str) -> bool:
        """Enters text with safe shell escaping."""
        if self.mock:
            self.mock.run_shell(f"input text '{text}'")
            return True

        if not self.serial:
            self.select_device()

        # Escape special characters for ADB input text
        safe_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        self.adb.run_shell(f"input text {safe_text}", serial=self.serial)
        return True

    def transfer_file(self, source: Path | str, destination: str) -> bool:
        """Pushes or pulls files to/from device."""
        if self.mock:
            return True

        if not self.serial:
            self.select_device()

        src = str(source)
        code, stdout, stderr = self.adb.run_command(["push", src, destination], serial=self.serial)
        if code != 0:
            raise DeviceError(f"Failed to transfer file {src} -> {destination}: {stderr}")
        return True
