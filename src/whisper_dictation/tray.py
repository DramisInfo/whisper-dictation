"""System tray icon — microphone shape, dark-grey bg = idle, red bg = recording."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw
import pystray

from . import startup
from .logger import get_logger, log_path

_log = get_logger(__name__)


_ICON_SIZE = 64


def _make_icon(recording: bool) -> Image.Image:
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    bg = (220, 50, 50, 255) if recording else (50, 50, 50, 255)
    draw.ellipse([4, 4, 60, 60], fill=bg)

    # Microphone elements in white
    w = (255, 255, 255, 255)

    # Capsule body — fully rounded rectangle (pill shape)
    draw.rounded_rectangle([24, 8, 40, 32], radius=8, fill=w)

    # Stand arc (∪ shape) — bounding box chosen so endpoints land at y=32,
    # matching the bottom of the capsule, with the arc curving down to y=46.
    # center_y = (18+46)/2 = 32  →  arc(0°→180°) endpoints sit at y=32.
    draw.arc([20, 18, 44, 46], start=0, end=180, fill=w, width=3)

    # Vertical stem from arc bottom to base
    draw.line([(32, 46), (32, 52)], fill=w, width=3)

    # Horizontal base
    draw.line([(22, 52), (42, 52)], fill=w, width=3)

    return img


class TrayIcon:
    def __init__(
        self,
        on_settings: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None

    def _toggle_autostart(self) -> None:
        if startup.is_autostart_enabled():
            startup.disable_autostart()
        else:
            startup.enable_autostart()
        if self._icon:
            self._icon.menu = self._build_menu()
            self._icon.update_menu()

    def _open_log_file(self) -> None:
        try:
            p = log_path()
            if sys.platform == "win32":
                os.startfile(str(p))
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as exc:
            _log.warning("Could not open log file: %s", exc)

    def _build_menu(self) -> pystray.Menu:
        autostart_label = (
            "Start with Windows ✓" if startup.is_autostart_enabled() else "Start with Windows"
        )
        return pystray.Menu(
            pystray.MenuItem(autostart_label, lambda icon, item: self._toggle_autostart()),
            pystray.MenuItem("Settings", lambda icon, item: self._on_settings()),
            pystray.MenuItem("Open Log File", lambda icon, item: self._open_log_file()),
            pystray.MenuItem("Quit", lambda icon, item: self._quit()),
        )

    def _quit(self) -> None:
        self._on_quit()
        if self._icon:
            self._icon.stop()

    def start(self) -> None:
        """Start the tray icon (blocks until stopped — call from dedicated thread)."""
        self._icon = pystray.Icon(
            "whisper-dictation",
            icon=_make_icon(recording=False),
            title="Whisper Dictation — idle",
            menu=self._build_menu(),
        )
        self._icon.run()

    def set_recording(self, recording: bool) -> None:
        if self._icon is None:
            return
        new_icon = _make_icon(recording)
        new_title = "Whisper Dictation — recording…" if recording else "Whisper Dictation — idle"

        def _update() -> None:
            if self._icon:
                self._icon.icon = new_icon
                self._icon.title = new_title

        threading.Timer(0, _update).start()

    def notify(self, title: str, message: str) -> None:
        if self._icon is None:
            return
        try:
            self._icon.notify(message, title)
        except Exception:
            pass

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
