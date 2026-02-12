"""
ClipTray – Caret Companion
A floating icon that appears near the text cursor (caret) whenever
the user is typing *anywhere* in Windows.

Detection strategy (tried in order, first success wins):
  1. Win32  GetGUIThreadInfo  → native Win32 apps (Notepad, Explorer search …)
  2. UIA    TextPattern2.GetCaretRange → WPF / UWP / modern frameworks
  3. UIA    TextPattern.GetSelection   → Chromium / Electron (VS Code, browsers)
  4. UIA    Focused-control bounding rect → ultimate fallback for any edit field
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import sys
import traceback
from typing import Optional, Tuple

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QCursor, QPen, QBrush, QPainterPath
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QSize, QPropertyAnimation,
    QEasingCurve, pyqtSignal, QObject
)


# ─────────────────────────────────────────────────────────
#  Win32 structures used by GetGUIThreadInfo
# ─────────────────────────────────────────────────────────
class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize",        ctypes.c_ulong),
        ("flags",         ctypes.c_ulong),
        ("hwndActive",    ctypes.c_void_p),
        ("hwndFocus",     ctypes.c_void_p),
        ("hwndCapture",   ctypes.c_void_p),
        ("hwndMenuOwner", ctypes.c_void_p),
        ("hwndMoveSize",  ctypes.c_void_p),
        ("hwndCaret",     ctypes.c_void_p),
        ("rcCaret",       ctypes.wintypes.RECT),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# ─────────────────────────────────────────────────────────
#  Method 1 – Win32 GetGUIThreadInfo
#  Works for classic Win32 apps: Notepad, WordPad,
#  Explorer address / search bars, legacy Office, etc.
# ─────────────────────────────────────────────────────────
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32


def _get_caret_win32() -> Optional[Tuple[int, int]]:
    """Return (x, y) screen coords of the caret bottom-left, or None."""
    gti = GUITHREADINFO()
    gti.cbSize = ctypes.sizeof(GUITHREADINFO)
    if not _user32.GetGUIThreadInfo(0, ctypes.byref(gti)):
        return None
    if not gti.hwndCaret:
        return None
    # Skip if the caret belongs to our own process (ClipTray itself)
    pid = ctypes.c_ulong()
    _user32.GetWindowThreadProcessId(gti.hwndCaret, ctypes.byref(pid))
    if pid.value == _kernel32.GetCurrentProcessId():
        return None
    pt = POINT(gti.rcCaret.left, gti.rcCaret.top)
    _user32.ClientToScreen(gti.hwndCaret, ctypes.byref(pt))
    caret_h = gti.rcCaret.bottom - gti.rcCaret.top
    return (pt.x, pt.y + caret_h)


# ─────────────────────────────────────────────────────────
#  UIA helpers – lazy-imported so the app doesn't crash
#  if comtypes isn't ready yet.
# ─────────────────────────────────────────────────────────
_uia_ready = False
_auto = None          # uiautomation module
_uiaclient = None     # comtypes.gen.UIAutomationClient

_TEXTPATTERN2_ID = 10024
_TEXTPATTERN_ID  = 10014


def _ensure_uia():
    """Lazily import uiautomation + comtypes interfaces."""
    global _uia_ready, _auto, _uiaclient
    if _uia_ready:
        return True
    try:
        import uiautomation as auto_mod
        import comtypes.gen.UIAutomationClient as uiac
        _auto = auto_mod
        _uiaclient = uiac
        _uia_ready = True
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────
#  Method 2 – UIA TextPattern2.GetCaretRange
#  Works for WPF, UWP, some Win32 rich-edit controls.
# ─────────────────────────────────────────────────────────
def _get_caret_uia_tp2() -> Optional[Tuple[int, int]]:
    """Use IUIAutomationTextPattern2.GetCaretRange for caret pos."""
    if not _ensure_uia():
        return None
    try:
        ctrl = _auto.GetFocusedControl()
        if ctrl is None:
            return None
        elem = ctrl.Element
        pat = elem.GetCurrentPattern(_TEXTPATTERN2_ID)
        if not pat:
            return None
        tp2 = pat.QueryInterface(_uiaclient.IUIAutomationTextPattern2)
        is_active = ctypes.c_int()
        caret_range = tp2.GetCaretRange(ctypes.byref(is_active))
        if caret_range and is_active.value:
            rects = caret_range.GetBoundingRectangles()
            if rects and len(rects) >= 4:
                x, y, w, h = rects[0], rects[1], rects[2], rects[3]
                return (int(x), int(y + h))
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────
#  Method 3 – UIA TextPattern.GetSelection
#  Works for Chromium / Electron (VS Code editor, chat,
#  browser address bars, etc.)
# ─────────────────────────────────────────────────────────
def _get_caret_uia_selection() -> Optional[Tuple[int, int]]:
    """Use TextPattern.GetSelection bounding rects as caret proxy."""
    if not _ensure_uia():
        return None
    try:
        ctrl = _auto.GetFocusedControl()
        if ctrl is None:
            return None
        tp = ctrl.GetTextPattern()
        if tp is None:
            return None
        sel = tp.GetSelection()
        if sel:
            for sr in sel:
                rects = sr.GetBoundingRectangles()
                if rects:
                    # rects is a Rect or list — first rect is x,y,w,h
                    if hasattr(rects, 'left'):
                        # It's a single Rect object
                        return (int(rects.left), int(rects.bottom))
                    elif hasattr(rects, '__getitem__'):
                        # Tuple/list  (x, y, w, h)
                        x, y, w, h = rects[0], rects[1], rects[2], rects[3]
                        return (int(x + w), int(y + h))
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────
#  Method 4 – Focused control bounding rectangle
#  Ultimate fallback: places the icon at the right edge
#  of whichever control has focus (terminals, custom UIs).
# ─────────────────────────────────────────────────────────
# Set of UIA ControlType names considered "editable"
_EDITABLE_TYPES = {"EditControl", "DocumentControl", "ComboBoxControl"}

# Pattern IDs that indicate a control can accept text
_EDITABLE_PATTERNS = {
    10002,  # ValuePattern
    10014,  # TextPattern
    10024,  # TextPattern2
    10032,  # TextEditPattern
}


def _get_caret_fallback() -> Optional[Tuple[int, int]]:
    """Return bottom-right of the focused control if it looks editable."""
    if not _ensure_uia():
        return None
    try:
        ctrl = _auto.GetFocusedControl()
        if ctrl is None:
            return None
        # Quick type check
        if ctrl.ControlTypeName not in _EDITABLE_TYPES:
            return None
        r = ctrl.BoundingRectangle
        if r.width() > 0 and r.height() > 0:
            return (int(r.right), int(r.bottom))
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────
#  Combined caret detection – tries all methods in order
# ─────────────────────────────────────────────────────────
def get_caret_screen_pos() -> Optional[Tuple[int, int]]:
    """
    Return (x, y) screen coordinates near the text caret,
    trying every detection method.  Returns None when no
    editable control appears to be focused.
    """
    # 1. Win32 – cheapest, most accurate for legacy apps
    pos = _get_caret_win32()
    if pos:
        return pos
    # 2. UIA TextPattern2.GetCaretRange
    pos = _get_caret_uia_tp2()
    if pos:
        return pos
    # 3. UIA TextPattern.GetSelection
    pos = _get_caret_uia_selection()
    if pos:
        return pos
    # 4. Focused control rect
    pos = _get_caret_fallback()
    if pos:
        return pos
    return None


def _is_editable_focused() -> bool:
    """Quick check: does the focused control look like a text input?"""
    if not _ensure_uia():
        return False
    try:
        ctrl = _auto.GetFocusedControl()
        if ctrl is None:
            return False
        # Check control type name
        if ctrl.ControlTypeName in _EDITABLE_TYPES:
            return True
        # Check if any editable pattern is present
        elem = ctrl.Element
        for pid in _EDITABLE_PATTERNS:
            try:
                if elem.GetCurrentPattern(pid):
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False


# ─────────────────────────────────────────────────────────
#  Mini clipboard icon (drawn programmatically)
# ─────────────────────────────────────────────────────────
def create_mini_icon(size: int = 22) -> QPixmap:
    """Draw a tiny clipboard icon for the companion."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Blue rounded rect background
    p.setBrush(QColor(108, 142, 255))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
    # White lines (clipboard content)
    pen = QPen(QColor(255, 255, 255))
    pen.setWidthF(1.4)
    p.setPen(pen)
    margin = size // 4
    for i in range(3):
        y = margin + i * 4
        if y < size - margin:
            p.drawLine(margin, y, size - margin, y)
    p.end()
    return pixmap


