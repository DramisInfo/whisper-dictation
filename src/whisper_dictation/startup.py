"""Windows auto-startup via HKCU registry — no admin rights required."""

from __future__ import annotations

import sys
from pathlib import Path

_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "WhisperDictation"


def _pythonw_exe() -> str:
    """Return the path to pythonw.exe alongside the current Python executable."""
    exe = Path(sys.executable)
    candidate = exe.parent / "pythonw.exe"
    if candidate.exists():
        return str(candidate)
    return str(exe)


def _startup_command() -> str:
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    return f'"{_pythonw_exe()}" -m whisper_dictation'


def enable_autostart() -> None:
    """Add a registry entry so the app starts silently at Windows login."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _startup_command())
        winreg.CloseKey(key)
    except Exception:
        pass


def disable_autostart() -> None:
    """Remove the auto-startup registry entry if it exists."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, _VALUE_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except Exception:
        pass


def is_autostart_enabled() -> bool:
    """Return True if the auto-startup registry entry exists."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
