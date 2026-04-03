"""SoundForge CLI commands."""

from __future__ import annotations

import sys
from pathlib import Path

import click

import soundforge
from soundforge.cli.formatting import (
    error_json,
    make_status_callback,
    output_human,
    output_json,
    status,
)
from soundforge.core.config import SoundForgeConfig


# -- Reusable option decorators --


def global_options(f):
    """Add global options to a command."""
    f = click.option(
        "--output-json", "output_json_flag", is_flag=True, help="Output JSON to stdout."
    )(f)
    f = click.option(
        "--quiet", "-q", is_flag=True, help="Suppress status messages."
    )(f)
    f = click.option(
        "--backend", "-b", default=None, help="Generation backend (default: from config)."
    )(f)
    f = click.option(
        "--config", "config_path", default=None, type=click.Path(), help="Config file path."
    )(f)
    return f


def _iter_audio_files(path: Path) -> list[Path]:
    """Return supported audio files for a file or directory input."""
    if path.is_dir():
        files = sorted(
            file_path
            for pattern in ("*.wav", "*.ogg")
            for file_path in path.glob(pattern)
        )
        return files
    return [path]


# -- CLI group --


class DefaultCommandGroup(click.Group):
    """Route unknown subcommands to 'generate' for shorthand."""

    def parse_args(self, ctx, args):
        if args and not args[0].startswith("-") and args[0] not in self.commands:
            from difflib import get_close_matches

            close = get_close_matches(args[0], self.commands.keys(), n=1, cutoff=0.6)
            if close:
                self.fail(
                    f"Unknown command '{args[0]}'. Did you mean '{close[0]}'?",
                    ctx=ctx,
                )
            args.insert(0, "generate")
        return super().parse_args(ctx, args)


@click.group(cls=DefaultCommandGroup)
@click.version_option(version=soundforge.__version__, prog_name="soundforge")
def cli():
    """SoundForge — AI-powered game audio asset generator."""


# -- info --


@cli.command()
@global_options
def info(output_json_flag, quiet, backend, config_path):
    """Show system info, config, and backend readiness."""
    try:
        cfg = _load_config(config_path, backend=backend)
        from soundforge.core.backends import get_backend

        be = get_backend(cfg.backend, cfg)
        result = soundforge.InfoResult(
            version=soundforge.__version__,
            config_path=str(cfg._config_path) if cfg._config_path else None,
            backend=cfg.backend,
            backend_available=be.is_available(),
            engine=cfg.engine,
            capabilities=be.capabilities(),
        )

        if output_json_flag:
            data = result.to_dict()
            data["backend_info"] = be.info()
            output_json(data)
        else:
            output_human(f"SoundForge v{result.version}")
            output_human(f"  Config: {result.config_path or 'none (using defaults)'}")
            output_human(f"  Backend: {result.backend} ({'ready' if result.backend_available else 'not configured'})")
            output_human(f"  Engine: {result.engine or 'none'}")
            be_info = be.info()
            if result.backend_available:
                if "gpu" in be_info:
                    output_human(f"  GPU: {be_info['gpu']} ({be_info.get('vram_gb', '?')}GB VRAM)")
            else:
                output_human(f"  Status: {be_info.get('status', 'unknown')}")
    except Exception as e:
        _handle_error(e, output_json_flag)


# -- setup --


@cli.command()
@click.option(
    "--backend", "-b", default=None,
    type=click.Choice(["stable-audio", "elevenlabs"], case_sensitive=False),
    help="Backend to set up (default: auto-detect from config).",
)
def setup(backend):
    """Configure SoundForge backend.

    \b
    Examples:
      soundforge setup                     # interactive — picks from config
      soundforge setup --backend stable-audio   # set up local GPU backend
      soundforge setup --backend elevenlabs     # set up ElevenLabs API key
    """
    output_human("SoundForge Setup")
    output_human("-" * 40)

    if backend is None:
        # Auto-detect from config or ask
        try:
            cfg = SoundForgeConfig.load()
            backend = cfg.backend
        except Exception:
            backend = "stable-audio"

        backend = click.prompt(
            "Which backend?",
            type=click.Choice(["stable-audio", "elevenlabs"], case_sensitive=False),
            default=backend,
        )

    if backend == "stable-audio":
        _setup_stable_audio()
    elif backend == "elevenlabs":
        _setup_elevenlabs()


