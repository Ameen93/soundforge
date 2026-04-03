---
project: soundforge
type: architecture
status: current
last_updated: 2026-03-29
tags: soundforge, architecture, audio, cli, backends, gamedev
---

# Architecture

## Goal

Keep SoundForge as a reusable core library with a thin CLI wrapper so the same logic can support:
- terminal workflows
- agent workflows
- future APIs
- future editor or web integrations

## System Shape

```text
user prompt
  -> CLI
  -> config resolution
  -> backend selection
  -> generation
  -> postprocess pipeline
  -> WAV export
  -> manifest output
```

## Package Layout

```text
soundforge/
├── soundforge/
│   ├── __init__.py
│   ├── py.typed
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   └── formatting.py
│   └── core/
│       ├── __init__.py
│       ├── analysis.py
│       ├── batch.py
│       ├── config.py
│       ├── export.py
│       ├── generate.py
│       ├── pack.py
│       ├── postprocess.py
│       ├── preview.py
│       ├── types.py
│       └── backends/
│           ├── __init__.py
│           ├── elevenlabs.py
│           └── stable_audio.py
└── tests/
```

## Separation Of Concerns

### CLI

CLI responsibilities:
- Click argument parsing
- config loading and CLI overrides
- human-readable output
- JSON output
- process exit behavior

Key file:
- `soundforge/cli/commands.py`

### Core

Core responsibilities:
- backend selection
- generation orchestration
- postprocessing
- analysis
- export and pack assembly

Core modules are imported by the CLI and can also be used directly.

## Request Flow

### Single generation

`generate` command flow:

1. load config
2. resolve engine preset and output defaults
3. instantiate backend
4. generate `(samples, sample_rate)`
5. run postprocess pipeline
6. write WAV
7. write manifest
8. return `GenerateResult`

Primary implementation:
- `soundforge/core/generate.py`

### Batch generation

`batch` command flow:

1. load config
2. resolve defaults
3. instantiate backend once
4. generate `N` variations
5. postprocess each result
6. export numbered WAV files
7. write one manifest for the pack
8. return `BatchResult`

Primary implementation:
- `soundforge/core/batch.py`

## Core Modules

### `config.py`

Responsibilities:
- find `.soundforge.toml`
- fall back to global config
- resolve engine presets
- collect backend-specific settings
- apply environment overrides

### `types.py`

Current shipped types:
- `AudioAsset`
- `GenerateResult`
- `BatchResult`
- `InspectResult`
- `InfoResult`

These are intentionally small and oriented around CLI and export workflows.

### `generate.py`

Single generation pipeline:
- parameter resolution
- seed support warning if backend cannot honor it
- loop intent detection
- postprocess manifest metadata assembly
- export handoff

### `batch.py`

Batch workflow:
- deterministic prefix selection
- repeated backend generation
- shared export manifest
- numbered output file naming

### `postprocess.py`

Current pipeline stages:
- silence trim
- loop smoothing
- fades
- peak normalization
- channel conversion
- resampling

This is a first-class subsystem, not a minor add-on. It is where a large share of the practical workflow value lives.

### `analysis.py`

Current analysis support:
- duration
- sample rate
- channel count
- peak dBFS
- file read helpers

### `export.py`

Responsibilities:
- sanitize names
- make deterministic filenames
- write WAV files
- validate written files
- write manifests with relative paths

### `pack.py`

Responsibilities:
- read existing WAV directories
- build manifest from analyzed files
- optionally create a zip archive

### `preview.py`

Simple playback helpers around `sounddevice`.

## Backends

All generation backends implement the shared `GenerationBackend` interface in `soundforge/core/backends/__init__.py`.

Required methods:
- `generate(...) -> tuple[np.ndarray, int]`
- `is_available()`
- `info()`
- `capabilities()`

### `elevenlabs`

Characteristics:
- cloud API backend
- requires API key
- supports loop flag
- does not support seed
- returns decoded audio arrays for local processing

### `stable-audio`

Characteristics:
- local GPU backend
- Stable Audio Open 1.0 via diffusers
- supports seed
- requires CUDA and model access
- lazy-loads the model on first generation

## Configuration Model

Config discovery order:

1. explicit `--config`
2. nearest `.soundforge.toml` walking upward
3. `~/.config/soundforge/config.toml`
4. built-in defaults

Config domains:
- defaults
- backend selection
- backend-specific settings
- postprocess defaults
- engine preset overrides

## Output Model

Current exported artifacts:
- WAV files
- manifest JSON
- optional pack zip archives

Manifest content includes:
- pack or asset name
- asset type
- engine
- backend
- prompt
- generated timestamp
- file metadata
- postprocess settings

## Invariants

- human-readable output goes to stderr
- JSON output goes to stdout
- generated file names are deterministic from prompt, type, prefix, and seed
- backends return arrays, not file paths
- optional dependencies are imported lazily where practical

## Known Constraints

- no OGG export yet
- no LUFS analysis yet
- no structured request object yet
- no backend fallback orchestration yet
- loop capability is not centrally preflight-validated across all backends

## Extension Points

The safest additions are:
- new backends implementing `GenerationBackend`
- richer analysis metadata
- additional export formats
- stronger loop validation
- structured request types once API reuse becomes more important
