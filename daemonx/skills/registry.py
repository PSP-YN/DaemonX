"""
Reusable Automation Skills Registry
Enables modular composition of device actions, perception, and data operations.
"""
from typing import Any, Callable
from pydantic import BaseModel, Field


class AutomationSkill(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    preconditions: list[str] = Field(default_factory=list)
    recovery_strategy: str = "retry_once"
    required_permissions: list[str] = Field(default_factory=list)


class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, AutomationSkill] = {}
        self._executors: dict[str, Callable[..., Any]] = {}
        self._register_default_skills()

    def register(self, skill: AutomationSkill, executor: Callable[..., Any]):
        self._skills[skill.name] = skill
        self._executors[skill.name] = executor

    def get_skill(self, name: str) -> AutomationSkill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[AutomationSkill]:
        return list(self._skills.values())

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self._executors:
            raise ValueError(f"Skill '{name}' is not registered.")
        return self._executors[name](**kwargs)

    def _register_default_skills(self):
        default_skills = [
            AutomationSkill(
                name="android_open_app",
                description="Launches an Android application and verifies foreground transition",
                input_schema={"package_name": "str"},
                output_schema={"success": "bool", "foreground": "str"}
            ),
            AutomationSkill(
                name="android_inspect_screen",
                description="Performs multi-modal perception combining XML hierarchy, OCR, and CV",
                input_schema={"run_ocr": "bool"},
                output_schema={"observation": "dict"}
            ),
            AutomationSkill(
                name="android_capture_screenshot",
                description="Captures live screen buffer and decodes into PNG",
                input_schema={},
                output_schema={"saved_path": "str", "dimensions": "list"}
            ),
            AutomationSkill(
                name="android_scroll",
                description="Performs smooth directional scroll",
                input_schema={"direction": "str", "distance_ratio": "float"},
                output_schema={"success": "bool"}
            ),
            AutomationSkill(
                name="android_find_element",
                description="Finds interactive UI element by text, id, or description",
                input_schema={"text": "str", "resource_id": "str"},
                output_schema={"element": "dict"}
            ),
            AutomationSkill(
                name="gallery_inventory",
                description="Discovers and hashes screenshots without modifying them",
                input_schema={"directory": "str"},
                output_schema={"inventory": "list"}
            ),
            AutomationSkill(
                name="gallery_process_screenshots",
                description="Performs OCR and entity extraction on pending screenshots",
                input_schema={"directory": "str"},
                output_schema={"processed_count": "int"}
            ),
            AutomationSkill(
                name="gallery_find_duplicates",
                description="Checks if an image matches existing records via pHash or sha256",
                input_schema={"sha256": "str", "phash": "str"},
                output_schema={"is_duplicate": "bool"}
            ),
            AutomationSkill(
                name="instagram_open_saved",
                description="Navigates safely to Instagram Saved collection",
                input_schema={},
                output_schema={"success": "bool"}
            ),
            AutomationSkill(
                name="instagram_extract_reel",
                description="Extracts creator, caption, hashtags, and on-screen text from active reel",
                input_schema={},
                output_schema={"reel_data": "dict"}
            ),
            AutomationSkill(
                name="instagram_process_collection",
                description="Iteratively inspects and records saved reels in active view",
                input_schema={"max_items": "int"},
                output_schema={"processed_count": "int"}
            ),
            AutomationSkill(
                name="knowledge_search",
                description="Queries SQLite FTS5 index for full-text matches",
                input_schema={"query": "str", "limit": "int"},
                output_schema={"results": "list"}
            ),
            AutomationSkill(
                name="knowledge_export",
                description="Exports knowledge records into JSON, CSV, or Markdown",
                input_schema={"format": "str"},
                output_schema={"content": "str"}
            ),
            AutomationSkill(
                name="cleanup_preview",
                description="Generates non-destructive preview of eligible cleanup files",
                input_schema={},
                output_schema={"preview": "dict"}
            ),
            AutomationSkill(
                name="cleanup_verified",
                description="Moves verified processed files into reversible quarantine vault",
                input_schema={"media_id": "str", "approved": "bool"},
                output_schema={"quarantined": "bool"}
            )
        ]

        for s in default_skills:
            self.register(s, lambda **kw: {"status": "skill_executed", "params": kw})