def _setup_stable_audio():
    """Set up the Stable Audio Open local GPU backend."""
    output_human("\nStable Audio Open (local GPU generation)")
    output_human("")

    # Check torch + CUDA
    output_human("Checking GPU dependencies...")
    try:
        import torch
        if not torch.cuda.is_available():
            output_human("  CUDA not available.")
            output_human("  Install PyTorch with CUDA: https://pytorch.org/get-started/locally/")
            return
        gpu = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        output_human(f"  GPU: {gpu} ({vram:.0f}GB VRAM)")
    except ImportError:
        output_human("  torch not installed.")
        output_human("  Run: uv pip install -e \".[local-gpu]\"")
        return

    # Check diffusers
    try:
        import diffusers  # noqa: F401
        output_human("  diffusers: installed")
    except ImportError:
        output_human("  diffusers not installed.")
        output_human("  Run: uv pip install -e \".[local-gpu]\"")
        return

    # Check HuggingFace auth
    output_human("\nChecking HuggingFace authentication...")
    logged_in = False
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        user_info = api.whoami()
        output_human(f"  Logged in as: {user_info.get('name', user_info.get('fullname', 'unknown'))}")
        logged_in = True
    except Exception:
        output_human("  Not logged in to HuggingFace.")
        output_human("")
        output_human("  The Stable Audio Open model requires:")
        output_human("  1. Accept the license at: https://huggingface.co/stabilityai/stable-audio-open-1.0")
        output_human("  2. Log in with a HuggingFace token")
        output_human("     (get one from https://huggingface.co/settings/tokens)")
        output_human("")
        if click.confirm("Log in now?", default=True):
            try:
                from huggingface_hub import login
                login()
                logged_in = True
            except Exception as e:
                output_human(f"  Login failed: {e}")
                output_human("  You can log in later with: uv run huggingface-cli login")
                return
        else:
            output_human("Skipping. Log in later with: uv run huggingface-cli login")
            return

    if not logged_in:
        return

    # Check model access
    output_human("\nChecking model access...")
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        api.model_info("stabilityai/stable-audio-open-1.0")
        output_human("  Model access: granted")
    except Exception:
        output_human("  Cannot access model. Make sure you've accepted the license at:")
        output_human("  https://huggingface.co/stabilityai/stable-audio-open-1.0")
        return

    output_human("\nStable Audio backend is ready!")
    output_human("Generate with: uv run soundforge generate \"coin pickup\" -o test_output/")


def _setup_elevenlabs():
    """Set up the ElevenLabs API backend."""
    output_human("\nElevenLabs API (cloud generation)")
    output_human("")

    api_key = click.prompt("ElevenLabs API key", default="", show_default=False)
    if not api_key:
        output_human("No key provided. Skipping.")
        return

    config_dir = Path.home() / ".config" / "soundforge"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.toml"

    content = f'[backend]\nelevenlabs_api_key = "{api_key}"\n'

    if config_file.exists():
        existing = config_file.read_text()
        if "[backend]" in existing:
            import re
            existing = re.sub(
                r'elevenlabs_api_key\s*=\s*"[^"]*"',
                f'elevenlabs_api_key = "{api_key}"',
                existing,
            )
            content = existing
        else:
            content = existing + "\n" + content

    config_file.write_text(content)
    output_human(f"API key saved to {config_file}")


# -- generate --


