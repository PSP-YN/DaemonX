"""
Safe Cleanup & Quarantine Vault Engine
Enforces multi-layer safety, preview approvals, non-destructive isolation, and one-click rollback.
"""
import shutil
import time
from pathlib import Path
from pydantic import BaseModel, Field

from nexora.core.config import QUARANTINE_DIR
from nexora.core.exceptions import QuarantineError
from nexora.storage.database import Database


class CleanupCandidate(BaseModel):
    media_id: str
    original_path: str
    sha256: str | None
    file_size: int
    status: str
    can_quarantine: bool = True
    reason: str = "Processed and verified"


class CleanupPreview(BaseModel):
    total_candidates: int
    total_size_bytes: int
    candidates: list[CleanupCandidate] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)


class QuarantineVault:
    def __init__(self, db: Database | None = None, vault_dir: Path | str = QUARANTINE_DIR):
        self.db = db or Database()
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def generate_preview(self) -> CleanupPreview:
        """
        Generates a cleanup preview of eligible files.
        Only files that are:
        1. Marked 'processed'
        2. Exist on host filesystem
        3. Have a valid media record
        are eligible.
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, original_path, sha256, file_size, status
                FROM media_items
                WHERE status = 'processed' AND original_path IS NOT NULL
                """
            ).fetchall()

        candidates = []
        total_size = 0

        for r in rows:
            orig = Path(r["original_path"])
            if orig.exists() and orig.is_file():
                candidates.append(
                    CleanupCandidate(
                        media_id=r["id"],
                        original_path=str(orig),
                        sha256=r["sha256"],
                        file_size=r["file_size"] or orig.stat().st_size,
                        status=r["status"]
                    )
                )
                total_size += r["file_size"] or orig.stat().st_size

        return CleanupPreview(
            total_candidates=len(candidates),
            total_size_bytes=total_size,
            candidates=candidates
        )

    def quarantine_file(self, media_id: str, approved: bool = False) -> str:
        """
        Safely moves a processed file to the quarantine vault.
        Requires approved=True.
        """
        if not approved:
            raise QuarantineError("Quarantine operation rejected: Explicit approval (approved=True) is required.")

        item = self.db.get_media_item(media_id)
        if not item or item["status"] != "processed":
            raise QuarantineError(f"Cannot quarantine unverified media '{media_id}'.")

        orig_path = Path(item["original_path"])
        if not orig_path.exists():
            raise QuarantineError(f"Original file '{orig_path}' does not exist on disk.")

        # Create isolated quarantine subdirectory
        dest_dir = self.vault_dir / media_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / orig_path.name

        try:
            shutil.move(str(orig_path), str(dest_file))
        except Exception as e:
            raise QuarantineError(f"Failed to move file to quarantine: {e}")

        # Update database record and log cleanup
        self.db.update_media_status(media_id=media_id, status="quarantined", quarantine_path=str(dest_file))
        self.db.log_cleanup(
            media_id=media_id,
            action="quarantine",
            original_path=str(orig_path),
            quarantine_path=str(dest_file),
            verified=True,
            details="Moved to reversible quarantine vault"
        )
        return str(dest_file)

    def restore_file(self, media_id: str) -> str:
        """
        Restores a quarantined file back to its exact original location.
        """
        item = self.db.get_media_item(media_id)
        if not item or item["status"] != "quarantined" or not item["quarantine_path"]:
            raise QuarantineError(f"Media '{media_id}' is not in quarantine.")

        q_file = Path(item["quarantine_path"])
        orig_file = Path(item["original_path"])

        if not q_file.exists():
            raise QuarantineError(f"Quarantined file '{q_file}' missing from vault.")

        orig_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(q_file), str(orig_file))
        except Exception as e:
            raise QuarantineError(f"Failed to restore file from quarantine: {e}")

        # Update status back to processed
        self.db.update_media_status(media_id=media_id, status="processed", quarantine_path="")
        self.db.log_cleanup(
            media_id=media_id,
            action="restore",
            original_path=str(orig_file),
            quarantine_path=str(q_file),
            verified=True,
            details="Restored from quarantine back to original path"
        )
        return str(orig_file)

    def permanent_delete(self, media_id: str, double_confirmed: bool = False) -> bool:
        """
        Permanently deletes ONLY files that are already inside the quarantine vault.
        Never directly deletes files from original user directories.
        """
        if not double_confirmed:
            raise QuarantineError("Permanent delete rejected: Requires explicit double confirmation.")

        item = self.db.get_media_item(media_id)
        if not item or item["status"] != "quarantined" or not item["quarantine_path"]:
            raise QuarantineError("Only files currently in quarantine can be permanently deleted.")

        q_file = Path(item["quarantine_path"])
        if q_file.exists():
            q_file.unlink()

        self.db.update_media_status(media_id=media_id, status="deleted")
        self.db.log_cleanup(
            media_id=media_id,
            action="delete",
            original_path=item["original_path"],
            quarantine_path=str(q_file),
            verified=True,
            details="Permanently deleted from quarantine vault"
        )
        return True