# ─────────────────────────────────────────────────────────
#  CaretCompanionIcon – the tiny floating widget
# ─────────────────────────────────────────────────────────
class CaretCompanionIcon(QWidget):
    """
    A small always-on-top frameless widget that follows the caret.
    Clicking it emits *clicked* so the overlay can open.
    """
    clicked = pyqtSignal()

    ICON_SIZE = 22
    OFFSET_X  = 6     # px to the right of the caret
    OFFSET_Y  = 4     # px below the caret

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Icon label
        self._icon_label = QLabel(self)
        self._icon_label.setPixmap(create_mini_icon(self.ICON_SIZE))
        self._icon_label.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)

        # Fade-out animation
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.92)

        self._fade_anim = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_anim.setDuration(600)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InQuad)

    # ── public helpers ──
    def move_near_caret(self, x: int, y: int):
        """Reposition to (x + offset, y + offset)."""
        self.move(x + self.OFFSET_X, y + self.OFFSET_Y)

    def fade_out(self):
        """Start a smooth fade-out, then hide."""
        if not self.isVisible():
            return
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity.opacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self._on_fade_done)
        self._fade_anim.start()

    def show_icon(self):
        """Show with full opacity."""
        self._fade_anim.stop()
        self._opacity.setOpacity(0.92)
        self.show()

    # ── internals ──
    def _on_fade_done(self):
        self._fade_anim.finished.disconnect(self._on_fade_done)
        self.hide()
        self._opacity.setOpacity(0.92)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(ev)


