"""
Tests for Phase 5: SQLite Knowledge Database, FTS5 Search, and Exports
"""
import pytest
from pathlib import Path
from daemonx.storage.database import Database
from daemonx.storage.schema import TAXONOMY_CATEGORIES


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_daemonx.db"
    return Database(db_path=db_file)


def test_schema_initialization_and_categories(temp_db: Database):
    with temp_db.get_connection() as conn:
        cats = conn.execute("SELECT COUNT(*) as cnt FROM categories").fetchone()["cnt"]
        assert cats == len(TAXONOMY_CATEGORIES)
        assert cats == 22


def test_storage_persistence(temp_db: Database):
    """TEST 10: Extract content and store into SQLite."""
    m_id = temp_db.insert_media_item(
        source_type="screenshot",
        original_path="/sdcard/DCIM/Screenshots/screen1.png",
        sha256="abcdef123456",
        phash="1010101010101010",
        width=1080,
        height=2460,
        file_size=512000
    )
    assert m_id.startswith("med_")

    c_id = temp_db.insert_extracted_content(
        media_id=m_id,
        full_text="Building autonomous AI agents using Claude Skills and FastMCP",
        ocr_confidence=0.98,
        caption="Agent tutorial",
        creator="tech_lead",
        source_url="https://github.com/agent-tools/mcp-suite",
        summary="A guide on building agents"
    )
    assert c_id.startswith("cnt_")

    # Add resource and tag
    r_id = temp_db.insert_resource(
        media_id=m_id,
        resource_type="github_repo",
        title="mcp-suite",
        url="https://github.com/agent-tools/mcp-suite",
        creator_or_author="agent-tools"
    )
    assert r_id.startswith("res_")

    temp_db.add_tag(media_id=m_id, tag_name="AI Agents", category_name="AI agents and automation")

    item = temp_db.get_media_item(m_id)
    assert item["sha256"] == "abcdef123456"
    assert item["status"] == "pending"


def test_fts5_search(temp_db: Database):
    """TEST 11: Search the database using full-text search."""
    m_id = temp_db.insert_media_item(source_type="instagram_reel", sha256="reel_hash_999")
    temp_db.insert_extracted_content(
        media_id=m_id,
        full_text="Deep dive into Python 3.12 performance optimization with OpenCV",
        caption="Python 3.12 speedups",
        creator="python_daily",
        summary="Tutorial covering GIL improvements and fast image diffing"
    )

    # Search for keyword "optimization"
    results = temp_db.search("optimization")
    assert len(results) >= 1
    assert results[0]["media_id"] == m_id

    # Search for creator
    results2 = temp_db.search("python_daily")
    assert len(results2) >= 1

    # Search for non-existent keyword
    results_empty = temp_db.search("nonexistentterm999")
    assert len(results_empty) == 0


def test_duplicate_detection(temp_db: Database):
    temp_db.insert_media_item(
        source_type="screenshot",
        sha256="unique_sha_123",
        phash="phash_abc_789"
    )

    dup1 = temp_db.find_duplicate_by_hash(sha256="unique_sha_123", phash=None)
    assert dup1 is not None

    dup2 = temp_db.find_duplicate_by_hash(sha256=None, phash="phash_abc_789")
    assert dup2 is not None

    no_dup = temp_db.find_duplicate_by_hash(sha256="different_sha", phash="different_phash")
    assert no_dup is None


def test_exports(temp_db: Database):
    m_id = temp_db.insert_media_item(source_type="screenshot", original_path="/path/test.png")
    temp_db.insert_extracted_content(
        media_id=m_id,
        full_text="Test content export",
        creator="tester"
    )

    json_exp = temp_db.export_knowledge("json")
    assert "Test content export" in json_exp
    assert "tester" in json_exp

    csv_exp = temp_db.export_knowledge("csv")
    assert "Test content export" in csv_exp

    md_exp = temp_db.export_knowledge("markdown")
    assert "# DAEMONX Knowledge Export" in md_exp
    assert "Test content export" in md_exp
