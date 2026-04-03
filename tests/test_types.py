"""Tests for core types."""

from pathlib import Path

from soundforge.core.types import (
    AssetType,
    AudioAsset,
    BatchResult,
    Engine,
    GenerateResult,
    InfoResult,
    InspectResult,
)


class TestAssetType:
    def test_values(self):
        assert AssetType.SFX == "sfx"
        assert AssetType.UI == "ui"
        assert AssetType.AMBIENCE == "ambience"
        assert AssetType.LOOP == "loop"


class TestEngine:
    def test_values(self):
        assert Engine.GODOT == "godot"
        assert Engine.UNITY == "unity"
        assert Engine.UNREAL == "unreal"


class TestAudioAsset:
    def test_to_dict(self):
        asset = AudioAsset(
            path=Path("test.wav"),
            duration_seconds=0.5123,
            sample_rate=44100,
            channels=1,
            peak_dbfs=-1.234,
        )
        d = asset.to_dict()
        assert d["path"] == "test.wav"
        assert d["duration_seconds"] == 0.512
        assert d["peak_dbfs"] == -1.2
        assert d["format"] == "wav"
        assert d["loop_safe"] is False


class TestGenerateResult:
    def test_to_dict(self):
        asset = AudioAsset(
            path=Path("sfx_coin.wav"),
            duration_seconds=0.5,
            sample_rate=44100,
            channels=1,
            peak_dbfs=-1.0,
        )
        result = GenerateResult(
            asset=asset,
            backend="elevenlabs",
            prompt_used="coin pickup",
            seed=42,
            manifest_path=Path("manifest.json"),
        )
        d = result.to_dict()
        assert d["output"] == "sfx_coin.wav"
        assert d["backend"] == "elevenlabs"
        assert d["seed"] == 42
        assert d["manifest"] == "manifest.json"


class TestBatchResult:
    def test_to_dict(self):
        asset = AudioAsset(
            path=Path("sfx_01.wav"),
            duration_seconds=0.5,
            sample_rate=44100,
            channels=1,
            peak_dbfs=-1.0,
        )
        result = BatchResult(
            results=[
                GenerateResult(asset=asset, backend="elevenlabs", prompt_used="test")
            ],
            pack_name="test_pack",
            manifest_path=Path("manifest.json"),
        )
        d = result.to_dict()
        assert d["pack_name"] == "test_pack"
        assert d["count"] == 1
        assert len(d["files"]) == 1


class TestInfoResult:
    def test_to_dict(self):
        result = InfoResult(
            version="0.1.0",
            config_path=None,
            backend="elevenlabs",
            backend_available=True,
            engine="godot",
        )
        d = result.to_dict()
        assert d["version"] == "0.1.0"
        assert d["backend_available"] is True