# ─────────────────────────────────────────────────────────
#  CaretSignalBridge – thread-safe Qt signal relay
# ─────────────────────────────────────────────────────────
class CaretSignalBridge(QObject):
    """Emits *key_pressed* from a background pynput thread."""
    key_pressed = pyqtSignal()


# ─────────────────────────────────────────────────────────
#  CaretCompanion – main manager
# ─────────────────────────────────────────────────────────
class CaretCompanion(QObject):
    """
    Manages the floating icon lifecycle:
      • Starts / stops a global keyboard listener (pynput)
      • On each keypress, polls the caret position via a QTimer
      • Shows / hides / repositions the CaretCompanionIcon
      • Fades the icon out after a few seconds of inactivity
    """
    open_requested = pyqtSignal()   # user clicked the companion icon

    _POLL_INTERVAL   = 120   # ms between caret-position polls
    _FADE_DELAY      = 4000  # ms before auto-fade
    _ACTIVITY_WINDOW = 400   # ms — treat repeated keys as one burst

    def __init__(self, parent=None):
        super().__init__(parent)

        self._enabled = False
        self._icon: Optional[CaretCompanionIcon] = None
        self._bridge = CaretSignalBridge()
        self._bridge.key_pressed.connect(self._on_key_activity)

        # Keyboard listener (pynput) — created on enable
        self._kb_listener = None

        # Polling timer — fires while icon is visible
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self._POLL_INTERVAL)
        self._poll_timer.timeout.connect(self._poll_caret)

        # Fade timer — hides icon after inactivity
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.setInterval(self._FADE_DELAY)
        self._fade_timer.timeout.connect(self._start_fade)

        # Last known caret pos  (to detect movement)
        self._last_pos: Optional[Tuple[int, int]] = None

    # ── public API ──────────────────────────────────────
    def set_enabled(self, on: bool):
        if on == self._enabled:
            return
        self._enabled = on
        if on:
            self._start_listener()
        else:
            self._stop_listener()
            self.hide_icon()

    def hide_icon(self):
        """Immediately hide the icon (e.g. when overlay opens)."""
        self._poll_timer.stop()
        self._fade_timer.stop()
        if self._icon:
            self._icon.hide()

    # ── keyboard listener ───────────────────────────────
    def _start_listener(self):
        if self._kb_listener is not None:
            return
        try:
            from pynput.keyboard import Listener
            self._kb_listener = Listener(on_press=self._on_kb_press)
            self._kb_listener.daemon = True
            self._kb_listener.start()
        except Exception:
            pass

    def _stop_listener(self):
        if self._kb_listener is not None:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
            self._kb_listener = None

    def _on_kb_press(self, key):
        """Called from pynput thread — relay via signal bridge."""
        try:
            self._bridge.key_pressed.emit()
        except Exception:
            pass

    # ── activity handling (runs on Qt main thread) ──────
    def _on_key_activity(self):
        if not self._enabled:
            return
        # Reset fade timer
        self._fade_timer.stop()
        self._fade_timer.start()
        # Start polling if not already
        if not self._poll_timer.isActive():
            self._poll_caret()           # immediate first poll
            self._poll_timer.start()

    # ── caret polling ───────────────────────────────────
    def _poll_caret(self):
        pos = get_caret_screen_pos()
        if pos is None:
            # No caret found — hide and stop polling
            self._poll_timer.stop()
            self._fade_timer.stop()
            if self._icon and self._icon.isVisible():
                self._icon.fade_out()
            return

        # Clamp to screen bounds
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = min(pos[0], geom.right() - 30)
            y = min(pos[1], geom.bottom() - 30)
            x = max(x, geom.left())
            y = max(y, geom.top())
            pos = (x, y)

        self._last_pos = pos
        self._ensure_icon()
        self._icon.move_near_caret(pos[0], pos[1])
        if not self._icon.isVisible():
            self._icon.show_icon()

    def _start_fade(self):
        """Fade timer expired — hide the icon smoothly."""
        self._poll_timer.stop()
        if self._icon:
            self._icon.fade_out()

    # ── icon lifecycle ──────────────────────────────────
    def _ensure_icon(self):
        if self._icon is None:
            self._icon = CaretCompanionIcon()
            self._icon.clicked.connect(self._on_icon_clicked)

    def _on_icon_clicked(self):
        self.hide_icon()
        self.open_requested.emit()
