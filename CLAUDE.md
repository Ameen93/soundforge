# CLAUDE.md

## Project

SoundForge is a Python CLI and core library for generating and packaging short-form game audio. It targets prompt-to-pack workflows for developers, not full DAW-style editing.

## Current State

- v0 is implemented
- two backends: `stable-audio`, `elevenlabs`
- commands: `info`, `setup`, `generate`, `batch`, `process`, `preview`, `inspect`, `pack`
- 181 tests passing

## Stack

- Python 3.12+
- Click
- httpx
- numpy
- soundfile
- scipy optional for resampling
- sounddevice optional for preview
- torch/diffusers optional for local GPU generation

## Working Norms

- treat `README.md` as user-facing truth
- treat `docs/ARCHITECTURE.md` as maintainer-facing truth
- treat `docs/TODO.md` as the real backlog
- CLI should stay thin
- core modules should remain reusable and testable
- human output goes to stderr, JSON goes to stdout

## Key Paths

- `soundforge/cli/commands.py`
- `soundforge/cli/formatting.py`
- `soundforge/core/config.py`
- `soundforge/core/generate.py`
- `soundforge/core/batch.py`
- `soundforge/core/postprocess.py`
- `soundforge/core/export.py`
- `soundforge/core/backends/`
- `tests/`

## Commands

```bash
uv sync
uv pip install -e ".[local-gpu]"
uv pip install -e ".[preview,resample]"
uv run soundforge info
uv run soundforge setup
uv run soundforge generate "coin pickup" --engine godot -o assets/audio
uv run soundforge batch "sword hit" --count 8 --prefix sfx_sword
uv run soundforge process raw/*.wav --normalize -1
uv run soundforge inspect assets/audio/
uv run soundforge preview assets/audio/sfx_coin_01.wav
uv run soundforge pack assets/audio/coins/ --name coin_pickups --zip
uv run pytest
```

## Architecture Summary

- CLI handles parsing, config loading, and output formatting
- core handles generation, postprocess, analysis, export, and pack assembly
- backends expose a shared `GenerationBackend` interface
- config discovery walks up to `.soundforge.toml`, then falls back to global config

## Known Gaps

- no OGG export yet
- no LUFS measurement yet
- no structured request type yet
- no backend fallback rules yet

## Editing Guidance

- prefer updating docs when behavior changes
- keep README concise and current
- keep TODO limited to real remaining work
- if code and docs disagree, fix the docs or fix the code in the same pass
