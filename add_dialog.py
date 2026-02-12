"""
ClipTray - Add / Edit Clip Dialog
A modal overlay dialog for creating or editing text clips.
Features a title field, text area, and color picker.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor

from clip_manager import ClipManager


class AddEditDialog(QWidget):
    """
    Floating dialog for creating or editing a clip.
    Appears over the overlay with its own dimmed backdrop.
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
        self.panel.setFixedWidth(440)
        self.panel.setMaximumHeight(520)

        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.setSpacing(16)

        # ── Title ──
        title_text = "Edit Clip" if self.clip else "New Clip"
        title = QLabel(title_text)
        title.setObjectName("DialogTitle")
        panel_layout.addWidget(title)

        # ── Clip Title Input ──
        lbl_title = QLabel("Title")
        lbl_title.setObjectName("DialogLabel")
        panel_layout.addWidget(lbl_title)

        self.title_input = QLineEdit()
        self.title_input.setObjectName("DialogInput")
        self.title_input.setPlaceholderText("e.g.  Email Signature")
        self.title_input.setMaxLength(100)
        panel_layout.addWidget(self.title_input)

        # ── Clip Text Input ──
        lbl_text = QLabel("Text content")
        lbl_text.setObjectName("DialogLabel")
        panel_layout.addWidget(lbl_text)

        self.text_input = QTextEdit()
        self.text_input.setObjectName("DialogTextEdit")
        self.text_input.setPlaceholderText("Paste or type the text you want to save...")
        self.text_input.setMinimumHeight(120)
        self.text_input.setMaximumHeight(180)
        panel_layout.addWidget(self.text_input)

        # ── Color Picker ──
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

        # ── Buttons ──
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
        text = self.text_input.toPlainText().strip()

        if not title:
            self.title_input.setFocus()
            self.title_input.setStyleSheet(
                "border: 1px solid rgba(255, 80, 80, 0.6); border-radius: 10px;"
            )
            return
        if not text:
            self.text_input.setFocus()
            return

        # Store data on the widget for the parent to read
        self.result_title = title
        self.result_text = text
        self.result_color = self.selected_color

        self.saved.emit()

    def _on_cancel(self):
        """Signal cancel."""
        self.cancelled.emit()

    def keyPressEvent(self, event):
        """Close on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
        super().keyPressEvent(event)
