"""
ClipTray - Build Script
Builds the application into a single .exe file using PyInstaller.
Run: python build.py
"""

import subprocess
import sys
import os


def build():
    """Build ClipTray.exe using PyInstaller."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    icon_file = os.path.join(script_dir, "icon.png")
    clips_file = os.path.join(script_dir, "clips.json")

    # Generate icon if it doesn't exist
    if not os.path.exists(icon_file):
        print("[BUILD] Generating icon...")
        try:
            from generate_icon import generate_icon
            generate_icon()
        except Exception as e:
            print(f"[BUILD] Warning: Could not generate icon: {e}")

    # Build data files list
    datas = []
    if os.path.exists(icon_file):
        datas.append(f"--add-data={icon_file};.")
    if os.path.exists(clips_file):
        datas.append(f"--add-data={clips_file};.")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",              # Single .exe
        "--windowed",             # No console window
        "--name=ClipTray",        # Output name
        "--clean",                # Clean cache
        "--noconfirm",            # Overwrite without asking
    ] + datas + [
        main_script
    ]

    print("[BUILD] Running PyInstaller...")
    print(f"[BUILD] Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        exe_path = os.path.join(script_dir, "dist", "ClipTray.exe")
        print()
        print("=" * 60)
        print("  BUILD SUCCESSFUL!")
        print(f"  Output: {exe_path}")
        print()
        print("  NOTE: Place clips.json next to ClipTray.exe")
        print("        if you want to pre-populate your clips.")
        print("=" * 60)

        # Copy clips.json to dist folder
        dist_clips = os.path.join(script_dir, "dist", "clips.json")
        if os.path.exists(clips_file) and not os.path.exists(dist_clips):
            import shutil
            shutil.copy2(clips_file, dist_clips)
            print(f"  Copied clips.json to dist/")
    else:
        print()
        print("[BUILD] FAILED — see errors above.")
        sys.exit(1)


if __name__ == "__main__":
    build()
