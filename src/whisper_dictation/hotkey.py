"""Global hotkey manager — pynput-based, supports combos like ctrl+windows."""

from __future__ import annotations

import threading
from typing import Callable, Optional

from pynput import keyboard as _kb
from pynput.keyboard import Key, KeyCode

from .logger import get_logger

_log = get_logger(__name__)

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

_CAPTURE_MOD_ORDER = ["ctrl", "alt", "shift", "windows"]

_CAPTURE_MOD_MAP: dict = {
    Key.ctrl: "ctrl", Key.alt: "alt", Key.shift: "shift", Key.cmd: "windows",
}


def _normalize(key: object) -> object:
    return _MODIFIER_NORMALIZE.get(key, key)  # type: ignore[arg-type]


def _key_to_token(key: object) -> str:
    norm = _MODIFIER_NORMALIZE.get(key, key)  # type: ignore[arg-type]
    if norm in _CAPTURE_MOD_MAP:
        return _CAPTURE_MOD_MAP[norm]
    if isinstance(key, KeyCode) and key.char:
        return key.char.lower()
    if isinstance(key, Key):
        return key.name.lower()
    return str(key)


def _combo_from_seen(seen: set) -> str:
    mods = [k for k in _CAPTURE_MOD_ORDER if k in seen]
    rest = sorted(k for k in seen if k not in _CAPTURE_MOD_ORDER)
    return "+".join(mods + rest)


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
        self._capture_active = False
        self._capture_pressed: set = set()
        self._capture_seen: set = set()
        self._capture_on_change: Optional[Callable[[str], None]] = None
        self._capture_on_done: Optional[Callable[[str], None]] = None
        self._last_captured: str = ""  # result of last completed capture

    def begin_capture(self, on_change: Callable[[str], None], on_done: Callable[[str], None]) -> None:
        """Enter capture mode: suppress hotkey activation, collect keys from pynput listener."""
        self._capture_active = True
        self._capture_pressed = set()
        self._capture_seen = set()
        self._capture_on_change = on_change
        self._capture_on_done = on_done
        self._held = False
        self._pressed.clear()

    def cancel_capture(self) -> None:
        self._capture_active = False
        self._capture_pressed = set()
        self._capture_seen = set()
        self._capture_on_change = None
        self._capture_on_done = None

    def start(self) -> None:
        self._required = _parse_hotkey(self._hotkey)
        self._pressed.clear()
        self._held = False
        _log.info("Hotkey registered: %s", self._hotkey)

        def on_press(key: object) -> None:
            if self._capture_active:
                token = _key_to_token(key)
                self._capture_pressed.add(token)
                self._capture_seen.add(token)
                combo = _combo_from_seen(self._capture_seen)
                cb = self._capture_on_change
                if cb is not None:
                    cb(combo)
                return
            norm = _normalize(key)
            self._pressed.add(norm)
            if self._required and self._required.issubset(self._pressed):
                with self._lock:
                    if self._held:
                        return
                    self._held = True
                _log.debug("Hotkey combo detected: %s", self._hotkey)
                self._on_press()

        def on_release(key: object) -> None:
            if self._capture_active:
                token = _key_to_token(key)
                self._capture_pressed.discard(token)
                if not self._capture_pressed and self._capture_seen:
                    combo = _combo_from_seen(self._capture_seen)
                    self._last_captured = combo  # store before clearing
                    cb = self._capture_on_done
                    if cb is not None:
                        cb(combo)  # set _capture_done[0]=True BEFORE cancel_capture clears _capture_active
                    self.cancel_capture()
                return
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
        self.cancel_capture()

    def restart(self, new_hotkey: str) -> None:
        self.stop()
        self._hotkey = new_hotkey
        self.start()
