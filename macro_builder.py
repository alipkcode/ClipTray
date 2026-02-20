"""
ClipTray - Macro Builder Widget
A visual builder for creating clip macros: sequences of text segments
interleaved with keyboard actions. The UI uses a vertical timeline
layout with step numbers, clean text editors, and inline action badges.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QSizePolicy, QScrollArea,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QCursor, QKeySequence

from clip_manager import TextStep, ActionStep


# ---- Key name mapping (Qt key -> pyautogui key name) ----

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

MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
}


def key_event_to_action(event) -> tuple:
    """Convert a QKeyEvent to (keys_list, label_str) for an ActionStep."""
    modifiers = event.modifiers()
    key = event.key()

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

    if key in QT_KEY_TO_NAME:
        key_name = QT_KEY_TO_NAME[key]
        label_parts.append(key_name.capitalize())
    else:
        text = event.text()
        if text and text.isprintable():
            key_name = text.lower()
            label_parts.append(text.upper())
        else:
            return None, None

    keys.append(key_name)
    label = " + ".join(label_parts)
    return keys, label


# ---- Individual step widgets ----


class StepTextEditor(QWidget):
    """A text editor row for a TextStep, with a step number indicator and delete button."""
    text_changed = pyqtSignal(int, str)  # index, new_text
    removed = pyqtSignal(int)

    def __init__(self, step: TextStep, index: int, step_number: int,
                 can_delete: bool = True, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("StepRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Step number pill
        num_label = QLabel(str(step_number))
        num_label.setObjectName("StepNumber")
        num_label.setFixedSize(24, 24)
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(num_label, alignment=Qt.AlignmentFlag.AlignTop)

        # Text editor
        self.editor = QTextEdit()
        self.editor.setObjectName("MacroTextEdit")
        self.editor.setPlaceholderText("Type text here...")
        self.editor.setPlainText(step.value)
        self.editor.setMinimumHeight(48)
        self.editor.setMaximumHeight(80)
        self.editor.textChanged.connect(self._on_changed)
        layout.addWidget(self.editor, 1)

        # Delete button
        if can_delete:
            del_btn = QPushButton("\u2715")
            del_btn.setObjectName("StepDeleteBtn")
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setFixedSize(22, 22)
            del_btn.setToolTip("Remove this step")
            del_btn.clicked.connect(lambda: self.removed.emit(self.index))
            layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

    def _on_changed(self):
        self.text_changed.emit(self.index, self.editor.toPlainText())


class StepActionBadge(QWidget):
    """An action badge row showing a captured key, with step number and delete."""
    removed = pyqtSignal(int)

    def __init__(self, action: ActionStep, index: int, step_number: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("StepRow")
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Step number pill
        num_label = QLabel(str(step_number))
        num_label.setObjectName("StepNumberAction")
        num_label.setFixedSize(24, 24)
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(num_label)

        # Badge container
        badge = QWidget()
        badge.setObjectName("ActionBadge")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(10, 4, 10, 4)
        badge_layout.setSpacing(6)

        icon = QLabel("\u2328")
        icon.setObjectName("ActionBadgeIcon")
        badge_layout.addWidget(icon)

        lbl = QLabel(action.label)
        lbl.setObjectName("ActionBadgeLabel")
        badge_layout.addWidget(lbl)

        badge_layout.addStretch()
        layout.addWidget(badge, 1)

        # Delete
        del_btn = QPushButton("\u2715")
        del_btn.setObjectName("StepDeleteBtn")
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setFixedSize(22, 22)
        del_btn.setToolTip("Remove this action")
        del_btn.clicked.connect(lambda: self.removed.emit(self.index))
        layout.addWidget(del_btn)


class KeyCaptureOverlay(QWidget):
    """
    An inline overlay that captures a single key press.
    Shows a pulsing prompt, then returns the captured action.
    """
    action_captured = pyqtSignal(object)  # ActionStep
    capture_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("KeyCaptureOverlay")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._listening = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("\u2328")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setObjectName("CaptureIcon")
        layout.addWidget(icon)

        prompt = QLabel("Press any key or combination...")
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prompt.setObjectName("CapturePrompt")
        layout.addWidget(prompt)

        hint = QLabel("e.g. Enter, Tab, Ctrl+A")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("CaptureHint")
        layout.addWidget(hint)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CaptureCancelBtn")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self._cancel)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def start(self):
        self._listening = True
        self.show()
        self.setFocus()
        self.grabKeyboard()

    def _stop(self):
        """Internal: stop listening and release keyboard."""
        self._listening = False
        self.releaseKeyboard()

    def _cancel(self):
        self._stop()
        self.capture_cancelled.emit()

    def keyPressEvent(self, event):
        if self._listening:
            keys, label = key_event_to_action(event)
            if keys is not None:
                self._stop()
                action = ActionStep(keys=keys, label=label)
                self.action_captured.emit(action)
                return
        super().keyPressEvent(event)


# ---- Main MacroBuilder ----


class MacroBuilder(QWidget):
    """
    The full macro builder UI with a clean vertical timeline layout.
    Each step has a number indicator. An '+ Add Action' button sits
    at the bottom. Pressing it reveals a key capture overlay.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps = []
        self._capture_insert_index = -1

        self._build_ui()
        self.steps.append(TextStep(value=""))
        self._refresh_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for steps
        self.scroll = QScrollArea()
        self.scroll.setObjectName("MacroScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(100)
        self.scroll.setMaximumHeight(280)

        self.steps_container = QWidget()
        self.steps_container.setObjectName("MacroStepsContainer")
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(4, 4, 4, 4)
        self.steps_layout.setSpacing(6)
        self.steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll.setWidget(self.steps_container)
        main_layout.addWidget(self.scroll)

        # Bottom toolbar: + Add Action
        toolbar = QWidget()
        toolbar.setObjectName("MacroToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 8, 0, 0)
        toolbar_layout.setSpacing(8)

        add_action_btn = QPushButton("\u2795  Add Action")
        add_action_btn.setObjectName("AddActionBtn")
        add_action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_action_btn.clicked.connect(self._on_add_action_clicked)
        toolbar_layout.addWidget(add_action_btn)

        add_text_btn = QPushButton("\u2795  Add Text Block")
        add_text_btn.setObjectName("AddTextBtn")
        add_text_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_text_btn.clicked.connect(self._on_add_text_clicked)
        toolbar_layout.addWidget(add_text_btn)

        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar)

        # Key capture overlay (hidden by default, shown inline when capturing)
        self.capture_widget = KeyCaptureOverlay()
        self.capture_widget.action_captured.connect(self._on_action_captured)
        self.capture_widget.capture_cancelled.connect(self._on_capture_cancelled)
        self.capture_widget.hide()
        main_layout.addWidget(self.capture_widget)

    def _refresh_ui(self):
        """Rebuild the visual step list from self.steps."""
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        can_delete = len(self.steps) > 1
        step_num = 1

        for i, step in enumerate(self.steps):
            if isinstance(step, TextStep):
                widget = StepTextEditor(
                    step, i, step_num, can_delete=can_delete
                )
                widget.text_changed.connect(self._on_text_changed)
                widget.removed.connect(self._on_remove_step)
                self.steps_layout.addWidget(widget)
            elif isinstance(step, ActionStep):
                widget = StepActionBadge(step, i, step_num)
                widget.removed.connect(self._on_remove_step)
                self.steps_layout.addWidget(widget)
            step_num += 1

    def _on_text_changed(self, index: int, text: str):
        if 0 <= index < len(self.steps) and isinstance(self.steps[index], TextStep):
            self.steps[index].value = text

    def _on_add_action_clicked(self):
        """User wants to add a keyboard action at the end."""
        self._capture_insert_index = len(self.steps)
        self.capture_widget.start()

    def _on_add_text_clicked(self):
        """Add a new empty text block at the end."""
        self.steps.append(TextStep(value=""))
        self._refresh_ui()
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _on_action_captured(self, action: ActionStep):
        """A key was captured. Insert the action step."""
        self.capture_widget.hide()
        idx = self._capture_insert_index
        self.steps.insert(idx, action)
        self._refresh_ui()
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def _on_capture_cancelled(self):
        self.capture_widget.hide()

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

            if not self.steps:
                self.steps = [TextStep(value="")]

            self._refresh_ui()

    def get_steps(self) -> list:
        """Return the current steps."""
        return list(self.steps)

    def set_steps(self, steps: list):
        """Load steps into the builder (for editing existing macros)."""
        self.steps = list(steps) if steps else [TextStep(value="")]
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
