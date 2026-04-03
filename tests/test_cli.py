"""CLI smoke tests using Click's CliRunner."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import soundfile as sf
from click.testing import CliRunner

from soundforge.cli.commands import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def test_wav(tmp_path):
    """Create a test WAV file."""
    path = tmp_path / "test.wav"
    samples = np.sin(np.linspace(0, 2 * np.pi * 440, 44100))
    sf.write(str(path), samples, 44100, subtype="PCM_16")
    return path


@pytest.fixture
def test_wav_dir(tmp_path):
    """Create a directory with test WAV files."""
    wav_dir = tmp_path / "wavs"
    wav_dir.mkdir()
    for i in range(3):
        path = wav_dir / f"test_{i:02d}.wav"
        samples = np.sin(np.linspace(0, 2 * np.pi * (440 + i * 50), 22050))
        sf.write(str(path), samples, 44100, subtype="PCM_16")
    return wav_dir


class TestHelp:
    def test_main_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SoundForge" in result.output

    @pytest.mark.parametrize("cmd", [
        "info", "setup", "generate", "batch", "process",
        "preview", "inspect", "pack",
    ])
    def test_command_help(self, runner, cmd):
        result = runner.invoke(cli, [cmd, "--help"])
        assert result.exit_code == 0


class TestVersion:
    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestInfo:
    def test_info_runs(self, runner):
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0

    def test_info_json(self, runner):
        result = runner.invoke(cli, ["info", "--output-json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "version" in data
        assert "backend" in data


class TestInspect:
    def test_inspect_file(self, runner, test_wav):
        result = runner.invoke(cli, ["inspect", str(test_wav)])
        assert result.exit_code == 0

    def test_inspect_directory(self, runner, test_wav_dir):
        result = runner.invoke(cli, ["inspect", str(test_wav_dir)])
        assert result.exit_code == 0

    def test_inspect_json(self, runner, test_wav):
        result = runner.invoke(cli, ["inspect", str(test_wav), "--output-json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "sample_rate" in data


class TestProcess:
    def test_process_file(self, runner, test_wav):
        result = runner.invoke(cli, ["process", str(test_wav)])
        assert result.exit_code == 0
        # Should create processed/ subdirectory
        processed = test_wav.parent / "processed" / test_wav.name
        assert processed.exists()

    def test_process_with_output(self, runner, test_wav, tmp_path):
        out = tmp_path / "output"
        result = runner.invoke(cli, ["process", str(test_wav), "-o", str(out)])
        assert result.exit_code == 0
        assert (out / test_wav.name).exists()


class TestGenerate:
    def test_generate_no_api_key(self, runner, monkeypatch):
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        result = runner.invoke(cli, ["generate", "test sound", "--backend", "elevenlabs"])
        assert result.exit_code == 1

    def test_generate_json_no_key(self, runner, monkeypatch):
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        result = runner.invoke(cli, ["generate", "test", "--output-json", "--backend", "elevenlabs"])
        assert result.exit_code == 1

    @patch("soundforge.core.generate.get_backend")
    def test_generate_loop_preflight_human_error(self, mock_get_backend, runner):
        backend = MagicMock()
        backend.capabilities.return_value = {
            "max_duration": 30,
            "supports_loop": False,
            "supports_seed": False,
        }
        mock_get_backend.return_value = backend

        result = runner.invoke(
            cli,
            ["generate", "test", "--backend", "stable-audio", "--loop"],
        )

        assert result.exit_code == 1
        assert "does not support loop generation" in result.output
        backend.generate.assert_not_called()

    @patch("soundforge.core.generate.get_backend")
    def test_generate_loop_preflight_json_error(self, mock_get_backend, runner):
        backend = MagicMock()
        backend.capabilities.return_value = {
            "max_duration": 30,
            "supports_loop": False,
            "supports_seed": False,
        }
        mock_get_backend.return_value = backend

        result = runner.invoke(
            cli,
            ["generate", "test", "--backend", "stable-audio", "--loop", "--output-json"],
        )

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "does not support loop generation" in data["error"]
        backend.generate.assert_not_called()


class TestPack:
    def test_pack_creates_manifest(self, runner, test_wav_dir):
        result = runner.invoke(cli, [
            "pack", str(test_wav_dir), "--name", "test_pack",
        ])
        assert result.exit_code == 0
        assert (test_wav_dir / "test_pack_manifest.json").exists()

    def test_pack_with_zip(self, runner, test_wav_dir):
        result = runner.invoke(cli, [
            "pack", str(test_wav_dir), "--name", "zipped", "--zip",
        ])
        assert result.exit_code == 0
        assert (test_wav_dir / "zipped.zip").exists()


class TestConfigPath:
    def test_bad_config_path_errors(self, runner):
        result = runner.invoke(cli, [
            "info", "--config", "/tmp/nonexistent_soundforge_config.toml",
        ])
        assert result.exit_code == 1


class TestInputValidation:
    def test_invalid_type_rejected(self, runner):
        result = runner.invoke(cli, ["generate", "test", "--type", "sfxx"])
        assert result.exit_code != 0
        assert "sfxx" in result.output or "Invalid value" in result.output

    def test_invalid_engine_rejected(self, runner):
        result = runner.invoke(cli, ["generate", "test", "--engine", "badengine"])
        assert result.exit_code != 0

    def test_valid_type_accepted(self, runner, monkeypatch):
        # Just check it parses — generation will fail without API key
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        result = runner.invoke(cli, ["generate", "test", "--type", "ambience"])
        # Will fail for API key, not for type validation
        assert "Invalid value" not in (result.output or "")

    def test_pack_invalid_type_rejected(self, runner, tmp_path):
        result = runner.invoke(cli, [
            "pack", str(tmp_path), "--name", "test", "--type", "invalid",
        ])
        assert result.exit_code != 0

    def test_batch_invalid_engine_rejected(self, runner):
        result = runner.invoke(cli, [
            "batch", "test", "--engine", "cryengine",
        ])
        assert result.exit_code != 0
