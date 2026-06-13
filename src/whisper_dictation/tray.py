"""System tray icon — white circle = idle, red circle = recording."""

from __future__ import annotations

import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw
import pystray


_ICON_SIZE = 64


def _make_icon(recording: bool) -> Image.Image:
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (220, 50, 50, 255) if recording else (240, 240, 240, 255)
    margin = 4
    draw.ellipse(
        [margin, margin, _ICON_SIZE - margin, _ICON_SIZE - margin],
        fill=color,
        outline=(80, 80, 80, 200),
        width=2,
    )
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

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("Settings", lambda icon, item: self._on_settings()),
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
        self._icon.icon = _make_icon(recording)
        self._icon.title = (
            "Whisper Dictation — recording…" if recording else "Whisper Dictation — idle"
        )

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
