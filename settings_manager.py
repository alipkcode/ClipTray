"""
ClipTray - Settings Manager
Handles loading and saving user preferences.
Settings are stored in settings.json next to the executable.
"""

import json
import os
from typing import Any


class SettingsManager:
    """Manages persistent user settings stored in a JSON file."""

    DEFAULTS = {
        "click_to_paste": False,  # When True, wait for user click before pasting
        "caret_companion": False,  # When True, show a small icon near the text cursor
    }

    def __init__(self, filepath: str = None):
        if filepath is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(base_dir, "settings.json")
        self.filepath = filepath
        self.settings: dict = {}
        self.load()

    def load(self):
        """Load settings from file, filling in defaults for missing keys."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.settings = {}
        else:
            self.settings = {}

        # Fill in any missing defaults
        for key, default in self.DEFAULTS.items():
            if key not in self.settings:
                self.settings[key] = default

    def save(self):
        """Save current settings to file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"[ClipTray] Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default if default is not None else self.DEFAULTS.get(key))

    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save()

    @property
    def click_to_paste(self) -> bool:
        """Whether click-to-paste mode is enabled."""
        return bool(self.get("click_to_paste", False))

    @click_to_paste.setter
    def click_to_paste(self, value: bool):
        self.set("click_to_paste", value)

    @property
    def caret_companion(self) -> bool:
        """Whether the caret companion icon is enabled."""
        return bool(self.get("caret_companion", False))

    @caret_companion.setter
    def caret_companion(self, value: bool):
        self.set("caret_companion", value)
