"""Tests for single generation pipeline."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from soundforge.core.config import SoundForgeConfig
from soundforge.core.generate import generate


def _fake_backend(samples=None, sr=44100):
    """Create a mock backend returning known audio."""
    if samples is None:
        samples = np.sin(np.linspace(0, 2 * np.pi * 440, sr)).astype(np.float64)
    backend = MagicMock()
    backend.generate.return_value = (samples, sr)
    backend.capabilities.return_value = {
        "max_duration": 30,
        "supports_loop": True,
        "supports_seed": False,
    }
    return backend


class TestGenerate:
    @patch("soundforge.core.generate.get_backend")
    def test_basic_generation(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = generate(
            "coin pickup",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        assert result.asset.path.exists()
        assert result.asset.path.suffix == ".wav"
        assert result.prompt_used == "coin pickup"
        assert result.manifest_path.exists()

    @patch("soundforge.core.generate.get_backend")
    def test_prompt_passed_to_backend(self, mock_get_backend, tmp_path):
        backend = _fake_backend()
        mock_get_backend.return_value = backend

        generate(
            "explosion",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        backend.generate.assert_called_once()
        call_kwargs = backend.generate.call_args
        assert call_kwargs.kwargs["text"] == "explosion"

    @patch("soundforge.core.generate.get_backend")
    def test_config_defaults_applied(self, mock_get_backend, tmp_path):
        backend = _fake_backend()
        mock_get_backend.return_value = backend

        cfg = SoundForgeConfig(
            elevenlabs_api_key="test",
            duration=3.5,
        )
        generate("test", output_dir=tmp_path, config=cfg)

        call_kwargs = backend.generate.call_args
        assert call_kwargs.kwargs["duration_seconds"] == 3.5

    @patch("soundforge.core.generate.get_backend")
    def test_engine_preset_resolves(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = generate(
            "test",
            engine="unreal",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test", engine="unreal"),
        )

        # Unreal preset is 48000 Hz mono
        assert result.asset.sample_rate == 48000

    @patch("soundforge.core.generate.get_backend")
    def test_postprocessing_runs(self, mock_get_backend, tmp_path):
        # Feed in quiet audio — normalization should boost it
        quiet = np.sin(np.linspace(0, 2 * np.pi * 440, 44100)) * 0.1
        mock_get_backend.return_value = _fake_backend(samples=quiet.astype(np.float64))

        cfg = SoundForgeConfig(
            elevenlabs_api_key="test",
            normalize=True,
            target_peak_dbfs=-1.0,
        )
        result = generate("test", output_dir=tmp_path, config=cfg)

        # Peak should be close to -1 dBFS after normalization
        assert result.asset.peak_dbfs == pytest.approx(-1.0, abs=0.5)

    @patch("soundforge.core.generate.get_backend")
    def test_manifest_written(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = generate(
            "test",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        import json
        manifest = json.loads(result.manifest_path.read_text())
        assert manifest["prompt"] == "test"
        assert len(manifest["files"]) == 1

    @patch("soundforge.core.generate.get_backend")
    def test_seed_warning(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        warnings = []
        generate(
            "test",
            seed=42,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
            on_status=warnings.append,
        )

        assert any("does not support seeds" in w for w in warnings)

    @patch("soundforge.core.generate.get_backend")
    def test_no_seed_no_warning(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        warnings = []
        generate(
            "test",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
            on_status=warnings.append,
        )

        assert not any("does not support seeds" in w for w in warnings)

    @patch("soundforge.core.generate.get_backend")
    def test_loop_type_enables_loop_without_flag(self, mock_get_backend, tmp_path):
        """--type loop should auto-enable loop at backend and postprocess."""
        backend = _fake_backend()
        mock_get_backend.return_value = backend

        result = generate(
            "ambient rain",
            asset_type="loop",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        # Backend should have been called with loop=True
        call_kwargs = backend.generate.call_args
        assert call_kwargs.kwargs["loop"] is True

        # Manifest should show loop_safe and loop_smooth
        import json
        manifest = json.loads(result.manifest_path.read_text())
        assert manifest["postprocess"]["loop_smooth"] is True
        assert manifest["files"][0]["loop_safe"] is True

    @patch("soundforge.core.generate.get_backend")
    def test_ambience_type_enables_loop(self, mock_get_backend, tmp_path):
        backend = _fake_backend()
        mock_get_backend.return_value = backend

        generate(
            "forest",
            asset_type="ambience",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        call_kwargs = backend.generate.call_args
        assert call_kwargs.kwargs["loop"] is True

    @patch("soundforge.core.generate.get_backend")
    def test_postprocess_settings_in_manifest(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = generate(
            "test",
            loop=True,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        import json
        manifest = json.loads(result.manifest_path.read_text())
        pp = manifest["postprocess"]
        assert "loop_smooth" in pp
        assert "sample_rate_conversion" in pp
        assert "channel_conversion" in pp

    @patch("soundforge.core.generate.get_backend")
    def test_duration_preflight_clamps_before_backend_call(
        self, mock_get_backend, tmp_path
    ):
        backend = _fake_backend()
        mock_get_backend.return_value = backend

        warnings = []
        generate(
            "test",
            duration=45.0,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
            on_status=warnings.append,
        )

        call_kwargs = backend.generate.call_args
        assert call_kwargs.kwargs["duration_seconds"] == 30.0
        assert any("clamping to 30" in warning for warning in warnings)

    @patch("soundforge.core.generate.get_backend")
    def test_loop_preflight_fails_before_backend_call(self, mock_get_backend, tmp_path):
        backend = _fake_backend()
        backend.capabilities.return_value = {
            "max_duration": 30,
            "supports_loop": False,
            "supports_seed": False,
        }
        mock_get_backend.return_value = backend

        with pytest.raises(RuntimeError, match="does not support loop generation"):
            generate(
                "test",
                loop=True,
                output_dir=tmp_path,
                config=SoundForgeConfig(elevenlabs_api_key="test"),
            )

        backend.generate.assert_not_called()
