"""
Tests for Phase 6: Screenshot Inventory and Analysis
"""
from PIL import Image, ImageDraw, ImageFont
import pytest
from pathlib import Path
from nexora.gallery.pipeline import GalleryPipeline
from nexora.storage.database import Database


@pytest.fixture
def gallery_setup(tmp_path: Path):
    db_file = tmp_path / "test_gallery.db"
    db = Database(db_path=db_file)
    pipeline = GalleryPipeline(db=db)

    # Create dummy screenshot directory with 2 test screenshots
    screen_dir = tmp_path / "screenshots"
    screen_dir.mkdir()

    font_path = Path("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf")
    font = ImageFont.truetype(str(font_path), 22) if font_path.exists() else None

    img1_path = screen_dir / "screen_01.png"
    img1 = Image.new("RGB", (800, 300), color=(255, 255, 255))
    d1 = ImageDraw.Draw(img1)
    d1.text((30, 50), "GitHub: https://github.com/google/gemini-cli", fill=(0, 0, 0), font=font)
    d1.text((30, 120), "Book: Clean Code by Robert Martin", fill=(0, 0, 0), font=font)
    img1.save(img1_path)

    img2_path = screen_dir / "screen_02.png"
    img2 = Image.new("RGB", (800, 300), color=(255, 255, 255))
    d2 = ImageDraw.Draw(img2)
    d2.text((30, 50), "Claude Skill tutorial at https://anthropic.com", fill=(0, 0, 0), font=font)
    img2.save(img2_path)

    return pipeline, screen_dir, img1_path, img2_path


def test_gallery_inventory(gallery_setup):
    """TEST 9: Inventory screenshots without modifying or deleting them."""
    pipeline, screen_dir, img1_path, img2_path = gallery_setup

    orig_mtime1 = img1_path.stat().st_mtime
    orig_size1 = img1_path.stat().st_size

    inventory = pipeline.inventory_directory(screen_dir)
    assert len(inventory) == 2

    # Verify original files are untouched
    assert img1_path.exists()
    assert img2_path.exists()
    assert img1_path.stat().st_size == orig_size1
    assert img1_path.stat().st_mtime == orig_mtime1

    # Check hash presence
    assert inventory[0]["sha256"] is not None
    assert inventory[0]["phash"] is not None


def test_screenshot_processing_pipeline(gallery_setup):
    """TEST 10: Extract screenshot content into SQLite."""
    pipeline, screen_dir, img1_path, _ = gallery_setup

    res = pipeline.process_screenshot_file(img1_path)
    assert res["status"] == "processed"
    assert res["media_id"] is not None

    # Verify extracted entities in DB
    item = pipeline.db.get_media_item(res["media_id"])
    assert item["status"] == "processed"

    search_hits = pipeline.db.search("gemini-cli")
    assert len(search_hits) >= 1
    assert search_hits[0]["media_id"] == res["media_id"]
