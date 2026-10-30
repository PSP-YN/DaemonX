"""
Tests for Phase 9: Safe Cleanup, Quarantine Vault, and Restoration Workflow
"""
import pytest
from pathlib import Path

from nexora.cleanup.vault import QuarantineVault
from nexora.core.exceptions import QuarantineError
from nexora.storage.database import Database


@pytest.fixture
def cleanup_setup(tmp_path: Path):
    db_file = tmp_path / "test_cleanup.db"
    vault_dir = tmp_path / "quarantine_vault"
    db = Database(db_path=db_file)
    vault = QuarantineVault(db=db, vault_dir=vault_dir)

    # Create dummy local file to simulate processed screenshot
    dummy_file = tmp_path / "screenshot_candidate.png"
    dummy_file.write_text("dummy image data")

    m_id = db.insert_media_item(
        source_type="screenshot",
        original_path=str(dummy_file),
        sha256="candidate_sha_123",
        file_size=len("dummy image data")
    )
    # Mark as processed
    db.update_media_status(media_id=m_id, status="processed")

    return vault, db, m_id, dummy_file


def test_cleanup_preview_and_restoration_workflow(cleanup_setup):
    """TEST 15: Demonstrate the cleanup preview and restoration workflow."""
    vault, db, m_id, dummy_file = cleanup_setup

    # 1. Generate preview
    preview = vault.generate_preview()
    assert preview.total_candidates == 1
    assert preview.candidates[0].media_id == m_id
    assert preview.candidates[0].original_path == str(dummy_file)

    # 2. Reject unapproved quarantine
    with pytest.raises(QuarantineError):
        vault.quarantine_file(m_id, approved=False)

    # 3. Quarantine with approval
    q_path = vault.quarantine_file(m_id, approved=True)
    assert Path(q_path).exists()
    assert not dummy_file.exists()  # Original moved into quarantine

    item_quarantined = db.get_media_item(m_id)
    assert item_quarantined["status"] == "quarantined"
    assert item_quarantined["quarantine_path"] == q_path

    # 4. One-click restoration
    restored_path = vault.restore_file(m_id)
    assert Path(restored_path).exists()
    assert dummy_file.exists()
    assert not Path(q_path).exists()  # Quarantine copy removed

    item_restored = db.get_media_item(m_id)
    assert item_restored["status"] == "processed"


def test_prevent_unprocessed_quarantine(cleanup_setup):
    vault, db, _, dummy_file = cleanup_setup

    # Insert pending (unprocessed) file
    unproc_file = dummy_file.parent / "unprocessed.png"
    unproc_file.write_text("raw unprocessed")
    unproc_id = db.insert_media_item(
        source_type="screenshot",
        original_path=str(unproc_file),
        sha256="unproc_sha"
    )

    # Attempting to quarantine unprocessed file must raise QuarantineError
    with pytest.raises(QuarantineError):
        vault.quarantine_file(unproc_id, approved=True)
    assert unproc_file.exists()
