"""
ClipTray - Settings Dialog
A settings panel accessible from the overlay, with toggle switches
for user preferences like Click-to-Paste mode.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QSizePolicy, QGridLayout,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPropertyAnimation, QEasingCurve, QTimer, QUrl
from PyQt6.QtGui import QColor, QCursor, QPainter, QBrush, QPen, QFont, QDesktopServices

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


class CaretPositionPicker(QWidget):
    """
    Visual position selector for the Caret Companion icon.
    Shows a simulated text cursor (blinking line) in the center
    with 8 clickable position slots around it.
    """

    position_changed = pyqtSignal(str)

    # Grid mapping: (row, col) → position key
    _GRID = {
        (0, 0): "top-left",
        (0, 1): "top",
        (0, 2): "top-right",
        (1, 0): "left",
        # (1,1) is the caret itself
        (1, 2): "right",
        (2, 0): "bottom-left",
        (2, 1): "bottom",
        (2, 2): "bottom-right",
    }

    _LABELS = {
        "top-left": "↖", "top": "↑", "top-right": "↗",
        "left": "←",                   "right": "→",
        "bottom-left": "↙", "bottom": "↓", "bottom-right": "↘",
    }

    def __init__(self, current: str = "top-right", parent=None):
        super().__init__(parent)
        self._selected = current
        self._buttons: dict[str, QPushButton] = {}
        self._blink_on = True

        self.setFixedSize(200, 160)
        self._build()

        # Blinking timer for the simulated caret
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(530)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start()

    def _build(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        for (r, c), pos_key in self._GRID.items():
            btn = QPushButton(self._LABELS[pos_key])
            btn.setFixedSize(42, 36)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setProperty("posKey", pos_key)
            btn.clicked.connect(self._on_btn_clicked)
            self._buttons[pos_key] = btn
            layout.addWidget(btn, r, c, Qt.AlignmentFlag.AlignCenter)

        # Center cell — the simulated caret
        self._caret_widget = QWidget()
        self._caret_widget.setFixedSize(42, 36)
        layout.addWidget(self._caret_widget, 1, 1, Qt.AlignmentFlag.AlignCenter)

        self._refresh_styles()

    def _on_btn_clicked(self):
        btn = self.sender()
        if btn:
            pos_key = btn.property("posKey")
            if pos_key and pos_key != self._selected:
                self._selected = pos_key
                self._refresh_styles()
                self.position_changed.emit(pos_key)

    def _refresh_styles(self):
        for key, btn in self._buttons.items():
            if key == self._selected:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background: rgba(108, 142, 255, 0.35);"
                    "  border: 2px solid #6C8EFF;"
                    "  border-radius: 6px;"
                    "  color: #FFFFFF;"
                    "  font-size: 16px;"
                    "  font-weight: bold;"
                    "}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton {"
                    "  background: rgba(255, 255, 255, 0.05);"
                    "  border: 1px solid rgba(255, 255, 255, 0.10);"
                    "  border-radius: 6px;"
                    "  color: #8888A0;"
                    "  font-size: 14px;"
                    "}"
                    "QPushButton:hover {"
                    "  background: rgba(108, 142, 255, 0.12);"
                    "  border: 1px solid rgba(108, 142, 255, 0.4);"
                    "  color: #BBBBDD;"
                    "}"
                )

    def _toggle_blink(self):
        self._blink_on = not self._blink_on
        self._caret_widget.update()
        self.update()

    def setSelected(self, pos: str):
        if pos in self._buttons and pos != self._selected:
            self._selected = pos
            self._refresh_styles()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw the blinking caret line in the center cell
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cw = self._caret_widget
        cx = cw.x() + cw.width() // 2
        cy = cw.y() + 4
        ch = cw.height() - 8

        if self._blink_on:
            pen = QPen(QColor(220, 220, 240))
            pen.setWidthF(2.0)
            painter.setPen(pen)
            painter.drawLine(cx, cy, cx, cy + ch)

        # Draw a small label under the grid
        painter.setPen(QColor(130, 130, 160))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        label_map = {
            "top-right": "Top Right", "top-left": "Top Left",
            "bottom-right": "Bottom Right", "bottom-left": "Bottom Left",
            "top": "Top", "bottom": "Bottom",
            "right": "Right", "left": "Left",
        }
        label = label_map.get(self._selected, self._selected)
        painter.drawText(self.rect().adjusted(0, 0, 0, -2),
                         Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                         label)
        painter.end()


class HotkeyRecorder(QPushButton):
    """
    A button that records keyboard shortcuts.
    Click to start recording, then press a modifier + key combination.
    At least one modifier (Ctrl, Alt, Shift) plus a regular key is required.
    Press Escape to cancel recording.
    """

    hotkey_changed = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    def __init__(self, current_hotkey: str = "", parent=None):
        super().__init__(parent)
        self._hotkey = current_hotkey
        self._recording = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(38)
        self._apply_normal_style()
        self.clicked.connect(self._toggle_recording)

    # ── Recording control ──

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._recording = True
        self.setText("  Press a shortcut\u2026")
        self.setStyleSheet(
            "QPushButton {"
            "  font-size: 13px; color: #6C8EFF;"
            "  background: rgba(108, 142, 255, 0.12);"
            "  border: 2px solid rgba(108, 142, 255, 0.50);"
            "  border-radius: 8px; padding: 6px 14px; text-align: left;"
            "}"
        )
        self.recording_started.emit()
        self.setFocus()
        self.grabKeyboard()

    def _stop_recording(self):
        self._recording = False
        self.releaseKeyboard()
        self._apply_normal_style()
        self.recording_stopped.emit()

    # ── Display ──

    def _apply_normal_style(self):
        if self._hotkey:
            display = self._hotkey.replace("+", "  +  ")
            self.setText(f"  {display}")
        else:
            self.setText("  Click to set shortcut")
        self.setStyleSheet(
            "QPushButton {"
            "  font-size: 13px; color: #CDD6F4;"
            "  background: rgba(255, 255, 255, 0.05);"
            "  border: 1px solid rgba(255, 255, 255, 0.10);"
            "  border-radius: 8px; padding: 6px 14px; text-align: left;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(108, 142, 255, 0.10);"
            "  border-color: rgba(108, 142, 255, 0.30);"
            "}"
        )

    # ── Key capture ──

    def keyPressEvent(self, event):
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Escape cancels recording
        if key == Qt.Key.Key_Escape:
            self._stop_recording()
            return

        # Ignore standalone modifier presses — wait for a real key
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift,
                   Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        modifiers = event.modifiers()
        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")

        # Require at least one modifier
        if not parts:
            return

        key_name = self._key_to_name(key)
        if key_name:
            parts.append(key_name)
            self._hotkey = "+".join(parts)
            self._stop_recording()
            self.hotkey_changed.emit(self._hotkey)

    def focusOutEvent(self, event):
        if self._recording:
            self._stop_recording()
        super().focusOutEvent(event)

    # ── Public helpers ──

    def get_hotkey(self) -> str:
        return self._hotkey

    def clear_hotkey(self):
        self._hotkey = ""
        self._apply_normal_style()
        self.hotkey_changed.emit("")

    # ── Key-name mapping ──

    @staticmethod
    def _key_to_name(key: int):
        """Convert a Qt key code to a human-readable name."""
        _SPECIAL = {
            Qt.Key.Key_Space: "Space",
            Qt.Key.Key_Return: "Enter", Qt.Key.Key_Enter: "Enter",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Delete: "Delete", Qt.Key.Key_Insert: "Insert",
            Qt.Key.Key_Home: "Home", Qt.Key.Key_End: "End",
            Qt.Key.Key_PageUp: "PageUp", Qt.Key.Key_PageDown: "PageDown",
            Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down",
            Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right",
            Qt.Key.Key_F1: "F1", Qt.Key.Key_F2: "F2",
            Qt.Key.Key_F3: "F3", Qt.Key.Key_F4: "F4",
            Qt.Key.Key_F5: "F5", Qt.Key.Key_F6: "F6",
            Qt.Key.Key_F7: "F7", Qt.Key.Key_F8: "F8",
            Qt.Key.Key_F9: "F9", Qt.Key.Key_F10: "F10",
            Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
            Qt.Key.Key_Minus: "-", Qt.Key.Key_Equal: "=",
            Qt.Key.Key_BracketLeft: "[", Qt.Key.Key_BracketRight: "]",
            Qt.Key.Key_Semicolon: ";", Qt.Key.Key_Apostrophe: "'",
            Qt.Key.Key_Comma: ",", Qt.Key.Key_Period: ".",
            Qt.Key.Key_Slash: "/", Qt.Key.Key_Backslash: "\\",
            Qt.Key.Key_QuoteLeft: "`",
        }
        if key in _SPECIAL:
            return _SPECIAL[key]
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(key)
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(key)
        return None


class CreditsDialog(QWidget):
    """
    Credits / About page for ClipTray.
    Shows developer credit, company, version, license, and GitHub link.
    """

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DialogOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()

    def _build_ui(self):
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.panel = QWidget()
        self.panel.setObjectName("DialogPanel")
        self.panel.setFixedWidth(460)
        self.panel.setMaximumHeight(560)

        shadow = QGraphicsDropShadowEffect(self.panel)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(28, 24, 28, 24)
        panel_layout.setSpacing(0)

        # ── Header ──
        header_layout = QHBoxLayout()
        title = QLabel("About ClipTray")
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

        # ── Scrollable content ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; }"
            "QScrollBar:vertical { width: 6px; background: transparent; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,0.10); border-radius: 3px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 16, 0, 12)
        cl.setSpacing(16)

        # ── App name & version ──
        app_name = QLabel("ClipTray")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #CDD6F4;"
            "letter-spacing: 1px;"
        )
        cl.addWidget(app_name)

        version_label = QLabel("Version 1.4")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(
            "font-size: 13px; color: #6C8EFF; font-weight: 600;"
            "background: rgba(108, 142, 255, 0.10); border-radius: 10px;"
            "padding: 4px 14px;"
        )
        cl.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

        cl.addSpacing(4)

        # ── Developer ──
        dev_title = QLabel("Developer")
        dev_title.setStyleSheet("font-size: 10px; color: #6C7086; text-transform: uppercase; letter-spacing: 1.5px;")
        cl.addWidget(dev_title)

        dev_name = QLabel("Ali Paknahal")
        dev_name.setStyleSheet("font-size: 15px; color: #CDD6F4; font-weight: 600;")
        cl.addWidget(dev_name)

        # ── Company ──
        company_title = QLabel("Company")
        company_title.setStyleSheet("font-size: 10px; color: #6C7086; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px;")
        cl.addWidget(company_title)

        company_name = QLabel("Certainty")
        company_name.setStyleSheet("font-size: 15px; color: #CDD6F4; font-weight: 600;")
        cl.addWidget(company_name)

        # ── Date ──
        date_title = QLabel("First Released")
        date_title.setStyleSheet("font-size: 10px; color: #6C7086; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px;")
        cl.addWidget(date_title)

        date_val = QLabel("February 2026")
        date_val.setStyleSheet("font-size: 14px; color: #BAC2DE;")
        cl.addWidget(date_val)

        # ── Divider ──
        sep1 = QWidget()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background: rgba(255,255,255,0.06);")
        cl.addWidget(sep1)

        # ── GitHub ──
        gh_title = QLabel("Source Code")
        gh_title.setStyleSheet("font-size: 10px; color: #6C7086; text-transform: uppercase; letter-spacing: 1.5px;")
        cl.addWidget(gh_title)

        gh_link = QPushButton("\U0001F517  github.com/alipkcode/ClipTray")
        gh_link.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        gh_link.setStyleSheet(
            "QPushButton {"
            "  font-size: 13px; color: #6C8EFF; background: rgba(108,142,255,0.08);"
            "  border: 1px solid rgba(108,142,255,0.20); border-radius: 8px;"
            "  padding: 8px 14px; text-align: left;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(108,142,255,0.18); border-color: rgba(108,142,255,0.40);"
            "}"
        )
        gh_link.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/alipkcode/ClipTray"))
        )
        cl.addWidget(gh_link)

        # ── Divider ──
        sep2 = QWidget()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background: rgba(255,255,255,0.06);")
        cl.addWidget(sep2)

        # ── License / Open Source notice ──
        license_title = QLabel("License")
        license_title.setStyleSheet("font-size: 10px; color: #6C7086; text-transform: uppercase; letter-spacing: 1.5px;")
        cl.addWidget(license_title)

        license_text = QLabel(
            "ClipTray is free and open-source software.\n\n"
            "You are free to use, modify, and distribute this software "
            "in any way you like. Developers and users alike are welcome "
            "to fork, adapt, and build upon it without restriction."
        )
        license_text.setWordWrap(True)
        license_text.setStyleSheet(
            "font-size: 12px; color: #A6ADC8; line-height: 1.5;"
            "background: rgba(255,255,255,0.03); border-radius: 8px;"
            "padding: 12px 14px;"
        )
        cl.addWidget(license_text)

        # ── Enjoy ──
        enjoy = QLabel("Enjoy! \U0001F389")
        enjoy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        enjoy.setStyleSheet(
            "font-size: 18px; color: #CDD6F4; font-weight: bold;"
            "padding: 12px 0 4px 0;"
        )
        cl.addWidget(enjoy)

        cl.addStretch()
        scroll.setWidget(content)
        panel_layout.addWidget(scroll)

        # ── Back button ──
        panel_layout.addSpacing(12)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        back_btn = QPushButton("Back")
        back_btn.setObjectName("SaveButton")
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.clicked.connect(self._on_close)
        btn_layout.addWidget(back_btn)
        panel_layout.addLayout(btn_layout)

        overlay_layout.addWidget(self.panel)

    def _on_close(self):
        self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()
        super().keyPressEvent(event)


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

        # ── Caret Companion Position Picker ──
        self.pos_section = QWidget()
        pos_section_layout = QVBoxLayout(self.pos_section)
        pos_section_layout.setContentsMargins(0, 0, 0, 0)
        pos_section_layout.setSpacing(8)

        pos_label = QLabel("Icon Position")
        pos_label.setObjectName("SettingsItemTitle")
        pos_label.setStyleSheet("font-size: 12px; color: #A6ADC8;")
        pos_section_layout.addWidget(pos_label)

        pos_desc = QLabel(
            "Choose where the mini clipboard icon appears\n"
            "relative to the blinking text cursor."
        )
        pos_desc.setObjectName("SettingsItemDesc")
        pos_desc.setWordWrap(True)
        pos_section_layout.addWidget(pos_desc)

        self.pos_picker = CaretPositionPicker(
            current=self.settings.caret_companion_position
        )
        self.pos_picker.position_changed.connect(self._on_position_changed)
        pos_section_layout.addWidget(
            self.pos_picker, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        # Only show position picker when caret companion is enabled
        self.pos_section.setVisible(self.settings.caret_companion)

        panel_layout.addWidget(self.pos_section)

        # ── Divider ──
        divider_hk = QWidget()
        divider_hk.setFixedHeight(1)
        divider_hk.setStyleSheet("background-color: rgba(255, 255, 255, 0.04);")
        panel_layout.addWidget(divider_hk)

        # ── Global Hotkey ──
        hk_row = QVBoxLayout()
        hk_row.setSpacing(6)

        hk_title = QLabel("\u2328  Global Hotkey")
        hk_title.setObjectName("SettingsItemTitle")
        hk_row.addWidget(hk_title)

        hk_desc = QLabel(
            "Set a keyboard shortcut to open ClipTray from\n"
            "anywhere, even when it\u2019s hidden in the system tray."
        )
        hk_desc.setObjectName("SettingsItemDesc")
        hk_desc.setWordWrap(True)
        hk_row.addWidget(hk_desc)

        hk_control_row = QHBoxLayout()
        hk_control_row.setSpacing(8)

        self.hotkey_recorder = HotkeyRecorder(
            current_hotkey=self.settings.hotkey
        )
        self.hotkey_recorder.hotkey_changed.connect(self._on_hotkey_changed)
        hk_control_row.addWidget(self.hotkey_recorder, 1)

        self.hk_clear_btn = QPushButton("\u2715")
        self.hk_clear_btn.setFixedSize(38, 38)
        self.hk_clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hk_clear_btn.setToolTip("Clear shortcut")
        self.hk_clear_btn.setStyleSheet(
            "QPushButton {"
            "  font-size: 14px; color: #A6ADC8;"
            "  background: rgba(255, 255, 255, 0.05);"
            "  border: 1px solid rgba(255, 255, 255, 0.10);"
            "  border-radius: 8px;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(255, 80, 80, 0.15);"
            "  color: #FF6B6B; border-color: rgba(255, 80, 80, 0.30);"
            "}"
        )
        self.hk_clear_btn.clicked.connect(self._on_hotkey_clear)
        self.hk_clear_btn.setVisible(bool(self.settings.hotkey))
        hk_control_row.addWidget(self.hk_clear_btn)

        hk_row.addLayout(hk_control_row)
        panel_layout.addLayout(hk_row)

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

        # ── Credits button ──
        credits_btn = QPushButton("ℹ️  Credits & About")
        credits_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        credits_btn.setStyleSheet(
            "QPushButton {"
            "  font-size: 12px; color: #A6ADC8; background: rgba(255,255,255,0.04);"
            "  border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;"
            "  padding: 8px 16px;"
            "}"
            "QPushButton:hover {"
            "  background: rgba(108,142,255,0.10); color: #CDD6F4;"
            "  border-color: rgba(108,142,255,0.30);"
            "}"
        )
        credits_btn.clicked.connect(self._open_credits)
        panel_layout.addWidget(credits_btn)

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
        self.pos_section.setVisible(checked)
        self._update_status_label()

    def _on_position_changed(self, pos: str):
        """Handle caret companion position change."""
        self.settings.caret_companion_position = pos

    def _on_hotkey_changed(self, hotkey: str):
        """Handle global hotkey change."""
        self.settings.hotkey = hotkey
        self.hk_clear_btn.setVisible(bool(hotkey))
        self._update_status_label()

    def _on_hotkey_clear(self):
        """Clear the global hotkey."""
        self.hotkey_recorder.clear_hotkey()

    def _update_status_label(self):
        """Update the status text below the toggles."""
        parts = []
        if self.settings.click_to_paste:
            parts.append("\u2713 Click-to-Paste is ON")
        if self.settings.caret_companion:
            parts.append("\u2713 Caret Companion is ON")
        if self.settings.hotkey:
            parts.append(f"\u2713 Hotkey: {self.settings.hotkey}")

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

    def _open_credits(self):
        """Show the credits / about page over the settings dialog."""
        self.panel.hide()
        self._credits = CreditsDialog(parent=self)
        self._credits.closed.connect(self._close_credits)
        self._credits.setGeometry(self.rect())
        self._credits.show()

    def _close_credits(self):
        """Return from credits page back to settings."""
        self._credits.hide()
        self._credits.deleteLater()
        self.panel.show()

    def _on_close(self):
        """Close the settings dialog."""
        self.closed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_credits') and self._credits.isVisible():
            self._credits.setGeometry(self.rect())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, '_credits') and self._credits.isVisible():
                self._close_credits()
            else:
                self._on_close()
        super().keyPressEvent(event)
