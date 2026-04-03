"""Tests for audio analysis."""

import numpy as np
import pytest
import soundfile as sf

from soundforge.core.analysis import analyze_array, analyze_file, peak_dbfs, read_audio
from pathlib import Path


class TestPeakDbfs:
    def test_full_scale(self):
        samples = np.array([1.0, -1.0, 0.5])
        assert peak_dbfs(samples) == pytest.approx(0.0, abs=0.01)

    def test_half_scale(self):
        samples = np.array([0.5, -0.5])
        assert peak_dbfs(samples) == pytest.approx(-6.02, abs=0.1)

    def test_silence(self):
        samples = np.zeros(100)
        assert peak_dbfs(samples) == -120.0


class TestAnalyzeArray:
    def test_mono(self):
        sr = 44100
        samples = np.sin(np.linspace(0, 2 * np.pi, sr))
        asset = analyze_array(samples, sr, Path("test.wav"))
        assert asset.duration_seconds == pytest.approx(1.0, abs=0.01)
        assert asset.sample_rate == 44100
        assert asset.channels == 1
        assert asset.peak_dbfs == pytest.approx(0.0, abs=0.1)

    def test_stereo(self):
        sr = 44100
        mono = np.sin(np.linspace(0, 2 * np.pi, sr))
        stereo = np.column_stack([mono, mono])
        asset = analyze_array(stereo, sr, Path("test.wav"))
        assert asset.channels == 2

    def test_custom_format(self):
        sr = 44100
        samples = np.sin(np.linspace(0, 2 * np.pi, sr))
        asset = analyze_array(samples, sr, Path("test.ogg"), audio_format="ogg")
        assert asset.format == "ogg"


class TestAnalyzeFile:
    def test_reads_wav(self, tmp_path):
        sr = 44100
        samples = np.sin(np.linspace(0, 2 * np.pi, sr))
        path = tmp_path / "test.wav"
        sf.write(str(path), samples, sr, subtype="PCM_16")

        result = analyze_file(path)
        assert result.sample_rate == 44100
        assert result.channels == 1
        assert result.duration_seconds == pytest.approx(1.0, abs=0.01)


class TestReadAudio:
    def test_reads_wav(self, tmp_path):
        sr = 22050
        samples = np.random.randn(sr)
        path = tmp_path / "test.wav"
        sf.write(str(path), samples, sr, subtype="PCM_16")

        data, rate = read_audio(path)
        assert rate == 22050
        assert len(data) == sr
