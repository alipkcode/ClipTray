"""
ClipTray - Clip Data Manager
Handles loading, saving, adding, editing, and deleting saved text clips.
Clips are stored in a JSON file next to the executable.
Clips can be simple text or macros (sequences of text + keyboard actions).
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union


# ── Step types for macro clips ──────────────────────────────

@dataclass
class TextStep:
    """A step that types text."""
    type: str = "text"
    value: str = ""

    def to_dict(self) -> dict:
        return {"type": self.type, "value": self.value}

    @classmethod
    def from_dict(cls, d: dict) -> "TextStep":
        return cls(value=d.get("value", ""))


@dataclass
class ActionStep:
    """A step that performs a keyboard action (key press or hotkey combo)."""
    type: str = "action"
    keys: List[str] = field(default_factory=list)  # e.g. ["ctrl", "a"] or ["enter"]
    label: str = ""  # Human-readable label, e.g. "Ctrl + A" or "Enter"

    def to_dict(self) -> dict:
        return {"type": self.type, "keys": self.keys, "label": self.label}

    @classmethod
    def from_dict(cls, d: dict) -> "ActionStep":
        return cls(keys=d.get("keys", []), label=d.get("label", ""))


def step_from_dict(d: dict) -> Union[TextStep, ActionStep]:
    """Factory to create the right step type from a dict."""
    if d.get("type") == "action":
        return ActionStep.from_dict(d)
    return TextStep.from_dict(d)


@dataclass
class Clip:
    """
    Represents a single saved clip.
    - Simple clip: just 'text' (backward compatible).
    - Macro clip: 'is_macro' is True and 'steps' holds a sequence
      of TextStep and ActionStep objects.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    text: str = ""
    color: str = "#6C8EFF"
    is_macro: bool = False
    steps: List[Union[TextStep, ActionStep]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "color": self.color,
            "is_macro": self.is_macro,
            "steps": [s.to_dict() for s in self.steps] if self.steps else [],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Clip":
        steps_data = data.get("steps", [])
        steps = [step_from_dict(s) for s in steps_data] if steps_data else []
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            text=data.get("text", ""),
            color=data.get("color", "#6C8EFF"),
            is_macro=data.get("is_macro", False),
            steps=steps,
        )

    def get_preview_text(self) -> str:
        """Get a human-readable preview of this clip's content."""
        if not self.is_macro or not self.steps:
            return self.text
        parts = []
        for step in self.steps:
            if isinstance(step, TextStep) and step.value.strip():
                preview = step.value.replace("\n", " ").strip()
                if len(preview) > 30:
                    preview = preview[:27] + "..."
                parts.append(preview)
            elif isinstance(step, ActionStep):
                parts.append(f"[{step.label}]")
        return " → ".join(parts) if parts else self.text


class ClipManager:
    """Manages the collection of saved clips with JSON persistence."""

    # Predefined accent colors for new clips (cycles through these)
    COLORS = [
        "#6C8EFF",  # Blue
        "#FF6C8E",  # Pink
        "#8EFF6C",  # Green
        "#FFD26C",  # Gold
        "#6CFFD2",  # Teal
        "#D26CFF",  # Purple
        "#FF8E6C",  # Orange
        "#6CD2FF",  # Sky blue
    ]

    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            # Store clips.json next to the script/exe
            base_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(base_dir, "clips.json")
        self.filepath = filepath
        self.clips: List[Clip] = []
        self._color_index = 0
        self.load()

    # ── Persistence ──────────────────────────────────────────────

    def load(self):
        """Load clips from the JSON file."""
        if not os.path.exists(self.filepath):
            self.clips = []
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.clips = [Clip.from_dict(c) for c in data.get("clips", [])]
        except (json.JSONDecodeError, IOError):
            self.clips = []

    def save(self):
        """Persist all clips to the JSON file."""
        data = {"clips": [c.to_dict() for c in self.clips]}
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"[ClipTray] Error saving clips: {e}")

    # ── CRUD Operations ──────────────────────────────────────────

    def add_clip(self, title: str, text: str, color: Optional[str] = None,
                 is_macro: bool = False, steps: Optional[List] = None) -> Clip:
        """Add a new clip and save."""
        if color is None:
            color = self.COLORS[self._color_index % len(self.COLORS)]
            self._color_index += 1
        clip = Clip(title=title, text=text, color=color,
                    is_macro=is_macro, steps=steps or [])
        self.clips.insert(0, clip)  # Newest first
        self.save()
        return clip

    def update_clip(self, clip_id: str, title: str, text: str,
                    is_macro: bool = False, steps: Optional[List] = None) -> Optional[Clip]:
        """Update an existing clip by ID."""
        for clip in self.clips:
            if clip.id == clip_id:
                clip.title = title
                clip.text = text
                clip.is_macro = is_macro
                clip.steps = steps or []
                self.save()
                return clip
        return None

    def delete_clip(self, clip_id: str) -> bool:
        """Delete a clip by ID."""
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                self.clips.pop(i)
                self.save()
                return True
        return False

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        """Get a clip by ID."""
        for clip in self.clips:
            if clip.id == clip_id:
                return clip
        return None

    def search(self, query: str) -> List[Clip]:
        """Search clips by title or text content."""
        query = query.lower().strip()
        if not query:
            return self.clips
        return [
            c for c in self.clips
            if query in c.title.lower() or query in c.text.lower()
        ]
