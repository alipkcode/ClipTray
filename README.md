![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Version](https://img.shields.io/badge/Version-1.4-6C8EFF)
![License](https://img.shields.io/badge/License-MIT-green)

# ClipTray

## 🚀 Overview

**ClipTray** is a Windows system tray application for managing and instantly pasting reusable text snippets and macros. It lives in the system tray, and on click, presents a fullscreen semi-transparent overlay with a searchable, scrollable list of saved clips. Selecting a clip automatically types or pastes the text into the currently focused field — no manual Ctrl+V required.

ClipTray also supports **macro clips** — sequences of text blocks interleaved with keyboard actions (e.g., type text → press Tab → type more text → press Enter), enabling complex multi-step input automation.

## 🧠 Architecture

- **Language:** Python 3.10+
- **GUI Framework:** PyQt6 — used for the overlay window, system tray icon, dialogs, and all widgets
- **Runtime:** Desktop (Windows), runs as a persistent system tray application
- **Design Pattern:** Single-process event-driven architecture with signal/slot communication (Qt signals), layered into manager and UI modules
- **Automation:** `pyautogui` for simulating keyboard input; `pyperclip` for clipboard-based paste; `pynput` for global mouse/keyboard listening
- **Accessibility:** Win32 API (`GetGUIThreadInfo`) and UI Automation (`comtypes` + `uiautomation`) for detecting the text caret position across native, WPF, UWP, and Chromium/Electron applications
- **Persistence:** JSON files (`clips.json` for clip data, `settings.json` for user preferences) stored alongside the executable
- **Build/Distribution:** PyInstaller packages the app into a single portable `.exe`

### High-Level Flow

1. Application starts → splash screen animates → system tray icon appears
2. User clicks tray icon → fullscreen overlay dims the desktop and shows clip list
3. User searches/selects a clip → overlay closes → text is pasted into the focused field via clipboard paste or macro execution
4. Optional: **Click-to-Paste** mode waits for the user to click a specific text field before pasting
5. Optional: **Caret Companion** shows a floating mini icon near the blinking text cursor for quick access

## ✨ Features

- **System Tray Integration** — runs quietly in the Windows taskbar; single-click to open, right-click for context menu (Open / Quit)
- **Fullscreen Overlay UI** — semi-transparent dimmed overlay with a centered panel; closes on Escape or clicking outside
- **Clip Management (CRUD)** — create, edit, delete, and search saved text snippets with a polished dialog UI
- **Instant Paste** — selecting a clip automatically types the text into the active window using clipboard-paste (`Ctrl+V`) with clipboard state preservation
- **Macro Clips** — build multi-step macros combining text typing and keyboard actions (e.g., Enter, Tab, Ctrl+A) via a visual macro builder with key capture
- **Click-to-Paste Mode** — optional mode where selecting a clip shows a floating "waiting" badge, then pastes only after the user clicks a target text field
- **Search & Filter** — real-time search by title or content with instant results
- **Pin Clips** — pin important clips to the top of the list; pinned and unpinned clips are visually separated
- **Drag-and-Drop Reordering** — reorder clips by dragging via a handle; visual drop indicator shows position
- **Color-Coded Clips** — assign accent colors to clips from a palette of 8 predefined colors
- **Caret Companion** — a floating mini clipboard icon that appears near the text cursor while typing, with configurable position (8 directions) and automatic screen-edge fallback
- **Caret Detection** — multi-method caret position detection: Win32 `GetGUIThreadInfo`, UIA `TextPattern2`, UIA `TextPattern.GetSelection`, and focused-control bounding rect fallback
- **Settings Panel** — toggle Click-to-Paste and Caret Companion; configure companion icon position with a visual picker
- **Credits / About Dialog** — displays version (1.4), developer (Ali Paknahal), company (Certainty), GitHub link, and license info
- **Welcome Splash Screen** — animated card on startup that shrinks and flies to the taskbar tray
- **Dark Theme** — modern dark UI styled with QSS (Catppuccin-inspired palette), custom toggle switches, drop shadows, and smooth animations
- **Programmatic Icon Generation** — creates a clipboard-style PNG icon if none exists; also provides an in-memory fallback icon
- **PyInstaller Build Script** — one-command build to a single portable `.exe` (`python build.py`)

## 🛠 Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI Framework | PyQt6 ≥ 6.5.0 |
| Input Automation | pyautogui ≥ 0.9.54 |
| Clipboard Access | pyperclip ≥ 1.8.0 |
| Global Input Listening | pynput ≥ 1.7.0 |
| Accessibility / Caret Detection | uiautomation ≥ 2.0.0, comtypes ≥ 1.2.0, Win32 API (ctypes) |
| Image Processing | Pillow ≥ 10.0.0 |
| Data Storage | JSON (file-based) |
| Build Tool | PyInstaller ≥ 6.0.0 |
| Platform | Windows |

## 📦 Installation

### Prerequisites

- **Python 3.10+** installed and available on PATH
- **Windows OS** (Caret Companion uses Win32 API and UI Automation)

### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/alipkcode/ClipTray.git
   cd ClipTray
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   python main.py
   ```

4. **Build a standalone `.exe` (optional):**

   ```bash
   python build.py
   ```

   The compiled executable will be at `dist/ClipTray.exe`.

## ⚙️ Configuration

ClipTray uses two JSON files for persistence, both stored alongside the script or executable:

| File | Purpose |
|---|---|
| `clips.json` | Stores all saved clips (title, text, color, macro steps, pin state) |
| `settings.json` | Stores user preferences (auto-created on first settings change) |

### Settings (`settings.json`)

| Key | Type | Default | Description |
|---|---|---|---|
| `click_to_paste` | `bool` | `false` | When `true`, selecting a clip waits for a mouse click before pasting |
| `caret_companion` | `bool` | `false` | When `true`, shows a floating icon near the text cursor while typing |
| `caret_companion_position` | `string` | `"top-right"` | Icon position relative to the caret (`top-left`, `top`, `top-right`, `left`, `right`, `bottom-left`, `bottom`, `bottom-right`) |

No environment variables are required.

## ▶️ Usage

### Running from source

```bash
python main.py
```

The application starts minimized to the system tray. Look for the clipboard icon in the Windows taskbar notification area.

### Interaction

- **Left-click** the tray icon to toggle the overlay
- **Right-click** the tray icon for the context menu (Open / Quit)
- In the overlay, **click a clip** to paste it into the last active text field
- Press **Esc** to close the overlay
- Use the **search bar** to filter clips in real time
- Click **＋ Add Clip** to create a new text or macro clip
- Toggle between **Simple Text** and **Macro Mode** in the add/edit dialog

### Building the executable

```bash
python build.py
```

Output: `dist/ClipTray.exe` — a single portable file. Place `clips.json` alongside it to pre-populate clips.

## 📁 Project Structure

```
ClipTray/
├── main.py               # Entry point — tray icon, app lifecycle, paste/macro execution
├── clip_manager.py       # Clip & macro data model, JSON CRUD operations
├── clip_widgets.py       # ClipCard widget — individual clip UI card with drag/pin/edit/delete
├── overlay.py            # Fullscreen overlay window with clip list, search, drag-drop reorder
├── add_dialog.py         # Add/Edit dialog — title, text, color picker, macro toggle
├── macro_builder.py      # Visual macro builder — text steps, action steps, key capture
├── settings_dialog.py    # Settings panel — toggles, caret position picker, credits/about
├── settings_manager.py   # Settings persistence (settings.json)
├── caret_companion.py    # Floating icon near text cursor — Win32/UIA caret detection
├── splash.py             # Animated welcome splash screen on startup
├── styles.py             # QSS stylesheet (dark theme)
├── generate_icon.py      # Programmatic PNG icon generator
├── build.py              # PyInstaller build script
├── requirements.txt      # Python dependencies
├── clips.json            # Saved clips data (JSON)
├── ClipTray.spec         # PyInstaller spec file (auto-generated)
└── build/                # PyInstaller build artifacts
```

## 🧪 Testing

No automated test suite is currently included in the project. Manual testing can be performed by:

1. Running `python main.py`
2. Creating, editing, searching, pinning, reordering, and deleting clips
3. Testing both Simple Text and Macro Mode clips
4. Toggling Click-to-Paste and Caret Companion settings
5. Building with `python build.py` and verifying the standalone `.exe`

## 📜 License


```
MIT License

Copyright (c) 2026 Ali Paknahal / Certainty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🤝 Contributing

Contributions are welcome! To get started:

1. **Fork** the repository
2. **Create a feature branch:** `git checkout -b feature/my-feature`
3. **Commit your changes:** `git commit -m "Add my feature"`
4. **Push to the branch:** `git push origin feature/my-feature`
5. **Open a Pull Request** against `main`

### Guidelines

- Follow existing code style and module structure
- Keep UI changes consistent with the dark theme in `styles.py`
- Test on Windows (the app uses platform-specific APIs)
- Update `requirements.txt` if adding new dependencies

## 📌 Roadmap

- [ ] Add automated unit and integration tests
- [ ] Add a LICENSE file to the repository
- [ ] Support clip categories or folders for better organization
- [ ] Add global hotkey to open the overlay without clicking the tray icon
- [ ] Clipboard history monitoring (auto-capture copied text)
- [ ] Import/export clips to share across machines
- [ ] Multi-monitor overlay positioning improvements
- [ ] Linux and macOS support (replace Win32/UIA caret detection)
