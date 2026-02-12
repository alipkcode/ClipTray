"""
ClipTray - Styles & Theming
Modern dark-themed QSS stylesheet for the overlay UI.
"""


def get_stylesheet() -> str:
    """Return the main application QSS stylesheet."""
    return """
    /* ── Global ─────────────────────────────────────────── */
    * {
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }

    /* ── Overlay background ─────────────────────────────── */
    #OverlayBackground {
        background-color: rgba(0, 0, 0, 160);
    }

    /* ── Main Panel ─────────────────────────────────────── */
    #MainPanel {
        background-color: #1E1E2E;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* ── Title Bar ──────────────────────────────────────── */
    #TitleBar {
        background: transparent;
        padding: 0px;
    }

    #TitleLabel {
        color: #CDD6F4;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    #SubtitleLabel {
        color: #6C7086;
        font-size: 12px;
        font-weight: 400;
    }

    #CloseButton {
        background-color: rgba(255, 255, 255, 0.05);
        border: none;
        border-radius: 8px;
        color: #6C7086;
        font-size: 18px;
        font-weight: bold;
        padding: 4px;
        min-width: 32px;
        min-height: 32px;
        max-width: 32px;
        max-height: 32px;
    }
    #CloseButton:hover {
        background-color: rgba(255, 80, 80, 0.3);
        color: #FF6C6C;
    }

    /* ── Search Bar ─────────────────────────────────────── */
    #SearchBar {
        background-color: #181825;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        color: #CDD6F4;
        font-size: 14px;
        padding: 10px 16px 10px 40px;
        selection-background-color: #6C8EFF;
    }
    #SearchBar:focus {
        border: 1px solid rgba(108, 142, 255, 0.5);
    }
    #SearchBar::placeholder {
        color: #45475A;
    }

    /* ── Scroll Area ────────────────────────────────────── */
    #ClipScrollArea {
        background: transparent;
        border: none;
    }
    #ClipScrollArea QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 4px 2px;
    }
    #ClipScrollArea QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 0.12);
        border-radius: 3px;
        min-height: 30px;
    }
    #ClipScrollArea QScrollBar::handle:vertical:hover {
        background: rgba(255, 255, 255, 0.25);
    }
    #ClipScrollArea QScrollBar::add-line:vertical,
    #ClipScrollArea QScrollBar::sub-line:vertical,
    #ClipScrollArea QScrollBar::add-page:vertical,
    #ClipScrollArea QScrollBar::sub-page:vertical {
        background: none;
        border: none;
        height: 0px;
    }

    /* ── Clip Cards ─────────────────────────────────────── */
    #ClipCard {
        background-color: #181825;
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 0px;
    }
    #ClipCard:hover {
        background-color: #1E1E30;
        border: 1px solid rgba(108, 142, 255, 0.2);
    }

    #ClipCardTitle {
        color: #CDD6F4;
        font-size: 14px;
        font-weight: 600;
    }

    #ClipCardText {
        color: #A6ADC8;
        font-size: 12px;
        font-weight: 400;
    }

    #ClipCardAccent {
        border-radius: 2px;
    }

    /* ── Action Buttons on Cards ────────────────────────── */
    #CardActionBtn {
        background: rgba(255, 255, 255, 0.04);
        border: none;
        border-radius: 6px;
        color: #6C7086;
        font-size: 13px;
        padding: 4px 8px;
        min-width: 28px;
        min-height: 28px;
        max-width: 28px;
        max-height: 28px;
    }
    #CardActionBtn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #CDD6F4;
    }
    #DeleteBtn {
        background: rgba(255, 255, 255, 0.04);
        border: none;
        border-radius: 6px;
        color: #6C7086;
        font-size: 13px;
        padding: 4px 8px;
        min-width: 28px;
        min-height: 28px;
        max-width: 28px;
        max-height: 28px;
    }
    #DeleteBtn:hover {
        background: rgba(255, 80, 80, 0.15);
        color: #FF6C6C;
    }

    /* ── Add Button ─────────────────────────────────────── */
    #AddButton {
        background-color: #6C8EFF;
        border: none;
        border-radius: 12px;
        color: white;
        font-size: 14px;
        font-weight: 600;
        padding: 10px 24px;
    }
    #AddButton:hover {
        background-color: #8BA4FF;
    }
    #AddButton:pressed {
        background-color: #5A7AE6;
    }

    /* ── Dialog (Add/Edit Clip) ──────────────────────────── */
    #DialogPanel {
        background-color: #1E1E2E;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    #DialogTitle {
        color: #CDD6F4;
        font-size: 18px;
        font-weight: 700;
    }

    #DialogLabel {
        color: #A6ADC8;
        font-size: 13px;
        font-weight: 500;
    }

    #DialogInput {
        background-color: #181825;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        color: #CDD6F4;
        font-size: 14px;
        padding: 10px 14px;
        selection-background-color: #6C8EFF;
    }
    #DialogInput:focus {
        border: 1px solid rgba(108, 142, 255, 0.5);
    }

    #DialogTextEdit {
        background-color: #181825;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        color: #CDD6F4;
        font-size: 14px;
        padding: 10px 14px;
        selection-background-color: #6C8EFF;
    }
    #DialogTextEdit:focus {
        border: 1px solid rgba(108, 142, 255, 0.5);
    }

    #SaveButton {
        background-color: #6C8EFF;
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 14px;
        font-weight: 600;
        padding: 10px 28px;
    }
    #SaveButton:hover {
        background-color: #8BA4FF;
    }

    #CancelButton {
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        color: #A6ADC8;
        font-size: 14px;
        font-weight: 500;
        padding: 10px 28px;
    }
    #CancelButton:hover {
        background-color: rgba(255, 255, 255, 0.1);
        color: #CDD6F4;
    }

    /* ── Empty State ─────────────────────────────────────── */
    #EmptyStateLabel {
        color: #45475A;
        font-size: 14px;
        font-weight: 400;
    }
    #EmptyStateIcon {
        color: #313244;
        font-size: 48px;
    }

    /* ── Tooltip-style info ──────────────────────────────── */
    QToolTip {
        background-color: #313244;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        color: #CDD6F4;
        font-size: 12px;
        padding: 6px 10px;
    }

    /* ── Color Picker Buttons ───────────────────────────── */
    #ColorPickerBtn {
        border: 2px solid transparent;
        border-radius: 12px;
        min-width: 24px;
        min-height: 24px;
        max-width: 24px;
        max-height: 24px;
    }
    #ColorPickerBtn:hover {
        border: 2px solid rgba(255, 255, 255, 0.3);
    }
    #ColorPickerBtnSelected {
        border: 2px solid white;
        border-radius: 12px;
        min-width: 24px;
        min-height: 24px;
        max-width: 24px;
        max-height: 24px;
    }

    /* ── Settings Button ─────────────────────────────────── */
    #SettingsButton {
        background-color: rgba(255, 255, 255, 0.05);
        border: none;
        border-radius: 8px;
        color: #6C7086;
        font-size: 17px;
        padding: 4px;
        min-width: 32px;
        min-height: 32px;
        max-width: 32px;
        max-height: 32px;
    }
    #SettingsButton:hover {
        background-color: rgba(108, 142, 255, 0.15);
        color: #6C8EFF;
    }

    /* ── Settings Dialog Items ───────────────────────────── */
    #SettingsItemTitle {
        color: #CDD6F4;
        font-size: 15px;
        font-weight: 600;
    }

    #SettingsItemDesc {
        color: #6C7086;
        font-size: 12px;
        font-weight: 400;
        line-height: 1.4;
    }

    #SettingsStatusLabel {
        color: #6C7086;
        font-size: 11px;
    }

    /* ── Waiting Indicator (floating badge) ──────────────── */
    #WaitingBadge {
        background-color: #1E1E2E;
        border: 1px solid rgba(108, 142, 255, 0.3);
        border-radius: 12px;
    }
    #WaitingBadgeText {
        color: #6C8EFF;
        font-size: 13px;
        font-weight: 500;
    }
    #WaitingBadgeHint {
        color: #6C7086;
        font-size: 11px;
    }
    #WaitingCancelBtn {
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        color: #A6ADC8;
        font-size: 12px;
        padding: 4px 14px;
    }
    #WaitingCancelBtn:hover {
        background-color: rgba(255, 80, 80, 0.15);
        color: #FF6C6C;
    }

    /* ── Macro Toggle (segmented) ── */
    #MacroToggleOuter {
        background-color: #181825;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
    }
    #MacroSegBtn {
        background-color: transparent;
        border: none;
        border-radius: 10px;
        color: #585B70;
        font-size: 13px;
        font-weight: 500;
        padding: 7px 0px;
    }
    #MacroSegBtn:hover {
        color: #A6ADC8;
    }
    #MacroSegBtn:checked {
        background-color: rgba(108, 142, 255, 0.14);
        color: #89B4FA;
        font-weight: 600;
    }

    /* ── Macro Builder Area ── */
    #MacroHint {
        color: #585B70;
        font-size: 11px;
        font-style: italic;
        padding: 0px;
        background: transparent;
        border: none;
    }
    #MacroScroll {
        background: transparent;
        border: none;
    }
    #MacroScroll QScrollBar:vertical {
        background: transparent;
        width: 5px;
        margin: 2px;
    }
    #MacroScroll QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 0.10);
        border-radius: 2px;
        min-height: 20px;
    }
    #MacroScroll QScrollBar::add-line:vertical,
    #MacroScroll QScrollBar::sub-line:vertical,
    #MacroScroll QScrollBar::add-page:vertical,
    #MacroScroll QScrollBar::sub-page:vertical {
        background: none;
        border: none;
        height: 0px;
    }
    #MacroStepsContainer {
        background: transparent;
    }

    /* Step number pills */
    #StepNumber {
        background-color: rgba(108, 142, 255, 0.12);
        border: 1px solid rgba(108, 142, 255, 0.2);
        border-radius: 12px;
        color: #89B4FA;
        font-size: 11px;
        font-weight: 700;
    }
    #StepNumberAction {
        background-color: rgba(249, 226, 175, 0.12);
        border: 1px solid rgba(249, 226, 175, 0.2);
        border-radius: 12px;
        color: #F9E2AF;
        font-size: 11px;
        font-weight: 700;
    }
    #StepDeleteBtn {
        background-color: transparent;
        border: none;
        border-radius: 4px;
        color: #45475A;
        font-size: 13px;
        padding: 2px;
    }
    #StepDeleteBtn:hover {
        background-color: rgba(255, 80, 80, 0.1);
        color: #F38BA8;
    }

    /* Text editor in macro */
    #MacroTextEdit {
        background-color: #181825;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        color: #CDD6F4;
        font-size: 13px;
        padding: 8px 10px;
        selection-background-color: rgba(108, 142, 255, 0.25);
    }
    #MacroTextEdit:focus {
        border: 1px solid rgba(108, 142, 255, 0.35);
    }

    /* Action badge */
    #ActionBadge {
        background-color: rgba(249, 226, 175, 0.08);
        border: 1px solid rgba(249, 226, 175, 0.18);
        border-radius: 10px;
    }
    #ActionBadgeIcon {
        color: #F9E2AF;
        font-size: 14px;
        background: transparent;
        border: none;
    }
    #ActionBadgeLabel {
        color: #F9E2AF;
        font-size: 12px;
        font-weight: 600;
        background: transparent;
        border: none;
    }

    /* Toolbar buttons */
    #AddActionBtn {
        background-color: rgba(249, 226, 175, 0.08);
        border: 1px solid rgba(249, 226, 175, 0.15);
        border-radius: 8px;
        color: #F9E2AF;
        font-size: 12px;
        font-weight: 500;
        padding: 6px 14px;
    }
    #AddActionBtn:hover {
        background-color: rgba(249, 226, 175, 0.16);
        border-color: rgba(249, 226, 175, 0.3);
    }
    #AddTextBtn {
        background-color: rgba(108, 142, 255, 0.08);
        border: 1px solid rgba(108, 142, 255, 0.15);
        border-radius: 8px;
        color: #89B4FA;
        font-size: 12px;
        font-weight: 500;
        padding: 6px 14px;
    }
    #AddTextBtn:hover {
        background-color: rgba(108, 142, 255, 0.16);
        border-color: rgba(108, 142, 255, 0.3);
    }

    /* Key capture overlay */
    #KeyCaptureOverlay {
        background-color: #181825;
        border: 1px solid rgba(166, 227, 161, 0.25);
        border-radius: 14px;
    }
    #CaptureIcon {
        color: #A6E3A1;
        font-size: 28px;
        background: transparent;
        border: none;
    }
    #CapturePrompt {
        color: #CDD6F4;
        font-size: 14px;
        font-weight: 600;
        background: transparent;
        border: none;
    }
    #CaptureHint {
        color: #585B70;
        font-size: 11px;
        background: transparent;
        border: none;
    }
    #CaptureCancelBtn {
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        color: #6C7086;
        font-size: 11px;
        padding: 4px 12px;
        margin-top: 4px;
    }
    #CaptureCancelBtn:hover {
        background-color: rgba(255, 80, 80, 0.12);
        color: #F38BA8;
    }

    /* Macro indicator on clip cards */
    #MacroIndicator {
        background-color: rgba(108, 142, 255, 0.15);
        border-radius: 10px;
        color: #6C8EFF;
        font-size: 12px;
    }
    """
