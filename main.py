"""
ClipTray - Main Entry Point
Creates the system tray icon and manages the application lifecycle.
When the user clicks the tray icon, it shows the overlay.
When a clip is selected, it types the text into the active window using pyautogui.
"""

import sys
import os
import time

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer

import pyautogui

from clip_manager import ClipManager
from overlay import OverlayWindow


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


class ClipTrayApp:
    """Main application class that orchestrates everything."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        self.app.setApplicationName("ClipTray")
        self.app.setApplicationDisplayName("ClipTray")

        # ── Data ──
        self.clip_manager = ClipManager()

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
        self.overlay = OverlayWindow(self.clip_manager)
        self.overlay.type_clip.connect(self._on_type_clip)

        # ── Show tray ──
        self.tray_icon.show()

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
        self.overlay.show_overlay()

    def _on_type_clip(self, text: str):
        """Handle clip selection — type the text into the active field."""
        # Give time for focus to return to the previous window
        time.sleep(0.15)
        type_text(text)

    def _quit(self):
        """Clean exit."""
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
