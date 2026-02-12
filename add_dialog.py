"""
ClipTray - Add / Edit Clip Dialog
A modal overlay dialog for creating or editing text clips.
Features a title field, text area, color picker, and a macro builder toggle.
When macro mode is on, users can build sequences of text + keyboard actions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QSizePolicy,
    QGraphicsDropShadowEffect, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor

from clip_manager import ClipManager, TextStep, ActionStep
from macro_builder import MacroBuilder


class MacroToggle(QWidget):
    """A compact toggle for switching between simple text and macro mode."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedHeight(32)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel()
        layout.addWidget(self.text_label)

        layout.addStretch()

        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedSize(44, 24)
        self.toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_btn.clicked.connect(self._on_toggle)
        layout.addWidget(self.toggle_btn)

        self._update_visual()

    def _on_toggle(self):
        self._checked = not self._checked
        self._update_visual()
        self.toggled.emit(self._checked)

    def isChecked(self):
        return self._checked

    def _update_visual(self):
        if self._checked:
            self.icon_label.setText("\u26a1")
            self.text_label.setText("Macro Mode")
            self.text_label.setStyleSheet(
                "color: #6C8EFF; font-size: 13px; font-weight: 600; background: transparent; border: none;"
            )
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6C8EFF;
                    border: none;
                    border-radius: 12px;
                }
            """)
        else:
            self.icon_label.setText("\U0001f4dd")
            self.text_label.setText("Simple Text")
            self.text_label.setStyleSheet(
                "color: #6C7086; font-size: 13px; font-weight: 500; background: transparent; border: none;"
            )
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #45475A;
                    border: none;
                    border-radius: 12px;
                }
            """)


