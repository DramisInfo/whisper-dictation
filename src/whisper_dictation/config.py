"""Config loader/saver — reads from %APPDATA%/whisper-dictation/config.yaml."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import yaml

_APP_DIR_NAME = "whisper-dictation"
_CONFIG_FILE = "config.yaml"
_DEFAULT_CONFIG_NAME = "config.default.yaml"

_DEFAULTS: dict[str, Any] = {
    "hotkey": "ctrl+windows",
    "model": "small",
    "language": "fr",
    "initial_prompt": "Transcription en français québécois. Vocabulaire informatique, développement logiciel, intelligence artificielle, architecture de solutions.",
    "autostart": True,
    "device": None,
    "overlay_x": 165,
}


def app_dir() -> Path:
    """Return (and create) the per-user application data directory."""
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    d = base / _APP_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def models_dir() -> Path:
    """Return (and create) the directory where Whisper model files are cached."""
    d = app_dir() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return app_dir() / _CONFIG_FILE


def _seed_config_if_missing() -> None:
    dest = config_path()
    if dest.exists():
        return
    # Try to copy the bundled default config next to this source file or the executable.
    for candidate in [
        Path(__file__).parent.parent.parent / _DEFAULT_CONFIG_NAME,
        Path(__file__).parent / _DEFAULT_CONFIG_NAME,
    ]:
        if candidate.exists():
            shutil.copy(candidate, dest)
            return
    # Fallback: write hard-coded defaults.
    with dest.open("w", encoding="utf-8") as fh:
        yaml.dump(_DEFAULTS, fh, default_flow_style=False, allow_unicode=True)


def load() -> dict[str, Any]:
    """Return the merged config (file values override hard-coded defaults)."""
    _seed_config_if_missing()
    with config_path().open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return {**_DEFAULTS, **data}


def save(data: dict) -> None:
    config_path().write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def open_in_editor() -> None:
    """Open config.yaml in the default system editor (Windows: notepad)."""
    import subprocess
    _seed_config_if_missing()
    subprocess.Popen(["notepad.exe", str(config_path())])
