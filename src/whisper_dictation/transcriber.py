"""Transcriber — wraps faster-whisper for local speech-to-text."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np


class Transcriber:
    def __init__(self, model_size: str = "base", language: Optional[str] = "fr") -> None:
        self._model_size = model_size
        self._language = language or None  # None triggers auto-detect
        self._model = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        from faster_whisper import WhisperModel
        from . import config as cfg

        model_dir = cfg.models_dir()
        print(
            f"[transcriber] Loading model '{self._model_size}' "
            f"(cache: {model_dir}) — first run may download ~150 MB …"
        )
        self._model = WhisperModel(
            self._model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(model_dir),
        )
        print("[transcriber] Model ready.")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """Return transcribed text, or empty string for silence/errors."""
        if audio.size == 0:
            return ""
        self._load_model()
        assert self._model is not None

        segments, _info = self._model.transcribe(
            audio,
            language=self._language,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text
