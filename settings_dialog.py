"""
ClipTray - Settings Dialog
A settings panel accessible from the overlay, with toggle switches
for user preferences like Click-to-Paste mode.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QCursor, QPainter, QBrush, QPen

from settings_manager import SettingsManager


class ToggleSwitch(QWidget):
    """A modern iOS-style toggle switch widget."""

    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._handle_position = 1.0 if checked else 0.0

        self.setFixedSize(48, 26)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Animation for smooth sliding
        self._animation = QPropertyAnimation(self, b"handlePosition")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        self._checked = checked
        self._animate(checked)

    def _get_handle_position(self) -> float:
        return self._handle_position

    def _set_handle_position(self, pos: float):
        self._handle_position = pos
        self.update()

    # Property for QPropertyAnimation
    from PyQt6.QtCore import pyqtProperty
    handlePosition = pyqtProperty(float, _get_handle_position, _set_handle_position)

    def _animate(self, checked: bool):
        self._animation.stop()
        self._animation.setStartValue(self._handle_position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._animate(self._checked)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2

        # Track colors
        if self._checked:
            # Interpolate based on handle position
            track_color = QColor(108, 142, 255)  # Blue when on
            track_color.setAlphaF(0.4 + 0.6 * self._handle_position)
        else:
            track_color = QColor(69, 71, 90)  # Gray when off
            track_color.setAlphaF(0.4 + 0.6 * (1.0 - self._handle_position))

        # Draw track
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Draw handle
        handle_radius = h - 6
        handle_x = 3 + self._handle_position * (w - handle_radius - 6)
        handle_y = 3

        # Handle shadow
        shadow_color = QColor(0, 0, 0, 40)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(int(handle_x), int(handle_y) + 1, int(handle_radius), int(handle_radius))

        # Handle
        handle_color = QColor(255, 255, 255) if self._checked else QColor(200, 200, 210)
        painter.setBrush(QBrush(handle_color))
        painter.drawEllipse(int(handle_x), int(handle_y), int(handle_radius), int(handle_radius))

        painter.end()


class SettingsDialog(QWidget):
    """
    Settings panel displayed over the overlay.
    Contains toggle switches for application preferences.
    """

    closed = pyqtSignal()

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings

        self.setObjectName("DialogOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()

    def _build_ui(self):
        """Construct the settings dialog UI."""
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # The dialog panel
        self.panel = QWidget()
        self.panel.setObjectName("DialogPanel")
        self.panel.setFixedWidth(440)

        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.setSpacing(20)

        # ── Header ──
        header_layout = QHBoxLayout()

        title = QLabel("Settings")
        title.setObjectName("DialogTitle")
        header_layout.addWidget(title)

        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseButton")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(close_btn)

        panel_layout.addLayout(header_layout)

        # ── Divider ──
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")
        panel_layout.addWidget(divider)

        # ── Click-to-Paste Toggle ──
        ctp_row = QHBoxLayout()
        ctp_row.setSpacing(16)

        # Icon + text column
        ctp_text_col = QVBoxLayout()
        ctp_text_col.setSpacing(4)

        ctp_title = QLabel("🖱  Click-to-Paste")
        ctp_title.setObjectName("SettingsItemTitle")
        ctp_text_col.addWidget(ctp_title)

        ctp_desc = QLabel(
            "When enabled, selecting a clip won't paste immediately.\n"
            "Instead, it waits for you to click on any text field first,\n"
            "then pastes the text there."
        )
        ctp_desc.setObjectName("SettingsItemDesc")
        ctp_desc.setWordWrap(True)
        ctp_text_col.addWidget(ctp_desc)

        ctp_row.addLayout(ctp_text_col, 1)

        # Toggle switch
        self.ctp_toggle = ToggleSwitch(checked=self.settings.click_to_paste)
        self.ctp_toggle.toggled.connect(self._on_ctp_toggled)
        ctp_row.addWidget(self.ctp_toggle, alignment=Qt.AlignmentFlag.AlignVCenter)

        panel_layout.addLayout(ctp_row)

        # ── Divider ──
        divider_mid = QWidget()
        divider_mid.setFixedHeight(1)
        divider_mid.setStyleSheet("background-color: rgba(255, 255, 255, 0.04);")
        panel_layout.addWidget(divider_mid)

        # ── Caret Companion Toggle ──
        cc_row = QHBoxLayout()
        cc_row.setSpacing(16)

        cc_text_col = QVBoxLayout()
        cc_text_col.setSpacing(4)

        cc_title = QLabel("\u2328  Caret Companion")
        cc_title.setObjectName("SettingsItemTitle")
        cc_text_col.addWidget(cc_title)

        cc_desc = QLabel(
            "Shows a tiny ClipTray icon near your text cursor\n"
            "while you type. Click it to open ClipTray without\n"
            "losing focus on your current text field."
        )
        cc_desc.setObjectName("SettingsItemDesc")
        cc_desc.setWordWrap(True)
        cc_text_col.addWidget(cc_desc)

        cc_row.addLayout(cc_text_col, 1)

        self.cc_toggle = ToggleSwitch(checked=self.settings.caret_companion)
        self.cc_toggle.toggled.connect(self._on_cc_toggled)
        cc_row.addWidget(self.cc_toggle, alignment=Qt.AlignmentFlag.AlignVCenter)

        panel_layout.addLayout(cc_row)

        # ── Status indicator ──
        self.status_label = QLabel()
        self.status_label.setObjectName("SettingsStatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_status_label()
        panel_layout.addWidget(self.status_label)

        # ── Divider ──
        divider2 = QWidget()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet("background-color: rgba(255, 255, 255, 0.06);")
        panel_layout.addWidget(divider2)

        # ── Close button ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        done_btn = QPushButton("Done")
        done_btn.setObjectName("SaveButton")
        done_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        done_btn.clicked.connect(self._on_close)
        btn_layout.addWidget(done_btn)

        panel_layout.addLayout(btn_layout)

        overlay_layout.addWidget(self.panel)

    def _on_ctp_toggled(self, checked: bool):
        """Handle click-to-paste toggle change."""
        self.settings.click_to_paste = checked
        self._update_status_label()

    def _on_cc_toggled(self, checked: bool):
        """Handle caret companion toggle change."""
        self.settings.caret_companion = checked
        self._update_status_label()

    def _update_status_label(self):
        """Update the status text below the toggles."""
        parts = []
        if self.settings.click_to_paste:
            parts.append("\u2713 Click-to-Paste is ON")
        if self.settings.caret_companion:
            parts.append("\u2713 Caret Companion is ON")

        if parts:
            self.status_label.setText("  \u00b7  ".join(parts))
            self.status_label.setStyleSheet(
                "color: #6C8EFF; font-size: 11px; padding: 8px 12px;"
                "background: rgba(108, 142, 255, 0.08); border-radius: 8px;"
            )
        else:
            self.status_label.setText("All features are using default behavior")
            self.status_label.setStyleSheet(
                "color: #6C7086; font-size: 11px; padding: 8px 12px;"
                "background: rgba(255, 255, 255, 0.03); border-radius: 8px;"
            )

    def _on_close(self):
        """Close the settings dialog."""
        self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()
        super().keyPressEvent(event)
