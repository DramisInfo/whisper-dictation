"""Settings GUI — tkinter window for editing config values."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

_MODELS = ["tiny", "base", "small", "medium", "large-v3"]

_BG = "#1e1e1e"
_FG = "#f0f0f0"
_ACCENT = "#e05050"
_INPUT_BG = "#2d2d2d"
_BTN_BG = "#3a3a3a"
_HINT = "#888888"
_FONT = ("Segoe UI", 10)
_FONT_SM = ("Segoe UI", 8)
_FONT_HDR = ("Segoe UI", 9, "bold")


class SettingsWindow:
    def __init__(self, config: dict, on_save: Callable[[dict], None]) -> None:
        self._config = config
        self._on_save = on_save
        self._lock = threading.Lock()
        self._open = False
        self._root: Optional[tk.Tk] = None

    def show(self) -> None:
        """Open the settings window (idempotent — only one at a time)."""
        with self._lock:
            if self._open:
                root = self._root
                if root is not None:
                    try:
                        root.after(0, root.lift)
                    except Exception:
                        pass
                return
            self._open = True
        threading.Thread(target=self._run, daemon=True).start()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            root = tk.Tk()
            with self._lock:
                self._root = root

            w, h = 420, 400
            root.title("Whisper Dictation — Settings")
            root.configure(bg=_BG)
            root.resizable(False, False)
            root.update_idletasks()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

            def close() -> None:
                root.destroy()

            root.protocol("WM_DELETE_WINDOW", close)
            self._build_content(root, close)
            root.mainloop()
        except Exception:
            pass
        finally:
            with self._lock:
                self._root = None
                self._open = False

    def _build_content(self, root: tk.Tk, close: Callable[[], None]) -> None:
        pad = {"padx": 16, "pady": 4}

        def lbl(parent: tk.Widget, text: str, **kw) -> tk.Label:
            return tk.Label(parent, text=text, bg=_BG, fg=_FG, font=_FONT, **kw)

        def section(text: str) -> tk.Label:
            return tk.Label(root, text=text, bg=_BG, fg=_ACCENT, font=_FONT_HDR, anchor="w")

        def entry(parent: tk.Widget, value: str) -> tk.Entry:
            e = tk.Entry(parent, bg=_INPUT_BG, fg=_FG, insertbackground=_FG,
                         relief="flat", font=_FONT)
            e.insert(0, value)
            return e

        def hint(text: str) -> tk.Label:
            return tk.Label(root, text=text, bg=_BG, fg=_HINT, font=_FONT_SM, anchor="w")

        # ── Transcription ──────────────────────────────────────────────
        section("Transcription").pack(anchor="w", padx=16, pady=(14, 2))

        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        lbl(row, "Hotkey:", width=10, anchor="w").pack(side="left")
        hotkey_entry = entry(row, self._config.get("hotkey", "right ctrl"))
        hotkey_entry.pack(side="left", fill="x", expand=True)
        hint("  e.g. right ctrl, f13, ctrl+shift+d").pack(anchor="w", padx=16)

        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        lbl(row, "Model:", width=10, anchor="w").pack(side="left")
        cur_model = self._config.get("model", "base")
        if cur_model not in _MODELS:
            cur_model = "base"
        model_var = tk.StringVar(value=cur_model)
        om = tk.OptionMenu(row, model_var, *_MODELS)
        om.configure(bg=_INPUT_BG, fg=_FG, activebackground=_BTN_BG, activeforeground=_FG,
                     highlightthickness=0, relief="flat", font=_FONT)
        om["menu"].configure(bg=_INPUT_BG, fg=_FG, font=_FONT)
        om.pack(side="left")
        hint("  Larger = more accurate but slower first run").pack(anchor="w", padx=16)

        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        lbl(row, "Language:", width=10, anchor="w").pack(side="left")
        lang_entry = entry(row, self._config.get("language", "fr"))
        lang_entry.pack(side="left", fill="x", expand=True)
        hint("  e.g. fr, en, auto").pack(anchor="w", padx=16)

        try:
            import sounddevice as _sd
            _input_names = [d["name"] for d in _sd.query_devices() if d["max_input_channels"] > 0]
        except Exception:
            _input_names = []
        mic_options = ["System default"] + _input_names
        cur_device = self._config.get("device", None)
        cur_mic = cur_device if cur_device in mic_options else "System default"
        mic_var = tk.StringVar(value=cur_mic)
        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        lbl(row, "Microphone:", width=10, anchor="w").pack(side="left")
        mic_om = tk.OptionMenu(row, mic_var, *mic_options)
        mic_om.configure(bg=_INPUT_BG, fg=_FG, activebackground=_BTN_BG, activeforeground=_FG,
                         highlightthickness=0, relief="flat", font=_FONT)
        mic_om["menu"].configure(bg=_INPUT_BG, fg=_FG, font=_FONT)
        mic_om.pack(side="left")
        hint("  Leave as System default unless you have multiple mics").pack(anchor="w", padx=16)

        # ── Behaviour ──────────────────────────────────────────────────
        section("Behaviour").pack(anchor="w", padx=16, pady=(12, 2))

        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        autostart_var = tk.BooleanVar(value=bool(self._config.get("autostart", True)))
        tk.Checkbutton(
            row, text="Start with Windows", variable=autostart_var,
            bg=_BG, fg=_FG, selectcolor=_INPUT_BG,
            activebackground=_BG, activeforeground=_FG, font=_FONT,
        ).pack(side="left")

        # ── Buttons ────────────────────────────────────────────────────
        btn_row = tk.Frame(root, bg=_BG)
        btn_row.pack(side="bottom", fill="x", padx=16, pady=14)

        def save() -> None:
            hk = hotkey_entry.get().strip()
            if not hk:
                messagebox.showerror(
                    "Invalid Hotkey", "Hotkey field cannot be empty.", parent=root
                )
                return
            new_config = {
                **self._config,
                "hotkey": hk,
                "model": model_var.get(),
                "language": lang_entry.get().strip(),
                "autostart": bool(autostart_var.get()),
                "device": None if mic_var.get() == "System default" else mic_var.get(),
            }
            self._on_save(new_config)
            close()

        tk.Button(
            btn_row, text="Save", command=save,
            bg=_ACCENT, fg=_FG, activebackground="#c03030", activeforeground=_FG,
            relief="flat", padx=16, pady=6, font=(*_FONT, "bold"), cursor="hand2",
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_row, text="Cancel", command=close,
            bg=_BTN_BG, fg=_FG, activebackground="#555555", activeforeground=_FG,
            relief="flat", padx=16, pady=6, font=_FONT, cursor="hand2",
        ).pack(side="right")
