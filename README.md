# SoundForge

AI-powered game audio asset generator for developers. SoundForge is a Python CLI plus reusable core library for generating, postprocessing, inspecting, previewing, and packaging short-form game audio.

It is optimized for:
- one-shot SFX
- UI sounds
- short ambience clips
- loop-intended assets
- deterministic exports for Godot, Unity, and Unreal

The product thesis is workflow, not just generation: prompt a sound, clean it up, export it with sane defaults, and hand an engine-ready manifest to a developer or agent.

## Status

Current state:
- v0 CLI is implemented and tested
- 2 generation backends: `stable-audio` and `elevenlabs`
- postprocessing pipeline: trim, fades, normalize, channel convert, resample, loop smoothing
- engine presets: Godot, Unity, Unreal
- manifest and pack export
- 181 tests passing

## Installation

```bash
# Base install
uv sync

# Local GPU generation support
uv pip install -e ".[local-gpu]"

# Optional preview + resampling extras
uv pip install -e ".[preview,resample]"
```

With `pip`:

```bash
pip install -e .
pip install -e ".[local-gpu]"
pip install -e ".[preview,resample]"
```

## Quick Start

```bash
# 1. Check backend readiness
uv run soundforge info

# 2. Configure a backend if needed
uv run soundforge setup

# 3. Generate a single asset
uv run soundforge generate "coin pickup" --engine godot -o assets/audio

# 4. Generate a batch of variations
uv run soundforge batch "sword clash" --count 4 --prefix sfx_sword

# 5. Inspect or preview output
uv run soundforge inspect assets/audio/
uv run soundforge preview assets/audio/sfx_coin_pickup.wav
```

## Backends

| Backend | Mode | Notes |
|--------|------|-------|
| `stable-audio` | Local GPU | Stable Audio Open 1.0 via diffusers. Supports seed. Requires CUDA GPU and model access. |
| `elevenlabs` | Cloud API | ElevenLabs sound generation API. Requires API key. Supports loop flag. |

Switch at runtime:

```bash
uv run soundforge generate "coin pickup" --backend stable-audio
uv run soundforge generate "coin pickup" --backend elevenlabs
```

### Stable Audio Open

Requirements:
- NVIDIA GPU with CUDA
- `uv pip install -e ".[local-gpu]"`
- HuggingFace account and accepted model license

Useful command:

```bash
uv run soundforge setup --backend stable-audio
```

### ElevenLabs

Requirements:
- ElevenLabs API key

Useful command:

```bash
uv run soundforge setup --backend elevenlabs
```

Or set:

```bash
export ELEVENLABS_API_KEY=...
```

## Commands

### `generate`

Generate one audio asset from a text prompt.

```bash
soundforge generate "coin pickup" --engine godot
soundforge generate "sword clash" --duration 2.5 -o assets/sfx
soundforge generate "cave ambience" --type ambience --loop
soundforge generate "magic chime" --seed 42
```

### `batch`

Generate multiple variations.

```bash
soundforge batch "sword hit" --count 8 --prefix sfx_sword
soundforge batch "footstep" -n 4 --engine unity -o assets/audio
soundforge batch "rain loop" --type ambience --loop
```

### `process`

Postprocess existing WAV files. By default, writes to a `processed/` subdirectory instead of overwriting the source.

```bash
soundforge process raw/*.wav --normalize -1
soundforge process audio.wav --sample-rate 44100 --channels 1
soundforge process track.wav --loop-smooth -o processed/
```

### `inspect`

Inspect one WAV file or all WAVs in a directory.

```bash
soundforge inspect assets/audio/sfx_coin.wav
soundforge inspect assets/audio/
soundforge inspect assets/audio/ --output-json
```

### `preview`

Play a file through the default audio device.

```bash
soundforge preview assets/audio/sfx_coin_01.wav
```

Requires the optional preview dependency.

### `pack`

Build a manifest from a directory of WAV files and optionally zip the pack.

```bash
soundforge pack assets/coins/ --name coin_pickups
soundforge pack audio/sfx/ --name ui_pack --type ui --zip
```

### `info`

Show config, backend readiness, and capabilities.

```bash
soundforge info
soundforge info --output-json
```

### `setup`

Configure either backend.

```bash
soundforge setup
soundforge setup --backend stable-audio
soundforge setup --backend elevenlabs
```

All commands support `--output-json` for machine-readable output and `--quiet` for agent or CI use.

## Configuration

SoundForge discovers `.soundforge.toml` by walking up from the current directory. If none is found, it falls back to `~/.config/soundforge/config.toml`.

Example:

```toml
[defaults]
engine = "godot"
asset_type = "sfx"
duration = 2.0
variations = 4

[backend]
default = "stable-audio"
elevenlabs_api_key = ""

[backend.stable-audio]
# num_inference_steps = 100
# negative_prompt = "low quality, distorted, noise"
# guidance_scale = 7.0
# model_path = "stabilityai/stable-audio-open-1.0"

[postprocess]
trim_silence = true
fade_in = 0.01
fade_out = 0.05
normalize = true
target_peak_dbfs = -1.0

[engine.godot]
sample_rate = 44100
channels = 1
output_dir = "audio/sfx"
```

Environment variables:
- `ELEVENLABS_API_KEY`

## Engine Presets

| Engine | Sample Rate | Channels | Default Output Dir |
|--------|-------------|----------|--------------------|
| Godot | 44100 Hz | Mono | `audio/sfx` |
| Unity | 44100 Hz | Mono | `Assets/Audio/SFX` |
| Unreal | 48000 Hz | Mono | `Content/Audio/SFX` |

These presets can be overridden in config with `[engine.<name>]`.

## Architecture

```text
soundforge/cli/   Thin Click wrapper
soundforge/core/  Reusable application logic
tests/            End-to-end and module tests
docs/             Product, architecture, and maintenance notes
```

Pipeline:

```text
prompt
  -> backend
  -> postprocess
  -> WAV export
  -> manifest JSON
```

## Development

```bash
uv sync --all-extras
uv run pytest
uv run pytest --cov=soundforge --cov-report=term-missing
```

Primary docs for maintainers:
- `docs/PROJECT_OVERVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/TODO.md`
