"""
Unified Screen Perception Observer Integrating XML Hierarchy, OCR, and Computer Vision
"""
import time
from PIL import Image
from daemonx.core.types import ScreenObservation, UIElement
from daemonx.device.controller import DeviceController
from daemonx.perception.ui_hierarchy import UIHierarchyParser
from daemonx.perception.ocr_engine import OCREngine
from daemonx.perception.cv_matcher import CVMatcher


class ScreenObserver:
    def __init__(self, controller: DeviceController, ocr_engine: OCREngine | None = None):
        self.controller = controller
        self.ocr = ocr_engine or OCREngine()
        self.last_observation: ScreenObservation | None = None
        self.last_screenshot: Image.Image | None = None

    def dump_hierarchy_xml(self) -> str:
        """Retrieves active screen UIAutomator XML dump."""
        if self.controller.mock:
            return self.controller.mock.run_shell("cat /sdcard/window_dump.xml")

        try:
            self.controller.adb.run_shell("uiautomator dump /sdcard/window_dump.xml", serial=self.controller.serial)
            return self.controller.adb.run_shell("cat /sdcard/window_dump.xml", serial=self.controller.serial)
        except Exception:
            return ""

    def observe(self, run_ocr: bool = True) -> ScreenObservation:
        """
        Executes a complete multi-modal screen observation pass:
        1. Captures live screen buffer
        2. Queries accessibility node hierarchy
        3. Executes local OCR for visible text
        4. Classifies screen type and computes confidence score
        """
        screenshot = self.controller.capture_screenshot()
        self.last_screenshot = screenshot
        width, height = screenshot.size

        # 1. UI Hierarchy nodes
        xml_dump = self.dump_hierarchy_xml()
        elements = UIHierarchyParser.parse_xml(xml_dump) if xml_dump else []

        # 2. Extract visible text via OCR or XML text
        visible_texts = []
        for elem in elements:
            if elem.text:
                visible_texts.append(elem.text)
            elif elem.content_desc:
                visible_texts.append(elem.content_desc)

        ocr_text = ""
        if run_ocr:
            ocr_text = self.ocr.extract_text(screenshot)
            if ocr_text:
                for line in ocr_text.splitlines():
                    cleaned = line.strip()
                    if cleaned and cleaned not in visible_texts:
                        visible_texts.append(cleaned)

        # 3. Determine active package
        foreground_app = self.controller.get_foreground_app()
        package_name = foreground_app if foreground_app != "Unknown" else (
            elements[0].package_name if elements else "unknown"
        )

        # 4. Classify screen type
        screen_type = self._classify_screen(package_name, visible_texts)

        confidence = 0.95 if elements else (0.80 if visible_texts else 0.50)

        observation = ScreenObservation(
            package_name=package_name,
            activity_name="",
            screen_type=screen_type,
            elements=elements,
            visible_text=visible_texts,
            dimensions=(width, height),
            confidence=confidence,
            timestamp=time.time()
        )
        self.last_observation = observation
        return observation

    def find_element(self, text: str | None = None, resource_id: str | None = None, clickable: bool | None = None) -> UIElement | None:
        """Finds element matching criteria within latest observation."""
        obs = self.last_observation or self.observe(run_ocr=False)
        for elem in obs.elements:
            if text and text.lower() in elem.text.lower():
                return elem
            if resource_id and resource_id.lower() in elem.resource_id.lower():
                return elem
            if clickable is not None and elem.clickable == clickable:
                return elem
        return None

    def tap_element(self, text: str | None = None, resource_id: str | None = None) -> bool:
        """Finds element and taps its center coordinate."""
        elem = self.find_element(text=text, resource_id=resource_id)
        if not elem:
            return False
        cx, cy = elem.center
        return self.controller.tap(cx, cy)

    @staticmethod
    def _classify_screen(package_name: str, texts: list[str]) -> str:
        combined = " ".join(texts).lower()
        if "instagram" in package_name:
            if "saved" in combined or "collection" in combined:
                return "instagram_saved"
            elif "reels" in combined or "reel" in combined:
                return "instagram_reels"
            return "instagram_feed"
        elif "gallery" in package_name or "photos" in package_name:
            return "gallery_library"
        elif "settings" in package_name:
            return "system_settings"
        elif "launcher" in package_name:
            return "home_launcher"
        return "general"
