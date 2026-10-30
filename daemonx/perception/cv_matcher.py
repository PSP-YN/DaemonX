"""
OpenCV Computer Vision Engine for Template Matching, Visual Diffing, and Change Detection
"""
import numpy as np
import cv2
from PIL import Image
import imagehash
from daemonx.core.exceptions import PerceptionError


class CVMatcher:
    @staticmethod
    def pil_to_cv2(image: Image.Image) -> np.ndarray:
        """Converts PIL Image to OpenCV BGR array."""
        rgb = np.array(image.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    @classmethod
    def match_template(cls, screen: Image.Image, template: Image.Image, threshold: float = 0.85) -> list[dict]:
        """
        Finds occurrences of template image within screen image using normalized correlation.
        Returns list of matching rectangles: [{'bounds': [x1, y1, x2, y2], 'confidence': float}]
        """
        img_bgr = cls.pil_to_cv2(screen)
        tmpl_bgr = cls.pil_to_cv2(template)

        th, tw = tmpl_bgr.shape[:2]
        if img_bgr.shape[0] < th or img_bgr.shape[1] < tw:
            return []

        res = cv2.matchTemplate(img_bgr, tmpl_bgr, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        matches = []
        for pt in zip(*loc[::-1]):  # (x, y)
            x, y = int(pt[0]), int(pt[1])
            conf = float(res[y, x])
            matches.append({
                "bounds": [x, y, x + tw, y + th],
                "confidence": round(conf, 4)
            })

        # Non-maximum suppression to filter overlapping duplicate hits
        return cls._nms(matches, overlap_threshold=0.3)

    @classmethod
    def compute_screen_difference(cls, img1: Image.Image, img2: Image.Image) -> float:
        """
        Calculates normalized visual difference ratio between two screenshots [0.0 = identical, 1.0 = completely different].
        """
        cv1 = cls.pil_to_cv2(img1)
        cv2_img = cls.pil_to_cv2(img2)

        if cv1.shape != cv2_img.shape:
            cv2_img = cv2.resize(cv2_img, (cv1.shape[1], cv1.shape[0]))

        gray1 = cv2.cvtColor(cv1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        non_zero = np.count_nonzero(diff > 25)
        total_pixels = diff.shape[0] * diff.shape[1]
        return round(float(non_zero / total_pixels), 4)

    @staticmethod
    def get_perceptual_hash(image: Image.Image) -> str:
        """Computes 64-bit perceptual hash (pHash) string."""
        return str(imagehash.phash(image))

    @staticmethod
    def _nms(matches: list[dict], overlap_threshold: float = 0.3) -> list[dict]:
        if not matches:
            return []

        # Sort by confidence descending
        matches = sorted(matches, key=lambda m: m["confidence"], reverse=True)
        picked = []

        for m in matches:
            b1 = m["bounds"]
            overlap = False
            for p in picked:
                b2 = p["bounds"]
                # Compute IoU
                x_left = max(b1[0], b2[0])
                y_top = max(b1[1], b2[1])
                x_right = min(b1[2], b2[2])
                y_bottom = min(b1[3], b2[3])

                if x_right > x_left and y_bottom > y_top:
                    intersection = (x_right - x_left) * (y_bottom - y_top)
                    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
                    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
                    union = area1 + area2 - intersection
                    iou = intersection / union if union > 0 else 0
                    if iou > overlap_threshold:
                        overlap = True
                        break
            if not overlap:
                picked.append(m)

        return picked
