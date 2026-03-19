"""Audio postprocessing — trim, fade, normalize, resample, channel convert, loop smooth."""

from __future__ import annotations

from typing import Callable

import numpy as np


def trim_silence(
    samples: np.ndarray,
    sample_rate: int,
    threshold_db: float = -40.0,
    min_silence_ms: float = 50.0,
) -> np.ndarray:
    """Trim leading and trailing silence below threshold."""
    if samples.size == 0:
        return samples

    # Work with mono amplitude for detection
    if samples.ndim == 2:
        mono = np.mean(np.abs(samples), axis=1)
    else:
        mono = np.abs(samples)

    threshold_linear = 10 ** (threshold_db / 20.0)
    above = mono > threshold_linear

    if not np.any(above):
        # All silence — return empty array with same shape properties
        return samples[:0]

    indices = np.nonzero(above)[0]
    # Add small margin (min_silence_ms worth of samples)
    margin = int(sample_rate * min_silence_ms / 1000)
    start = max(0, indices[0] - margin)
    end = min(len(samples), indices[-1] + margin + 1)

    return samples[start:end]


def apply_fade(
    samples: np.ndarray,
    sample_rate: int,
    fade_in: float = 0.01,
    fade_out: float = 0.05,
) -> np.ndarray:
    """Apply linear fade-in and fade-out."""
    if samples.size == 0:
        return samples

    n = len(samples)
    fade_in_samples = min(int(sample_rate * fade_in), n // 2)
    fade_out_samples = min(int(sample_rate * fade_out), n // 2)

    result = samples.copy()

    if fade_in_samples > 0:
        fade_in_curve = np.linspace(0.0, 1.0, fade_in_samples)
        if result.ndim == 2:
            fade_in_curve = fade_in_curve[:, np.newaxis]
        result[:fade_in_samples] *= fade_in_curve

    if fade_out_samples > 0:
        fade_out_curve = np.linspace(1.0, 0.0, fade_out_samples)
        if result.ndim == 2:
            fade_out_curve = fade_out_curve[:, np.newaxis]
        result[-fade_out_samples:] *= fade_out_curve

    return result


def normalize_peak(
    samples: np.ndarray,
    target_dbfs: float = -1.0,
) -> np.ndarray:
    """Normalize audio to target peak dBFS."""
    if samples.size == 0:
        return samples

    peak = np.max(np.abs(samples))
    if peak == 0:
        return samples

    target_linear = 10 ** (target_dbfs / 20.0)
    gain = target_linear / peak
    return samples * gain


def convert_channels(
    samples: np.ndarray,
    target_channels: int,
) -> np.ndarray:
    """Convert between mono and stereo."""
    if samples.size == 0:
        return samples

    current_channels = samples.shape[1] if samples.ndim == 2 else 1

    if current_channels == target_channels:
        return samples

    if target_channels == 1 and current_channels == 2:
        # Stereo to mono: average channels
        return np.mean(samples, axis=1)

    if target_channels == 2 and current_channels == 1:
        # Mono to stereo: duplicate channel
        return np.column_stack([samples, samples])

    return samples


def resample(
    samples: np.ndarray,
    current_rate: int,
    target_rate: int,
) -> np.ndarray:
    """Resample audio to target sample rate. Requires scipy."""
    if current_rate == target_rate:
        return samples

    try:
        from scipy.signal import resample_poly
    except ImportError:
        raise RuntimeError(
            "scipy is required for sample rate conversion. "
            "Install it with: pip install soundforge[resample]"
        )

    from math import gcd

    g = gcd(current_rate, target_rate)
    up = target_rate // g
    down = current_rate // g

    if samples.ndim == 1:
        return resample_poly(samples, up, down)

    # Process each channel independently
    channels = []
    for ch in range(samples.shape[1]):
        channels.append(resample_poly(samples[:, ch], up, down))
    return np.column_stack(channels)


def loop_smooth(
    samples: np.ndarray,
    sample_rate: int,
    crossfade_ms: float = 100.0,
) -> np.ndarray:
    """Apply crossfade smoothing at loop boundary for seamless looping."""
    if samples.size == 0:
        return samples

    crossfade_samples = int(sample_rate * crossfade_ms / 1000)
    if crossfade_samples >= len(samples) // 2:
        crossfade_samples = len(samples) // 4

    if crossfade_samples < 2:
        return samples

    # Crossfade: blend end into beginning
    fade_out = np.linspace(1.0, 0.0, crossfade_samples)
    fade_in = np.linspace(0.0, 1.0, crossfade_samples)

    if samples.ndim == 2:
        fade_out = fade_out[:, np.newaxis]
        fade_in = fade_in[:, np.newaxis]

    result = samples.copy()
    # Blend the end region with the beginning region
    end_region = result[-crossfade_samples:] * fade_out
    start_region = result[:crossfade_samples] * fade_in

    result[:crossfade_samples] = start_region + end_region
    # Trim the crossfade region from the end
    result = result[:-crossfade_samples]

    return result


def run_pipeline(
    samples: np.ndarray,
    sample_rate: int,
    *,
    trim: bool = True,
    fade_in_sec: float = 0.01,
    fade_out_sec: float = 0.05,
    normalize: bool = True,
    target_peak_dbfs: float = -1.0,
    target_sample_rate: int | None = None,
    target_channels: int | None = None,
    loop: bool = False,
    on_status: Callable[[str], None] | None = None,
) -> tuple[np.ndarray, int]:
    """Run the full postprocessing pipeline. Returns (processed_samples, sample_rate)."""
    if trim:
        if on_status:
            on_status("Trimming silence...")
        samples = trim_silence(samples, sample_rate)

    if loop:
        if on_status:
            on_status("Applying loop smoothing...")
        samples = loop_smooth(samples, sample_rate)

    if fade_in_sec > 0 or fade_out_sec > 0:
        if on_status:
            on_status("Applying fades...")
        samples = apply_fade(samples, sample_rate, fade_in_sec, fade_out_sec)

    if normalize:
        if on_status:
            on_status(f"Normalizing to {target_peak_dbfs} dBFS...")
        samples = normalize_peak(samples, target_peak_dbfs)

    if target_channels is not None:
        current_ch = samples.shape[1] if samples.ndim == 2 else 1
        if current_ch != target_channels:
            if on_status:
                on_status(f"Converting to {'mono' if target_channels == 1 else 'stereo'}...")
            samples = convert_channels(samples, target_channels)

    if target_sample_rate is not None and target_sample_rate != sample_rate:
        if on_status:
            on_status(f"Resampling {sample_rate} → {target_sample_rate} Hz...")
        samples = resample(samples, sample_rate, target_sample_rate)
        sample_rate = target_sample_rate

    return samples, sample_rate
