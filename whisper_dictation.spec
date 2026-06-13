# PyInstaller spec for whisper-dictation — produces a single Windows .exe
# Usage: pyinstaller whisper_dictation.spec

import sys
from pathlib import Path

block_cipher = None

src_root = Path(SPECPATH) / "src"

a = Analysis(
    [str(src_root / "whisper_dictation" / "main.py")],
    pathex=[str(src_root)],
    binaries=[],
    datas=[
        # Bundle the default config so first-run seeding works offline
        ("config.default.yaml", "."),
    ],
    hiddenimports=[
        "whisper_dictation",
        "whisper_dictation.config",
        "whisper_dictation.recorder",
        "whisper_dictation.transcriber",
        "whisper_dictation.injector",
        "whisper_dictation.hotkey",
        "whisper_dictation.tray",
        "faster_whisper",
        "sounddevice",
        "numpy",
        "keyboard",
        "pyperclip",
        "pystray",
        "PIL",
        "pyautogui",
        "yaml",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="whisper-dictation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No terminal window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Set to an .ico path if desired
)
