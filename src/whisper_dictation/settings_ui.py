"""Settings GUI — tkinter window for editing config values."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .hotkey import HotkeyManager

_MODELS = ["tiny", "base", "small", "medium", "large-v3"]

LANGUAGES = {
    "auto": "Auto-detect",
    "af": "Afrikaans", "sq": "Albanian", "am": "Amharic", "ar": "Arabic",
    "hy": "Armenian", "as": "Assamese", "az": "Azerbaijani", "ba": "Bashkir",
    "eu": "Basque", "be": "Belarusian", "bn": "Bengali", "bs": "Bosnian",
    "br": "Breton", "bg": "Bulgarian", "ca": "Catalan", "zh": "Chinese",
    "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
    "en": "English", "et": "Estonian", "fo": "Faroese", "fi": "Finnish",
    "fr": "French", "gl": "Galician", "ka": "Georgian", "de": "German",
    "el": "Greek", "gu": "Gujarati", "ht": "Haitian Creole", "ha": "Hausa",
    "haw": "Hawaiian", "he": "Hebrew", "hi": "Hindi", "hu": "Hungarian",
    "is": "Icelandic", "id": "Indonesian", "it": "Italian", "ja": "Japanese",
    "jw": "Javanese", "kn": "Kannada", "kk": "Kazakh", "km": "Khmer",
    "ko": "Korean", "lo": "Lao", "la": "Latin", "lv": "Latvian",
    "ln": "Lingala", "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian",
    "mg": "Malagasy", "ms": "Malay", "ml": "Malayalam", "mt": "Maltese",
    "mi": "Maori", "mr": "Marathi", "mn": "Mongolian", "my": "Myanmar",
    "ne": "Nepali", "no": "Norwegian", "nn": "Nynorsk", "oc": "Occitan",
    "ps": "Pashto", "fa": "Persian", "pl": "Polish", "pt": "Portuguese",
    "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sa": "Sanskrit",
    "sr": "Serbian", "sn": "Shona", "sd": "Sindhi", "si": "Sinhala",
    "sk": "Slovak", "sl": "Slovenian", "so": "Somali", "es": "Spanish",
    "su": "Sundanese", "sw": "Swahili", "sv": "Swedish", "tl": "Tagalog",
    "tg": "Tajik", "ta": "Tamil", "tt": "Tatar", "te": "Telugu",
    "th": "Thai", "bo": "Tibetan", "tr": "Turkish", "tk": "Turkmen",
    "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek", "vi": "Vietnamese",
    "cy": "Welsh", "yi": "Yiddish", "yo": "Yoruba",
}

_CODE_TO_NAME: dict[str, str] = {k: v for k, v in LANGUAGES.items()}
_NAME_TO_CODE: dict[str, str] = {v: k for k, v in LANGUAGES.items()}

_FIXED_TOP = ["Auto-detect", "French"]
_LANG_VALUES = _FIXED_TOP + sorted(
    name for name in _NAME_TO_CODE if name not in _FIXED_TOP
)

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
    def __init__(
        self,
        config: dict,
        on_save: Callable[[dict], None],
        hotkey_manager: Optional["HotkeyManager"] = None,
    ) -> None:
        self._config = config
        self._on_save = on_save
        self._hotkey_manager = hotkey_manager
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

            w, h = 420, 450
            root.title("Whisper Dictation — Settings")
            root.configure(bg=_BG)
            root.resizable(False, False)
            root.update_idletasks()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

            def close() -> None:
                if self._hotkey_manager is not None:
                    self._hotkey_manager.cancel_capture()
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
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#2d2d2d", background="#3a3a3a",
                        foreground="#f0f0f0", selectbackground="#3a3a3a",
                        selectforeground="#f0f0f0", arrowcolor="#f0f0f0")

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

        # --- Hotkey capture widget ---
        cur_hotkey = self._config.get("hotkey", "ctrl+windows")
        hotkey_var = tk.StringVar(value=cur_hotkey)

        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        lbl(row, "Hotkey:", width=10, anchor="w").pack(side="left")

        hk_frame = tk.Frame(row, bg=_INPUT_BG, padx=8, pady=4, cursor="hand2")
        hk_frame.pack(side="left", fill="x", expand=True)
        hk_label = tk.Label(hk_frame, textvariable=hotkey_var, bg=_INPUT_BG,
                            fg=_FG, font=_FONT, anchor="w")
        hk_label.pack(fill="x")

        def _start_capture(e=None) -> None:
            if self._hotkey_manager is None:
                return
            hotkey_var.set("Press keys…")
            hk_label.config(fg=_ACCENT)

            # Use a mutable container to pass results from pynput thread to Tk thread safely
            _capture_result: list[str] = []
            _capture_done: list[bool] = [False]

            def on_change(combo: str) -> None:
                _capture_result[:] = [combo]

            def on_done(combo: str) -> None:
                _capture_result[:] = [combo]
                _capture_done[0] = True

            self._hotkey_manager.begin_capture(on_change=on_change, on_done=on_done)

            def _poll() -> None:
                """Poll capture state from the Tk thread — avoids cross-thread after() issues."""
                hm = self._hotkey_manager
                if hm is None:
                    return
                # Update label with latest partial combo
                if _capture_result:
                    hotkey_var.set(_capture_result[0])
                # Done — cb was called, combo is final
                if _capture_done[0]:
                    hk_label.config(fg=_FG)
                    return
                # Still waiting — keep polling
                root.after(50, _poll)

            root.after(50, _poll)

        for w in (hk_frame, hk_label):
            w.bind("<Button-1>", _start_capture)

        hint("  Click the box, then press your key combination").pack(anchor="w", padx=16)

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
        cur_lang_code = self._config.get("language", "fr")
        cur_lang_name = _CODE_TO_NAME.get(cur_lang_code, "French")
        lang_combo = ttk.Combobox(row, values=_LANG_VALUES, state="readonly", width=28,
                                  font=_FONT)
        lang_combo.set(cur_lang_name)
        lang_combo.pack(side="left")
        hint("  99 languages supported — Auto-detect works well for mixed content").pack(
            anchor="w", padx=16
        )

        row = tk.Frame(root, bg=_BG)
        row.pack(fill="x", **pad)
        lbl(row, "Context hint:", width=13, anchor="w").pack(side="left")
        cur_prompt = self._config.get("initial_prompt", "")
        prompt_entry = entry(row, cur_prompt if cur_prompt else "")
        prompt_entry.pack(side="left", fill="x", expand=True)
        hint("  Helps Whisper pick the right vocabulary").pack(anchor="w", padx=16)

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
        # Read real registry state — not just config file value — to avoid desync
        from . import startup as _startup
        real_autostart = _startup.is_autostart_enabled()
        autostart_var = tk.BooleanVar(value=real_autostart)
        tk.Checkbutton(
            row, text="Start with Windows", variable=autostart_var,
            bg=_BG, fg=_FG, selectcolor=_INPUT_BG,
            activebackground=_BG, activeforeground=_FG, font=_FONT,
        ).pack(side="left")

        # ── Buttons ────────────────────────────────────────────────────
        btn_row = tk.Frame(root, bg=_BG)
        btn_row.pack(side="bottom", fill="x", padx=16, pady=14)

        def save() -> None:
            hk = hotkey_var.get().strip()
            if not hk or hk == "Press keys…":
                messagebox.showerror(
                    "Invalid Hotkey", "Hotkey field cannot be empty.", parent=root
                )
                return
            new_config = {
                **self._config,
                "hotkey": hk,
                "model": model_var.get(),
                "language": _NAME_TO_CODE.get(lang_combo.get(), "fr"),
                "initial_prompt": prompt_entry.get().strip() or None,
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
