"""Audio recorder — captures microphone input into a numpy buffer."""

from __future__ import annotations

import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from .logger import get_logger

_log = get_logger(__name__)

_SAMPLE_RATE = 16_000  # Hz — Whisper expects 16 kHz
_CHANNELS = 1
_DTYPE = "float32"


class RecordingError(RuntimeError):
    pass


class Recorder:
    def __init__(
        self,
        device: str | None = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._device = device
        self._on_audio_level = on_audio_level
        self._lock = threading.Lock()
        self._chunks: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        with self._lock:
            if self._recording:
                return
            if not self._has_input_device():
                raise RecordingError(
                    "No microphone found. Connect a microphone and try again."
                )
            self._chunks = []
            self._recording = True
            self._stream = sd.InputStream(
                samplerate=_SAMPLE_RATE,
                channels=_CHANNELS,
                dtype=_DTYPE,
                callback=self._callback,
                device=self._device,
            )
            self._stream.start()
            _log.info("Recording started (device=%s)", self._device)

    def stop(self) -> np.ndarray:
        """Stop recording and return the captured audio as a 1-D float32 array."""
        with self._lock:
            if not self._recording:
                return np.array([], dtype=np.float32)
            self._recording = False
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            if not self._chunks:
                _log.info("Recording stopped — no audio captured")
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self._chunks, axis=0).flatten()
            self._chunks = []
            _log.info("Recording stopped — %.2f seconds captured", len(audio) / _SAMPLE_RATE)
            return audio

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time: object,
        status: sd.CallbackFlags,
    ) -> None:
        if self._recording:
            self._chunks.append(indata.copy())
            if self._on_audio_level is not None:
                rms = float(np.sqrt(np.mean(indata ** 2)))
                self._on_audio_level(min(1.0, rms * 50))

    @staticmethod
    def list_input_devices() -> list[str]:
        devices = sd.query_devices()
        return [d["name"] for d in devices if d["max_input_channels"] > 0]

    @staticmethod
    def _has_input_device() -> bool:
        try:
            devices = sd.query_devices()
            return any(d["max_input_channels"] > 0 for d in devices)
        except Exception:
            _log.warning("Could not query audio devices", exc_info=True)
            return False

    @property
    def sample_rate(self) -> int:
        return _SAMPLE_RATE
