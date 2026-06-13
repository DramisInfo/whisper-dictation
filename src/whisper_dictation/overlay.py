"""Taskbar-integrated status overlay — Windows 11 widget style."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import random
import sys
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
_BAR_MAX_H = 40
_BAR_MIN_H = 2
_BAR_X0 = 10
_BAR_BOTTOM = 46

# ---------------------------------------------------------------------------
# Win32 always-on-top helpers (Windows only — graceful no-op on other OSes)
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    _user32 = ctypes.WinDLL("user32", use_last_error=True)

    # Types
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        _LONG_PTR = ctypes.c_longlong
    else:
        _LONG_PTR = ctypes.c_long

    _WNDPROC = ctypes.WINFUNCTYPE(
        _LONG_PTR,
        ctypes.wintypes.HWND,
        ctypes.wintypes.UINT,
        ctypes.wintypes.WPARAM,
        ctypes.wintypes.LPARAM,
    )
    _WINEVENTPROC = ctypes.WINFUNCTYPE(
        None,
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.HWND,
        ctypes.wintypes.LONG,
        ctypes.wintypes.LONG,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
    )

    # Prototypes
    _user32.GetWindowLongPtrW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
    _user32.GetWindowLongPtrW.restype = _LONG_PTR
    _user32.SetWindowLongPtrW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, _LONG_PTR]
    _user32.SetWindowLongPtrW.restype = _LONG_PTR
    _user32.SetWindowPos.argtypes = [
        ctypes.wintypes.HWND, ctypes.wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.wintypes.UINT,
    ]
    _user32.SetWindowPos.restype = ctypes.wintypes.BOOL
    _user32.CallWindowProcW.argtypes = [
        _LONG_PTR, ctypes.wintypes.HWND, ctypes.wintypes.UINT,
        ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
    ]
    _user32.CallWindowProcW.restype = _LONG_PTR
    _user32.SetWinEventHook.argtypes = [
        ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
        ctypes.wintypes.HMODULE, _WINEVENTPROC,
        ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
    ]
    _user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE
    _user32.UnhookWinEvent.argtypes = [ctypes.wintypes.HANDLE]
    _user32.UnhookWinEvent.restype = ctypes.wintypes.BOOL

    class _WINDOWPOS(ctypes.Structure):
        _fields_ = [
            ("hwnd", ctypes.wintypes.HWND),
            ("hwndInsertAfter", ctypes.wintypes.HWND),
            ("x", ctypes.c_int), ("y", ctypes.c_int),
            ("cx", ctypes.c_int), ("cy", ctypes.c_int),
            ("flags", ctypes.wintypes.UINT),
        ]

    # Constants
    _GWL_EXSTYLE = -20
    _GWLP_WNDPROC = -4
    _WS_EX_TOPMOST    = 0x00000008
    _WS_EX_TOOLWINDOW = 0x00000080
    _WS_EX_NOACTIVATE = 0x08000000
    _HWND_TOPMOST = ctypes.wintypes.HWND(-1)
    _SWP_NOSIZE       = 0x0001
    _SWP_NOMOVE       = 0x0002
    _SWP_NOZORDER     = 0x0004
    _SWP_NOACTIVATE   = 0x0010
    _SWP_FRAMECHANGED = 0x0020
    _SWP_SHOWWINDOW   = 0x0040
    _WM_WINDOWPOSCHANGING = 0x0046
    _WM_WINDOWPOSCHANGED  = 0x0047
    _WM_DESTROY           = 0x0002
    _EVENT_SYSTEM_FOREGROUND    = 0x0003
    _EVENT_OBJECT_SHOW          = 0x8002
    _EVENT_OBJECT_LOCATIONCHANGE = 0x800B
    _WINEVENT_OUTOFCONTEXT   = 0x0000
    _WINEVENT_SKIPOWNPROCESS = 0x0002


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
        # Win32 subclassing state
        self._hwnd: Optional[int] = None
        self._old_wndproc: Optional[int] = None
        self._new_wndproc_ref = None  # keep reference alive
        self._winevent_hooks: list = []
        self._winevent_proc_ref = None  # keep reference alive
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

        root.geometry(f"{_W}x{_H}+{self._overlay_x}+0")

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

        # Apply robust always-on-top after window is fully realized
        root.after(100, self._install_win32_topmost)
        # Watchdog fallback — slower than before since event hooks cover most cases
        root.after(1500, self._watchdog_topmost)

        root.mainloop()

    def _install_win32_topmost(self) -> None:
        """Apply Win32 extended styles + subclass + event hooks for robust topmost."""
        if sys.platform != "win32" or self._root is None:
            return
        try:
            self._hwnd = self._root.winfo_id()
            hwnd = ctypes.wintypes.HWND(self._hwnd)

            # 1. Set extended styles: TOPMOST + TOOLWINDOW + NOACTIVATE
            exstyle = _user32.GetWindowLongPtrW(hwnd, _GWL_EXSTYLE)
            exstyle |= _WS_EX_TOPMOST | _WS_EX_TOOLWINDOW | _WS_EX_NOACTIVATE
            _user32.SetWindowLongPtrW(hwnd, _GWL_EXSTYLE, exstyle)

            # 2. Apply HWND_TOPMOST with FRAMECHANGED to commit style change
            _user32.SetWindowPos(
                hwnd, _HWND_TOPMOST, 0, 0, 0, 0,
                _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE | _SWP_FRAMECHANGED | _SWP_SHOWWINDOW,
            )

            # 3. Subclass our own window to intercept WM_WINDOWPOSCHANGING
            def wndproc(h, msg, wparam, lparam):
                if msg == _WM_WINDOWPOSCHANGING:
                    # Force HWND_TOPMOST before any z-order change is applied
                    wp = ctypes.cast(lparam, ctypes.POINTER(_WINDOWPOS)).contents
                    wp.hwndInsertAfter = _HWND_TOPMOST
                    wp.flags &= ~_SWP_NOZORDER
                    wp.flags |= _SWP_NOACTIVATE
                elif msg == _WM_WINDOWPOSCHANGED:
                    # After any change, schedule a re-assert on the Tk thread
                    if self._root is not None:
                        self._root.after_idle(self._force_topmost)
                elif msg == _WM_DESTROY:
                    self._uninstall_win32_topmost()
                return _user32.CallWindowProcW(self._old_wndproc, h, msg, wparam, lparam)

            self._new_wndproc_ref = _WNDPROC(wndproc)
            self._old_wndproc = _user32.SetWindowLongPtrW(
                hwnd, _GWLP_WNDPROC,
                ctypes.cast(self._new_wndproc_ref, ctypes.c_void_p).value,
            )

            # 4. SetWinEventHook — fires immediately when foreground changes
            #    (user clicks taskbar, Start, notification center, other app, etc.)
            def on_win_event(hook, event, h, id_obj, id_child, thread, time):
                self._force_topmost()

            self._winevent_proc_ref = _WINEVENTPROC(on_win_event)

            h1 = _user32.SetWinEventHook(
                _EVENT_SYSTEM_FOREGROUND, _EVENT_SYSTEM_FOREGROUND,
                None, self._winevent_proc_ref, 0, 0,
                _WINEVENT_OUTOFCONTEXT | _WINEVENT_SKIPOWNPROCESS,
            )
            if h1:
                self._winevent_hooks.append(h1)

            h2 = _user32.SetWinEventHook(
                _EVENT_OBJECT_SHOW, _EVENT_OBJECT_LOCATIONCHANGE,
                None, self._winevent_proc_ref, 0, 0,
                _WINEVENT_OUTOFCONTEXT | _WINEVENT_SKIPOWNPROCESS,
            )
            if h2:
                self._winevent_hooks.append(h2)

        except Exception:
            pass  # Non-Windows or restricted environment — degrade gracefully

    def _force_topmost(self) -> None:
        """Assert HWND_TOPMOST — safe to call from any thread."""
        if sys.platform != "win32" or not self._hwnd:
            return
        try:
            _user32.SetWindowPos(
                ctypes.wintypes.HWND(self._hwnd), _HWND_TOPMOST, 0, 0, 0, 0,
                _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE | _SWP_SHOWWINDOW,
            )
        except Exception:
            pass

    def _watchdog_topmost(self) -> None:
        """Slow fallback watchdog — 1500ms, most cases covered by event hooks."""
        if self._root is None:
            return
        self._force_topmost()
        self._root.after(1500, self._watchdog_topmost)

    def _uninstall_win32_topmost(self) -> None:
        """Clean up hooks and subclass on destroy."""
        if sys.platform != "win32":
            return
        for hook in self._winevent_hooks:
            try:
                _user32.UnhookWinEvent(hook)
            except Exception:
                pass
        self._winevent_hooks.clear()
        if self._hwnd and self._old_wndproc:
            try:
                _user32.SetWindowLongPtrW(
                    ctypes.wintypes.HWND(self._hwnd), _GWLP_WNDPROC, self._old_wndproc
                )
            except Exception:
                pass
        self._old_wndproc = None

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
        self._root.geometry(f"{_W}x{_H}+{new_x}+0")
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
                    target = level * random.uniform(0.6, 1.4) * _BAR_MAX_H
                    self._bar_heights[i] = self._bar_heights[i] * 0.35 + target * 0.65
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
