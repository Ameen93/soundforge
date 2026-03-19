"""Pack assembly — build manifests from existing audio file directories."""

from __future__ import annotations

import zipfile
from pathlib import Path

from soundforge.core.analysis import analyze_file
from soundforge.core.export import write_manifest
from soundforge.core.types import AudioAsset


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
    wav_files = sorted(directory.glob("*.wav"))
    if not wav_files:
        raise ValueError(f"No WAV files found in {directory}")

    assets: list[AudioAsset] = []
    for wav_path in wav_files:
        result = analyze_file(wav_path)
        assets.append(
            AudioAsset(
                path=wav_path,
                duration_seconds=result.duration_seconds,
                sample_rate=result.sample_rate,
                channels=result.channels,
                peak_dbfs=result.peak_dbfs,
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
            for wav_path in wav_files:
                zf.write(wav_path, wav_path.name)
            zf.write(manifest_path, manifest_path.name)

    return manifest_path, zip_path
