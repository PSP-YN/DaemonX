"""
Tests for Phase 2: Screen Perception Engine (OCR, CV, UI Hierarchy)
"""
from PIL import Image, ImageDraw
import pytest

from nexora.device.controller import DeviceController
from nexora.device.mock_backend import MockAdbBackend, SAMPLE_INSTAGRAM_XML
from nexora.perception.ui_hierarchy import UIHierarchyParser
from nexora.perception.ocr_engine import OCREngine
from nexora.perception.cv_matcher import CVMatcher
from nexora.perception.observer import ScreenObserver


def test_ui_hierarchy_parsing():
    elements = UIHierarchyParser.parse_xml(SAMPLE_INSTAGRAM_XML)
    assert len(elements) >= 3

    # Check title element
    title_elem = next((e for e in elements if e.text == "Saved"), None)
    assert title_elem is not None
    assert title_elem.resource_id == "com.instagram.android:id/action_bar_title"
    assert title_elem.bounds == [150, 120, 450, 220]
    assert title_elem.center == (300, 170)
    assert title_elem.width == 300
    assert title_elem.height == 100


def test_ocr_engine_text_extraction():
    ocr = OCREngine()
    # Create synthetic image with readable text
    img = Image.new("RGB", (400, 150), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 50), "NEXORA OCR TEST", fill=(0, 0, 0))

    text = ocr.extract_text(img)
    assert "NEXORA" in text or "OCR" in text or "TEST" in text

    data = ocr.extract_data(img, min_confidence=20.0)
    assert len(data) > 0
    assert any("OCR" in d["text"] or "TEST" in d["text"] or "NEXORA" in d["text"] for d in data)


def test_cv_matcher_and_screen_diff():
    # Test identical screen diff
    img1 = Image.new("RGB", (200, 200), color=(100, 100, 100))
    img2 = Image.new("RGB", (200, 200), color=(100, 100, 100))
    diff = CVMatcher.compute_screen_difference(img1, img2)
    assert diff == 0.0

    # Test changed screen diff
    draw = ImageDraw.Draw(img2)
    draw.rectangle([50, 50, 150, 150], fill=(255, 255, 255))
    diff2 = CVMatcher.compute_screen_difference(img1, img2)
    assert diff2 > 0.1

    # Test template matching with textured pattern
    draw.line([50, 50, 150, 150], fill=(0, 0, 0), width=3)
    draw.line([50, 150, 150, 50], fill=(255, 0, 0), width=3)
    template = img2.crop([50, 50, 150, 150])
    matches = CVMatcher.match_template(img2, template, threshold=0.90)
    assert len(matches) >= 1
    assert matches[0]["bounds"] == [50, 50, 150, 150]


def test_screen_observer_full_cycle():
    """TEST 4: Extract visible text and accessible UI elements."""
    mock = MockAdbBackend()
    mock.foreground_app = "com.instagram.android"
    controller = DeviceController(mock_backend=mock)
    observer = ScreenObserver(controller=controller)

    obs = observer.observe(run_ocr=True)
    assert obs is not None
    assert obs.package_name == "com.instagram.android"
    assert obs.screen_type == "instagram_saved"
    assert len(obs.elements) > 0
    assert len(obs.visible_text) > 0

    # Semantic element finding and tapping
    elem = observer.find_element(text="Saved")
    assert elem is not None

    tap_success = observer.tap_element(text="Saved")
    assert tap_success is True
    assert elem.center in mock.taps
