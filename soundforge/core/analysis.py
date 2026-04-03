"""Audio analysis — extract metadata from audio arrays and files."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from soundforge.core.types import AudioAsset, InspectResult


def peak_dbfs(samples: np.ndarray) -> float:
    """Calculate peak amplitude in dBFS."""
    peak = np.max(np.abs(samples))
    if peak == 0:
        return -120.0
    return float(20 * np.log10(peak))


def analyze_array(
    samples: np.ndarray,
    sample_rate: int,
    path: Path,
    audio_format: str = "wav",
    loop_safe: bool = False,
) -> AudioAsset:
    """Analyze a numpy audio array and return an AudioAsset."""
    channels = samples.shape[1] if samples.ndim == 2 else 1
    duration = len(samples) / sample_rate
    peak = peak_dbfs(samples)

    return AudioAsset(
        path=path,
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
        peak_dbfs=peak,
        format=audio_format,
        loop_safe=loop_safe,
    )


def analyze_file(path: Path) -> InspectResult:
    """Read an audio file and return inspection metadata."""
    info = sf.info(str(path))
    samples, sample_rate = sf.read(str(path), dtype="float64")
    peak = peak_dbfs(samples)

    return InspectResult(
        path=path,
        duration_seconds=info.duration,
        sample_rate=info.samplerate,
        channels=info.channels,
        peak_dbfs=peak,
        format_info=f"{info.format} {info.subtype}",
    )


def read_audio(path: Path) -> tuple[np.ndarray, int]:
    """Read an audio file and return (samples, sample_rate)."""
    samples, sample_rate = sf.read(str(path), dtype="float64")
    return samples, sample_rate
