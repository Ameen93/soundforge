"""Batch variation generation."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from soundforge.core.backends import get_backend
from soundforge.core.config import SoundForgeConfig
from soundforge.core.export import export_batch, sanitize_name
from soundforge.core.postprocess import run_pipeline
from soundforge.core.types import BatchResult, GenerateResult
from soundforge.core.validation import validate_generation_request


def batch_generate(
    prompt: str,
    *,
    count: int = 4,
    prefix: str | None = None,
    asset_type: str = "sfx",
    duration: float | None = None,
    loop: bool = False,
    prompt_influence: float = 0.3,
    engine: str | None = None,
    output_dir: Path | None = None,
    output_format: str | None = None,
    config: SoundForgeConfig | None = None,
    on_status: Callable[[str], None] | None = None,
) -> BatchResult:
    """Generate multiple variations of an audio asset.

    Returns a BatchResult with all exported files and manifest.
    """
    cfg = config or SoundForgeConfig.load()

    use_engine = engine or cfg.engine
    use_asset_type = asset_type or cfg.asset_type
    use_duration = duration if duration is not None else cfg.duration
    use_output = output_dir or cfg.resolve_output_dir()
    use_prefix = prefix or f"{use_asset_type}_{sanitize_name(prompt, max_length=20)}"
    use_format = output_format or cfg.resolve_format()
    target_sr = cfg.resolve_sample_rate()
    target_ch = cfg.resolve_channels()

    backend = get_backend(cfg.backend, cfg)
    capabilities = backend.capabilities()
    # Determine loop behavior: explicit --loop flag OR loop/ambience asset type
    is_loop = loop or use_asset_type in ("ambience", "loop")
    use_duration = validate_generation_request(
        backend_name=cfg.backend,
        capabilities=capabilities,
        duration=use_duration,
        loop=is_loop,
        on_status=on_status,
    )

    processed_results: list[tuple] = []
    orig_sample_rate = None
    orig_channels = None

    try:
        for i in range(1, count + 1):
            if on_status:
                on_status(f"Generating variation {i}/{count}...")

            samples, sample_rate = backend.generate(
                text=prompt,
                duration_seconds=use_duration,
                loop=is_loop,
                prompt_influence=prompt_influence,
                seed=None,
                on_status=None,  # suppress per-generation status in batch
            )

            # Capture pre-processing state from first variation
            if orig_sample_rate is None:
                orig_sample_rate = sample_rate
                orig_channels = samples.shape[1] if samples.ndim == 2 else 1

            # Postprocess each variation
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
                on_status=None,
            )

            processed_results.append((samples, sample_rate))
    finally:
        backend.cleanup()

    if on_status:
        on_status(f"Exporting {count} files...")

    final_channels = (
        processed_results[0][0].shape[1]
        if processed_results and processed_results[0][0].ndim == 2
        else 1
    ) if processed_results else orig_channels

    postprocess_settings = {
        "trim": cfg.trim_silence,
        "normalize": cfg.target_peak_dbfs if cfg.normalize else None,
        "fade_in": cfg.fade_in,
        "fade_out": cfg.fade_out,
        "loop_smooth": is_loop,
        "sample_rate_conversion": (
            {"from": orig_sample_rate, "to": sample_rate}
            if orig_sample_rate is not None and orig_sample_rate != sample_rate else None
        ),
        "channel_conversion": (
            {"from": orig_channels, "to": final_channels}
            if orig_channels is not None and orig_channels != final_channels else None
        ),
    }

    assets, manifest_path = export_batch(
        results=processed_results,
        output_dir=use_output,
        prefix=use_prefix,
        prompt=prompt,
        asset_type=use_asset_type,
        engine=use_engine,
        backend=cfg.backend,
        audio_format=use_format,
        loop_safe=is_loop,
        postprocess_settings=postprocess_settings,
    )

    results = [
        GenerateResult(
            asset=asset,
            backend=cfg.backend,
            prompt_used=prompt,
        )
        for asset in assets
    ]

    if on_status:
        on_status(f"Batch complete: {count} files + manifest")

    return BatchResult(
        results=results,
        pack_name=use_prefix,
        manifest_path=manifest_path,
    )
