"""Tests for backend interface and ElevenLabs backend."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from soundforge.core.backends import GenerationBackend, get_backend
from soundforge.core.backends.elevenlabs import ElevenLabsBackend
from soundforge.core.config import SoundForgeConfig


class TestGetBackend:
    def test_returns_elevenlabs(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = get_backend("elevenlabs", cfg)
        assert isinstance(backend, ElevenLabsBackend)

    def test_unknown_raises(self):
        cfg = SoundForgeConfig()
        with pytest.raises(ValueError, match="Available: elevenlabs, stable-audio"):
            get_backend("unknown", cfg)


class TestElevenLabsAvailability:
    def test_available_with_key(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        assert backend.is_available() is True

    def test_unavailable_without_key(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="")
        backend = ElevenLabsBackend(cfg)
        assert backend.is_available() is False


class TestElevenLabsInfo:
    def test_info_keys(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        info = backend.info()
        assert "name" in info
        assert "model" in info
        assert "api_base" in info
        assert "available" in info
        assert info["name"] == "elevenlabs"
        assert info["available"] is True

    def test_info_unavailable(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="")
        backend = ElevenLabsBackend(cfg)
        info = backend.info()
        assert info["available"] is False
        assert "not configured" in info["status"]


class TestElevenLabsCapabilities:
    def test_capabilities(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        caps = backend.capabilities()
        assert caps["max_duration"] == 30
        assert caps["supports_loop"] is True
        assert caps["supports_seed"] is False


def _make_mp3_bytes():
    """Create minimal valid audio bytes that soundfile can read."""
    import io
    import soundfile as sf

    samples = np.sin(np.linspace(0, 2 * np.pi * 440, 4410)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, samples, 44100, format="WAV")
    return buf.getvalue()


class TestElevenLabsGenerate:
    def test_no_api_key_raises(self):
        cfg = SoundForgeConfig(elevenlabs_api_key="")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="API key not configured"):
            backend.generate("test sound")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = _make_mp3_bytes()
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        samples, sr = backend.generate("coin pickup")

        assert isinstance(samples, np.ndarray)
        assert sr == 44100
        assert samples.dtype == np.float64

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_http_401(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="bad-key")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="Invalid or expired API key"):
            backend.generate("test")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_http_429(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            backend.generate("test")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_http_500(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="server error"):
            backend.generate("test")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_http_other_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Unprocessable entity"
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="HTTP 422"):
            backend.generate("test")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_timeout(self, mock_post):
        import httpx

        mock_post.side_effect = httpx.TimeoutException("timeout")

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="timed out"):
            backend.generate("test")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_connect_error(self, mock_post):
        import httpx

        mock_post.side_effect = httpx.ConnectError("connection refused")

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        with pytest.raises(RuntimeError, match="Could not connect"):
            backend.generate("test")

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_duration_clamping_warning(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = _make_mp3_bytes()
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        warnings = []
        backend.generate("test", duration_seconds=60.0, on_status=warnings.append)
        assert any("clamped" in w for w in warnings)

    @patch("soundforge.core.backends.elevenlabs.httpx.post")
    def test_no_warning_for_valid_duration(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = _make_mp3_bytes()
        mock_post.return_value = mock_response

        cfg = SoundForgeConfig(elevenlabs_api_key="test-key")
        backend = ElevenLabsBackend(cfg)
        warnings = []
        backend.generate("test", duration_seconds=5.0, on_status=warnings.append)
        assert not any("clamped" in w for w in warnings)
