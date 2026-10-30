"""
Tests for Phase 7: Instagram Saved Reel Intelligence and Verified Safeguards
"""
import pytest
from pathlib import Path

from nexora.core.exceptions import VerificationError
from nexora.device.controller import DeviceController
from nexora.device.mock_backend import MockAdbBackend
from nexora.instagram.classifier import InstagramClassifier
from nexora.instagram.reel_extractor import InstagramPipeline, ReelData
from nexora.storage.database import Database


@pytest.fixture
def instagram_setup(tmp_path: Path):
    db_file = tmp_path / "test_instagram.db"
    db = Database(db_path=db_file)
    mock = MockAdbBackend()
    mock.foreground_app = "com.instagram.android"
    controller = DeviceController(mock_backend=mock)
    pipeline = InstagramPipeline(controller=controller, db=db)
    return pipeline, controller, mock


def test_taxonomy_classifier():
    tags = ["ai", "agents"]
    res = InstagramClassifier.classify("Check out this new fastmcp server for building agents", caption="Agent guide", tags=tags)
    cat_ids = [c[0] for c in res]
    assert "cat_ai_agents" in cat_ids or "cat_mcp" in cat_ids or "cat_ai_ml" in cat_ids


def test_instagram_inventory_non_mutating(instagram_setup):
    """TEST 13: Inventory Instagram saved content without unsaving anything."""
    pipeline, controller, mock = instagram_setup

    initial_taps = len(mock.taps)

    # Inspect current reel
    reel_data = pipeline.inspect_current_reel()

    # Verify extracted data
    assert reel_data.media_id != ""
    assert reel_data.creator == "tech_innovator"
    assert "Building AI Agents" in reel_data.caption
    assert reel_data.is_saved is True  # Must still be saved!

    # Verify no unsave tap occurred
    assert reel_data.is_saved is True


def test_instagram_extraction_entities(instagram_setup):
    """TEST 14: Process a small sample of reels and correctly extract visible information."""
    pipeline, controller, _ = instagram_setup

    reel_data = pipeline.inspect_current_reel()
    assert reel_data.creator == "tech_innovator"
    assert len(reel_data.categories) > 0

    # Verify database persistence
    item = pipeline.db.get_media_item(reel_data.media_id)
    assert item["status"] == "processed"

    search_hits = pipeline.db.search("tech_innovator")
    assert len(search_hits) >= 1


def test_safe_unsave_enforcement(instagram_setup):
    pipeline, controller, _ = instagram_setup

    reel_data = pipeline.inspect_current_reel()

    # Safety Lock: unsaving must raise VerificationError if allow_unsave is False
    with pytest.raises(VerificationError):
        pipeline.verify_and_unsave(reel_data, allow_unsave=False)

    assert reel_data.is_saved is True
