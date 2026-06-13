"""Global hotkey manager — supports single keys and combos like ctrl+windows."""

from __future__ import annotations

import threading
from typing import Callable

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
        keys = [k.strip().lower() for k in self._hotkey.replace("+", " ").split()]

        def _press(e: keyboard.KeyboardEvent) -> None:
            # For combos, all modifier keys must be currently held.
            if len(keys) > 1:
                modifiers = keys[:-1]
                if not all(keyboard.is_pressed(m) for m in modifiers):
                    return
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

        # Hook only on the final key of the combo.
        trigger_key = keys[-1]
        self._hooks.append(keyboard.on_press_key(trigger_key, _press, suppress=False))
        self._hooks.append(keyboard.on_release_key(trigger_key, _release, suppress=False))

    def stop(self) -> None:
        for hook in self._hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._hooks.clear()
        self._held = False

    def restart(self, new_hotkey: str) -> None:
        self.stop()
        self._hotkey = new_hotkey
        self.start()
