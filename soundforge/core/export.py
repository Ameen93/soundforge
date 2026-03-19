"""Export — WAV file writing, manifest JSON writing, file naming."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

from soundforge.core.analysis import analyze_array, analyze_file
from soundforge.core.types import AudioAsset


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
) -> str:
    """Generate a filename for a single generation."""
    sanitized = sanitize_name(prompt)
    name = f"{asset_type}_{sanitized}"
    if seed is not None:
        name = f"{name}_{seed}"
    return f"{name}.wav"


def make_batch_filename(prefix: str, index: int) -> str:
    """Generate a numbered filename for batch output."""
    return f"{prefix}_{index:02d}.wav"


def write_wav(
    samples: np.ndarray,
    sample_rate: int,
    path: Path,
) -> Path:
    """Write audio samples to a WAV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), samples, sample_rate, subtype="PCM_16")
    return path


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
    loop_safe: bool = False,
    postprocess_settings: dict | None = None,
) -> tuple[AudioAsset, Path]:
    """Export a single generated audio file with manifest. Returns (asset, manifest_path)."""
    filename = make_single_filename(prompt, asset_type, seed)
    wav_path = output_dir / filename
    write_wav(samples, sample_rate, wav_path)

    # Validate the written WAV is readable
    try:
        sf.info(str(wav_path))
    except Exception as e:
        raise RuntimeError(f"Written WAV failed validation: {wav_path} — {e}")

    asset = analyze_array(samples, sample_rate, wav_path, loop_safe=loop_safe)

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
    loop_safe: bool = False,
    postprocess_settings: dict | None = None,
) -> tuple[list[AudioAsset], Path]:
    """Export a batch of generated audio files with manifest. Returns (assets, manifest_path)."""
    assets: list[AudioAsset] = []

    for i, (samples, sample_rate) in enumerate(results, start=1):
        filename = make_batch_filename(prefix, i)
        wav_path = output_dir / filename
        write_wav(samples, sample_rate, wav_path)

        # Validate the written WAV is readable
        try:
            sf.info(str(wav_path))
        except Exception as e:
            raise RuntimeError(f"Written WAV failed validation: {wav_path} — {e}")

        asset = analyze_array(samples, sample_rate, wav_path, loop_safe=loop_safe)
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
