"""Audio preview — playback helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf


def play_file(path: Path) -> None:
    """Play an audio file through the default audio device."""
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError(
            "sounddevice is required for audio preview. "
            "Install it with: pip install soundforge[preview]"
        )

    samples, sample_rate = sf.read(str(path), dtype="float64")
    sd.play(samples, sample_rate)
    sd.wait()


def play_array(samples: np.ndarray, sample_rate: int) -> None:
    """Play a numpy audio array through the default audio device."""
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError(
            "sounddevice is required for audio preview. "
            "Install it with: pip install soundforge[preview]"
        )

    sd.play(samples, sample_rate)
    sd.wait()
