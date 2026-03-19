"""Tests for configuration loading."""

import os
from pathlib import Path

import pytest

from soundforge.core.config import ENGINE_PRESETS, SoundForgeConfig, _find_config


class TestEnginePresets:
    def test_godot_preset(self):
        assert ENGINE_PRESETS["godot"]["sample_rate"] == 44100
        assert ENGINE_PRESETS["godot"]["channels"] == 1

    def test_unity_preset(self):
        assert ENGINE_PRESETS["unity"]["sample_rate"] == 44100

    def test_unreal_preset(self):
        assert ENGINE_PRESETS["unreal"]["sample_rate"] == 48000


class TestConfig:
    def test_defaults(self):
        cfg = SoundForgeConfig()
        assert cfg.backend == "elevenlabs"
        assert cfg.asset_type == "sfx"
        assert cfg.duration == 2.0
        assert cfg.variations == 4
        assert cfg.trim_silence is True
        assert cfg.normalize is True
        assert cfg.target_peak_dbfs == -1.0

    def test_merge_cli_args(self):
        cfg = SoundForgeConfig()
        merged = cfg.merge_cli_args(engine="godot", duration=5.0)
        assert merged.engine == "godot"
        assert merged.duration == 5.0
        # Original unchanged
        assert cfg.engine is None
        assert cfg.duration == 2.0

    def test_merge_ignores_none(self):
        cfg = SoundForgeConfig(engine="unity")
        merged = cfg.merge_cli_args(engine=None)
        assert merged.engine == "unity"

    def test_resolve_engine_preset(self):
        cfg = SoundForgeConfig(engine="godot")
        preset = cfg.resolve_engine_preset()
        assert preset["sample_rate"] == 44100
        assert preset["output_dir"] == "audio/sfx"

    def test_resolve_no_engine(self):
        cfg = SoundForgeConfig()
        preset = cfg.resolve_engine_preset()
        assert preset == {}

    def test_resolve_output_dir_from_engine(self):
        cfg = SoundForgeConfig(engine="unity")
        assert cfg.resolve_output_dir() == Path("Assets/Audio/SFX")

    def test_resolve_output_dir_explicit(self):
        cfg = SoundForgeConfig(output_dir="my/dir")
        assert cfg.resolve_output_dir() == Path("my/dir")

    def test_resolve_output_dir_default(self):
        cfg = SoundForgeConfig()
        assert cfg.resolve_output_dir() == Path(".")

    def test_resolve_sample_rate_from_engine(self):
        cfg = SoundForgeConfig(engine="unreal")
        assert cfg.resolve_sample_rate() == 48000

    def test_resolve_sample_rate_explicit(self):
        cfg = SoundForgeConfig(sample_rate=22050)
        assert cfg.resolve_sample_rate() == 22050

    def test_resolve_channels_from_engine(self):
        cfg = SoundForgeConfig(engine="godot")
        assert cfg.resolve_channels() == 1

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-123")
        cfg = SoundForgeConfig()
        cfg._resolve_env()
        assert cfg.elevenlabs_api_key == "test-key-123"

    def test_load_from_toml(self, tmp_path):
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text("""
[defaults]
engine = "unity"
duration = 3.5

[backend]
default = "elevenlabs"
elevenlabs_api_key = "test-key"

[postprocess]
trim_silence = false
target_peak_dbfs = -3.0
""")
        cfg = SoundForgeConfig.load(config_file)
        assert cfg.engine == "unity"
        assert cfg.duration == 3.5
        assert cfg.elevenlabs_api_key == "test-key"
        assert cfg.trim_silence is False
        assert cfg.target_peak_dbfs == -3.0


class TestFindConfig:
    def test_walk_up_finds_config(self, tmp_path):
        # Create config in parent, search from child
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text('[defaults]\nengine = "godot"\n')
        child = tmp_path / "sub" / "deep"
        child.mkdir(parents=True)

        result = _find_config(child)
        assert result == config_file

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        # Ensure no global config interferes
        monkeypatch.setattr(
            "soundforge.core.config.GLOBAL_CONFIG_PATH",
            tmp_path / "nonexistent" / "config.toml",
        )
        result = _find_config(tmp_path)
        assert result is None


class TestEngineOverrides:
    def test_toml_engine_overrides(self, tmp_path):
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text("""
[defaults]
engine = "godot"

[engine.godot]
sample_rate = 22050
channels = 2
""")
        cfg = SoundForgeConfig.load(config_file)
        preset = cfg.resolve_engine_preset()
        assert preset["sample_rate"] == 22050
        assert preset["channels"] == 2
        # Should still have unoverridden defaults from hardcoded preset
        assert preset["format"] == "wav"
        assert preset["output_dir"] == "audio/sfx"

    def test_custom_engine_from_toml(self, tmp_path):
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text("""
[defaults]
engine = "custom"

[engine.custom]
sample_rate = 48000
channels = 2
output_dir = "audio/custom"
""")
        cfg = SoundForgeConfig.load(config_file)
        preset = cfg.resolve_engine_preset()
        assert preset["sample_rate"] == 48000
        assert preset["channels"] == 2

    def test_no_overrides_uses_hardcoded(self):
        cfg = SoundForgeConfig(engine="godot")
        preset = cfg.resolve_engine_preset()
        assert preset["sample_rate"] == 44100


class TestOutputDirFromToml:
    def test_output_dir_from_defaults(self, tmp_path):
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text("""
[defaults]
output_dir = "custom/out"
""")
        cfg = SoundForgeConfig.load(config_file)
        assert cfg.output_dir == "custom/out"
        assert cfg.resolve_output_dir() == Path("custom/out")

    def test_output_dir_overrides_engine_preset(self, tmp_path):
        config_file = tmp_path / ".soundforge.toml"
        config_file.write_text("""
[defaults]
engine = "godot"
output_dir = "my/override"
""")
        cfg = SoundForgeConfig.load(config_file)
        # Explicit output_dir takes priority over engine preset
        assert cfg.resolve_output_dir() == Path("my/override")


class TestBadConfigPath:
    def test_nonexistent_config_raises(self, tmp_path):
        bad_path = tmp_path / "nonexistent.toml"
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            SoundForgeConfig.load(bad_path)
