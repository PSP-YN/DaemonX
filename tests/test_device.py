"""
Tests for Phase 1: ADB Device Connection and Control
"""
import pytest
from daemonx.core.exceptions import DeviceConnectionError, DeviceNotFoundError
from daemonx.core.types import DeviceState
from daemonx.device.controller import DeviceController
from daemonx.device.mock_backend import MockAdbBackend


def test_device_discovery_mock():
    """TEST 1: Detect Android Device over USB / Mock."""
    mock = MockAdbBackend(serial="mock-android-device")
    controller = DeviceController(mock_backend=mock)

    devices = controller.get_devices()
    assert len(devices) == 1
    dev = devices[0]
    assert dev.model == "Android Device"
    assert dev.android_version == "16"
    assert dev.sdk_version == 36
    assert dev.width == 1080
    assert dev.height == 2400
    assert dev.density == 420
    assert dev.state == DeviceState.ONLINE


def test_device_selection_and_status():
    mock = MockAdbBackend()
    controller = DeviceController(mock_backend=mock)

    dev_info = controller.select_device()
    assert dev_info.serial == "mock-android-device"

    status = controller.get_device_status()
    assert status.serial == "mock-android-device"
    assert status.model == "Android Device"


def test_connection_recovery():
    """TEST 2: Detect and recover from USB / Device disconnection."""
    mock = MockAdbBackend()
    controller = DeviceController(mock_backend=mock)

    controller.select_device()

    # Simulate unexpected cable disconnection
    mock.set_connected(False)
    with pytest.raises(DeviceConnectionError):
        controller.get_device_status()

    # Simulate phone reconnected
    mock.set_connected(True)
    status = controller.get_device_status()
    assert status.state == DeviceState.ONLINE


def test_device_touch_and_input():
    mock = MockAdbBackend()
    controller = DeviceController(mock_backend=mock)
    controller.select_device()

    # Test tap
    assert controller.tap(540, 1200) is True
    assert (540, 1200) in mock.taps

    # Test swipe
    assert controller.swipe(100, 500, 100, 100, duration_ms=250) is True
    assert (100, 500, 100, 100, 250) in mock.swipes

    # Test scroll
    assert controller.scroll("down") is True
    assert controller.scroll("up") is True

    # Test input text
    assert controller.input_text("Hello DaemonX") is True
    assert len(mock.inputs) > 0

    # Test navigation keys
    assert controller.press_back() is True
    assert controller.press_home() is True


def test_app_lifecycle_and_foreground():
    """TEST 5: Open an application and verify its foreground state."""
    mock = MockAdbBackend()
    controller = DeviceController(mock_backend=mock)
    controller.select_device()

    assert controller.launch_app("com.instagram.android") is True
    assert controller.get_foreground_app() == "com.instagram.android"

    # Press Home to return to launcher
    controller.press_home()
    assert controller.get_foreground_app() == "com.android.launcher"


def test_screen_capture_decoding():
    """TEST 3: Capture the actual phone screen."""
    mock = MockAdbBackend()
    controller = DeviceController(mock_backend=mock)
    controller.select_device()

    img = controller.capture_screenshot()
    assert img is not None
    assert img.size == (1080, 2460)
    assert img.mode == "RGB"
