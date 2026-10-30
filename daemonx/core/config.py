"""
DaemonX System Configuration
"""
from pathlib import Path
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "daemonx.db"
QUARANTINE_DIR = DATA_DIR / "quarantine"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = PROJECT_ROOT / "logs"


class DeviceConfig(BaseModel):
    default_serial: str | None = None
    adb_path: str = "/usr/bin/adb"
    timeout_seconds: float = 15.0
    connect_retries: int = 3
    screenshot_dir: Path = DATA_DIR / "screenshots"


class PerceptionConfig(BaseModel):
    tesseract_cmd: str = "/usr/bin/tesseract"
    ocr_confidence_threshold: float = 40.0
    ocr_languages: str = "eng"
    cv_match_threshold: float = 0.85


class StorageConfig(BaseModel):
    database_path: Path = DATABASE_PATH
    fts_enabled: bool = True
    backup_dir: Path = DATA_DIR / "backups"


class SystemConfig(BaseModel):
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    perception: PerceptionConfig = Field(default_factory=PerceptionConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    data_dir: Path = DATA_DIR
    quarantine_dir: Path = QUARANTINE_DIR


def ensure_directories():
    """Ensure all required runtime directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "screenshots").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "backups").mkdir(parents=True, exist_ok=True)


config = SystemConfig()
ensure_directories()
