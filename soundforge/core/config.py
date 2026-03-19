"""SoundForge configuration — .soundforge.toml loading and engine presets."""

from __future__ import annotations

import dataclasses
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ENGINE_PRESETS: dict[str, dict] = {
    "godot": {
        "format": "wav",
        "sample_rate": 44100,
        "channels": 1,
        "output_dir": "audio/sfx",
    },
    "unity": {
        "format": "wav",
        "sample_rate": 44100,
        "channels": 1,
        "output_dir": "Assets/Audio/SFX",
    },
    "unreal": {
        "format": "wav",
        "sample_rate": 48000,
        "channels": 1,
        "output_dir": "Content/Audio/SFX",
    },
}

CONFIG_FILENAME = ".soundforge.toml"
GLOBAL_CONFIG_PATH = Path.home() / ".config" / "soundforge" / "config.toml"


def _find_config(start: Path | None = None) -> Path | None:
    """Walk up directories looking for .soundforge.toml."""
    current = (start or Path.cwd()).resolve()
    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    if GLOBAL_CONFIG_PATH.is_file():
        return GLOBAL_CONFIG_PATH
    return None


@dataclass
class SoundForgeConfig:
    # Defaults
    backend: str = "elevenlabs"
    engine: str | None = None
    asset_type: str = "sfx"
    duration: float = 2.0
    variations: int = 4
    output_dir: str | None = None

    # Postprocess
    trim_silence: bool = True
    fade_in: float = 0.01
    fade_out: float = 0.05
    normalize: bool = True
    target_peak_dbfs: float = -1.0
    sample_rate: int | None = None
    channels: int | None = None

    # Backend keys
    elevenlabs_api_key: str = ""

    _config_path: Path | None = field(default=None, repr=False, compare=False)
    _engine_overrides: dict = field(default_factory=dict, repr=False, compare=False)
    _backend_settings: dict = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def load(cls, path: Path | None = None) -> SoundForgeConfig:
        """Load config from .soundforge.toml, walking up directories."""
        if path is not None and not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        config_path = path if path else _find_config()
        if config_path is None:
            cfg = cls()
            cfg._resolve_env()
            return cfg

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        cfg = cls()
        cfg._config_path = config_path

        # [defaults]
        defaults = data.get("defaults", {})
        if "engine" in defaults:
            cfg.engine = defaults["engine"]
        if "asset_type" in defaults:
            cfg.asset_type = defaults["asset_type"]
        if "duration" in defaults:
            cfg.duration = float(defaults["duration"])
        if "variations" in defaults:
            cfg.variations = int(defaults["variations"])
        if "output_dir" in defaults:
            cfg.output_dir = defaults["output_dir"]

        # [backend]
        backend = data.get("backend", {})
        if "default" in backend:
            cfg.backend = backend["default"]
        if "elevenlabs_api_key" in backend:
            cfg.elevenlabs_api_key = backend["elevenlabs_api_key"]

        # [backend.*] sub-tables — backend-specific settings
        for key, value in backend.items():
            if isinstance(value, dict):
                cfg._backend_settings[key] = dict(value)

        # [postprocess]
        pp = data.get("postprocess", {})
        if "trim_silence" in pp:
            cfg.trim_silence = bool(pp["trim_silence"])
        if "fade_in" in pp:
            cfg.fade_in = float(pp["fade_in"])
        if "fade_out" in pp:
            cfg.fade_out = float(pp["fade_out"])
        if "normalize" in pp:
            cfg.normalize = bool(pp["normalize"])
        if "target_peak_dbfs" in pp:
            cfg.target_peak_dbfs = float(pp["target_peak_dbfs"])
        if "sample_rate" in pp:
            cfg.sample_rate = int(pp["sample_rate"])
        if "channels" in pp:
            cfg.channels = int(pp["channels"])

        # [engine.*] sections — custom engine presets override hardcoded defaults
        for key, value in data.items():
            if key.startswith("engine.") and isinstance(value, dict):
                engine_name = key[len("engine."):]
                cfg._engine_overrides[engine_name] = dict(value)
            elif key == "engine" and isinstance(value, dict):
                # Also support [engine] as a table with sub-tables
                for engine_name, engine_cfg in value.items():
                    if isinstance(engine_cfg, dict):
                        cfg._engine_overrides[engine_name] = dict(engine_cfg)

        cfg._resolve_env()
        return cfg

    def _resolve_env(self) -> None:
        """Override config values from environment variables."""
        env_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if env_key:
            self.elevenlabs_api_key = env_key

    def merge_cli_args(self, **kwargs: object) -> SoundForgeConfig:
        """Return new config with non-None CLI arguments applied."""
        overrides = {k: v for k, v in kwargs.items() if v is not None}
        return dataclasses.replace(self, **overrides)

    def resolve_engine_preset(self) -> dict:
        """Get engine preset values, or empty dict if no engine set."""
        if not self.engine:
            return {}
        # Start with hardcoded defaults, override with TOML values
        preset = dict(ENGINE_PRESETS.get(self.engine, {}))
        if self.engine in self._engine_overrides:
            preset.update(self._engine_overrides[self.engine])
        return preset

    def resolve_output_dir(self) -> Path:
        """Resolve the output directory from CLI arg, engine preset, or cwd."""
        if self.output_dir:
            return Path(self.output_dir)
        preset = self.resolve_engine_preset()
        if "output_dir" in preset:
            return Path(preset["output_dir"])
        return Path(".")

    def resolve_sample_rate(self) -> int:
        """Resolve sample rate from config, engine preset, or default 44100."""
        if self.sample_rate:
            return self.sample_rate
        preset = self.resolve_engine_preset()
        return preset.get("sample_rate", 44100)

    def resolve_channels(self) -> int:
        """Resolve channel count from config, engine preset, or default 1."""
        if self.channels:
            return self.channels
        preset = self.resolve_engine_preset()
        return preset.get("channels", 1)
