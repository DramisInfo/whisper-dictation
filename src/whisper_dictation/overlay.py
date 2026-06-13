"""Floating always-on-top status overlay showing recording/transcribing state."""

from __future__ import annotations

import threading
import tkinter as tk
from typing import Optional


_W, _H = 300, 36
_BG = "#1e1e1e"
_FONT = ("Segoe UI", 10)


class Overlay:
    def __init__(self) -> None:
        self._state = "idle"
        self._root: Optional[tk.Tk] = None
        self._label: Optional[tk.Label] = None
        self._pulse_id: Optional[str] = None
        self._pulse_visible = True
        threading.Thread(target=self._run, daemon=True, name="overlay-tk").start()

    def _run(self) -> None:
        root = tk.Tk()
        root.overrideredirect(True)
        root.wm_attributes("-topmost", True)
        root.wm_attributes("-alpha", 0.85)
        root.configure(bg=_BG)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - _W) // 2
        y = sh - _H - 40
        root.geometry(f"{_W}x{_H}+{x}+{y}")

        for event in ("<Button-1>", "<Button-2>", "<Button-3>", "<ButtonRelease-1>"):
            root.bind(event, lambda e: "break")

        label = tk.Label(
            root,
            text="🎙  Whisper Dictation — idle",
            bg=_BG,
            fg="#666666",
            font=_FONT,
            padx=10,
            pady=0,
        )
        label.pack(fill="both", expand=True)
        self._label = label
        self._root = root
        root.mainloop()

    def set_state(self, state: str) -> None:
        self._state = state
        root = self._root
        if root is None:
            return
        root.after(0, self._apply_state)

    def _cancel_pulse(self) -> None:
        if self._pulse_id is not None and self._root is not None:
            try:
                self._root.after_cancel(self._pulse_id)
            except Exception:
                pass
            self._pulse_id = None

    def _apply_state(self) -> None:
        self._cancel_pulse()
        label = self._label
        if label is None:
            return
        if self._state == "idle":
            label.config(text="🎙  Whisper Dictation — idle", fg="#666666")
        elif self._state == "recording":
            self._pulse_visible = True
            label.config(text="🔴  Recording...", fg="#ff4444")
            self._pulse()
        elif self._state == "transcribing":
            label.config(text="⏳  Transcribing...", fg="#ffaa00")

    def _pulse(self) -> None:
        if self._state != "recording" or self._root is None or self._label is None:
            return
        self._pulse_visible = not self._pulse_visible
        text = "🔴  Recording..." if self._pulse_visible else "⚫  Recording..."
        self._label.config(text=text)
        self._pulse_id = self._root.after(500, self._pulse)
