"""Global hotkey manager — pynput-based, supports combos like ctrl+windows."""

from __future__ import annotations

import threading
from typing import Callable, Optional

from pynput import keyboard as _kb
from pynput.keyboard import Key, KeyCode

# Normalize left/right modifier variants to their generic form
_MODIFIER_NORMALIZE: dict = {}


def _build_normalize_map() -> None:
    for attr, generic in [
        ("ctrl_l", Key.ctrl), ("ctrl_r", Key.ctrl),
        ("shift_l", Key.shift), ("shift_r", Key.shift),
        ("alt_l", Key.alt), ("alt_r", Key.alt), ("alt_gr", Key.alt),
        ("cmd_l", Key.cmd), ("cmd_r", Key.cmd),
    ]:
        if hasattr(Key, attr):
            _MODIFIER_NORMALIZE[getattr(Key, attr)] = generic


_build_normalize_map()

_PART_TO_KEY: dict[str, Key] = {
    "ctrl": Key.ctrl,
    "control": Key.ctrl,
    "shift": Key.shift,
    "alt": Key.alt,
    "windows": Key.cmd,
    "win": Key.cmd,
    "cmd": Key.cmd,
    "super": Key.cmd,
    **{f"f{i}": getattr(Key, f"f{i}") for i in range(1, 13)},
}


def _normalize(key: object) -> object:
    return _MODIFIER_NORMALIZE.get(key, key)  # type: ignore[arg-type]


def _parse_hotkey(hotkey: str) -> frozenset:
    """Parse 'ctrl+windows' or 'ctrl+shift+f9' into a frozenset of pynput key objects."""
    result: set = set()
    for part in (p.strip().lower() for p in hotkey.split("+")):
        if part in _PART_TO_KEY:
            result.add(_PART_TO_KEY[part])
        elif len(part) == 1:
            result.add(KeyCode.from_char(part))
        else:
            try:
                result.add(Key[part])
            except KeyError:
                pass
    return frozenset(result)


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
        self._pressed: set = set()
        self._required: frozenset = frozenset()
        self._listener: Optional[_kb.Listener] = None

    def start(self) -> None:
        self._required = _parse_hotkey(self._hotkey)
        self._pressed.clear()
        self._held = False

        def on_press(key: object) -> None:
            norm = _normalize(key)
            self._pressed.add(norm)
            if self._required and self._required.issubset(self._pressed):
                with self._lock:
                    if self._held:
                        return
                    self._held = True
                self._on_press()

        def on_release(key: object) -> None:
            norm = _normalize(key)
            self._pressed.discard(norm)
            if norm in self._required:
                with self._lock:
                    if not self._held:
                        return
                    self._held = False
                self._on_release()

        self._listener = _kb.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._pressed.clear()
        self._held = False

    def restart(self, new_hotkey: str) -> None:
        self.stop()
        self._hotkey = new_hotkey
        self.start()
