"""Pack assembly — build manifests from existing audio file directories."""

from __future__ import annotations

import zipfile
from pathlib import Path

from soundforge.core.analysis import analyze_file
from soundforge.core.export import write_manifest
from soundforge.core.types import AudioAsset

AUDIO_EXTENSIONS = ("*.wav", "*.ogg")


def build_pack(
    directory: Path,
    name: str,
    asset_type: str = "sfx",
    engine: str | None = None,
    create_zip: bool = False,
) -> tuple[Path, Path | None]:
    """Build a manifest from a directory of audio files.

    Returns (manifest_path, zip_path or None).
    """
    audio_files = sorted(
        file_path
        for pattern in AUDIO_EXTENSIONS
        for file_path in directory.glob(pattern)
    )
    if not audio_files:
        raise ValueError(f"No supported audio files found in {directory}")

    assets: list[AudioAsset] = []
    for audio_path in audio_files:
        result = analyze_file(audio_path)
        assets.append(
            AudioAsset(
                path=audio_path,
                duration_seconds=result.duration_seconds,
                sample_rate=result.sample_rate,
                channels=result.channels,
                peak_dbfs=result.peak_dbfs,
                format=audio_path.suffix.lstrip(".").lower(),
            )
        )

    manifest_path = directory / f"{name}_manifest.json"
    write_manifest(
        manifest_path,
        name=name,
        asset_type=asset_type,
        engine=engine,
        backend="existing",
        prompt="(packed from existing files)",
        files=assets,
    )

    zip_path = None
    if create_zip:
        zip_path = directory / f"{name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for audio_path in audio_files:
                zf.write(audio_path, audio_path.name)
            zf.write(manifest_path, manifest_path.name)

    return manifest_path, zip_path
