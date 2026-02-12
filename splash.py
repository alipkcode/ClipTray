"""
ClipTray - Welcome Splash Screen
Shows a beautiful welcome message on startup, then smoothly
animates shrinking down toward the system tray in the taskbar.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QPoint, QParallelAnimationGroup, QSequentialAnimationGroup,
    pyqtSignal, pyqtProperty, QSize
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont

from styles import get_stylesheet


class SplashOverlay(QWidget):
    """
    Full-screen dimmed overlay with a centered welcome card.
    After a pause, the card shrinks and flies down to the taskbar tray area,
    then the whole overlay fades out.
    """

    finished = pyqtSignal()  # Emitted when the animation completes

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Window flags: fullscreen transparent overlay ──
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ── Dim level for background (animated) ──
        self._dim_opacity = 160  # 0-255

        # ── Position on screen ──
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        # ── Build the card ──
        self._build_card()

        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())

    def _build_card(self):
        """Create the welcome card widget."""
        self.card = QWidget(self)
        self.card.setObjectName("SplashCard")
        self.card.setStyleSheet("""
            #SplashCard {
                background-color: #1E1E2E;
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

        card_w, card_h = 420, 240
        self.card.setFixedSize(card_w, card_h)

        # Center the card
        sw = self.width()
        sh = self.height()
        cx = (sw - card_w) // 2
        cy = (sh - card_h) // 2
        self.card.move(cx, cy)

        # Shadow
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(80)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.card.setGraphicsEffect(shadow)

        # ── Card contents ──
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Clipboard emoji icon
        icon_label = QLabel("📋")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 42px; background: transparent; border: none;")
        layout.addWidget(icon_label)

        # Welcome title
        title = QLabel("Welcome to ClipTray")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #CDD6F4;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title)

        # Subtitle message
        subtitle = QLabel("We're waiting for you to click on us\nin the system tray!")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            color: #6C7086;
            font-size: 14px;
            font-weight: 400;
            background: transparent;
            border: none;
        """)
        layout.addWidget(subtitle)

        # Tray hint with arrow
        hint = QLabel("▼  Find us in the taskbar")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("""
            color: #6C8EFF;
            font-size: 12px;
            font-weight: 500;
            margin-top: 8px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(hint)

    # ── Background dim painting ──

    def _get_dim_opacity(self):
        return self._dim_opacity

    def _set_dim_opacity(self, val):
        self._dim_opacity = int(val)
        self.update()

    dimOpacity = pyqtProperty(int, _get_dim_opacity, _set_dim_opacity)

    def paintEvent(self, event):
        """Draw the semi-transparent dimmed background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, self._dim_opacity))
        painter.end()

    # ── Animation sequence ──

    def start(self):
        """Show the splash and start the animation sequence."""
        self.show()
        self.raise_()
        self.activateWindow()

        # Fade in the dim background
        self._fade_in_bg = QPropertyAnimation(self, b"dimOpacity")
        self._fade_in_bg.setDuration(400)
        self._fade_in_bg.setStartValue(0)
        self._fade_in_bg.setEndValue(160)
        self._fade_in_bg.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Card scale-in entrance (simulate via geometry animation)
        card_w, card_h = self.card.width(), self.card.height()
        cx = (self.width() - card_w) // 2
        cy = (self.height() - card_h) // 2
        final_rect = QRect(cx, cy, card_w, card_h)

        # Start slightly smaller and lower
        start_rect = QRect(
            cx + 20, cy + 30,
            card_w - 40, card_h - 20
        )

        self._card_entrance = QPropertyAnimation(self.card, b"geometry")
        self._card_entrance.setDuration(500)
        self._card_entrance.setStartValue(start_rect)
        self._card_entrance.setEndValue(final_rect)
        self._card_entrance.setEasingCurve(QEasingCurve.Type.OutBack)

        # Play entrance together
        self._entrance_group = QParallelAnimationGroup()
        self._entrance_group.addAnimation(self._fade_in_bg)
        self._entrance_group.addAnimation(self._card_entrance)
        self._entrance_group.start()

        # After 2.5 seconds, start the shrink-to-tray animation
        QTimer.singleShot(2500, self._animate_shrink_to_tray)

    def _animate_shrink_to_tray(self):
        """Shrink the card down toward the system tray area and fade out."""
        # Target: bottom-right corner of the screen (where tray usually is)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            # Tray is typically bottom-right on Windows
            tray_x = geo.x() + geo.width() - 40
            tray_y = geo.y() + geo.height() - 10
        else:
            tray_x = self.width() - 40
            tray_y = self.height() - 10

        # Target rect: tiny, at the tray location
        target_rect = QRect(tray_x - 20, tray_y - 10, 40, 20)

        current_rect = self.card.geometry()

        # Card shrink + fly to tray
        self._card_shrink = QPropertyAnimation(self.card, b"geometry")
        self._card_shrink.setDuration(800)
        self._card_shrink.setStartValue(current_rect)
        self._card_shrink.setEndValue(target_rect)
        self._card_shrink.setEasingCurve(QEasingCurve.Type.InBack)

        # Fade out the dim background
        self._fade_out_bg = QPropertyAnimation(self, b"dimOpacity")
        self._fade_out_bg.setDuration(600)
        self._fade_out_bg.setStartValue(160)
        self._fade_out_bg.setEndValue(0)
        self._fade_out_bg.setEasingCurve(QEasingCurve.Type.InCubic)

        # Play shrink and fade together
        self._exit_group = QParallelAnimationGroup()
        self._exit_group.addAnimation(self._card_shrink)
        self._exit_group.addAnimation(self._fade_out_bg)
        self._exit_group.finished.connect(self._on_animation_done)
        self._exit_group.start()

    def _on_animation_done(self):
        """Called when the full animation is complete."""
        self.hide()
        self.finished.emit()
        self.deleteLater()
