"""
DaemonX Core Data Models and Types
"""
from enum import Enum
from pydantic import BaseModel, Field


class ConnectionType(str, Enum):
    USB = "usb"
    WIRELESS = "wireless"
    MOCK = "mock"


class DeviceState(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"


class DeviceInfo(BaseModel):
    serial: str
    state: DeviceState
    model: str = "Unknown"
    product: str = "Unknown"
    android_version: str = "Unknown"
    sdk_version: int = 0
    width: int = 1080
    height: int = 2400
    density: int = 440
    connection_type: ConnectionType = ConnectionType.USB


class UIElement(BaseModel):
    id: str = ""
    resource_id: str = ""
    text: str = ""
    content_desc: str = ""
    class_name: str = ""
    package_name: str = ""
    clickable: bool = False
    scrollable: bool = False
    enabled: bool = True
    focused: bool = False
    bounds: list[int] = Field(default_factory=lambda: [0, 0, 0, 0])  # [x1, y1, x2, y2]
    confidence: float = 1.0

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bounds
        return (x1 + x2) // 2, (y1 + y2) // 2

    @property
    def width(self) -> int:
        return self.bounds[2] - self.bounds[0]

    @property
    def height(self) -> int:
        return self.bounds[3] - self.bounds[1]


class ScreenObservation(BaseModel):
    package_name: str = ""
    activity_name: str = ""
    screen_type: str = "general"
    elements: list[UIElement] = Field(default_factory=list)
    visible_text: list[str] = Field(default_factory=list)
    dimensions: tuple[int, int] = (1080, 2400)
    confidence: float = 1.0
    timestamp: float = 0.0
