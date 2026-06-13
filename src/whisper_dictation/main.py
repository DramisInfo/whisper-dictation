"""Entry point — wires recorder, transcriber, injector, hotkey, and tray together."""

from __future__ import annotations

import sys
import threading
from typing import Optional

from . import config as cfg
from .hotkey import HotkeyManager
from .recorder import Recorder, RecordingError
from .transcriber import Transcriber
from .injector import inject
from .tray import TrayIcon


class App:
    def __init__(self) -> None:
        self._conf = cfg.load()
        self._recorder = Recorder()
        self._transcriber = Transcriber(
            model_size=self._conf["model"],
            language=self._conf.get("language"),
        )
        self._tray = TrayIcon(
            on_settings=self._open_settings,
            on_quit=self._quit,
        )
        self._hotkey_mgr = HotkeyManager(
            hotkey=self._conf["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._stopping = False
        self._transcribe_thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Hotkey callbacks (called from keyboard listener thread)
    # ------------------------------------------------------------------

    def _on_press(self) -> None:
        try:
            self._recorder.start()
            self._tray.set_recording(True)
        except RecordingError as exc:
            self._tray.set_recording(False)
            self._tray.notify("Whisper Dictation — Error", str(exc))

    def _on_release(self) -> None:
        audio = self._recorder.stop()
        self._tray.set_recording(False)
        if audio.size == 0:
            return
        # Transcription is slow — run off the hotkey thread.
        self._transcribe_thread = threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio,),
            daemon=True,
        )
        self._transcribe_thread.start()

    def _transcribe_and_inject(self, audio) -> None:
        try:
            text = self._transcriber.transcribe(audio, self._recorder.sample_rate)
            if text:
                inject(text)
        except Exception as exc:
            self._tray.notify("Whisper Dictation — Transcription Error", str(exc))

    # ------------------------------------------------------------------
    # Tray menu actions
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        cfg.open_in_editor()

    def _quit(self) -> None:
        self._stopping = True
        self._hotkey_mgr.stop()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._hotkey_mgr.start()
        # Tray blocks the calling thread; run it on the main thread so the
        # process stays alive until the user clicks Quit.
        self._tray.start()


def main() -> None:
    try:
        app = App()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
