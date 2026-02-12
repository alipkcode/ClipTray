"""
ClipTray - Overlay Window
The main fullscreen semi-transparent overlay that dims the desktop
and shows the clip manager panel in the center.
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QCursor, QScreen

from clip_manager import ClipManager
from clip_widgets import ClipCard
from add_dialog import AddEditDialog
from settings_dialog import SettingsDialog
from settings_manager import SettingsManager
from styles import get_stylesheet


class OverlayWindow(QWidget):
    """
    Fullscreen transparent overlay that:
    - Dims and blurs the background
    - Shows a centered panel with saved clips
    - Allows searching, adding, editing, deleting
    - On clip click: hides and types the clip text into the active field
    """

    # Signal emitted when user selects a clip to type
    type_clip = pyqtSignal(str)  # clip text
    # Signal emitted when click-to-paste mode: user selects a clip, wait for click
    wait_and_type_clip = pyqtSignal(str)  # clip text
    # Signal for macro execution (passes clip object as dict)
    execute_macro = pyqtSignal(object)  # clip object
    wait_and_execute_macro = pyqtSignal(object)  # clip object

    def __init__(self, clip_manager: ClipManager, settings: SettingsManager = None, parent=None):
        super().__init__(parent)
        self.clip_manager = clip_manager
        self.settings = settings or SettingsManager()
        self.dialog = None  # Active add/edit dialog
        self.settings_dialog = None  # Active settings dialog

        # ── Window setup ──
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("OverlayBackground")

        self._build_ui()
        self.setStyleSheet(get_stylesheet())

    def _build_ui(self):
        """Construct the full overlay UI."""
        # Root layout — fills the screen
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Dimmed background layer ──
        self.bg = QWidget()
        self.bg.setObjectName("OverlayBackground")
        self.bg.setStyleSheet("background-color: rgba(0, 0, 0, 160);")

        bg_layout = QVBoxLayout(self.bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Central panel ──
        self.panel = QWidget()
        self.panel.setObjectName("MainPanel")
        self.panel.setFixedWidth(520)
        self.panel.setMinimumHeight(400)
        self.panel.setMaximumHeight(620)

        # Panel shadow
        panel_shadow = QGraphicsDropShadowEffect(self.panel)
        panel_shadow.setBlurRadius(60)
        panel_shadow.setOffset(0, 10)
        panel_shadow.setColor(QColor(0, 0, 0, 120))
        self.panel.setGraphicsEffect(panel_shadow)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(24, 20, 24, 20)
        panel_layout.setSpacing(14)

        # ── Title bar ──
        title_bar = QHBoxLayout()
        title_bar.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_label = QLabel("ClipTray")
        title_label.setObjectName("TitleLabel")
        title_col.addWidget(title_label)

        subtitle = QLabel("Click a clip to type it instantly")
        subtitle.setObjectName("SubtitleLabel")
        title_col.addWidget(subtitle)

        title_bar.addLayout(title_col)
        title_bar.addStretch()

        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._on_settings)
        title_bar.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignTop)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setToolTip("Close  (Esc)")
        close_btn.clicked.connect(self.hide_overlay)
        title_bar.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)

        panel_layout.addLayout(title_bar)

        # ── Search bar ──
        search_container = QHBoxLayout()
        search_container.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.setPlaceholderText("🔍  Search your clips...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search)
        search_container.addWidget(self.search_input)

        panel_layout.addLayout(search_container)

        # ── Clip list (scrollable) ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ClipScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.clip_list_widget = QWidget()
        self.clip_list_layout = QVBoxLayout(self.clip_list_widget)
        self.clip_list_layout.setContentsMargins(0, 0, 4, 0)
        self.clip_list_layout.setSpacing(8)
        self.clip_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.clip_list_widget)
        panel_layout.addWidget(self.scroll_area, 1)

        # ── Bottom bar: Add button ──
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 4, 0, 0)
        bottom_bar.addStretch()

        add_btn = QPushButton("＋  Add Clip")
        add_btn.setObjectName("AddButton")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.clicked.connect(self._on_add)
        bottom_bar.addWidget(add_btn)

        bottom_bar.addStretch()
        panel_layout.addLayout(bottom_bar)

        bg_layout.addWidget(self.panel)
        root.addWidget(self.bg)

    # ── Show / Hide ──────────────────────────────────────────

    def show_overlay(self):
        """Show the overlay fullscreen on the active monitor."""
        # Get the screen that currently has the cursor
        screen = QApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QApplication.primaryScreen()

        geometry = screen.geometry()
        self.setGeometry(geometry)
        self.bg.setFixedSize(geometry.size())

        self._refresh_clips()
        self.search_input.clear()
        self.search_input.setFocus()
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_overlay(self):
        """Hide the overlay and any dialog."""
        if self.dialog:
            self.dialog.hide()
            self.dialog.deleteLater()
            self.dialog = None
        if self.settings_dialog:
            self.settings_dialog.hide()
            self.settings_dialog.deleteLater()
            self.settings_dialog = None
        self.hide()

    # ── Clip List ────────────────────────────────────────────

    def _refresh_clips(self, query: str = ""):
        """Rebuild the clip card list."""
        # Clear existing cards
        while self.clip_list_layout.count():
            item = self.clip_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        clips = self.clip_manager.search(query)

        if not clips:
            self._show_empty_state(query)
            return

        for clip in clips:
            card = ClipCard(
                clip_id=clip.id,
                title=clip.title,
                text=clip.get_preview_text() if clip.is_macro else clip.text,
                color=clip.color,
                is_macro=clip.is_macro,
                parent=self.clip_list_widget
            )
            card.clicked.connect(self._on_clip_clicked)
            card.edit_clicked.connect(self._on_edit)
            card.delete_clicked.connect(self._on_delete)
            self.clip_list_layout.addWidget(card)

    def _show_empty_state(self, query: str = ""):
        """Show empty state message."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 40, 0, 40)

        icon_label = QLabel("📋")
        icon_label.setObjectName("EmptyStateIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        if query:
            text = f'No clips matching "{query}"'
        else:
            text = "No clips yet — click Add Clip to get started!"
        msg = QLabel(text)
        msg.setObjectName("EmptyStateLabel")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        self.clip_list_layout.addWidget(container)

    # ── Event Handlers ───────────────────────────────────────

    def _on_search(self, text: str):
        """Filter clips as user types in search."""
        self._refresh_clips(text)

    def _on_clip_clicked(self, clip_id: str):
        """User clicked a clip — type it or wait for click depending on setting."""
        clip = self.clip_manager.get_clip(clip_id)
        if clip:
            self.hide_overlay()
            if clip.is_macro and clip.steps:
                # Macro clip — execute the sequence
                if self.settings.click_to_paste:
                    QTimer.singleShot(200, lambda: self.wait_and_execute_macro.emit(clip))
                else:
                    QTimer.singleShot(300, lambda: self.execute_macro.emit(clip))
            else:
                # Simple text clip
                if self.settings.click_to_paste:
                    QTimer.singleShot(200, lambda: self.wait_and_type_clip.emit(clip.text))
                else:
                    QTimer.singleShot(300, lambda: self.type_clip.emit(clip.text))

    def _on_add(self):
        """Open the add clip dialog."""
        self._open_dialog(clip=None)

    def _on_edit(self, clip_id: str):
        """Open the edit dialog for a clip."""
        clip = self.clip_manager.get_clip(clip_id)
        if clip:
            self._open_dialog(clip=clip)

    def _on_delete(self, clip_id: str):
        """Delete a clip and refresh."""
        self.clip_manager.delete_clip(clip_id)
        query = self.search_input.text().strip()
        self._refresh_clips(query)

    def _on_settings(self):
        """Open the settings dialog."""
        if self.settings_dialog:
            self.settings_dialog.deleteLater()

        self.settings_dialog = SettingsDialog(settings=self.settings, parent=self)
        self.settings_dialog.closed.connect(self._on_settings_closed)
        self.settings_dialog.setGeometry(self.rect())
        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def _on_settings_closed(self):
        """Handle settings dialog close."""
        if self.settings_dialog:
            self.settings_dialog.hide()
            self.settings_dialog.deleteLater()
            self.settings_dialog = None
        # Notify main app that settings may have changed
        if hasattr(self, 'settings_changed') and callable(self.settings_changed):
            self.settings_changed()

    def _open_dialog(self, clip=None):
        """Show the add/edit dialog overlaid on the panel."""
        if self.dialog:
            self.dialog.deleteLater()

        self.dialog = AddEditDialog(parent=self, clip=clip)
        self.dialog.saved.connect(lambda: self._on_dialog_saved(clip))
        self.dialog.cancelled.connect(self._on_dialog_cancelled)

        # Position the dialog centered in the overlay
        self.dialog.setGeometry(self.rect())
        self.dialog.show()
        self.dialog.raise_()

    def _on_dialog_saved(self, original_clip):
        """Handle dialog save."""
        if self.dialog is None:
            return

        title = self.dialog.result_title
        text = self.dialog.result_text
        color = self.dialog.result_color
        is_macro = getattr(self.dialog, 'result_is_macro', False)
        steps = getattr(self.dialog, 'result_steps', [])

        if original_clip:
            # Update existing
            self.clip_manager.update_clip(
                original_clip.id, title, text,
                is_macro=is_macro, steps=steps
            )
            # Also update color
            c = self.clip_manager.get_clip(original_clip.id)
            if c:
                c.color = color
                self.clip_manager.save()
        else:
            # Create new
            self.clip_manager.add_clip(
                title, text, color,
                is_macro=is_macro, steps=steps
            )

        self.dialog.hide()
        self.dialog.deleteLater()
        self.dialog = None

        query = self.search_input.text().strip()
        self._refresh_clips(query)

    def _on_dialog_cancelled(self):
        """Handle dialog cancel."""
        if self.dialog:
            self.dialog.hide()
            self.dialog.deleteLater()
            self.dialog = None

    # ── Keyboard ─────────────────────────────────────────────

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Escape:
            if self.settings_dialog:
                self._on_settings_closed()
            elif self.dialog:
                self._on_dialog_cancelled()
            else:
                self.hide_overlay()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Close when clicking outside the panel."""
        # Check if click is outside the panel
        if self.settings_dialog:
            if not self.settings_dialog.panel.geometry().contains(
                self.settings_dialog.mapFromParent(event.pos())
            ):
                self._on_settings_closed()
        elif self.dialog:
            if not self.dialog.panel.geometry().contains(
                self.dialog.mapFromParent(event.pos())
            ):
                self._on_dialog_cancelled()
        elif not self.panel.geometry().contains(
            self.bg.mapFromParent(event.pos())
        ):
            self.hide_overlay()
        super().mousePressEvent(event)
