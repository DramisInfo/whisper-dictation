"""Global hotkey manager — fires callbacks on press and release."""

from __future__ import annotations

import threading
from typing import Callable, Optional

import keyboard


class HotkeyManager:
    def __init__(
        self,
        hotkey: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        self._hotkey = hotkey
        self._on_press = on_press
        self._on_release = on_release
        self._held = False
        self._lock = threading.Lock()
        self._hooks: list = []

    def start(self) -> None:
        # keyboard fires repeated events while key is held; guard with _held flag.
        def _press(e: keyboard.KeyboardEvent) -> None:
            with self._lock:
                if self._held:
                    return
                self._held = True
            self._on_press()

        def _release(e: keyboard.KeyboardEvent) -> None:
            with self._lock:
                if not self._held:
                    return
                self._held = False
            self._on_release()

        key_name = self._hotkey.strip().lower()
        self._hooks.append(keyboard.on_press_key(key_name, _press, suppress=False))
        self._hooks.append(keyboard.on_release_key(key_name, _release, suppress=False))

    def stop(self) -> None:
        for hook in self._hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._hooks.clear()
        self._held = False
