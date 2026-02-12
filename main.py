"""
ClipTray - Main Entry Point
Creates the system tray icon and manages the application lifecycle.
When the user clicks the tray icon, it shows the overlay.
When a clip is selected, it types the text into the active window using pyautogui.
Supports Click-to-Paste mode: waits for user to click a text field first.
"""

import sys
import os
import time
import threading

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QFont, QCursor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

import pyautogui

from clip_manager import ClipManager, TextStep, ActionStep
from settings_manager import SettingsManager
from overlay import OverlayWindow
from splash import SplashOverlay
from caret_companion import CaretCompanion


# ── Disable pyautogui fail-safe for smoother operation ──
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.02  # Small pause between key events


def get_resource_path(filename: str) -> str:
    """Get the absolute path to a resource file, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running from PyInstaller bundle
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def create_fallback_icon() -> QIcon:
    """Create a simple icon programmatically if icon.png is missing."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw a rounded rectangle (clipboard board)
    painter.setBrush(QColor(108, 142, 255))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(10, 8, 44, 50, 6, 6)

    # Draw clip at top
    painter.setBrush(QColor(200, 210, 230))
    painter.drawRoundedRect(22, 4, 20, 12, 3, 3)

    # Draw paper
    painter.setBrush(QColor(240, 242, 248))
    painter.drawRoundedRect(15, 18, 34, 36, 3, 3)

    # Draw text lines
    painter.setBrush(QColor(160, 175, 210))
    for y in [24, 30, 36, 42]:
        w = 26 if y < 42 else 18
        painter.drawRect(19, y, w, 2)

    painter.end()
    return QIcon(pixmap)


def load_icon() -> QIcon:
    """Load the tray icon."""
    icon_path = get_resource_path("icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return create_fallback_icon()


def type_text(text: str):
    """
    Type the given text into the currently focused field.
    Uses pyperclip + Ctrl+V for reliability with special characters,
    falls back to pyautogui.write() for simple ASCII text.
    """
    try:
        import pyperclip

        # Save current clipboard
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = ""

        # Copy our text to clipboard
        pyperclip.copy(text)
        time.sleep(0.05)

        # Paste it
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)

        # Restore old clipboard after a delay
        QTimer.singleShot(1000, lambda: _restore_clipboard(old_clipboard))

    except ImportError:
        # pyperclip not available, use direct typing
        # This works well for ASCII but may fail with special chars
        for char in text:
            if char == '\n':
                pyautogui.press('enter')
            elif char == '\t':
                pyautogui.press('tab')
            else:
                try:
                    pyautogui.write(char, interval=0.01)
                except Exception:
                    pass


def _restore_clipboard(old_text: str):
    """Restore the clipboard content."""
    try:
        import pyperclip
        pyperclip.copy(old_text)
    except Exception:
        pass


def execute_macro(steps):
    """
    Execute a macro — a sequence of TextStep and ActionStep objects.
    For TextStep: types the text using clipboard paste.
    For ActionStep: presses the specified key combination.
    """
    import pyperclip

    # Save clipboard once at the start
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    for i, step in enumerate(steps):
        if isinstance(step, TextStep) and step.value:
            pyperclip.copy(step.value)
            time.sleep(0.05)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
        elif isinstance(step, ActionStep) and step.keys:
            time.sleep(0.05)
            pyautogui.hotkey(*step.keys)
            time.sleep(0.1)

        # Small gap between steps for reliability
        if i < len(steps) - 1:
            time.sleep(0.05)

    # Restore clipboard after a delay
    QTimer.singleShot(1000, lambda: _restore_clipboard(old_clipboard))


class ClickSignalBridge(QObject):
    """Bridge to safely emit Qt signals from a background pynput thread."""
    click_detected = pyqtSignal()


