"""
ClipTray - Caret Companion
A tiny floating icon that appears near the text cursor (caret) when the
user is typing anywhere in Windows. Clicking the icon opens ClipTray
without stealing focus from the active text field.

Uses Win32 APIs to detect the caret position in any application.
"""

import ctypes
import ctypes.wintypes
import threading

from PyQt6.QtWidgets import QWidget, QLabel, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QCursor, QIcon, QPen, QBrush,
    QLinearGradient, QRadialGradient
)


# ── Win32 API structures and functions ──

class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("hwndActive", ctypes.wintypes.HWND),
        ("hwndFocus", ctypes.wintypes.HWND),
        ("hwndCapture", ctypes.wintypes.HWND),
        ("hwndMenuOwner", ctypes.wintypes.HWND),
        ("hwndMoveSize", ctypes.wintypes.HWND),
        ("hwndCaret", ctypes.wintypes.HWND),
        ("rcCaret", ctypes.wintypes.RECT),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

GetGUIThreadInfo = user32.GetGUIThreadInfo
GetGUIThreadInfo.argtypes = [ctypes.wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
GetGUIThreadInfo.restype = ctypes.wintypes.BOOL

GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = ctypes.wintypes.HWND

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

ClientToScreen = user32.ClientToScreen
ClientToScreen.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(POINT)]
ClientToScreen.restype = ctypes.wintypes.BOOL

GetCurrentProcessId = kernel32.GetCurrentProcessId
GetCurrentProcessId.restype = ctypes.wintypes.DWORD

# GUI_CARETBLINKING flag
GUI_CARETBLINKING = 0x00000001


def get_caret_screen_pos():
    """
    Get the screen-space position of the text caret in the foreground window.
    Returns (x, y, caret_height) or None if no caret is found.
    """
    try:
        hwnd_fg = GetForegroundWindow()
        if not hwnd_fg:
            return None

        # Don't track our own process
        pid = ctypes.wintypes.DWORD()
        tid = GetWindowThreadProcessId(hwnd_fg, ctypes.byref(pid))
        if pid.value == GetCurrentProcessId():
            return None

        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)

        if not GetGUIThreadInfo(tid, ctypes.byref(gui_info)):
            return None

        # Check if there's actually a caret
        if not gui_info.hwndCaret:
            return None

        caret_rect = gui_info.rcCaret
        caret_x = caret_rect.left
        caret_y = caret_rect.top
        caret_h = max(caret_rect.bottom - caret_rect.top, 16)

        # Convert from client coordinates to screen coordinates
        pt = POINT(caret_x, caret_y)
        if not ClientToScreen(gui_info.hwndCaret, ctypes.byref(pt)):
            return None

        return (pt.x, pt.y, caret_h)
    except Exception:
        return None


# ── Signal bridge for thread-safe communication ──

class CaretSignalBridge(QObject):
    """Bridge to safely emit Qt signals from background threads."""
    caret_moved = pyqtSignal(int, int, int)  # x, y, caret_height
    caret_lost = pyqtSignal()


# ── The tiny floating icon ──

