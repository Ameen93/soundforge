"""Tests for Stable Audio Open backend."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from soundforge.core.backends import get_backend
from soundforge.core.config import SoundForgeConfig


def _make_backend(cfg=None):
    """Create a StableAudioBackend without importing torch/diffusers."""
    from soundforge.core.backends.stable_audio import StableAudioBackend

    if cfg is None:
        cfg = SoundForgeConfig(backend="stable-audio")
    return StableAudioBackend(cfg)


def _make_mock_torch():
    """Create a mock torch module with the bits generate() uses."""
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.OutOfMemoryError = type("OutOfMemoryError", (RuntimeError,), {})
    # Generator mock
    mock_generator = MagicMock()
    mock_generator.seed.return_value = 12345
    mock_torch.Generator.return_value = mock_generator
    return mock_torch


def _make_fake_result(duration_samples=44100, channels=2):
    """Create a fake pipeline result using numpy (no torch required)."""
    # Simulate a tensor-like object with .float().cpu().numpy() chain
    raw = np.random.randn(channels, duration_samples).astype(np.float32)
    mock_tensor = MagicMock()
    mock_tensor.float.return_value.cpu.return_value.numpy.return_value = raw
    result = MagicMock()
    result.audios = [mock_tensor]
    return result


def _make_ready_backend(cfg=None, duration_samples=44100):
    """Create a backend with a mocked pipeline and torch, no real GPU needed."""
    backend = _make_backend(cfg)
    fake_result = _make_fake_result(duration_samples=duration_samples)
    mock_pipe = MagicMock()
    mock_pipe.return_value = fake_result
    backend._pipe = mock_pipe
    backend._torch = _make_mock_torch()
    return backend, mock_pipe


class TestFactory:
    def test_returns_stable_audio(self):
        cfg = SoundForgeConfig(backend="stable-audio")
        backend = get_backend("stable-audio", cfg)
        from soundforge.core.backends.stable_audio import StableAudioBackend

        assert isinstance(backend, StableAudioBackend)

    def test_error_lists_both_backends(self):
        cfg = SoundForgeConfig()
        with pytest.raises(ValueError, match="Available: elevenlabs, stable-audio"):
            get_backend("unknown", cfg)


class TestCapabilities:
    def test_max_duration(self):
        backend = _make_backend()
        assert backend.capabilities()["max_duration"] == 47

    def test_supports_seed(self):
        backend = _make_backend()
        assert backend.capabilities()["supports_seed"] is True

    def test_no_native_loop(self):
        backend = _make_backend()
        assert backend.capabilities()["supports_loop"] is False


class TestAvailability:
    def test_unavailable_without_torch(self):
        backend = _make_backend()
        with patch.object(backend, "is_available", return_value=False):
            assert backend.is_available() is False

    def test_available_with_cuda(self):
        backend = _make_backend()
        with patch.object(backend, "is_available", return_value=True):
            assert backend.is_available() is True


class TestInfo:
    def test_info_unavailable(self):
        backend = _make_backend()
        with patch.object(backend, "is_available", return_value=False):
            info = backend.info()
            assert info["name"] == "stable-audio"
            assert info["available"] is False
            assert "not installed" in info["status"]

    def test_info_available(self):
        backend = _make_backend()
        mock_torch = MagicMock()
        mock_torch.cuda.get_device_name.return_value = "RTX 4080"
        mock_props = MagicMock()
        mock_props.total_memory = 12 * (1024**3)
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with patch.object(backend, "is_available", return_value=True):
            original_import = __import__
            def mock_import(name, *args, **kwargs):
                if name == "torch":
                    return mock_torch
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                info = backend.info()
                assert info["available"] is True
                assert info["gpu"] == "RTX 4080"
                assert info["vram_gb"] == 12.0


class TestGenerate:
    @patch("soundforge.core.backends.stable_audio.StableAudioBackend._load_pipeline")
    def test_missing_deps_raises(self, mock_load):
        mock_load.side_effect = RuntimeError(
            "Stable Audio backend requires torch and diffusers. "
            "Install with: pip install soundforge[local-gpu]"
        )
        backend = _make_backend()
        with pytest.raises(RuntimeError, match="torch and diffusers"):
            backend.generate("test")

    def test_success_returns_ndarray(self):
        backend, mock_pipe = _make_ready_backend(duration_samples=88200)
        samples, sr = backend.generate("coin pickup", duration_seconds=2.0)

        assert isinstance(samples, np.ndarray)
        assert sr == 44100
        assert samples.dtype == np.float64
        assert samples.ndim == 2  # stereo

    def test_default_duration(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test")
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["audio_end_in_s"] == 5.0

    def test_duration_clamped(self):
        backend, mock_pipe = _make_ready_backend()
        warnings = []
        backend.generate("test", duration_seconds=60.0, on_status=warnings.append)
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["audio_end_in_s"] == 47.0
        assert any("clamped" in w for w in warnings)

    def test_no_warning_for_valid_duration(self):
        backend, mock_pipe = _make_ready_backend()
        warnings = []
        backend.generate("test", duration_seconds=5.0, on_status=warnings.append)
        assert not any("clamped" in w for w in warnings)

    def test_prompt_influence_low_steps(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test", prompt_influence=0.0)
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["num_inference_steps"] == 50

    def test_prompt_influence_high_steps(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test", prompt_influence=1.0)
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["num_inference_steps"] == 200

    def test_prompt_influence_default(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test", prompt_influence=0.3)
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["num_inference_steps"] == 95

    def test_fixed_steps_from_config(self):
        cfg = SoundForgeConfig(backend="stable-audio")
        cfg._backend_settings["stable-audio"] = {"num_inference_steps": 75}
        backend, mock_pipe = _make_ready_backend(cfg=cfg)
        backend.generate("test", prompt_influence=1.0)
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["num_inference_steps"] == 75

    def test_loop_modifies_prompt(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("rain", loop=True)
        call_args = mock_pipe.call_args
        assert call_args[0][0] == "seamless loop, rain"

    def test_no_loop_keeps_prompt(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("rain", loop=False)
        call_args = mock_pipe.call_args
        assert call_args[0][0] == "rain"

    def test_seed_sets_manual_seed(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test", seed=42)
        backend._torch.Generator.return_value.manual_seed.assert_called_with(42)

    def test_no_seed_uses_random(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test", seed=None)
        backend._torch.Generator.return_value.manual_seed.assert_not_called()

    def test_negative_prompt_default(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test")
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["negative_prompt"] == "low quality, distorted, noise"

    def test_negative_prompt_from_config(self):
        cfg = SoundForgeConfig(backend="stable-audio")
        cfg._backend_settings["stable-audio"] = {"negative_prompt": "silence"}
        backend, mock_pipe = _make_ready_backend(cfg=cfg)
        backend.generate("test")
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["negative_prompt"] == "silence"

    def test_guidance_scale_default(self):
        backend, mock_pipe = _make_ready_backend()
        backend.generate("test")
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["guidance_scale"] == 7.0

    def test_guidance_scale_from_config(self):
        cfg = SoundForgeConfig(backend="stable-audio")
        cfg._backend_settings["stable-audio"] = {"guidance_scale": 3.5}
        backend, mock_pipe = _make_ready_backend(cfg=cfg)
        backend.generate("test")
        call_kwargs = mock_pipe.call_args[1]
        assert call_kwargs["guidance_scale"] == 3.5

    def test_oom_raises_friendly_error(self):
        backend, mock_pipe = _make_ready_backend()
        OOMError = backend._torch.cuda.OutOfMemoryError
        mock_pipe.side_effect = OOMError("CUDA OOM")
        with pytest.raises(RuntimeError, match="GPU out of memory"):
            backend.generate("test")

    def test_status_callbacks(self):
        backend, mock_pipe = _make_ready_backend(duration_samples=44100)
        statuses = []
        backend.generate("coin pickup", on_status=statuses.append)
        assert any("Generating" in s for s in statuses)
        assert any("Generated" in s for s in statuses)


class TestStepMapping:
    def test_clamps_below_zero(self):
        backend = _make_backend()
        assert backend._map_steps(-0.5) == 50

    def test_clamps_above_one(self):
        backend = _make_backend()
        assert backend._map_steps(1.5) == 200

    def test_midpoint(self):
        backend = _make_backend()
        assert backend._map_steps(0.5) == 125


class TestConfigIntegration:
    def test_backend_settings_from_toml(self, tmp_path):
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text(
            '[backend]\ndefault = "stable-audio"\n\n'
            "[backend.stable-audio]\n"
            "num_inference_steps = 75\n"
            'negative_prompt = "noise"\n'
            "guidance_scale = 5.0\n"
        )
        cfg = SoundForgeConfig.load(config_file)
        assert cfg.backend == "stable-audio"
        settings = cfg._backend_settings.get("stable-audio", {})
        assert settings["num_inference_steps"] == 75
        assert settings["negative_prompt"] == "noise"
        assert settings["guidance_scale"] == 5.0

    def test_no_backend_settings_is_empty(self):
        cfg = SoundForgeConfig()
        assert cfg._backend_settings == {}

    def test_model_path_from_config(self):
        cfg = SoundForgeConfig(backend="stable-audio")
        cfg._backend_settings["stable-audio"] = {"model_path": "/local/model"}
        backend = _make_backend(cfg)
        assert backend._model_path == "/local/model"

    def test_default_model_path(self):
        backend = _make_backend()
        assert backend._model_path == "stabilityai/stable-audio-open-1.0"