@cli.command()
@click.argument("prompt")
@global_options
@click.option("--type", "-t", "asset_type", default=None, type=click.Choice(["sfx", "ui", "ambience", "loop"], case_sensitive=False), help="Asset type.")
@click.option("--duration", "-d", type=float, default=None, help="Duration in seconds (0.5-30).")
@click.option("--loop", is_flag=True, help="Generate a seamless loop.")
@click.option("--prompt-influence", type=float, default=None, help="Prompt adherence (0-1).")
@click.option("--seed", type=int, default=None, help="Seed recorded in manifest and filename (backend support varies).")
@click.option("--engine", "-e", default=None, type=click.Choice(["godot", "unity", "unreal"], case_sensitive=False), help="Engine preset.")
@click.option("--format", "output_format", default=None, type=click.Choice(["wav", "ogg"], case_sensitive=False), help="Export format.")
@click.option("--output", "-o", "output_dir", default=None, type=click.Path(), help="Output directory.")
def generate(
    prompt, output_json_flag, quiet, backend, config_path,
    asset_type, duration, loop, prompt_influence, seed, engine, output_format, output_dir,
):
    """Generate a single sound effect from a text prompt.

    \b
    Examples:
      soundforge generate "coin pickup" --engine godot
      soundforge generate "sword clash" --duration 2.5 -o assets/sfx
      soundforge generate "cave ambience" --type ambience --loop
    """
    try:
        cfg = _load_config(config_path, backend=backend, engine=engine)
        on_status = make_status_callback(quiet)

        from soundforge.core.generate import generate as core_generate

        result = core_generate(
            prompt=prompt,
            asset_type=asset_type or cfg.asset_type,
            duration=duration,
            loop=loop,
            prompt_influence=prompt_influence if prompt_influence is not None else 0.3,
            seed=seed,
            engine=engine or cfg.engine,
            output_dir=Path(output_dir) if output_dir else None,
            output_format=output_format,
            config=cfg,
            on_status=on_status,
        )

        if output_json_flag:
            output_json(result.to_dict())
        else:
            a = result.asset
            output_human(f"Generated: {a.path}")
            output_human(f"  Duration: {a.duration_seconds:.2f}s | {a.sample_rate} Hz | {'mono' if a.channels == 1 else 'stereo'} | Peak: {a.peak_dbfs:.1f} dBFS")
            output_human(f"  Manifest: {result.manifest_path}")

    except Exception as e:
        _handle_error(e, output_json_flag)


# -- batch --


@cli.command()
@click.argument("prompt")
@global_options
@click.option("--count", "-n", type=int, default=None, help="Number of variations (default: from config).")
@click.option("--prefix", "-p", default=None, help="Filename prefix (default: auto from prompt).")
@click.option("--type", "-t", "asset_type", default=None, type=click.Choice(["sfx", "ui", "ambience", "loop"], case_sensitive=False), help="Asset type.")
@click.option("--duration", "-d", type=float, default=None, help="Duration in seconds (0.5-30).")
@click.option("--loop", is_flag=True, help="Generate seamless loops.")
@click.option("--prompt-influence", type=float, default=None, help="Prompt adherence (0-1).")
@click.option("--engine", "-e", default=None, type=click.Choice(["godot", "unity", "unreal"], case_sensitive=False), help="Engine preset.")
@click.option("--format", "output_format", default=None, type=click.Choice(["wav", "ogg"], case_sensitive=False), help="Export format.")
@click.option("--output", "-o", "output_dir", default=None, type=click.Path(), help="Output directory.")
def batch(
    prompt, output_json_flag, quiet, backend, config_path,
    count, prefix, asset_type, duration, loop, prompt_influence, engine, output_format, output_dir,
):
    """Generate multiple variations of a sound effect.

    \b
    Examples:
      soundforge batch "sword hit" --count 8 --prefix sfx_sword
      soundforge batch "footstep" -n 4 --engine unity -o assets/audio
      soundforge batch "rain loop" --type ambience --loop
    """
    try:
        cfg = _load_config(config_path, backend=backend, engine=engine)
        on_status = make_status_callback(quiet)

        from soundforge.core.batch import batch_generate

        result = batch_generate(
            prompt=prompt,
            count=count or cfg.variations,
            prefix=prefix,
            asset_type=asset_type or cfg.asset_type,
            duration=duration,
            loop=loop,
            prompt_influence=prompt_influence if prompt_influence is not None else 0.3,
            engine=engine or cfg.engine,
            output_dir=Path(output_dir) if output_dir else None,
            output_format=output_format,
            config=cfg,
            on_status=on_status,
        )

        if output_json_flag:
            output_json(result.to_dict())
        else:
            output_human(f"Batch complete: {len(result.results)} files")
            for r in result.results:
                a = r.asset
                output_human(f"  {a.path.name}  ({a.duration_seconds:.2f}s, {a.peak_dbfs:.1f} dBFS)")
            output_human(f"  Manifest: {result.manifest_path}")

    except Exception as e:
        _handle_error(e, output_json_flag)