def create_mini_icon(size: int = 24) -> QPixmap:
    """Create a tiny ClipTray icon programmatically."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Gradient background circle
    gradient = QRadialGradient(size / 2, size / 2, size / 2)
    gradient.setColorAt(0, QColor(108, 142, 255))
    gradient.setColorAt(1, QColor(80, 110, 220))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 6, 6)

    # Clipboard lines (simplified icon)
    painter.setPen(QPen(QColor(255, 255, 255, 220), 1.5))
    mid = size // 2
    for dy in [-3, 0, 3]:
        w = 8 if dy < 3 else 5
        painter.drawLine(mid - w // 2, mid + dy, mid + w // 2, mid + dy)

    painter.end()
    return pixmap


class CaretCompanionIcon(QWidget):
    """
    A tiny floating icon that appears near the caret.
    Clicking it opens the ClipTray overlay.
    """
    clicked = pyqtSignal()

    ICON_SIZE = 22
    FADE_TIMEOUT_MS = 4000  # Hide after 4 seconds of no caret movement

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.ICON_SIZE + 4, self.ICON_SIZE + 4)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Icon label
        self._icon_pixmap = create_mini_icon(self.ICON_SIZE)
        self._label = QLabel(self)
        self._label.setPixmap(self._icon_pixmap)
        self._label.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        self._label.move(2, 2)

        # Subtle shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Fade-out timer
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._fade_out)

        self._opacity = 1.0
        self._last_pos = None

    def show_at(self, x: int, y: int, caret_h: int):
        """Position the icon to the right of the caret and show it."""
        new_pos = QPoint(x + 6, y + caret_h - self.ICON_SIZE // 2)

        # Don't flicker if position barely changed
        if self._last_pos and abs(new_pos.x() - self._last_pos.x()) < 3 \
                and abs(new_pos.y() - self._last_pos.y()) < 3:
            self._restart_fade_timer()
            return

        self._last_pos = new_pos

        # Clamp to screen bounds
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            nx = min(new_pos.x(), geo.right() - self.width() - 4)
            ny = min(new_pos.y(), geo.bottom() - self.height() - 4)
            nx = max(nx, geo.left())
            ny = max(ny, geo.top())
            new_pos = QPoint(nx, ny)

        self.move(new_pos)
        self._opacity = 1.0
        self.setWindowOpacity(1.0)
        if not self.isVisible():
            self.show()

        self._restart_fade_timer()

    def _restart_fade_timer(self):
        self._fade_timer.stop()
        self._fade_timer.start(self.FADE_TIMEOUT_MS)

    def _fade_out(self):
        """Gradually fade out and hide."""
        self._opacity -= 0.15
        if self._opacity <= 0:
            self.hide()
            self._opacity = 1.0
            self._last_pos = None
        else:
            self.setWindowOpacity(self._opacity)
            QTimer.singleShot(40, self._fade_out)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hide()
            self._last_pos = None
            self._fade_timer.stop()
            self.clicked.emit()
        super().mousePressEvent(event)

    def force_hide(self):
        """Immediately hide without fade."""
        self._fade_timer.stop()
        self.hide()
        self._last_pos = None


class CaretCompanion(QObject):
    """
    Manages the caret companion feature.
    Polls the caret position periodically and shows/hides the floating icon.
    Uses a keyboard listener to only poll when the user is actively typing.
    """
    open_requested = pyqtSignal()  # User clicked the companion icon

    POLL_INTERVAL_MS = 300   # How often to check caret position when typing
    IDLE_TIMEOUT_MS = 3000   # Stop polling after this much idle time

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False
        self._icon = None
        self._poll_timer = None
        self._idle_timer = None
        self._keyboard_listener = None
        self._typing_active = False
        self._bridge = CaretSignalBridge()
        self._bridge.caret_moved.connect(self._on_caret_moved)
        self._bridge.caret_lost.connect(self._on_caret_lost)

    def set_enabled(self, enabled: bool):
        """Enable or disable the caret companion."""
        if enabled == self._enabled:
            return
        self._enabled = enabled
        if enabled:
            self._start()
        else:
            self._stop()

    def _start(self):
        """Start the caret companion system."""
        # Create the floating icon
        self._icon = CaretCompanionIcon()
        self._icon.clicked.connect(self._on_icon_clicked)

        # Create poll timer (runs on main thread)
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_caret)
        # Don't start polling yet — wait for keyboard activity

        # Create idle timer
        self._idle_timer = QTimer()
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle)

        # Start keyboard listener
        self._start_keyboard_listener()

    def _stop(self):
        """Stop everything."""
        self._stop_keyboard_listener()

        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        if self._idle_timer:
            self._idle_timer.stop()
            self._idle_timer = None

        if self._icon:
            self._icon.force_hide()
            self._icon.deleteLater()
            self._icon = None

        self._typing_active = False

    def _start_keyboard_listener(self):
        """Start listening for keyboard activity using pynput."""
        self._stop_keyboard_listener()
        try:
            from pynput import keyboard

            def on_key_press(key):
                if self._enabled:
                    self._bridge.caret_moved.emit(0, 0, 0)  # Signal to start polling

            self._keyboard_listener = keyboard.Listener(on_press=on_key_press)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()
        except ImportError:
            # pynput not available, fall back to continuous polling
            if self._poll_timer:
                self._poll_timer.start(self.POLL_INTERVAL_MS)

    def _stop_keyboard_listener(self):
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

    def _on_caret_moved(self, x, y, h):
        """Called from keyboard listener — a key was pressed, start/continue polling."""
        if not self._enabled:
            return

        # Reset idle timer
        if self._idle_timer:
            self._idle_timer.stop()
            self._idle_timer.start(self.IDLE_TIMEOUT_MS)

        # Start poll timer if not running
        if self._poll_timer and not self._poll_timer.isActive():
            self._poll_timer.start(self.POLL_INTERVAL_MS)
            # Also do an immediate poll
            QTimer.singleShot(80, self._poll_caret)

    def _on_idle(self):
        """User stopped typing — stop polling and fade out icon."""
        if self._poll_timer:
            self._poll_timer.stop()
        if self._icon:
            self._icon.force_hide()

    def _poll_caret(self):
        """Check the current caret position and update the icon."""
        if not self._enabled or not self._icon:
            return

        pos = get_caret_screen_pos()
        if pos:
            x, y, h = pos
            self._icon.show_at(x, y, h)
        else:
            # No caret found — hide if visible
            if self._icon.isVisible():
                self._icon.force_hide()

    def _on_caret_lost(self):
        if self._icon:
            self._icon.force_hide()

    def _on_icon_clicked(self):
        """User clicked the companion icon — open ClipTray."""
        self.open_requested.emit()

    def hide_icon(self):
        """Hide the icon (e.g. when overlay is opening)."""
        if self._icon:
            self._icon.force_hide()
