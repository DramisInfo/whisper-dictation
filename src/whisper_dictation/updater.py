"""Background update checker — polls GitHub Releases and prompts the user if a newer version is available."""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from typing import Optional

from . import __version__

_RELEASES_URL = "https://api.github.com/repos/DramisInfo/whisper-dictation/releases/latest"


def _parse_version(tag: str) -> tuple[int, ...]:
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def check_for_update() -> Optional[dict]:
    """Return the latest release dict if a newer version exists, else None."""
    try:
        req = urllib.request.Request(
            _RELEASES_URL,
            headers={"User-Agent": f"whisper-dictation/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            release: dict = json.loads(resp.read().decode())
        tag = release.get("tag_name", "")
        if not tag:
            return None
        if _parse_version(tag) > _parse_version(__version__):
            return release
        return None
    except Exception:
        return None


def prompt_update(release: dict) -> None:
    """Show a Windows MessageBox asking the user to update; open browser if Yes."""
    if sys.platform != "win32":
        return
    tag = release.get("tag_name", "")
    assets = release.get("assets", [])
    download_url = release.get("html_url", "")
    for asset in assets:
        if asset.get("name", "").endswith(".exe"):
            download_url = asset["browser_download_url"]
            break
    try:
        import ctypes
        MB_YESNO = 0x00000004
        MB_ICONINFORMATION = 0x00000040
        IDYES = 6
        result = ctypes.windll.user32.MessageBoxW(
            0,
            f"Version {tag} is available. Update now?",
            "Whisper Dictation — Update Available",
            MB_YESNO | MB_ICONINFORMATION,
        )
        if result == IDYES and download_url:
            webbrowser.open(download_url)
    except Exception:
        pass


def run_update_check_async() -> None:
    """Run the update check in a daemon thread; if update found, prompt from main thread."""
    def _worker() -> None:
        release = check_for_update()
        if release:
            threading.Timer(0, prompt_update, args=(release,)).start()

    threading.Thread(target=_worker, daemon=True).start()
