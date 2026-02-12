"""
ClipTray - Clip Data Manager
Handles loading, saving, adding, editing, and deleting saved text clips.
Clips are stored in a JSON file next to the executable.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Clip:
    """Represents a single saved text clip."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    text: str = ""
    color: str = "#6C8EFF"  # Default accent color for the clip card

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Clip":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            text=data.get("text", ""),
            color=data.get("color", "#6C8EFF"),
        )


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

    def add_clip(self, title: str, text: str, color: Optional[str] = None) -> Clip:
        """Add a new clip and save."""
        if color is None:
            color = self.COLORS[self._color_index % len(self.COLORS)]
            self._color_index += 1
        clip = Clip(title=title, text=text, color=color)
        self.clips.insert(0, clip)  # Newest first
        self.save()
        return clip

    def update_clip(self, clip_id: str, title: str, text: str) -> Optional[Clip]:
        """Update an existing clip by ID."""
        for clip in self.clips:
            if clip.id == clip_id:
                clip.title = title
                clip.text = text
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