# -- process --


@cli.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@global_options
@click.option("--no-trim", is_flag=True, help="Skip silence trimming.")
@click.option("--fade-in", type=float, default=None, help="Fade-in duration in seconds.")
@click.option("--fade-out", type=float, default=None, help="Fade-out duration in seconds.")
@click.option("--normalize", type=float, default=None, help="Target peak dBFS (e.g. -1.0).")
@click.option("--no-normalize", is_flag=True, help="Skip normalization.")
@click.option("--sample-rate", type=int, default=None, help="Target sample rate.")
@click.option("--channels", type=int, default=None, help="Target channels (1=mono, 2=stereo).")
@click.option("--loop-smooth", is_flag=True, help="Apply loop-safe crossfade smoothing.")
@click.option("--format", "output_format", default=None, type=click.Choice(["wav", "ogg"], case_sensitive=False), help="Export format.")
@click.option("--output", "-o", "output_dir", default=None, type=click.Path(), help="Output directory.")
def process(
    paths, output_json_flag, quiet, backend, config_path,
    no_trim, fade_in, fade_out, normalize, no_normalize,
    sample_rate, channels, loop_smooth, output_format, output_dir,
):
    """Postprocess existing audio files (trim, fade, normalize, resample).

    \b
    Examples:
      soundforge process raw/*.wav --normalize -1
      soundforge process audio.wav --sample-rate 44100 --channels 1
      soundforge process track.wav --loop-smooth -o processed/
      soundforge process *.wav --no-trim --fade-in 0.05 --fade-out 0.1
    """
    try:
        cfg = _load_config(config_path)
        on_status = make_status_callback(quiet)
        resolved_format = (output_format or cfg.resolve_format()).lower()

        from soundforge.core.analysis import read_audio
        from soundforge.core.export import write_audio
        from soundforge.core.postprocess import run_pipeline

        results = []

        for path_str in paths:
            path = Path(path_str)
            wav_files = _iter_audio_files(path)

            for wav_path in wav_files:
                if on_status:
                    on_status(f"Processing: {wav_path.name}")

                samples, sr = read_audio(wav_path)

                target_peak = cfg.target_peak_dbfs
                if normalize is not None:
                    target_peak = normalize

                samples, sr = run_pipeline(
                    samples,
                    sr,
                    trim=not no_trim and cfg.trim_silence,
                    fade_in_sec=fade_in if fade_in is not None else cfg.fade_in,
                    fade_out_sec=fade_out if fade_out is not None else cfg.fade_out,
                    normalize=not no_normalize and cfg.normalize,
                    target_peak_dbfs=target_peak,
                    target_sample_rate=sample_rate,
                    target_channels=channels,
                    loop=loop_smooth,
                    on_status=on_status if not quiet else None,
                )

                if output_dir:
                    out_dir = Path(output_dir)
                else:
                    # Avoid overwriting input: default to processed/ subdirectory
                    out_dir = wav_path.parent / "processed"
                    if on_status and out_dir != wav_path.parent:
                        on_status("No --output specified, writing to processed/")
                out_path = out_dir / f"{wav_path.stem}.{resolved_format}"
                write_audio(samples, sr, out_path, audio_format=resolved_format)

                from soundforge.core.analysis import analyze_file
                info = analyze_file(out_path)
                results.append(info.to_dict())

                if on_status:
                    on_status(f"  → {out_path} ({info.duration_seconds:.2f}s, {info.peak_dbfs:.1f} dBFS)")

        if output_json_flag:
            output_json({"processed": results})
        elif not quiet:
            output_human(f"Processed {len(results)} file(s)")

    except Exception as e:
        _handle_error(e, output_json_flag)


# -- preview --


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@global_options
def preview(path, output_json_flag, quiet, backend, config_path):
    """Play an audio file through the default audio device."""
    try:
        from soundforge.core.preview import play_file
        from soundforge.core.analysis import analyze_file

        file_path = Path(path)
        info = analyze_file(file_path)

        if not quiet:
            output_human(f"Playing: {file_path.name} ({info.duration_seconds:.2f}s)")

        play_file(file_path)

        if output_json_flag:
            output_json(info.to_dict())
        elif not quiet:
            output_human("Playback complete.")

    except Exception as e:
        _handle_error(e, output_json_flag)


