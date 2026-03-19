"""Tests for export module."""

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from soundforge.core.export import (
    export_batch,
    export_single,
    make_batch_filename,
    make_single_filename,
    sanitize_name,
    write_manifest,
    write_wav,
)


class TestSanitizeName:
    def test_basic(self):
        assert sanitize_name("coin pickup") == "coin_pickup"

    def test_special_chars(self):
        assert sanitize_name("sword hit! (heavy)") == "sword_hit_heavy"

    def test_truncation(self):
        result = sanitize_name("a" * 100, max_length=20)
        assert len(result) <= 20

    def test_empty(self):
        assert sanitize_name("!!!") == "sound"

    def test_mixed_case(self):
        assert sanitize_name("Coin Pickup") == "coin_pickup"


class TestFilenames:
    def test_single_filename(self):
        result = make_single_filename("coin pickup", "sfx")
        assert result == "sfx_coin_pickup.wav"

    def test_single_with_seed(self):
        result = make_single_filename("coin pickup", "sfx", seed=42)
        assert result == "sfx_coin_pickup_42.wav"

    def test_batch_filename(self):
        assert make_batch_filename("sfx_coin", 1) == "sfx_coin_01.wav"
        assert make_batch_filename("sfx_coin", 12) == "sfx_coin_12.wav"


class TestWriteWav:
    def test_writes_valid_wav(self, tmp_path):
        import soundfile as sf

        samples = np.sin(np.linspace(0, 1, 44100))
        path = tmp_path / "test.wav"
        write_wav(samples, 44100, path)

        assert path.exists()
        data, sr = sf.read(str(path))
        assert sr == 44100
        assert len(data) == 44100

    def test_creates_parent_dirs(self, tmp_path):
        samples = np.zeros(100)
        path = tmp_path / "deep" / "nested" / "test.wav"
        write_wav(samples, 44100, path)
        assert path.exists()


class TestWriteManifest:
    def test_writes_valid_json(self, tmp_path):
        from soundforge.core.types import AudioAsset
        from pathlib import Path

        asset = AudioAsset(
            path=tmp_path / "test.wav",
            duration_seconds=0.5,
            sample_rate=44100,
            channels=1,
            peak_dbfs=-1.0,
        )
        manifest_path = tmp_path / "manifest.json"
        write_manifest(
            manifest_path,
            name="test",
            asset_type="sfx",
            engine="godot",
            backend="elevenlabs",
            prompt="test prompt",
            files=[asset],
        )

        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["name"] == "test"
        assert data["asset_type"] == "sfx"
        assert data["engine"] == "godot"
        assert len(data["files"]) == 1
        assert data["files"][0]["duration_seconds"] == 0.5


class TestExportSingle:
    def test_creates_wav_and_manifest(self, tmp_path):
        samples = np.sin(np.linspace(0, 2 * np.pi * 440, 44100)).astype(np.float64)
        asset, manifest_path = export_single(
            samples=samples,
            sample_rate=44100,
            output_dir=tmp_path,
            prompt="coin pickup",
            asset_type="sfx",
            engine="godot",
            backend="elevenlabs",
        )

        assert asset.path.exists()
        assert manifest_path.exists()
        assert asset.sample_rate == 44100
        assert asset.channels == 1

        manifest = json.loads(manifest_path.read_text())
        assert manifest["prompt"] == "coin pickup"
        assert len(manifest["files"]) == 1
        # Path should be relative in manifest
        assert not Path(manifest["files"][0]["path"]).is_absolute()

    def test_with_seed(self, tmp_path):
        samples = np.zeros(1000, dtype=np.float64)
        asset, _ = export_single(
            samples=samples,
            sample_rate=44100,
            output_dir=tmp_path,
            prompt="test",
            asset_type="sfx",
            engine=None,
            backend="elevenlabs",
            seed=42,
        )

        assert "42" in asset.path.name


class TestExportBatch:
    def test_creates_wavs_and_manifest(self, tmp_path):
        results = [
            (np.sin(np.linspace(0, 2 * np.pi * 440, 22050)).astype(np.float64), 44100),
            (np.sin(np.linspace(0, 2 * np.pi * 880, 22050)).astype(np.float64), 44100),
        ]
        assets, manifest_path = export_batch(
            results=results,
            output_dir=tmp_path,
            prefix="sfx_test",
            prompt="test",
            asset_type="sfx",
            engine="godot",
            backend="elevenlabs",
        )

        assert len(assets) == 2
        for asset in assets:
            assert asset.path.exists()
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text())
        assert len(manifest["files"]) == 2
        # Paths should be relative
        for f in manifest["files"]:
            assert not Path(f["path"]).is_absolute()