class AddEditDialog(QWidget):
    """
    Floating dialog for creating or editing a clip.
    Appears over the overlay with its own dimmed backdrop.
    Supports both simple text mode and macro mode (text + keyboard actions).
    """

    # Signals
    saved = pyqtSignal()       # Emitted after save — parent should refresh
    cancelled = pyqtSignal()   # Emitted on cancel

    COLORS = ClipManager.COLORS

    def __init__(self, parent=None, clip=None):
        """
        Args:
            parent: Parent widget (the overlay).
            clip: If provided, edit this clip. Otherwise create a new one.
        """
        super().__init__(parent)
        self.clip = clip
        self.selected_color = clip.color if clip else self.COLORS[0]
        self.color_buttons = []

        self.setObjectName("DialogOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._populate()

    def _build_ui(self):
        """Construct the dialog UI."""
        # Full-size overlay container
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # The dialog panel
        self.panel = QWidget()
        self.panel.setObjectName("DialogPanel")
        self.panel.setFixedWidth(480)
        self.panel.setMaximumHeight(650)

        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.setSpacing(14)

        # \u2500\u2500 Title \u2500\u2500
        title_text = "Edit Clip" if self.clip else "New Clip"
        title = QLabel(title_text)
        title.setObjectName("DialogTitle")
        panel_layout.addWidget(title)

        # \u2500\u2500 Clip Title Input \u2500\u2500
        lbl_title = QLabel("Title")
        lbl_title.setObjectName("DialogLabel")
        panel_layout.addWidget(lbl_title)

        self.title_input = QLineEdit()
        self.title_input.setObjectName("DialogInput")
        self.title_input.setPlaceholderText("e.g.  Email Signature")
        self.title_input.setMaxLength(100)
        panel_layout.addWidget(self.title_input)

        # \u2500\u2500 Macro Mode Toggle \u2500\u2500
        self.macro_toggle = MacroToggle(
            checked=(self.clip.is_macro if self.clip else False)
        )
        self.macro_toggle.toggled.connect(self._on_macro_toggled)
        panel_layout.addWidget(self.macro_toggle)

        # \u2500\u2500 Simple Text Input (visible when macro mode is OFF) \u2500\u2500
        self.simple_text_container = QWidget()
        simple_layout = QVBoxLayout(self.simple_text_container)
        simple_layout.setContentsMargins(0, 0, 0, 0)
        simple_layout.setSpacing(6)

        lbl_text = QLabel("Text content")
        lbl_text.setObjectName("DialogLabel")
        simple_layout.addWidget(lbl_text)

        self.text_input = QTextEdit()
        self.text_input.setObjectName("DialogTextEdit")
        self.text_input.setPlaceholderText("Paste or type the text you want to save...")
        self.text_input.setMinimumHeight(100)
        self.text_input.setMaximumHeight(160)
        simple_layout.addWidget(self.text_input)

        panel_layout.addWidget(self.simple_text_container)

        # \u2500\u2500 Macro Builder (visible when macro mode is ON) \u2500\u2500
        self.macro_container = QWidget()
        macro_layout = QVBoxLayout(self.macro_container)
        macro_layout.setContentsMargins(0, 0, 0, 0)
        macro_layout.setSpacing(6)

        macro_header = QHBoxLayout()
        lbl_macro = QLabel("Build your macro")
        lbl_macro.setObjectName("DialogLabel")
        macro_header.addWidget(lbl_macro)

        macro_hint = QLabel("Add text and keyboard actions in sequence")
        macro_hint.setStyleSheet("color: #45475A; font-size: 11px; background: transparent; border: none;")
        macro_header.addStretch()
        macro_header.addWidget(macro_hint)
        macro_layout.addLayout(macro_header)

        self.macro_builder = MacroBuilder()
        macro_layout.addWidget(self.macro_builder)

        panel_layout.addWidget(self.macro_container)
        self.macro_container.hide()  # Hidden by default

        # \u2500\u2500 Color Picker \u2500\u2500
        lbl_color = QLabel("Accent Color")
        lbl_color.setObjectName("DialogLabel")
        panel_layout.addWidget(lbl_color)

        color_layout = QHBoxLayout()
        color_layout.setSpacing(8)
        color_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for color in self.COLORS:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setProperty("color_value", color)
            self._update_color_btn_style(btn, color, color == self.selected_color)
            btn.clicked.connect(lambda checked, c=color, b=btn: self._select_color(c))
            color_layout.addWidget(btn)
            self.color_buttons.append(btn)

        panel_layout.addLayout(color_layout)

        # \u2500\u2500 Buttons \u2500\u2500
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CancelButton")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Clip")
        save_btn.setObjectName("SaveButton")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        panel_layout.addLayout(btn_layout)

        overlay_layout.addWidget(self.panel)

    def _populate(self):
        """Fill fields if editing an existing clip."""
        if self.clip:
            self.title_input.setText(self.clip.title)
            self.text_input.setPlainText(self.clip.text)

            if self.clip.is_macro and self.clip.steps:
                self.macro_toggle._checked = True
                self.macro_toggle._update_visual()
                self.macro_builder.set_steps(self.clip.steps)
                self.simple_text_container.hide()
                self.macro_container.show()

    def _on_macro_toggled(self, is_macro: bool):
        """Toggle between simple text and macro mode."""
        if is_macro:
            # Switching to macro mode \u2014 pre-fill with current text
            current_text = self.text_input.toPlainText().strip()
            if current_text and not self.macro_builder.steps[0].value:
                self.macro_builder.steps[0].value = current_text
                self.macro_builder._refresh_ui()
            self.simple_text_container.hide()
            self.macro_container.show()
        else:
            # Switching to simple text
            plain = self.macro_builder.get_plain_text()
            if plain and not self.text_input.toPlainText().strip():
                self.text_input.setPlainText(plain)
            self.macro_container.hide()
            self.simple_text_container.show()

    def _update_color_btn_style(self, btn, color, selected):
        """Set the style of a color picker button."""
        obj_name = "ColorPickerBtnSelected" if selected else "ColorPickerBtn"
        btn.setObjectName(obj_name)
        btn.setStyleSheet(f"background-color: {color};")
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def _select_color(self, color):
        """Handle color selection."""
        self.selected_color = color
        for btn in self.color_buttons:
            btn_color = btn.property("color_value")
            is_selected = (btn_color == color)
            self._update_color_btn_style(btn, btn_color, is_selected)

    def _on_save(self):
        """Validate and signal save."""
        title = self.title_input.text().strip()
        is_macro = self.macro_toggle.isChecked()

        if not title:
            self.title_input.setFocus()
            self.title_input.setStyleSheet(
                "border: 1px solid rgba(255, 80, 80, 0.6); border-radius: 10px;"
            )
            return

        if is_macro:
            steps = self.macro_builder.get_steps()
            # Build plain text from text steps for preview
            text_parts = []
            for s in steps:
                if isinstance(s, TextStep):
                    text_parts.append(s.value)
            text = "".join(text_parts).strip()

            if not text and not any(isinstance(s, ActionStep) for s in steps):
                return  # Nothing to save

            self.result_title = title
            self.result_text = text if text else f"[Macro: {title}]"
            self.result_color = self.selected_color
            self.result_is_macro = True
            self.result_steps = steps
        else:
            text = self.text_input.toPlainText().strip()
            if not text:
                self.text_input.setFocus()
                return

            self.result_title = title
            self.result_text = text
            self.result_color = self.selected_color
            self.result_is_macro = False
            self.result_steps = []

        self.saved.emit()

    def _on_cancel(self):
        """Signal cancel."""
        self.cancelled.emit()

    def keyPressEvent(self, event):
        """Close on Escape (unless macro builder is capturing)."""
        if event.key() == Qt.Key.Key_Escape:
            # Don't close if macro builder is capturing a key
            if hasattr(self, 'macro_builder') and self.macro_builder.capture_widget.isVisible():
                self.macro_builder.capture_widget.hide()
                return
            self._on_cancel()
        super().keyPressEvent(event)
