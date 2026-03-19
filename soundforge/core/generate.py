"""Single audio asset generation pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from soundforge.core.backends import get_backend
from soundforge.core.config import SoundForgeConfig
from soundforge.core.export import export_single
from soundforge.core.postprocess import run_pipeline
from soundforge.core.types import GenerateResult


def generate(
    prompt: str,
    *,
    asset_type: str = "sfx",
    duration: float | None = None,
    loop: bool = False,
    prompt_influence: float = 0.3,
    seed: int | None = None,
    engine: str | None = None,
    output_dir: Path | None = None,
    config: SoundForgeConfig | None = None,
    on_status: Callable[[str], None] | None = None,
) -> GenerateResult:
    """Generate a single audio asset from a text prompt.

    Returns a GenerateResult with the exported file path and metadata.
    """
    cfg = config or SoundForgeConfig.load()

    # Resolve parameters from config where not explicitly set
    use_engine = engine or cfg.engine
    use_asset_type = asset_type or cfg.asset_type
    use_duration = duration if duration is not None else cfg.duration
    use_output = output_dir or cfg.resolve_output_dir()
    target_sr = cfg.resolve_sample_rate()
    target_ch = cfg.resolve_channels()

    # Get backend and generate
    backend = get_backend(cfg.backend, cfg)

    if seed is not None and not backend.capabilities().get("supports_seed", False):
        if on_status:
            on_status(
                f"Warning: backend '{cfg.backend}' does not support seeds — "
                "seed will be recorded in manifest but won't affect generation"
            )

    # Determine loop behavior: explicit --loop flag OR loop/ambience asset type
    is_loop = loop or use_asset_type in ("ambience", "loop")

    samples, sample_rate = backend.generate(
        text=prompt,
        duration_seconds=use_duration,
        loop=is_loop,
        prompt_influence=prompt_influence,
        seed=seed,
        on_status=on_status,
    )

    # Capture pre-processing state for manifest tracking
    orig_sample_rate = sample_rate
    orig_channels = samples.shape[1] if samples.ndim == 2 else 1
    samples, sample_rate = run_pipeline(
        samples,
        sample_rate,
        trim=cfg.trim_silence,
        fade_in_sec=cfg.fade_in,
        fade_out_sec=cfg.fade_out,
        normalize=cfg.normalize,
        target_peak_dbfs=cfg.target_peak_dbfs,
        target_sample_rate=target_sr,
        target_channels=target_ch,
        loop=is_loop,
        on_status=on_status,
    )

    # Export
    final_channels = samples.shape[1] if samples.ndim == 2 else 1
    postprocess_settings = {
        "trim": cfg.trim_silence,
        "normalize": cfg.target_peak_dbfs if cfg.normalize else None,
        "fade_in": cfg.fade_in,
        "fade_out": cfg.fade_out,
        "loop_smooth": is_loop,
        "sample_rate_conversion": (
            {"from": orig_sample_rate, "to": sample_rate}
            if orig_sample_rate != sample_rate else None
        ),
        "channel_conversion": (
            {"from": orig_channels, "to": final_channels}
            if orig_channels != final_channels else None
        ),
    }

    asset, manifest_path = export_single(
        samples=samples,
        sample_rate=sample_rate,
        output_dir=use_output,
        prompt=prompt,
        asset_type=use_asset_type,
        engine=use_engine,
        backend=cfg.backend,
        seed=seed,
        loop_safe=is_loop,
        postprocess_settings=postprocess_settings,
    )

    if on_status:
        on_status(f"Exported: {asset.path}")

    return GenerateResult(
        asset=asset,
        backend=cfg.backend,
        prompt_used=prompt,
        seed=seed,
        manifest_path=manifest_path,
    )
