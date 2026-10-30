"""
DaemonX Core Exceptions
"""

class DaemonXError(Exception):
    """Base exception for all DaemonX operations."""
    pass


class DeviceError(DaemonXError):
    """Raised when an ADB or device interaction fails."""
    pass


class DeviceNotFoundError(DeviceError):
    """Raised when no authorized target device is available."""
    pass


class DeviceConnectionError(DeviceError):
    """Raised when communication with the device drops."""
    pass


class PerceptionError(DaemonXError):
    """Raised when screen perception, OCR, or UI hierarchy parsing fails."""
    pass


class StorageError(DaemonXError):
    """Raised when database operations encounter an error."""
    pass


class TaskExecutionError(DaemonXError):
    """Raised when a task or workflow step encounters an unrecoverable failure."""
    pass


class QuarantineError(DaemonXError):
    """Raised when file quarantine or restoration fails safety verification."""
    pass


class VerificationError(DaemonXError):
    """Raised when an assertion or post-condition fails."""
    pass
