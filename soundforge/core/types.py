"""SoundForge core types — dataclasses, enums, and result structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class AssetType(str, Enum):
    SFX = "sfx"
    UI = "ui"
    AMBIENCE = "ambience"
    LOOP = "loop"


class Engine(str, Enum):
    GODOT = "godot"
    UNITY = "unity"
    UNREAL = "unreal"


@dataclass
class AudioAsset:
    """Metadata for a single exported audio file."""

    path: Path
    duration_seconds: float
    sample_rate: int
    channels: int
    peak_dbfs: float
    format: str = "wav"
    loop_safe: bool = False

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "duration_seconds": round(self.duration_seconds, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "peak_dbfs": round(self.peak_dbfs, 1),
            "format": self.format,
            "loop_safe": self.loop_safe,
        }


@dataclass
class GenerateResult:
    """Result of a single generation."""

    asset: AudioAsset
    backend: str
    prompt_used: str
    seed: int | None = None
    manifest_path: Path | None = None

    def to_dict(self) -> dict:
        d = {
            "output": str(self.asset.path),
            **self.asset.to_dict(),
            "backend": self.backend,
            "prompt_used": self.prompt_used,
        }
        if self.seed is not None:
            d["seed"] = self.seed
        if self.manifest_path is not None:
            d["manifest"] = str(self.manifest_path)
        return d


@dataclass
class BatchResult:
    """Result of a batch generation."""

    results: list[GenerateResult]
    pack_name: str
    manifest_path: Path | None = None

    def to_dict(self) -> dict:
        return {
            "pack_name": self.pack_name,
            "count": len(self.results),
            "files": [r.asset.to_dict() for r in self.results],
            "manifest": str(self.manifest_path) if self.manifest_path else None,
        }


@dataclass
class InspectResult:
    """Result of inspecting an audio file."""

    path: Path
    duration_seconds: float
    sample_rate: int
    channels: int
    peak_dbfs: float
    format_info: str = "WAV"

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "duration_seconds": round(self.duration_seconds, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "peak_dbfs": round(self.peak_dbfs, 1),
            "format": self.format_info,
        }


@dataclass
class InfoResult:
    """Result of the info command."""

    version: str
    config_path: str | None
    backend: str
    backend_available: bool
    engine: str | None
    capabilities: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "config_path": self.config_path,
            "backend": self.backend,
            "backend_available": self.backend_available,
            "engine": self.engine,
            "capabilities": self.capabilities,
        }
