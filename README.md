# SoundForge

AI-powered game audio asset generator. Generate, process, and package game sound effects from text prompts — locally on your GPU or via cloud API — with engine-aware export for Godot, Unity, and Unreal.

## Installation

```bash
# With uv (recommended)
uv sync

# Local GPU generation (requires NVIDIA GPU with CUDA)
uv pip install -e ".[local-gpu]"

# With pip
pip install -e .
pip install -e ".[local-gpu]"    # for GPU generation

# Optional: audio preview + resampling
pip install -e ".[preview,resample]"
```

## Quick Start

```bash
# 1. Set up backend (checks GPU, HuggingFace auth, model access)
uv run soundforge setup

# 2. Generate a sound effect
uv run soundforge generate "coin pickup" --engine godot -o assets/audio/

# 3. Generate variations
uv run soundforge batch "sword clash" --count 4 --prefix sfx_sword

# 4. Check system status
uv run soundforge info
```

## Backends

| Backend | Type | Output | Cost | Setup |
|---------|------|--------|------|-------|
| **stable-audio** (default) | Local GPU | 44.1 kHz stereo | Free | CUDA GPU + HuggingFace account |
| **elevenlabs** | Cloud API | 44.1 kHz | Paid | API key |

Switch backends with `--backend` or set `default` in `.soundforge.toml`:

```bash
uv run soundforge generate "coin pickup" --backend stable-audio
uv run soundforge generate "coin pickup" --backend elevenlabs
```

### Stable Audio Open (local)

Uses [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0) via diffusers. Requires:
- NVIDIA GPU with 12GB+ VRAM
- `uv pip install -e ".[local-gpu]"`
- HuggingFace account with model license accepted
- Run `uv run soundforge setup` to configure

The model (~4GB) downloads on first generation and is cached locally. Generation takes ~6-12s per sound effect.

### ElevenLabs (cloud)

Uses the [ElevenLabs Sound Effects API](https://elevenlabs.io). Requires an API key — run `uv run soundforge setup --backend elevenlabs` to configure.

## Commands

### generate

Generate a single sound effect from a text prompt.

```bash
soundforge generate "coin pickup" --engine godot
soundforge generate "sword clash" --duration 2.5 -o assets/sfx
soundforge generate "cave ambience" --type ambience --loop
```

### batch

Generate multiple variations of a sound effect.

```bash
soundforge batch "sword hit" --count 8 --prefix sfx_sword
soundforge batch "footstep" -n 4 --engine unity -o assets/audio
soundforge batch "rain loop" --type ambience --loop
```

### process

Postprocess existing audio files (trim, fade, normalize, resample).

```bash
soundforge process raw/*.wav --normalize -1
soundforge process audio.wav --sample-rate 44100 --channels 1
soundforge process track.wav --loop-smooth -o processed/
```

### inspect

Show audio file metadata.

```bash
soundforge inspect assets/audio/sfx_coin.wav
soundforge inspect assets/audio/           # all WAVs in directory
```

### preview

Play an audio file through the default audio device.

```bash
soundforge preview assets/audio/sfx_coin_01.wav
```

### pack

Build a manifest (and optional zip) from a directory of audio files.

```bash
soundforge pack assets/coins/ --name coin_pickups
soundforge pack audio/sfx/ --name ui_pack --type ui --zip
```

### info

Show system info, config, and backend readiness.

```bash
soundforge info
soundforge info --output-json
```

### setup

Configure SoundForge backend (GPU check, HuggingFace auth, or API key).

```bash
soundforge setup                          # interactive
soundforge setup --backend stable-audio   # local GPU setup
soundforge setup --backend elevenlabs     # cloud API setup
```

All commands support `--output-json` for structured output and `--quiet` for agent/CI use.

## Configuration

Create a `.soundforge.toml` in your project root (or copy from `.soundforge.toml.example`):

```toml
[defaults]
engine = "godot"
asset_type = "sfx"
duration = 2.0
variations = 4

[backend]
default = "stable-audio"   # stable-audio | elevenlabs
elevenlabs_api_key = ""    # for elevenlabs backend

[backend.stable-audio]
# num_inference_steps = 100       # override prompt_influence mapping
# negative_prompt = "low quality, distorted, noise"
# guidance_scale = 7.0
# model_path = "/path/to/local/model"

[postprocess]
trim_silence = true
fade_in = 0.01
fade_out = 0.05
normalize = true
target_peak_dbfs = -1.0

# Override engine presets
[engine.godot]
sample_rate = 44100
channels = 1
```

Config is discovered by walking up directories from cwd, falling back to `~/.config/soundforge/config.toml`.

## Engine Presets

| Engine | Sample Rate | Channels | Output Dir |
|--------|-------------|----------|------------|
| Godot  | 44100 Hz    | Mono     | `audio/sfx` |
| Unity  | 44100 Hz    | Mono     | `Assets/Audio/SFX` |
| Unreal | 48000 Hz    | Mono     | `Content/Audio/SFX` |

Presets can be overridden in `.soundforge.toml` with `[engine.<name>]` sections.

## Architecture

```
soundforge/core/     — Pure library. Returns dataclasses, no IO or CLI deps.
soundforge/cli/      — Thin Click wrapper. Formats core results for humans or JSON.
```

Pipeline: text prompt → backend (Stable Audio Open / ElevenLabs) → postprocess (trim, fade, normalize, resample) → WAV + manifest JSON

## Development

```bash
uv sync --all-extras
uv run pytest                                    # run tests
uv run pytest --cov=soundforge --cov-report=term-missing  # with coverage
```
