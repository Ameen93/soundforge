"""Tests for the postprocessing pipeline."""

import numpy as np
import pytest

from soundforge.core.postprocess import (
    apply_fade,
    convert_channels,
    loop_smooth,
    normalize_peak,
    resample,
    run_pipeline,
    trim_silence,
)


def _make_tone(freq=440, duration=0.5, sr=44100, amplitude=0.8):
    """Create a simple sine tone for testing."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return amplitude * np.sin(2 * np.pi * freq * t), sr


class TestTrimSilence:
    def test_trims_leading_silence(self):
        sr = 44100
        silence = np.zeros(int(sr * 0.1))
        tone, _ = _make_tone(sr=sr, duration=0.3)
        samples = np.concatenate([silence, tone])
        trimmed = trim_silence(samples, sr)
        assert len(trimmed) < len(samples)

    def test_trims_trailing_silence(self):
        sr = 44100
        silence = np.zeros(int(sr * 0.1))
        tone, _ = _make_tone(sr=sr, duration=0.3)
        samples = np.concatenate([tone, silence])
        trimmed = trim_silence(samples, sr)
        assert len(trimmed) < len(samples)

    def test_empty_input(self):
        result = trim_silence(np.array([]), 44100)
        assert len(result) == 0

    def test_all_silence(self):
        samples = np.zeros(1000)
        result = trim_silence(samples, 44100)
        assert len(result) == 0


class TestFade:
    def test_fade_in(self):
        tone, sr = _make_tone()
        faded = apply_fade(tone, sr, fade_in=0.01, fade_out=0.0)
        # First sample should be near zero
        assert abs(faded[0]) < 0.01

    def test_fade_out(self):
        tone, sr = _make_tone()
        faded = apply_fade(tone, sr, fade_in=0.0, fade_out=0.01)
        # Last sample should be near zero
        assert abs(faded[-1]) < 0.01

    def test_empty_input(self):
        result = apply_fade(np.array([]), 44100, 0.01, 0.01)
        assert len(result) == 0


class TestNormalize:
    def test_normalize_to_target(self):
        tone, _ = _make_tone(amplitude=0.5)
        normalized = normalize_peak(tone, target_dbfs=-1.0)
        peak = np.max(np.abs(normalized))
        expected = 10 ** (-1.0 / 20)
        assert abs(peak - expected) < 0.001

    def test_empty_input(self):
        result = normalize_peak(np.array([]), -1.0)
        assert len(result) == 0

    def test_silence_unchanged(self):
        silence = np.zeros(100)
        result = normalize_peak(silence, -1.0)
        assert np.all(result == 0)


class TestChannelConvert:
    def test_stereo_to_mono(self):
        stereo = np.column_stack([np.ones(100), np.zeros(100)])
        mono = convert_channels(stereo, 1)
        assert mono.ndim == 1
        assert abs(mono[0] - 0.5) < 0.001

    def test_mono_to_stereo(self):
        mono = np.ones(100)
        stereo = convert_channels(mono, 2)
        assert stereo.ndim == 2
        assert stereo.shape[1] == 2

    def test_same_channels_unchanged(self):
        mono = np.ones(100)
        result = convert_channels(mono, 1)
        assert np.array_equal(result, mono)


class TestResample:
    def test_upsample(self):
        tone, _ = _make_tone(sr=22050, duration=0.1)
        resampled = resample(tone, 22050, 44100)
        expected_len = int(len(tone) * 44100 / 22050)
        assert abs(len(resampled) - expected_len) <= 1

    def test_same_rate_unchanged(self):
        tone, _ = _make_tone()
        result = resample(tone, 44100, 44100)
        assert np.array_equal(result, tone)


class TestLoopSmooth:
    def test_shortens_audio(self):
        tone, sr = _make_tone(duration=1.0)
        smoothed = loop_smooth(tone, sr, crossfade_ms=100)
        assert len(smoothed) < len(tone)

    def test_empty_input(self):
        result = loop_smooth(np.array([]), 44100)
        assert len(result) == 0


class TestStereoPostprocess:
    def test_trim_stereo(self):
        sr = 44100
        mono_silence = np.zeros(int(sr * 0.1))
        mono_tone, _ = _make_tone(sr=sr, duration=0.3)
        mono = np.concatenate([mono_silence, mono_tone, mono_silence])
        stereo = np.column_stack([mono, mono])
        trimmed = trim_silence(stereo, sr)
        assert trimmed.ndim == 2
        assert len(trimmed) < len(stereo)

    def test_fade_stereo(self):
        mono_tone, sr = _make_tone()
        stereo = np.column_stack([mono_tone, mono_tone])
        faded = apply_fade(stereo, sr, fade_in=0.01, fade_out=0.01)
        assert faded.ndim == 2
        assert abs(faded[0, 0]) < 0.01
        assert abs(faded[-1, 0]) < 0.01

    def test_normalize_stereo(self):
        mono_tone, _ = _make_tone(amplitude=0.5)
        stereo = np.column_stack([mono_tone, mono_tone])
        normalized = normalize_peak(stereo, target_dbfs=-1.0)
        peak = np.max(np.abs(normalized))
        expected = 10 ** (-1.0 / 20)
        assert abs(peak - expected) < 0.001


class TestPipeline:
    def test_full_pipeline(self):
        sr = 44100
        silence = np.zeros(int(sr * 0.1))
        tone, _ = _make_tone(sr=sr, duration=0.3, amplitude=0.5)
        samples = np.concatenate([silence, tone, silence])

        result, result_sr = run_pipeline(
            samples, sr,
            trim=True,
            fade_in_sec=0.01,
            fade_out_sec=0.01,
            normalize=True,
            target_peak_dbfs=-1.0,
        )

        # Should be trimmed
        assert len(result) < len(samples)
        # Should be normalized
        peak = np.max(np.abs(result))
        expected = 10 ** (-1.0 / 20)
        assert abs(peak - expected) < 0.01

    def test_pipeline_with_resample_and_channels(self):
        sr = 22050
        tone, _ = _make_tone(sr=sr, duration=0.2, amplitude=0.8)

        result, result_sr = run_pipeline(
            tone, sr,
            trim=False,
            fade_in_sec=0.0,
            fade_out_sec=0.0,
            normalize=False,
            target_sample_rate=44100,
            target_channels=2,
        )

        assert result_sr == 44100
        assert result.ndim == 2
        assert result.shape[1] == 2

    def test_pipeline_noop(self):
        tone, sr = _make_tone()
        original = tone.copy()

        result, result_sr = run_pipeline(
            tone, sr,
            trim=False,
            fade_in_sec=0.0,
            fade_out_sec=0.0,
            normalize=False,
        )

        assert result_sr == sr
        assert np.array_equal(result, original)
