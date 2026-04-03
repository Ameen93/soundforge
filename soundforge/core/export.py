"""Export — audio file writing, manifest JSON writing, file naming."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

from soundforge.core.analysis import analyze_array
from soundforge.core.types import AudioAsset

MANIFEST_VERSION = "1"
SUPPORTED_FORMATS = {"wav", "ogg"}


def sanitize_name(text: str, max_length: int = 40) -> str:
    """Sanitize a text string into a safe filename component."""
    # Lowercase, replace non-alphanumeric with underscore
    name = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    # Strip leading/trailing underscores
    name = name.strip("_")
    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip("_")
    return name or "sound"


def make_single_filename(
    prompt: str,
    asset_type: str = "sfx",
    seed: int | None = None,
    extension: str = "wav",
) -> str:
    """Generate a filename for a single generation."""
    sanitized = sanitize_name(prompt)
    name = f"{asset_type}_{sanitized}"
    if seed is not None:
        name = f"{name}_{seed}"
    return f"{name}.{extension}"


def make_batch_filename(prefix: str, index: int, extension: str = "wav") -> str:
    """Generate a numbered filename for batch output."""
    return f"{prefix}_{index:02d}.{extension}"


def validate_format(audio_format: str) -> str:
    """Normalize and validate an export format."""
    normalized = audio_format.lower()
    if normalized not in SUPPORTED_FORMATS:
        available = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"Unsupported audio format '{audio_format}'. Available: {available}")
    return normalized


def write_audio(
    samples: np.ndarray,
    sample_rate: int,
    path: Path,
    audio_format: str = "wav",
) -> Path:
    """Write audio samples to a supported export format."""
    audio_format = validate_format(audio_format)
    path.parent.mkdir(parents=True, exist_ok=True)
    if audio_format == "wav":
        sf.write(str(path), samples, sample_rate, format="WAV", subtype="PCM_16")
    elif audio_format == "ogg":
        sf.write(str(path), samples, sample_rate, format="OGG", subtype="VORBIS")
    return path


def write_wav(
    samples: np.ndarray,
    sample_rate: int,
    path: Path,
) -> Path:
    """Write audio samples to a WAV file."""
    return write_audio(samples, sample_rate, path, audio_format="wav")


def write_manifest(
    path: Path,
    *,
    name: str,
    asset_type: str,
    engine: str | None,
    backend: str,
    prompt: str,
    files: list[AudioAsset],
    postprocess: dict | None = None,
) -> Path:
    """Write a manifest JSON file."""
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "name": name,
        "asset_type": asset_type,
        "engine": engine,
        "backend": backend,
        "prompt": prompt,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [f.to_dict() for f in files],
    }
    if postprocess:
        manifest["postprocess"] = postprocess

    # Make file paths relative to manifest location
    manifest_dir = path.parent
    for f in manifest["files"]:
        try:
            f["path"] = str(Path(f["path"]).relative_to(manifest_dir))
        except ValueError:
            pass

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    return path


def export_single(
    samples: np.ndarray,
    sample_rate: int,
    output_dir: Path,
    prompt: str,
    asset_type: str,
    engine: str | None,
    backend: str,
    seed: int | None = None,
    audio_format: str = "wav",
    loop_safe: bool = False,
    postprocess_settings: dict | None = None,
) -> tuple[AudioAsset, Path]:
    """Export a single generated audio file with manifest. Returns (asset, manifest_path)."""
    audio_format = validate_format(audio_format)
    filename = make_single_filename(prompt, asset_type, seed, extension=audio_format)
    output_path = output_dir / filename
    write_audio(samples, sample_rate, output_path, audio_format=audio_format)

    # Validate the written file is readable
    try:
        sf.info(str(output_path))
    except Exception as e:
        raise RuntimeError(f"Written audio failed validation: {output_path} — {e}")

    asset = analyze_array(
        samples,
        sample_rate,
        output_path,
        audio_format=audio_format,
        loop_safe=loop_safe,
    )

    manifest_name = sanitize_name(prompt)
    manifest_path = output_dir / f"{asset_type}_{manifest_name}_manifest.json"
    write_manifest(
        manifest_path,
        name=f"{asset_type}_{manifest_name}",
        asset_type=asset_type,
        engine=engine,
        backend=backend,
        prompt=prompt,
        files=[asset],
        postprocess=postprocess_settings,
    )

    return asset, manifest_path


def export_batch(
    results: list[tuple[np.ndarray, int]],
    output_dir: Path,
    prefix: str,
    prompt: str,
    asset_type: str,
    engine: str | None,
    backend: str,
    audio_format: str = "wav",
    loop_safe: bool = False,
    postprocess_settings: dict | None = None,
) -> tuple[list[AudioAsset], Path]:
    """Export a batch of generated audio files with manifest. Returns (assets, manifest_path)."""
    audio_format = validate_format(audio_format)
    assets: list[AudioAsset] = []

    for i, (samples, sample_rate) in enumerate(results, start=1):
        filename = make_batch_filename(prefix, i, extension=audio_format)
        output_path = output_dir / filename
        write_audio(samples, sample_rate, output_path, audio_format=audio_format)

        # Validate the written file is readable
        try:
            sf.info(str(output_path))
        except Exception as e:
            raise RuntimeError(f"Written audio failed validation: {output_path} — {e}")

        asset = analyze_array(
            samples,
            sample_rate,
            output_path,
            audio_format=audio_format,
            loop_safe=loop_safe,
        )
        assets.append(asset)

    manifest_path = output_dir / f"{prefix}_manifest.json"
    write_manifest(
        manifest_path,
        name=prefix,
        asset_type=asset_type,
        engine=engine,
        backend=backend,
        prompt=prompt,
        files=assets,
        postprocess=postprocess_settings,
    )

    return assets, manifest_path
