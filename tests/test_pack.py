"""Tests for pack assembly."""

import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from soundforge.core.pack import build_pack


def _create_test_wavs(directory: Path, count: int = 3) -> list[Path]:
    """Create test WAV files in directory."""
    paths = []
    for i in range(count):
        path = directory / f"test_{i:02d}.wav"
        samples = np.sin(np.linspace(0, 2 * np.pi * (440 + i * 50), 22050))
        sf.write(str(path), samples, 44100, subtype="PCM_16")
        paths.append(path)
    return paths


class TestBuildPack:
    def test_creates_manifest(self, tmp_path):
        _create_test_wavs(tmp_path)

        manifest_path, zip_path = build_pack(
            directory=tmp_path,
            name="test_pack",
            asset_type="sfx",
        )

        assert manifest_path.exists()
        assert zip_path is None

        manifest = json.loads(manifest_path.read_text())
        assert manifest["name"] == "test_pack"
        assert manifest["asset_type"] == "sfx"
        assert manifest["backend"] == "existing"
        assert len(manifest["files"]) == 3

    def test_manifest_metadata(self, tmp_path):
        _create_test_wavs(tmp_path, count=2)

        manifest_path, _ = build_pack(
            directory=tmp_path,
            name="meta_test",
            asset_type="ui",
            engine="unity",
        )

        manifest = json.loads(manifest_path.read_text())
        assert manifest["engine"] == "unity"
        assert manifest["asset_type"] == "ui"
        for f in manifest["files"]:
            assert "duration_seconds" in f
            assert "sample_rate" in f
            assert "channels" in f
            assert "peak_dbfs" in f

    def test_creates_zip(self, tmp_path):
        wav_paths = _create_test_wavs(tmp_path)

        manifest_path, zip_path = build_pack(
            directory=tmp_path,
            name="zip_test",
            create_zip=True,
        )

        assert zip_path is not None
        assert zip_path.exists()

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            # Should contain all WAVs + manifest
            assert len(names) == 4
            for wp in wav_paths:
                assert wp.name in names
            assert manifest_path.name in names

    def test_empty_directory_raises(self, tmp_path):
        with pytest.raises(ValueError, match="No supported audio files"):
            build_pack(directory=tmp_path, name="empty")

    def test_builds_manifest_from_ogg_files(self, tmp_path):
        path = tmp_path / "test_00.ogg"
        samples = np.sin(np.linspace(0, 2 * np.pi * 440, 22050))
        sf.write(str(path), samples, 44100, format="OGG", subtype="VORBIS")

        manifest_path, _ = build_pack(
            directory=tmp_path,
            name="ogg_pack",
        )

        manifest = json.loads(manifest_path.read_text())
        assert len(manifest["files"]) == 1
        assert manifest["files"][0]["format"] == "ogg"

    def test_engine_in_manifest(self, tmp_path):
        _create_test_wavs(tmp_path, count=1)

        manifest_path, _ = build_pack(
            directory=tmp_path,
            name="engine_test",
            engine="godot",
        )

        manifest = json.loads(manifest_path.read_text())
        assert manifest["engine"] == "godot"

    def test_no_engine_in_manifest(self, tmp_path):
        _create_test_wavs(tmp_path, count=1)

        manifest_path, _ = build_pack(
            directory=tmp_path,
            name="no_engine",
        )

        manifest = json.loads(manifest_path.read_text())
        assert manifest["engine"] is None
