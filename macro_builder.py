"""
ClipTray - Macro Builder Widget
A visual builder for creating clip macros — sequences of text segments
and keyboard actions. Users can add text blocks with "+" buttons between
them to insert key actions (captured by listening for actual key presses).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QSizePolicy, QScrollArea,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QCursor, QKeySequence

from clip_manager import TextStep, ActionStep


# ── Key name mapping (Qt key → pyautogui key name) ──

QT_KEY_TO_NAME = {
    Qt.Key.Key_Return: "enter",
    Qt.Key.Key_Enter: "enter",
    Qt.Key.Key_Tab: "tab",
    Qt.Key.Key_Backspace: "backspace",
    Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_Escape: "escape",
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_Home: "home",
    Qt.Key.Key_End: "end",
    Qt.Key.Key_PageUp: "pageup",
    Qt.Key.Key_PageDown: "pagedown",
    Qt.Key.Key_F1: "f1", Qt.Key.Key_F2: "f2", Qt.Key.Key_F3: "f3",
    Qt.Key.Key_F4: "f4", Qt.Key.Key_F5: "f5", Qt.Key.Key_F6: "f6",
    Qt.Key.Key_F7: "f7", Qt.Key.Key_F8: "f8", Qt.Key.Key_F9: "f9",
    Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
    Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_CapsLock: "capslock",
    Qt.Key.Key_Print: "printscreen",
}

# Modifier-only keys (we track these but they aren't standalone actions)
MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
}


def key_event_to_action(event) -> tuple:
    """
    Convert a QKeyEvent to (keys_list, label_str) for an ActionStep.
    Returns (None, None) if it's just a modifier press with no actual key.
    """
    modifiers = event.modifiers()
    key = event.key()

    # Skip if it's only a modifier key
    if key in MODIFIER_KEYS:
        return None, None

    keys = []
    label_parts = []

    if modifiers & Qt.KeyboardModifier.ControlModifier:
        keys.append("ctrl")
        label_parts.append("Ctrl")
    if modifiers & Qt.KeyboardModifier.AltModifier:
        keys.append("alt")
        label_parts.append("Alt")
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        keys.append("shift")
        label_parts.append("Shift")
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        keys.append("win")
        label_parts.append("Win")

    # Get the actual key name
    if key in QT_KEY_TO_NAME:
        key_name = QT_KEY_TO_NAME[key]
        label_parts.append(key_name.capitalize())
    else:
        # Try to get the text representation
        text = event.text()
        if text and text.isprintable():
            key_name = text.lower()
            label_parts.append(text.upper())
        else:
            return None, None

    keys.append(key_name)
    label = " + ".join(label_parts)
    return keys, label


class KeyCaptureButton(QPushButton):
    """
    A button that, when clicked, starts listening for a key press.
    The captured key combination is emitted as an ActionStep.
    """
    action_captured = pyqtSignal(object)  # emits ActionStep

    def __init__(self, parent=None):
        super().__init__("Press any key...", parent)
        self.setObjectName("KeyCaptureBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._listening = False

    def start_listening(self):
        """Start capturing the next key press."""
        self._listening = True
        self.setText("⌨  Waiting for key press...")
        self.setStyleSheet("""
            background-color: rgba(108, 142, 255, 0.15);
            border: 1px dashed rgba(108, 142, 255, 0.5);
            border-radius: 8px;
            color: #6C8EFF;
            font-size: 13px;
            padding: 8px 16px;
        """)
        self.setFocus()

    def keyPressEvent(self, event):
        if self._listening:
            keys, label = key_event_to_action(event)
            if keys is not None:
                self._listening = False
                action = ActionStep(keys=keys, label=label)
                self.action_captured.emit(action)
                return
        super().keyPressEvent(event)


class ActionBadge(QWidget):
    """
    A small badge showing a captured key action, e.g. [Enter] or [Ctrl + A].
    Has a delete button to remove it.
    """
    removed = pyqtSignal(int)  # index of this badge

    def __init__(self, action: ActionStep, index: int, parent=None):
        super().__init__(parent)
        self.action = action
        self.index = index
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 6, 4)
        layout.setSpacing(6)

        # Key icon
        icon = QLabel("⌨")
        icon.setStyleSheet("color: #6C8EFF; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(icon)

        # Label
        lbl = QLabel(action.label)
        lbl.setObjectName("ActionBadgeLabel")
        layout.addWidget(lbl)

        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setObjectName("ActionBadgeDelete")
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setFixedSize(20, 20)
        del_btn.clicked.connect(lambda: self.removed.emit(self.index))
        layout.addWidget(del_btn)

        self.setObjectName("ActionBadge")


class AddActionButton(QPushButton):
    """A styled '+ Add Action' button placed between text segments."""

    def __init__(self, index: int, parent=None):
        super().__init__("＋ Action", parent)
        self.index = index
        self.setObjectName("AddActionBtn")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(28)


class MacroBuilder(QWidget):
    """
    The full macro builder UI.
    Shows a sequence of:  [+ action]  [text area]  [+ action]  [text area]  ...
    Users build a sequence by adding text and key actions between them.
    
    The data structure is a list of steps: TextStep and ActionStep interleaved.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps = []  # List of TextStep / ActionStep
        self._capture_insert_index = -1  # Where to insert the next captured action

        self._build_ui()
        # Start with one empty text step
        self.steps.append(TextStep(value=""))
        self._refresh_ui()

    def _build_ui(self):
        """Build the scrollable builder area."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for the steps
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setMaximumHeight(260)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 5px; margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.12); border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none; border: none; height: 0px;
            }
        """)

        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(4)
        self.steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.steps_container)
        main_layout.addWidget(self.scroll)

        # Key capture overlay (hidden by default)
        self.capture_widget = KeyCaptureButton(self)
        self.capture_widget.action_captured.connect(self._on_action_captured)
        self.capture_widget.hide()

    def _refresh_ui(self):
        """Rebuild the visual step list from self.steps."""
        # Clear existing widgets
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for i, step in enumerate(self.steps):
            # Add "+" action button ABOVE each step
            add_btn_top = AddActionButton(index=i)
            add_btn_top.clicked.connect(lambda checked, idx=i: self._on_add_action(idx))
            self.steps_layout.addWidget(add_btn_top)

            if isinstance(step, TextStep):
                # Text editor
                text_widget = self._create_text_widget(step, i)
                self.steps_layout.addWidget(text_widget)
            elif isinstance(step, ActionStep):
                # Action badge
                badge = ActionBadge(step, i)
                badge.removed.connect(self._on_remove_step)
                self.steps_layout.addWidget(badge)

        # Final "+" button at the bottom
        add_btn_bottom = AddActionButton(index=len(self.steps))
        add_btn_bottom.clicked.connect(lambda checked, idx=len(self.steps): self._on_add_action(idx))
        self.steps_layout.addWidget(add_btn_bottom)

    def _create_text_widget(self, step: TextStep, index: int) -> QWidget:
        """Create a text editor widget for a TextStep."""
        container = QWidget()
        container.setObjectName("MacroTextContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        editor = QTextEdit()
        editor.setObjectName("MacroTextEdit")
        editor.setPlaceholderText("Type text here...")
        editor.setPlainText(step.value)
        editor.setMinimumHeight(50)
        editor.setMaximumHeight(80)
        editor.setStyleSheet("""
            QTextEdit {
                background-color: #181825;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                color: #CDD6F4;
                font-size: 13px;
                padding: 8px 10px;
            }
            QTextEdit:focus {
                border: 1px solid rgba(108, 142, 255, 0.4);
            }
        """)
        # Auto-save text as user types
        editor.textChanged.connect(lambda idx=index, e=editor: self._on_text_changed(idx, e))
        layout.addWidget(editor, 1)

        # Delete button (only if there are multiple steps)
        if len(self.steps) > 1:
            del_btn = QPushButton("✕")
            del_btn.setObjectName("ActionBadgeDelete")
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setFixedSize(22, 22)
            del_btn.clicked.connect(lambda checked, idx=index: self._on_remove_step(idx))
            layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        return container

    def _on_text_changed(self, index: int, editor: QTextEdit):
        """Update the step text when user types."""
        if 0 <= index < len(self.steps) and isinstance(self.steps[index], TextStep):
            self.steps[index].value = editor.toPlainText()

    def _on_add_action(self, insert_index: int):
        """User clicked '+ Action' — start key capture."""
        self._capture_insert_index = insert_index
        self.capture_widget.show()
        self.capture_widget.start_listening()

    def _on_action_captured(self, action: ActionStep):
        """A key was captured — insert it and add a text step after if needed."""
        self.capture_widget.hide()
        idx = self._capture_insert_index

        # Insert the action step
        self.steps.insert(idx, action)

        # If the action is between two non-text steps or at a boundary,
        # ensure there's a text step after it for the user to type in
        next_idx = idx + 1
        if next_idx >= len(self.steps) or isinstance(self.steps[next_idx], ActionStep):
            self.steps.insert(next_idx, TextStep(value=""))

        # Also ensure there's a text step before if needed
        if idx == 0 or isinstance(self.steps[idx - 1], ActionStep):
            self.steps.insert(idx, TextStep(value=""))

        self._refresh_ui()

    def _on_remove_step(self, index: int):
        """Remove a step and merge adjacent text steps if needed."""
        if 0 <= index < len(self.steps):
            self.steps.pop(index)

            # Merge adjacent text steps
            merged = []
            for step in self.steps:
                if merged and isinstance(merged[-1], TextStep) and isinstance(step, TextStep):
                    merged[-1].value += step.value
                else:
                    merged.append(step)
            self.steps = merged

            # Ensure at least one text step
            if not self.steps:
                self.steps = [TextStep(value="")]

            self._refresh_ui()

    def get_steps(self) -> list:
        """Return the current steps, filtering out empty text steps between actions."""
        result = []
        for step in self.steps:
            if isinstance(step, TextStep):
                # Keep all text steps (even empty ones between actions, user may want those)
                result.append(step)
            elif isinstance(step, ActionStep):
                result.append(step)
        return result

    def set_steps(self, steps: list):
        """Load steps into the builder (for editing existing macros)."""
        self.steps = steps if steps else [TextStep(value="")]
        self._refresh_ui()

    def get_plain_text(self) -> str:
        """Get all text content combined (for preview/fallback)."""
        parts = []
        for step in self.steps:
            if isinstance(step, TextStep):
                parts.append(step.value)
            elif isinstance(step, ActionStep):
                parts.append(f"[{step.label}]")
        return "".join(parts)
