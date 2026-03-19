# CLAUDE.md

## Project

SoundForge — AI-powered game audio asset generator. CLI + core library for generating, cleaning, and packaging game sound effects and ambient loops from text prompts. Companion to PixelForge.

## Status: v0 Complete

Working CLI with two backends (Stable Audio Open local GPU + ElevenLabs API), postprocessing pipeline, engine presets, and pack export. BMAD planning artifacts in `_bmad-output/soundforge/`.

## Stack

Python 3.12+, Click CLI, httpx, numpy, soundfile, scipy (optional), sounddevice (optional), hatchling (build), uv (package manager). Optional GPU deps: torch, diffusers, transformers, accelerate, torchsde.

## Commands

```bash
cd soundforge
uv sync                                                              # Install deps
uv pip install -e ".[local-gpu]"                                     # Install GPU deps
uv run soundforge setup                                              # Configure backend + HuggingFace auth
uv run soundforge info                                               # Check setup
uv run soundforge generate "coin pickup" --engine godot -o assets/audio  # Single SFX
uv run soundforge batch "sword hit" --count 8 --prefix sfx_sword -e unity  # Variations
uv run soundforge process raw/*.wav --normalize -1 --sample-rate 44100  # Clean existing files
uv run soundforge inspect assets/audio/                              # View metadata
uv run soundforge preview assets/audio/sfx_coin_01.wav               # Play audio
uv run soundforge pack assets/audio/coins/ --name coin_pickups --zip  # Pack + archive
```

All commands support `--output-json` for structured output and `--quiet` for agent use.

## Architecture

### Core principle: clean separation

```
soundforge/core/     — Pure library. No IO, no prints, no CLI deps. Returns dataclasses.
soundforge/cli/      — Thin Click wrapper. Formats core results for humans or JSON.
```

### Pipeline

Text prompt → backend (Stable Audio Open or ElevenLabs) → postprocess (trim, fade, normalize, resample) → WAV + manifest

### Backends

- **`stable-audio`** (default) — Local GPU generation via Stable Audio Open 1.0. Outputs 44.1 kHz stereo. Requires CUDA GPU + HuggingFace auth. Model lazy-loaded on first generate. Config via `[backend.stable-audio]` TOML section.
- **`elevenlabs`** — Cloud API generation. Requires API key. Outputs 44.1 kHz MP3 decoded to numpy.

Backend interface: `GenerationBackend` ABC in `backends/__init__.py`. Factory: `get_backend(name, config)`. Backends return `(ndarray float64, sample_rate)`.

### Key modules (`soundforge/core/`)

- **types.py** — `GenerateResult`, `BatchResult`, `InspectResult`, `InfoResult` dataclasses
- **config.py** — `SoundForgeConfig`, `.soundforge.toml` loading, engine presets, `_backend_settings` for per-backend config
- **generate.py** — Single generation pipeline
- **batch.py** — Batch variation generation
- **postprocess.py** — Trim, fade, normalize, resample, channel convert, loop smooth
- **analysis.py** — Audio metadata extraction (duration, peak, sample rate)
- **export.py** — WAV writing, manifest JSON, file naming
- **pack.py** — Pack assembly from existing directory
- **preview.py** — Audio playback
- **backends/** — `GenerationBackend` ABC + `stable_audio.py` + `elevenlabs.py`

### Configuration

- `.soundforge.toml` — project-level config (discovered walking up dirs)
- `~/.config/soundforge/config.toml` — global fallback
- `[backend.stable-audio]` — local backend settings (steps, guidance_scale, negative_prompt, model_path)
- `ELEVENLABS_API_KEY` env var — API key for ElevenLabs backend
- Engine presets: `godot` (44100/mono), `unity` (44100/mono), `unreal` (48000/mono)

## Conventions

- Core functions return structured dataclasses, never print or write files
- Status updates via optional `on_status` callback (CLI routes to stderr)
- `--output-json` outputs to stdout; human messages to stderr
- Backend interface returns `(ndarray, sample_rate)`, never file paths
- All generated files have deterministic names
- GPU deps (torch, diffusers) are optional — imported lazily inside methods

## Tests

```bash
uv run pytest
uv run pytest --cov=soundforge
```

181 tests, 86% coverage. Backend tests mock torch/diffusers so they run without a GPU.
