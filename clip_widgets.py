"""
ClipTray - Clip Card Widgets
Individual clip card UI components displayed in the scrollable list.
Each card shows the clip title, a preview of the text, and action buttons.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QCursor


class ClipCard(QWidget):
    """A single clip card widget with title, preview text, and action buttons."""

    # Signals
    clicked = pyqtSignal(str)      # clip_id — user wants to type this clip
    edit_clicked = pyqtSignal(str)  # clip_id — user wants to edit
    delete_clicked = pyqtSignal(str)  # clip_id — user wants to delete

    def __init__(self, clip_id: str, title: str, text: str, color: str = "#6C8EFF",
                 is_macro: bool = False, parent=None):
        super().__init__(parent)
        self.clip_id = clip_id
        self.clip_title = title
        self.clip_text = text
        self.accent_color = color
        self.is_macro = is_macro

        self.setObjectName("ClipCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(72)
        self.setMaximumHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()
        self._add_shadow()

    def _build_ui(self):
        """Construct the card layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(12)

        # ── Color accent strip ──
        accent = QLabel()
        accent.setObjectName("ClipCardAccent")
        accent.setFixedWidth(4)
        accent.setStyleSheet(f"background-color: {self.accent_color};")
        main_layout.addWidget(accent)

        # ── Text content area ──
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Title row (with optional macro badge)
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)

        if self.is_macro:
            macro_badge = QLabel("⚡")
            macro_badge.setObjectName("MacroIndicator")
            macro_badge.setFixedSize(20, 20)
            macro_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_row.addWidget(macro_badge)

        self.title_label = QLabel(self.clip_title)
        self.title_label.setObjectName("ClipCardTitle")
        self.title_label.setWordWrap(False)
        title_row.addWidget(self.title_label, 1)
        text_layout.addLayout(title_row)

        # Preview text (truncated to one line)
        preview = self.clip_text.replace("\n", " ").strip()
        if len(preview) > 80:
            preview = preview[:77] + "..."
        self.text_label = QLabel(preview)
        self.text_label.setObjectName("ClipCardText")
        self.text_label.setWordWrap(False)
        text_layout.addWidget(self.text_label)

        main_layout.addLayout(text_layout, 1)

        # ── Action buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # Edit button
        self.edit_btn = QPushButton("✎")
        self.edit_btn.setObjectName("CardActionBtn")
        self.edit_btn.setToolTip("Edit this clip")
        self.edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.clip_id))
        btn_layout.addWidget(self.edit_btn)

        # Delete button
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setObjectName("DeleteBtn")
        self.delete_btn.setToolTip("Delete this clip")
        self.delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.clip_id))
        btn_layout.addWidget(self.delete_btn)

        main_layout.addLayout(btn_layout)

    def _add_shadow(self):
        """Add a subtle drop shadow to the card."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        """Handle card click — emit signal to type this clip."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only emit if the click was not on a button
            child = self.childAt(event.pos())
            if child not in (self.edit_btn, self.delete_btn):
                self.clicked.emit(self.clip_id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Slight scale-up hover effect via stylesheet adjustment."""
        self.setStyleSheet("""
            #ClipCard {
                background-color: #1E1E30;
                border: 1px solid rgba(108, 142, 255, 0.2);
                border-radius: 12px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reset hover style."""
        self.setStyleSheet("")
        super().leaveEvent(event)