class WaitingBadge(QWidget):
    """
    A small floating badge that tells the user ClipTray is waiting
    for them to click on a text field. Includes a Cancel button.
    """
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(340, 70)

        self._build_ui()
        self._position_bottom_center()

    def _build_ui(self):
        panel = QWidget(self)
        panel.setObjectName("WaitingBadge")
        panel.setGeometry(0, 0, 340, 70)

        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 100))
        panel.setGraphicsEffect(shadow)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # Pulsing dot indicator
        dot = QLabel("●")
        dot.setStyleSheet("color: #6C8EFF; font-size: 16px;")
        layout.addWidget(dot)

        # Text
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title = QLabel("Click on a text field...")
        title.setObjectName("WaitingBadgeText")
        text_col.addWidget(title)

        hint = QLabel("ClipTray will paste when you click")
        hint.setObjectName("WaitingBadgeHint")
        text_col.addWidget(hint)

        layout.addLayout(text_col, 1)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("WaitingCancelBtn")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)

    def _position_bottom_center(self):
        """Position the badge at the bottom center of the screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() - self.height() - 40
            self.move(x, y)

    def _on_cancel(self):
        self.cancelled.emit()


class ClipTrayApp:
    """Main application class that orchestrates everything."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        self.app.setApplicationName("ClipTray")
        self.app.setApplicationDisplayName("ClipTray")

        # ── Data ──
        self.clip_manager = ClipManager()
        self.settings = SettingsManager()

        # ── Click-to-paste state ──
        self._waiting_text = None       # Text waiting to be pasted
        self._waiting_macro = None      # Macro clip waiting to be executed
        self._mouse_listener = None     # pynput listener thread
        self._waiting_badge = None      # Floating badge widget
        self._click_bridge = ClickSignalBridge()
        self._click_bridge.click_detected.connect(self._on_global_click)

        # ── Tray Icon ──
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(load_icon())
        self.tray_icon.setToolTip("ClipTray — Click to open your clips")
        self.tray_icon.activated.connect(self._on_tray_activated)

        # ── Tray context menu ──
        menu = QMenu()

        show_action = QAction("Open ClipTray", menu)
        show_action.triggered.connect(self._show_overlay)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

        # ── Overlay Window ──
        self.overlay = OverlayWindow(self.clip_manager, self.settings)
        self.overlay.type_clip.connect(self._on_type_clip)
        self.overlay.wait_and_type_clip.connect(self._on_wait_and_type_clip)
        self.overlay.execute_macro.connect(self._on_execute_macro)
        self.overlay.wait_and_execute_macro.connect(self._on_wait_and_execute_macro)

        # Import stylesheet for badge
        from styles import get_stylesheet
        self._badge_stylesheet = get_stylesheet()

        # ── Caret Companion ──
        self.caret_companion = CaretCompanion()
        self.caret_companion.open_requested.connect(self._on_companion_open)
        self.caret_companion.set_enabled(self.settings.caret_companion)

        # Watch for settings changes (re-check after overlay closes)
        self.overlay.settings_changed = self._on_settings_changed

        # ── Show tray ──
        self.tray_icon.show()

        # ── Welcome splash on startup ──
        self.splash = SplashOverlay()
        self.splash.finished.connect(self._on_splash_done)
        self.splash.start()

    def _on_splash_done(self):
        """Splash animation finished — app is ready in the tray."""
        self.splash = None

    def _on_tray_activated(self, reason):
        """Handle tray icon clicks."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click — toggle overlay
            if self.overlay.isVisible():
                self.overlay.hide_overlay()
            else:
                self._show_overlay()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_overlay()

    def _show_overlay(self):
        """Show the overlay window."""
        if self.caret_companion:
            self.caret_companion.hide_icon()
        self.overlay.show_overlay()

    def _on_companion_open(self):
        """User clicked the caret companion icon — open overlay."""
        self.caret_companion.hide_icon()
        self.overlay.show_overlay()

    def _on_settings_changed(self):
        """Called when settings dialog closes — re-sync caret companion."""
        self.caret_companion.set_enabled(self.settings.caret_companion)

    def _on_type_clip(self, text: str):
        """Handle clip selection — type the text into the active field (immediate mode)."""
        # Give time for focus to return to the previous window
        time.sleep(0.15)
        type_text(text)

    def _on_wait_and_type_clip(self, text: str):
        """Handle clip selection in Click-to-Paste mode — wait for user click."""
        self._waiting_text = text
        self._waiting_macro = None
        self._show_waiting_badge()
        self._start_click_listener()

    def _on_execute_macro(self, clip):
        """Handle macro clip selection — execute the step sequence immediately."""
        time.sleep(0.15)
        execute_macro(clip.steps)

    def _on_wait_and_execute_macro(self, clip):
        """Handle macro clip selection in Click-to-Paste mode — wait for user click."""
        self._waiting_text = None
        self._waiting_macro = clip
        self._show_waiting_badge()
        self._start_click_listener()

    def _show_waiting_badge(self):
        """Show the floating indicator that we're waiting for a click."""
        if self._waiting_badge:
            self._waiting_badge.hide()
            self._waiting_badge.deleteLater()

        self._waiting_badge = WaitingBadge()
        self._waiting_badge.setStyleSheet(self._badge_stylesheet)
        self._waiting_badge.cancelled.connect(self._cancel_waiting)
        self._waiting_badge.show()

    def _hide_waiting_badge(self):
        """Hide and clean up the waiting badge."""
        if self._waiting_badge:
            self._waiting_badge.hide()
            self._waiting_badge.deleteLater()
            self._waiting_badge = None

    def _start_click_listener(self):
        """Start a global mouse listener that waits for the next click."""
        self._stop_click_listener()  # Clean up any existing listener

        try:
            from pynput import mouse

            def on_click(x, y, button, pressed):
                if pressed and button == mouse.Button.left:
                    # Emit signal from background thread to Qt main thread
                    self._click_bridge.click_detected.emit()
                    return False  # Stop the listener

            self._mouse_listener = mouse.Listener(on_click=on_click)
            self._mouse_listener.start()
        except ImportError:
            # pynput not available — fall back to a simple timer approach
            print("[ClipTray] pynput not found, using timer fallback")
            QTimer.singleShot(2000, self._on_global_click)

    def _stop_click_listener(self):
        """Stop the global mouse listener if running."""
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

    def _on_global_click(self):
        """Called when a global mouse click is detected — paste the waiting text."""
        self._stop_click_listener()
        self._hide_waiting_badge()

        if self._waiting_macro:
            clip = self._waiting_macro
            self._waiting_macro = None
            self._waiting_text = None
            QTimer.singleShot(150, lambda: execute_macro(clip.steps))
        elif self._waiting_text:
            text = self._waiting_text
            self._waiting_text = None
            # Small delay to let the click register in the target field
            QTimer.singleShot(150, lambda: type_text(text))

    def _cancel_waiting(self):
        """User cancelled the click-to-paste wait."""
        self._stop_click_listener()
        self._hide_waiting_badge()
        self._waiting_text = None
        self._waiting_macro = None

    def _quit(self):
        """Clean exit."""
        self._stop_click_listener()
        self._hide_waiting_badge()
        self.caret_companion.set_enabled(False)
        self.tray_icon.hide()
        self.app.quit()

    def run(self) -> int:
        """Start the application event loop."""
        return self.app.exec()


def main():
    """Entry point."""
    # Generate icon if missing
    icon_path = get_resource_path("icon.png")
    if not os.path.exists(icon_path):
        try:
            from generate_icon import generate_icon
            generate_icon()
        except Exception:
            pass  # Will use fallback icon

    app = ClipTrayApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
