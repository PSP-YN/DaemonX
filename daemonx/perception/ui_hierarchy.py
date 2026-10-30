"""
Android UI Hierarchy Parser for uiautomator XML Dumps
"""
import re
import xml.etree.ElementTree as ET
from daemonx.core.types import UIElement
from daemonx.core.exceptions import PerceptionError


BOUNDS_REGEX = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


class UIHierarchyParser:
    @staticmethod
    def parse_bounds(bounds_str: str) -> list[int]:
        """Parses '[x1,y1][x2,y2]' into [x1, y1, x2, y2]."""
        match = BOUNDS_REGEX.match(bounds_str)
        if match:
            return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]
        return [0, 0, 0, 0]

    @classmethod
    def parse_xml(cls, xml_content: str) -> list[UIElement]:
        """Parses uiautomator XML string into a flat list of UIElements."""
        if not xml_content or not xml_content.strip():
            return []

        try:
            root = ET.fromstring(xml_content.strip())
        except ET.ParseError as e:
            raise PerceptionError(f"Malformed accessibility XML: {e}")

        elements = []
        elem_counter = 0

        for node in root.iter("node"):
            text = node.get("text", "")
            resource_id = node.get("resource-id", "")
            content_desc = node.get("content-desc", "")
            class_name = node.get("class", "")
            package_name = node.get("package", "")
            clickable = node.get("clickable", "false").lower() == "true"
            scrollable = node.get("scrollable", "false").lower() == "true"
            enabled = node.get("enabled", "true").lower() == "true"
            focused = node.get("focused", "false").lower() == "true"
            bounds = cls.parse_bounds(node.get("bounds", ""))

            # Filter out non-informative root-level containers with zero dimensions
            if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
                continue

            elem_id = f"elem_{elem_counter}"
            elem_counter += 1

            elements.append(
                UIElement(
                    id=elem_id,
                    resource_id=resource_id,
                    text=text,
                    content_desc=content_desc,
                    class_name=class_name,
                    package_name=package_name,
                    clickable=clickable,
                    scrollable=scrollable,
                    enabled=enabled,
                    focused=focused,
                    bounds=bounds,
                    confidence=1.0
                )
            )

        return elements
