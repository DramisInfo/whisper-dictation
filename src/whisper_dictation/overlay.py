"""Taskbar-integrated status overlay — Windows 11 widget style."""

from __future__ import annotations

import random
import threading
import tkinter as tk
from typing import Callable, Optional

_W, _H = 180, 48
_BG_ROOT = "#1e1e1e"
_BG_PILL = "#2d2d2d"
_ALPHA = 0.82
_RADIUS = 8
_DEFAULT_X = 165

# Equalizer bar geometry
_N_BARS = 6
_BAR_W = 4
_BAR_GAP = 2
_BAR_MAX_H = 22
_BAR_MIN_H = 2
_BAR_X0 = 10
_BAR_BOTTOM = 35  # y of bar bottom edge (center=24, max_h/2=11 → 24+11=35)


class Overlay:
    def __init__(
        self,
        overlay_x: int = _DEFAULT_X,
        on_x_change: Optional[Callable[[int], None]] = None,
    ) -> None:
        self._state = "idle"
        self._level = 0.0
        self._overlay_x = overlay_x
        self._on_x_change = on_x_change
        self._root: Optional[tk.Tk] = None
        self._canvas: Optional[tk.Canvas] = None
        self._bar_ids: list[int] = []
        self._bar_heights = [float(_BAR_MIN_H)] * _N_BARS
        self._spin_step = 0
        self._drag_start_x = 0
        self._drag_win_x = overlay_x
        threading.Thread(target=self._run, daemon=True, name="overlay-tk").start()

    # ------------------------------------------------------------------
    # Tk thread
    # ------------------------------------------------------------------

    def _run(self) -> None:
        root = tk.Tk()
        root.overrideredirect(True)
        root.wm_attributes("-topmost", True)
        root.wm_attributes("-alpha", _ALPHA)
        root.configure(bg=_BG_ROOT)

        sh = root.winfo_screenheight()
        root.geometry(f"{_W}x{_H}+{self._overlay_x}+{sh - _H}")

        canvas = tk.Canvas(root, width=_W, height=_H, bg=_BG_ROOT, highlightthickness=0)
        canvas.pack()

        self._draw_pill(canvas)
        canvas.bind("<ButtonPress-1>", self._on_drag_start)
        canvas.bind("<B1-Motion>", self._on_drag_motion)
        canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        self._canvas = canvas
        self._root = root

        self._apply_state()
        self._animate()
        root.mainloop()

    def _draw_pill(self, canvas: tk.Canvas) -> None:
        r, fill = _RADIUS, _BG_PILL
        canvas.create_rectangle(r, 0, _W - r, _H, fill=fill, outline="", tags="pill")
        canvas.create_rectangle(0, r, _W, _H - r, fill=fill, outline="", tags="pill")
        canvas.create_oval(0, 0, 2 * r, 2 * r, fill=fill, outline="", tags="pill")
        canvas.create_oval(_W - 2 * r, 0, _W, 2 * r, fill=fill, outline="", tags="pill")
        canvas.create_oval(0, _H - 2 * r, 2 * r, _H, fill=fill, outline="", tags="pill")
        canvas.create_oval(_W - 2 * r, _H - 2 * r, _W, _H, fill=fill, outline="", tags="pill")

    # ------------------------------------------------------------------
    # Drag support
    # ------------------------------------------------------------------

    def _on_drag_start(self, event) -> None:  # type: ignore[override]
        self._drag_start_x = event.x_root
        if self._root is not None:
            self._drag_win_x = self._root.winfo_x()

    def _on_drag_motion(self, event) -> None:  # type: ignore[override]
        if self._root is None:
            return
        dx = event.x_root - self._drag_start_x
        new_x = self._drag_win_x + dx
        sh = self._root.winfo_screenheight()
        self._root.geometry(f"{_W}x{_H}+{new_x}+{sh - _H}")
        self._overlay_x = new_x

    def _on_drag_end(self, event) -> None:  # type: ignore[override]
        if self._on_x_change is not None:
            self._on_x_change(self._overlay_x)

    # ------------------------------------------------------------------
    # Public API (thread-safe)
    # ------------------------------------------------------------------

    def update_level(self, level: float) -> None:
        """Called from audio callback thread; GIL-safe float write."""
        self._level = level

    def set_state(self, state: str) -> None:
        self._state = state
        if self._root is not None:
            self._root.after(0, self._apply_state)

    # ------------------------------------------------------------------
    # State rendering (Tk thread only)
    # ------------------------------------------------------------------

    def _apply_state(self) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        canvas.delete("dynamic")
        self._bar_ids = []
        self._bar_heights = [float(_BAR_MIN_H)] * _N_BARS
        self._spin_step = 0

        if self._state == "idle":
            canvas.create_text(16, 24, text="🎙", font=("Segoe UI", 12), fill="#555555",
                               anchor="w", tags="dynamic")
            canvas.create_text(40, 24, text="Whisper", font=("Segoe UI", 9), fill="#666666",
                               anchor="w", tags="dynamic")

        elif self._state == "recording":
            for i in range(_N_BARS):
                x0 = _BAR_X0 + i * (_BAR_W + _BAR_GAP)
                x1 = x0 + _BAR_W
                bid = canvas.create_rectangle(
                    x0, _BAR_BOTTOM - _BAR_MIN_H, x1, _BAR_BOTTOM,
                    fill="#ff4444", outline="", tags="dynamic",
                )
                self._bar_ids.append(bid)
            canvas.create_text(58, 24, text="Recording", font=("Segoe UI", 9), fill="#ff4444",
                               anchor="w", tags="dynamic")

        elif self._state == "transcribing":
            canvas.create_text(16, 24, text="⏳", font=("Segoe UI", 11), fill="#ffcc00",
                               anchor="w", tags="dynamic")
            canvas.create_text(40, 24, text="Transcribing.", font=("Segoe UI", 9), fill="#ffcc00",
                               anchor="w", tags=("dynamic", "spin_text"))

    # ------------------------------------------------------------------
    # Animation loop — 30 fps
    # ------------------------------------------------------------------

    def _animate(self) -> None:
        if self._root is None:
            return
        canvas = self._canvas

        if canvas is not None:
            if self._state == "recording" and self._bar_ids:
                level = self._level
                for i, bid in enumerate(self._bar_ids):
                    target = level * random.uniform(0.5, 1.5) * _BAR_MAX_H
                    self._bar_heights[i] = self._bar_heights[i] * 0.6 + target * 0.4
                    h = max(_BAR_MIN_H, min(_BAR_MAX_H, self._bar_heights[i]))
                    x0 = _BAR_X0 + i * (_BAR_W + _BAR_GAP)
                    x1 = x0 + _BAR_W
                    canvas.coords(bid, x0, _BAR_BOTTOM - h, x1, _BAR_BOTTOM)

            elif self._state == "transcribing":
                self._spin_step += 1
                dots = "." * (1 + self._spin_step % 3)
                try:
                    canvas.itemconfig("spin_text", text=f"Transcribing{dots}")
                except tk.TclError:
                    pass

        self._root.after(33, self._animate)
