"""
Nexora Core Exceptions
"""

class NexoraError(Exception):
    """Base exception for all Nexora operations."""
    pass


class DeviceError(NexoraError):
    """Raised when an ADB or device interaction fails."""
    pass


class DeviceNotFoundError(DeviceError):
    """Raised when no authorized target device is available."""
    pass


class DeviceConnectionError(DeviceError):
    """Raised when communication with the device drops."""
    pass


class PerceptionError(NexoraError):
    """Raised when screen perception, OCR, or UI hierarchy parsing fails."""
    pass


class StorageError(NexoraError):
    """Raised when database operations encounter an error."""
    pass


class TaskExecutionError(NexoraError):
    """Raised when a task or workflow step encounters an unrecoverable failure."""
    pass


class QuarantineError(NexoraError):
    """Raised when file quarantine or restoration fails safety verification."""
    pass


class VerificationError(NexoraError):
    """Raised when an assertion or post-condition fails."""
    pass
