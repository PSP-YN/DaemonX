"""
Screenshot Intelligence & Gallery Pipeline
Handles screenshot inventory, deduplication, OCR processing, entity extraction, and persistence.
"""
import hashlib
from pathlib import Path
from PIL import Image
import imagehash

from daemonx.core.exceptions import StorageError
from daemonx.device.controller import DeviceController
from daemonx.knowledge.extractor import KnowledgeExtractor
from daemonx.perception.ocr_engine import OCREngine
from daemonx.storage.database import Database


class GalleryPipeline:
    def __init__(self, db: Database | None = None, ocr_engine: OCREngine | None = None, controller: DeviceController | None = None):
        self.db = db or Database()
        self.ocr = ocr_engine or OCREngine()
        self.controller = controller

    @staticmethod
    def compute_sha256(file_path: Path | str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def compute_phash(image: Image.Image) -> str:
        return str(imagehash.phash(image))

    def inventory_directory(self, directory: Path | str) -> list[dict]:
        """
        Inventories screenshot files in a local directory without modifying or deleting them.
        Returns list of metadata dicts with sha256, phash, dimensions, and duplicate flags.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        inventory = []
        extensions = (".png", ".jpg", ".jpeg", ".webp")
        files = [p for p in dir_path.rglob("*") if p.suffix.lower() in extensions]

        for p in files:
            file_size = p.stat().st_size
            sha = self.compute_sha256(p)

            try:
                with Image.open(p) as img:
                    width, height = img.size
                    phash = self.compute_phash(img)
            except Exception:
                width, height, phash = 0, 0, ""

            # Check existing duplicate in DB
            dup = self.db.find_duplicate_by_hash(sha256=sha, phash=phash)
            is_dup = dup is not None

            # Record in DB as inventory item (never modifies the file)
            m_id = self.db.insert_media_item(
                source_type="screenshot",
                original_path=str(p.resolve()),
                sha256=sha,
                phash=phash,
                width=width,
                height=height,
                file_size=file_size
            )

            inventory.append({
                "media_id": m_id,
                "path": str(p),
                "sha256": sha,
                "phash": phash,
                "width": width,
                "height": height,
                "size_bytes": file_size,
                "is_duplicate": is_dup
            })

        return inventory

    def process_screenshot_file(self, file_path: Path | str, media_id: str | None = None) -> dict:
        """
        Processes a single screenshot:
        1. Loads image
        2. Computes SHA256 and pHash
        3. Executes local OCR
        4. Extracts entities (GitHub repos, books, tools, code)
        5. Persists complete record into SQLite
        """
        p = Path(file_path)
        sha = self.compute_sha256(p)

        with Image.open(p) as img:
            rgb_img = img.convert("RGB")
            width, height = rgb_img.size
            phash = self.compute_phash(rgb_img)
            ocr_text = self.ocr.extract_text(rgb_img)

        # Insert or update media item
        m_id = media_id or self.db.insert_media_item(
            source_type="screenshot",
            original_path=str(p.resolve()),
            sha256=sha,
            phash=phash,
            width=width,
            height=height,
            file_size=p.stat().st_size
        )

        # Extract entities
        entities = KnowledgeExtractor.extract_from_text(ocr_text)

        # Insert extracted content
        self.db.insert_extracted_content(
            media_id=m_id,
            full_text=ocr_text,
            ocr_confidence=0.95 if ocr_text else 0.0,
            summary=f"Screenshot containing {len(entities.github_repos)} repos, {len(entities.books)} books"
        )

        # Insert resources
        for repo in entities.github_repos:
            self.db.insert_resource(
                media_id=m_id,
                resource_type="github_repo",
                title=repo["title"],
                url=repo["url"],
                creator_or_author=repo["owner"]
            )

        for book in entities.books:
            self.db.insert_resource(
                media_id=m_id,
                resource_type="book",
                title=book["title"],
                creator_or_author=book["author"]
            )

        for tag in entities.tags:
            self.db.add_tag(media_id=m_id, tag_name=tag)

        # Mark as processed
        self.db.update_media_status(media_id=m_id, status="processed")

        return {
            "media_id": m_id,
            "path": str(p),
            "ocr_text": ocr_text,
            "entities": entities.model_dump(),
            "status": "processed"
        }
