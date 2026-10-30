"""
High-Fidelity Mock ADB Backend for Deterministic Testing and Continuous Verification
"""
import io
import time
from PIL import Image, ImageDraw, ImageFont
from daemonx.core.types import DeviceInfo, DeviceState, ConnectionType
from daemonx.core.exceptions import DeviceConnectionError, DeviceError


SAMPLE_INSTAGRAM_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.instagram.android" content-desc="" clickable="false" enabled="true" focused="false" scrollable="false" bounds="[0,0][1080,2460]">
    <node index="0" text="Saved" resource-id="com.instagram.android:id/action_bar_title" class="android.widget.TextView" package="com.instagram.android" content-desc="" clickable="false" enabled="true" focused="false" scrollable="false" bounds="[150,120][450,220]" />
    <node index="1" text="" resource-id="com.instagram.android:id/action_bar_button_back" class="android.widget.ImageView" package="com.instagram.android" content-desc="Back" clickable="true" enabled="true" focused="false" scrollable="false" bounds="[30,120][130,220]" />
    <node index="2" text="" resource-id="com.instagram.android:id/media_feed" class="androidx.recyclerview.widget.RecyclerView" package="com.instagram.android" content-desc="" clickable="false" enabled="true" focused="false" scrollable="true" bounds="[0,240][1080,2300]">
      <node index="0" text="Reel by @tech_innovator: Building AI Agents with Python and MCP" resource-id="com.instagram.android:id/row_feed_caption" class="android.widget.TextView" package="com.instagram.android" content-desc="" clickable="true" enabled="true" focused="false" scrollable="false" bounds="[60,300][1020,550]" />
      <node index="1" text="Save to collection" resource-id="com.instagram.android:id/row_feed_button_save" class="android.widget.ImageView" package="com.instagram.android" content-desc="Saved" clickable="true" enabled="true" focused="false" scrollable="false" bounds="[900,560][1020,680]" />
    </node>
  </node>
</hierarchy>
"""


class MockAdbBackend:
    def __init__(self, serial: str = "mock-android-device"):
        self.serial = serial
        self.is_connected = True
        self.authorized = True
        self.foreground_app = "com.android.launcher"
        self.taps: list[tuple[int, int]] = []
        self.swipes: list[tuple[int, int, int, int, int]] = []
        self.inputs: list[str] = []
        self.files: dict[str, bytes] = {}
        self.current_screen_type = "instagram_saved"

    def set_connected(self, connected: bool):
        self.is_connected = connected

    def set_authorized(self, authorized: bool):
        self.authorized = authorized

    def get_devices(self) -> list[DeviceInfo]:
        if not self.is_connected:
            return []
        state = DeviceState.ONLINE if self.authorized else DeviceState.UNAUTHORIZED
        return [
            DeviceInfo(
                serial=self.serial,
                state=state,
                model="Android Device",
                product="generic",
                android_version="16",
                sdk_version=36,
                width=1080,
                height=2400,
                density=420,
                connection_type=ConnectionType.MOCK
            )
        ]

    def check_connection(self):
        if not self.is_connected:
            raise DeviceConnectionError("Mock device disconnected")
        if not self.authorized:
            raise DeviceConnectionError("Mock device unauthorized")

    def run_shell(self, cmd: str) -> str:
        self.check_connection()
        cmd = cmd.strip()

        if "getprop ro.product.model" in cmd:
            return "Android Device"
        elif "getprop ro.build.version.release" in cmd:
            return "16"
        elif "getprop ro.build.version.sdk" in cmd:
            return "36"
        elif "wm size" in cmd:
            return "Physical size: 1080x2460"
        elif "wm density" in cmd:
            return "Physical density: 440"
        elif "dumpsys window" in cmd or "mCurrentFocus" in cmd:
            return f"mCurrentFocus=Window{{mock u0 {self.foreground_app}/.MainActivity}}"
        elif cmd.startswith("input tap"):
            parts = cmd.split()
            x, y = int(parts[2]), int(parts[3])
            self.taps.append((x, y))
            return ""
        elif cmd.startswith("input swipe"):
            parts = cmd.split()
            x1, y1, x2, y2 = int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
            duration = int(parts[6]) if len(parts) > 6 else 300
            self.swipes.append((x1, y1, x2, y2, duration))
            return ""
        elif cmd.startswith("input text"):
            text = cmd[len("input text "):].strip()
            self.inputs.append(text)
            return ""
        elif cmd.startswith("input keyevent"):
            key = cmd.split()[2]
            if key == "4":  # KEYCODE_BACK
                return ""
            elif key == "3":  # KEYCODE_HOME
                self.foreground_app = "com.android.launcher"
                return ""
            return ""
        elif cmd.startswith("monkey -p"):
            parts = cmd.split()
            pkg = parts[2]
            self.foreground_app = pkg
            return f"Events injected: 1"
        elif "uiautomator dump" in cmd:
            return "UI hierchary dumped to: /sdcard/window_dump.xml"
        elif "cat /sdcard/window_dump.xml" in cmd:
            return SAMPLE_INSTAGRAM_XML
        elif "ls -la /sdcard" in cmd:
            return "-rw-rw---- 1 root sdcard_rw 204800 2026-10-30 12:00 screenshot_01.png"
        return ""

    def capture_screenshot_bytes(self) -> bytes:
        self.check_connection()
        img = Image.new("RGB", (1080, 2460), color=(24, 24, 27))
        draw = ImageDraw.Draw(img)

        # Draw a mock mobile UI
        draw.rectangle([0, 0, 1080, 100], fill=(15, 23, 42))  # status bar
        draw.text((40, 30), "12:00", fill=(255, 255, 255))
        draw.text((950, 30), "5G  100%", fill=(255, 255, 255))

        draw.rectangle([0, 100, 1080, 220], fill=(30, 41, 59))  # header
        draw.text((60, 140), "DAEMONX MOBILE EXPLORER", fill=(255, 255, 255))

        draw.rectangle([60, 280, 1020, 750], fill=(51, 65, 85))  # card 1
        draw.text((100, 320), "Project: https://github.com/mcp-android/daemonx", fill=(56, 189, 248))
        draw.text((100, 380), "Book: Designing Data-Intensive Applications by Martin Kleppmann", fill=(226, 232, 240))
        draw.text((100, 440), "Contact: dev@example.com | +1-800-555-0199", fill=(148, 163, 184))
        draw.text((100, 500), "Tags: #AI #Agents #Python #Automation", fill=(168, 85, 247))

        draw.rectangle([60, 800, 1020, 1250], fill=(51, 65, 85))  # card 2
        draw.text((100, 840), "GitHub: https://github.com/anthropics/anthropic-tools", fill=(56, 189, 248))
        draw.text((100, 900), "Skill: Claude Code Assistant for Terminal Automation", fill=(226, 232, 240))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