# -- inspect --


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@global_options
def inspect(path, output_json_flag, quiet, backend, config_path):
    """Show audio file metadata (duration, sample rate, channels, peak).

    \b
    Examples:
      soundforge inspect assets/audio/sfx_coin.wav
      soundforge inspect assets/audio/           # inspect all WAVs in dir
      soundforge inspect track.wav --output-json
    """
    try:
        from soundforge.core.analysis import analyze_file

        file_path = Path(path)

        if file_path.is_dir():
            wav_files = _iter_audio_files(file_path)
            if not wav_files:
                raise click.ClickException(f"No supported audio files found in {file_path}")

            results = [analyze_file(f) for f in wav_files]

            if output_json_flag:
                output_json({"files": [r.to_dict() for r in results]})
            else:
                output_human(f"{'File':<30} {'Duration':>8} {'Rate':>6} {'Ch':>3} {'Peak dBFS':>10}")
                output_human("-" * 62)
                for r in results:
                    output_human(
                        f"{r.path.name:<30} {r.duration_seconds:>7.2f}s {r.sample_rate:>6} {r.channels:>3} {r.peak_dbfs:>9.1f}"
                    )
        else:
            result = analyze_file(file_path)

            if output_json_flag:
                output_json(result.to_dict())
            else:
                output_human(f"File: {result.path.name}")
                output_human(f"  Duration:    {result.duration_seconds:.3f}s")
                output_human(f"  Sample rate: {result.sample_rate} Hz")
                output_human(f"  Channels:    {result.channels}")
                output_human(f"  Peak:        {result.peak_dbfs:.1f} dBFS")
                output_human(f"  Format:      {result.format_info}")

    except Exception as e:
        _handle_error(e, output_json_flag)


# -- pack --


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@global_options
@click.option("--name", "-n", required=True, help="Pack name for manifest and archive.")
@click.option("--type", "-t", "asset_type", default="sfx", type=click.Choice(["sfx", "ui", "ambience", "loop"], case_sensitive=False), help="Asset type.")
@click.option("--engine", "-e", default=None, type=click.Choice(["godot", "unity", "unreal"], case_sensitive=False), help="Engine preset.")
@click.option("--zip", "create_zip", is_flag=True, help="Create a zip archive of the pack.")
def pack(path, output_json_flag, quiet, backend, config_path, name, asset_type, engine, create_zip):
    """Build a manifest (and optional zip) from a directory of audio files.

    \b
    Examples:
      soundforge pack assets/coins/ --name coin_pickups
      soundforge pack audio/sfx/ --name ui_pack --type ui --zip
      soundforge pack sounds/ --name ambient --engine godot --zip
    """
    try:
        from soundforge.core.pack import build_pack

        dir_path = Path(path)
        if not dir_path.is_dir():
            raise click.ClickException(f"{path} is not a directory")

        on_status = make_status_callback(quiet)
        if on_status:
            on_status(f"Packing: {dir_path}")

        manifest_path, zip_path = build_pack(
            directory=dir_path,
            name=name,
            asset_type=asset_type,
            engine=engine,
            create_zip=create_zip,
        )

        if output_json_flag:
            data = {"manifest": str(manifest_path)}
            if zip_path:
                data["archive"] = str(zip_path)
            output_json(data)
        else:
            output_human(f"Manifest: {manifest_path}")
            if zip_path:
                output_human(f"Archive: {zip_path}")

    except Exception as e:
        _handle_error(e, output_json_flag)


# -- Helpers --


def _load_config(
    config_path: str | None,
    backend: str | None = None,
    engine: str | None = None,
) -> SoundForgeConfig:
    """Load config and apply CLI overrides."""
    cfg = SoundForgeConfig.load(Path(config_path) if config_path else None)
    overrides = {}
    if backend:
        overrides["backend"] = backend
    if engine:
        overrides["engine"] = engine
    if overrides:
        cfg = cfg.merge_cli_args(**overrides)
    return cfg


def _handle_error(e: Exception, output_json_flag: bool) -> None:
    """Handle errors consistently."""
    if output_json_flag:
        error_json(str(e))
    else:
        output_human(f"Error: {e}")
    sys.exit(1)
