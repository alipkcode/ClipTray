"""
ClipTray - Clip Card Widgets
Individual clip card UI components displayed in the scrollable list.
Each card shows the clip title, a preview of the text, and action buttons.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QMimeData, QPoint
from PyQt6.QtGui import QColor, QCursor, QDrag


class ClipCard(QWidget):
    """A single clip card widget with title, preview text, and action buttons."""

    # Signals
    clicked = pyqtSignal(str)      # clip_id — user wants to type this clip
    edit_clicked = pyqtSignal(str)  # clip_id — user wants to edit
    delete_clicked = pyqtSignal(str)  # clip_id — user wants to delete
    pin_clicked = pyqtSignal(str)  # clip_id — user wants to pin/unpin

    def __init__(self, clip_id: str, title: str, text: str, color: str = "#6C8EFF",
                 is_macro: bool = False, pinned: bool = False,
                 draggable: bool = True, parent=None):
        super().__init__(parent)
        self.clip_id = clip_id
        self.clip_title = title
        self.clip_text = text
        self.accent_color = color
        self.is_macro = is_macro
        self.pinned = pinned
        self.draggable = draggable
        self._drag_start_pos = None

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
        main_layout.setSpacing(10)

        # ── Drag handle ──
        if self.draggable:
            self.drag_handle = QLabel("⠿")
            self.drag_handle.setObjectName("DragHandle")
            self.drag_handle.setFixedSize(20, 40)
            self.drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drag_handle.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            main_layout.addWidget(self.drag_handle)

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

        # Title row (with optional pin/macro badges)
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)

        if self.pinned:
            pin_indicator = QLabel("📌")
            pin_indicator.setObjectName("PinIndicator")
            pin_indicator.setFixedSize(18, 18)
            pin_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_row.addWidget(pin_indicator)

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

        # Pin button
        pin_text = "📌" if self.pinned else "📍"
        self.pin_btn = QPushButton(pin_text)
        self.pin_btn.setObjectName("PinBtnActive" if self.pinned else "PinBtn")
        self.pin_btn.setToolTip("Unpin" if self.pinned else "Pin to top")
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pin_btn.clicked.connect(lambda: self.pin_clicked.emit(self.clip_id))
        btn_layout.addWidget(self.pin_btn)

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
        """Handle card click — start drag or emit click signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            # Start drag if clicking on drag handle
            if self.draggable and hasattr(self, 'drag_handle') and child is self.drag_handle:
                self._drag_start_pos = event.pos()
                return
            # Emit click if not clicking on any button
            interactive = [self.edit_btn, self.delete_btn, self.pin_btn]
            if hasattr(self, 'drag_handle'):
                interactive.append(self.drag_handle)
            if child not in interactive:
                self.clicked.emit(self.clip_id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Start drag operation if mouse moved far enough from drag handle."""
        if (self._drag_start_pos is not None and
                event.buttons() & Qt.MouseButton.LeftButton):
            distance = (event.pos() - self._drag_start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self._perform_drag()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Reset drag state."""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def _perform_drag(self):
        """Initiate a QDrag operation for reordering."""
        self._drag_start_pos = None

        # Grab pixmap before changing visual
        pixmap = self.grab()

        # Dim the card while it is being dragged
        opacity = QGraphicsOpacityEffect(self)
        opacity.setOpacity(0.3)
        self.setGraphicsEffect(opacity)

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-cliptray-clip", self.clip_id.encode())
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

        drag.exec(Qt.DropAction.MoveAction)

        # Restore shadow effect after drag completes
        self._add_shadow()

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
