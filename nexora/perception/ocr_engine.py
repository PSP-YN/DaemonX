"""
High-Performance Local OCR Engine Powered by Native Tesseract 5.5.3
"""
from PIL import Image
import pytesseract
from nexora.core.exceptions import PerceptionError


class OCREngine:
    def __init__(self, tesseract_cmd: str = "/usr/bin/tesseract", languages: str = "eng"):
        self.tesseract_cmd = tesseract_cmd
        self.languages = languages
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text(self, image: Image.Image) -> str:
        """Extracts plain text string from PIL Image."""
        try:
            return pytesseract.image_to_string(image, lang=self.languages).strip()
        except Exception as e:
            raise PerceptionError(f"Tesseract OCR text extraction failed: {e}")

    def extract_data(self, image: Image.Image, min_confidence: float = 30.0) -> list[dict]:
        """
        Extracts words with bounding boxes, confidence scores, and line numbers.
        Returns list of dicts: [{'text': str, 'confidence': float, 'bounds': [x1, y1, x2, y2]}]
        """
        try:
            data = pytesseract.image_to_data(image, lang=self.languages, output_type=pytesseract.Output.DICT)
        except Exception as e:
            raise PerceptionError(f"Tesseract OCR data extraction failed: {e}")

        results = []
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])
            if text and conf >= min_confidence:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                results.append({
                    "text": text,
                    "confidence": conf / 100.0,
                    "bounds": [x, y, x + w, y + h]
                })
        return results
