# PyInstaller spec for whisper-dictation — onedir Windows build
# Usage: pyinstaller whisper_dictation.spec
# Output: dist\whisper-dictation\

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

src_root = Path(SPECPATH) / "src"

fw_datas, fw_binaries, fw_hiddenimports = collect_all("faster_whisper")

a = Analysis(
    [str(Path(SPECPATH) / "run.py")],
    pathex=[str(src_root)],
    binaries=fw_binaries,
    datas=[
        ("config.default.yaml", "."),
        ("assets/icon.ico", "assets"),
        *fw_datas,
    ],
    hiddenimports=[
        "whisper_dictation",
        "whisper_dictation.config",
        "whisper_dictation.logger",
        "whisper_dictation.recorder",
        "whisper_dictation.transcriber",
        "whisper_dictation.injector",
        "whisper_dictation.hotkey",
        "whisper_dictation.tray",
        "whisper_dictation.updater",
        "whisper_dictation.startup",
        "whisper_dictation.settings_ui",
        "whisper_dictation.main",
        "requests",
        "faster_whisper",
        "sounddevice",
        "numpy",
        "pynput",
        "pynput.keyboard",
        "pynput.mouse",
        "pyperclip",
        "pystray",
        "PIL",
        "pyautogui",
        "winreg",
        "ctypes",
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        *fw_hiddenimports,
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
    [],
    exclude_binaries=True,
    name="whisper-dictation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="whisper-dictation",
)
