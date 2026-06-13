"""Entry point — wires recorder, transcriber, injector, hotkey, and tray together."""

from __future__ import annotations

import sys
import threading
from typing import Optional

from . import config as cfg
from . import startup
from . import updater
from .hotkey import HotkeyManager
from .logger import get_logger
from .recorder import Recorder, RecordingError
from .transcriber import Transcriber
from .injector import inject
from .tray import TrayIcon
from .overlay import Overlay
from .settings_ui import SettingsWindow

_log = get_logger(__name__)


class App:
    def __init__(self) -> None:
        _log.info("Whisper Dictation starting")
        self._conf = cfg.load()
        if self._conf.get("autostart", True):
            startup.enable_autostart()
        else:
            startup.disable_autostart()
        self._overlay = Overlay(
            overlay_x=self._conf.get("overlay_x", 165),
            on_x_change=self._save_overlay_x,
        )
        self._recorder = Recorder(
            device=self._conf.get("device"),
            on_audio_level=self._overlay.update_level,
        )
        self._transcriber = Transcriber(
            model_size=self._conf["model"],
            language=self._conf.get("language"),
            initial_prompt=self._conf.get("initial_prompt"),
        )
        self._hotkey_mgr = HotkeyManager(
            hotkey=self._conf["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._settings_window = SettingsWindow(self._conf, self._on_settings_save, self._hotkey_mgr)
        self._tray = TrayIcon(
            on_settings=self._settings_window.show,
            on_quit=self._quit,
        )
        self._stopping = False
        self._transcribe_thread: Optional[threading.Thread] = None
        updater.run_update_check_async()

    # ------------------------------------------------------------------
    # Hotkey callbacks (called from keyboard listener thread)
    # ------------------------------------------------------------------

    def _on_press(self) -> None:
        try:
            self._recorder.start()
            self._overlay.set_state("recording")
        except RecordingError as exc:
            _log.error("Recording error: %s", exc)
            self._overlay.set_state("idle")
            self._tray.notify("Whisper Dictation — Error", str(exc))

    def _on_release(self) -> None:
        audio = self._recorder.stop()
        if audio.size == 0:
            self._overlay.set_state("idle")
            return
        self._overlay.set_state("transcribing")
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
            _log.error("Transcription/injection error: %s", exc, exc_info=True)
            self._tray.notify("Whisper Dictation — Transcription Error", str(exc))
        finally:
            self._overlay.set_state("idle")

    # ------------------------------------------------------------------
    # Tray menu actions
    # ------------------------------------------------------------------

    def _save_overlay_x(self, x: int) -> None:
        self._conf["overlay_x"] = x
        cfg.save(self._conf)

    def _on_settings_save(self, new_config: dict) -> None:
        old_hotkey = self._conf.get("hotkey")
        old_autostart = self._conf.get("autostart")
        cfg.save(new_config)
        _log.info("Settings saved (hotkey=%s, model=%s)", new_config.get("hotkey"), new_config.get("model"))
        self._conf = new_config
        self._settings_window._config = new_config
        self._recorder = Recorder(
            device=new_config.get("device"),
            on_audio_level=self._overlay.update_level,
        )
        self._transcriber = Transcriber(
            model_size=new_config["model"],
            language=new_config.get("language"),
            initial_prompt=new_config.get("initial_prompt"),
        )
        if new_config.get("hotkey") != old_hotkey:
            self._hotkey_mgr.restart(new_config["hotkey"])
        # Always apply autostart — don't rely on "changed" check, registry may be out of sync
        if new_config.get("autostart"):
            startup.enable_autostart()
        else:
            startup.disable_autostart()

    def _quit(self) -> None:
        _log.info("Whisper Dictation stopping")
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
    if "--unregister-autostart" in sys.argv:
        startup.disable_autostart()
        return
    try:
        app = App()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        _log.critical("Fatal error: %s", exc, exc_info=True)
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
