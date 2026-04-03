"""Tests for batch variation generation."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from soundforge.core.batch import batch_generate
from soundforge.core.config import SoundForgeConfig


def _fake_backend(sr=44100):
    """Create a mock backend returning different audio each call."""
    backend = MagicMock()
    call_count = 0

    def gen_audio(**kwargs):
        nonlocal call_count
        call_count += 1
        # Slightly different frequency each time for uniqueness
        freq = 440 + call_count * 10
        samples = np.sin(np.linspace(0, 2 * np.pi * freq, sr)).astype(np.float64)
        return samples, sr

    backend.generate.side_effect = gen_audio
    backend.capabilities.return_value = {
        "max_duration": 30,
        "supports_loop": True,
        "supports_seed": False,
    }
    return backend


class TestBatchGenerate:
    @patch("soundforge.core.batch.get_backend")
    def test_produces_n_files(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = batch_generate(
            "coin pickup",
            count=3,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        assert len(result.results) == 3
        for r in result.results:
            assert r.asset.path.exists()
            assert r.asset.path.suffix == ".wav"

    @patch("soundforge.core.batch.get_backend")
    def test_manifest_lists_all_files(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = batch_generate(
            "test",
            count=3,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        manifest = json.loads(result.manifest_path.read_text())
        assert len(manifest["files"]) == 3

    @patch("soundforge.core.batch.get_backend")
    def test_prefix_auto_derived(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = batch_generate(
            "sword clash",
            count=2,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        # Auto prefix should include asset_type + sanitized prompt
        assert "sfx" in result.pack_name
        assert "sword" in result.pack_name

    @patch("soundforge.core.batch.get_backend")
    def test_explicit_prefix(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = batch_generate(
            "test",
            count=2,
            prefix="my_custom",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        assert result.pack_name == "my_custom"
        for r in result.results:
            assert "my_custom" in r.asset.path.name

    @patch("soundforge.core.batch.get_backend")
    def test_deterministic_naming(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = batch_generate(
            "test",
            count=3,
            prefix="sfx_test",
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        names = [r.asset.path.name for r in result.results]
        assert names == ["sfx_test_01.wav", "sfx_test_02.wav", "sfx_test_03.wav"]

    @patch("soundforge.core.batch.get_backend")
    def test_each_variation_postprocessed(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        cfg = SoundForgeConfig(
            elevenlabs_api_key="test",
            normalize=True,
            target_peak_dbfs=-1.0,
        )
        result = batch_generate(
            "test",
            count=3,
            output_dir=tmp_path,
            config=cfg,
        )

        for r in result.results:
            assert r.asset.peak_dbfs == pytest.approx(-1.0, abs=0.5)

    @patch("soundforge.core.batch.get_backend")
    def test_postprocess_tracking(self, mock_get_backend, tmp_path):
        mock_get_backend.return_value = _fake_backend()

        result = batch_generate(
            "test",
            count=2,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
        )

        manifest = json.loads(result.manifest_path.read_text())
        pp = manifest["postprocess"]
        assert "loop_smooth" in pp
        assert "sample_rate_conversion" in pp
        assert "channel_conversion" in pp

    @patch("soundforge.core.batch.get_backend")
    def test_duration_preflight_clamps_before_backend_calls(
        self, mock_get_backend, tmp_path
    ):
        backend = _fake_backend()
        mock_get_backend.return_value = backend

        warnings = []
        batch_generate(
            "test",
            count=2,
            duration=45.0,
            output_dir=tmp_path,
            config=SoundForgeConfig(elevenlabs_api_key="test"),
            on_status=warnings.append,
        )

        for call in backend.generate.call_args_list:
            assert call.kwargs["duration_seconds"] == 30.0
        assert any("clamping to 30" in warning for warning in warnings)

    @patch("soundforge.core.batch.get_backend")
    def test_loop_preflight_fails_before_backend_calls(self, mock_get_backend, tmp_path):
        backend = _fake_backend()
        backend.capabilities.return_value = {
            "max_duration": 30,
            "supports_loop": False,
            "supports_seed": False,
        }
        mock_get_backend.return_value = backend

        with pytest.raises(RuntimeError, match="does not support loop generation"):
            batch_generate(
                "test",
                count=2,
                loop=True,
                output_dir=tmp_path,
                config=SoundForgeConfig(elevenlabs_api_key="test"),
            )

        backend.generate.assert_not_called()
