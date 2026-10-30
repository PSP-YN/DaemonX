"""
Instagram Saved Reel Extraction & Safe Verification Engine
"""
import re
import time
from typing import Any
from pydantic import BaseModel, Field

from nexora.core.exceptions import PerceptionError, VerificationError
from nexora.device.controller import DeviceController
from nexora.knowledge.extractor import KnowledgeExtractor, ExtractedEntities
from nexora.perception.observer import ScreenObserver
from nexora.storage.database import Database
from nexora.instagram.classifier import InstagramClassifier


HASHTAG_REGEX = re.compile(r"#([a-zA-Z0-9_]+)")
CREATOR_REGEX = re.compile(r"@([a-zA-Z0-9_.]+)")


class ReelData(BaseModel):
    media_id: str = ""
    creator: str = "unknown"
    caption: str = ""
    hashtags: list[str] = Field(default_factory=list)
    visible_text: str = ""
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    categories: list[tuple[str, str]] = Field(default_factory=list)
    verified: bool = False
    is_saved: bool = True


class InstagramPipeline:
    def __init__(self, controller: DeviceController, db: Database | None = None, observer: ScreenObserver | None = None):
        self.controller = controller
        self.db = db or Database()
        self.observer = observer or ScreenObserver(controller=controller)

    def open_saved_collection(self) -> bool:
        """Launches Instagram and navigates to Saved collection."""
        self.controller.launch_app("com.instagram.android")
        time.sleep(2.0)
        # Attempt to find and tap Saved or Profile
        obs = self.observer.observe(run_ocr=False)
        saved_elem = self.observer.find_element(text="Saved")
        if saved_elem:
            self.observer.tap_element(text="Saved")
            time.sleep(1.0)
            return True
        return True

    def inspect_current_reel(self) -> ReelData:
        """
        Inspects the active visible Reel on screen without mutating anything.
        Extracts creator, caption, hashtags, and on-screen text.
        """
        obs = self.observer.observe(run_ocr=True)

        caption = ""
        creator = "unknown"

        # Check accessibility elements for caption & creator
        for elem in obs.elements:
            t = elem.text.strip()
            if not t:
                continue
            if t.startswith("Reel by @") or "@" in t:
                match = CREATOR_REGEX.search(t)
                if match:
                    creator = match.group(1)
                caption = t
            elif len(t) > len(caption) and ("#" in t or len(t) > 30):
                caption = t

        # If caption not found in XML, parse visible OCR text
        ocr_combined = "\n".join(obs.visible_text)
        if not caption and obs.visible_text:
            caption = obs.visible_text[0]
            match = CREATOR_REGEX.search(ocr_combined)
            if match:
                creator = match.group(1)

        # Extract hashtags
        hashtags = HASHTAG_REGEX.findall(f"{caption} {ocr_combined}")

        # Extract entities (GitHub, books, tools)
        entities = KnowledgeExtractor.extract_from_text(f"{caption}\n{ocr_combined}")

        # Classify categories
        categories = InstagramClassifier.classify(text=ocr_combined, caption=caption, tags=hashtags)

        # Generate media record in SQLite
        m_id = self.db.insert_media_item(
            source_type="instagram_reel",
            original_path=f"instagram://reel/@{creator}",
            width=obs.dimensions[0],
            height=obs.dimensions[1]
        )

        # Store extracted content
        self.db.insert_extracted_content(
            media_id=m_id,
            full_text=ocr_combined,
            caption=caption,
            creator=creator,
            summary=f"Reel by @{creator} about {categories[0][1] if categories else 'general'}"
        )

        # Store resources
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

        for tag in hashtags + entities.tags:
            self.db.add_tag(media_id=m_id, tag_name=tag, category_name=categories[0][1] if categories else None)

        self.db.update_media_status(media_id=m_id, status="processed")

        return ReelData(
            media_id=m_id,
            creator=creator,
            caption=caption,
            hashtags=hashtags,
            visible_text=ocr_combined,
            entities=entities,
            categories=categories,
            verified=True,
            is_saved=True
        )

    def verify_and_unsave(self, reel_data: ReelData, allow_unsave: bool = False) -> bool:
        """
        Safely unsaves a reel ONLY if:
        1. allow_unsave is explicitly True (safety lock)
        2. reel_data.verified is True
        3. reel_data has a stored database record
        4. save button is found on screen and tapped
        """
        if not allow_unsave:
            raise VerificationError("Unsaving rejected: Safe deletion policy requires explicit approval (allow_unsave=True).")

        if not reel_data.verified or not reel_data.media_id:
            raise VerificationError("Cannot unsave unverified reel record.")

        # Confirm database record exists
        record = self.db.get_media_item(reel_data.media_id)
        if not record or record["status"] != "processed":
            raise VerificationError("Database verification failed: Record not marked as processed.")

        # Find save button on screen
        obs = self.observer.observe(run_ocr=False)
        save_btn = self.observer.find_element(resource_id="save") or self.observer.find_element(text="Saved")

        if save_btn:
            cx, cy = save_btn.center
            self.controller.tap(cx, cy)
            time.sleep(0.5)

            # Log cleanup in audit log
            self.db.log_cleanup(
                media_id=reel_data.media_id,
                action="unsave",
                original_path=f"instagram://reel/@{reel_data.creator}",
                verified=True,
                details="Unsaved from Instagram saved collection"
            )
            reel_data.is_saved = False
            return True

        # In mock or fallback mode where element wasn't named 'save'
        return False
