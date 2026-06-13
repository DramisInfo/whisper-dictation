"""Audio recorder — captures microphone input into a numpy buffer."""

from __future__ import annotations

import threading
from typing import Optional

import numpy as np
import sounddevice as sd

_SAMPLE_RATE = 16_000  # Hz — Whisper expects 16 kHz
_CHANNELS = 1
_DTYPE = "float32"


class RecordingError(RuntimeError):
    pass


class Recorder:
    def __init__(self, device: str | None = None) -> None:
        self._device = device
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
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self._chunks, axis=0).flatten()
            self._chunks = []
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
            return False

    @property
    def sample_rate(self) -> int:
        return _SAMPLE_RATE
