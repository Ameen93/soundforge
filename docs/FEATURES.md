---
project: soundforge
type: features
status: current
last_updated: 2026-03-29
tags: soundforge, features, v0, audio, gamedev
---

# Features

## Shipped In Current v0

### Single asset generation

- text prompt to one exported WAV
- optional duration
- optional seed
- engine-aware output defaults
- manifest emission

### Batch variation generation

- one prompt to many numbered WAV files
- deterministic file naming
- one manifest for the pack
- configurable prefix

### Ambience and loop-intended workflows

- `ambience` and `loop` asset types
- explicit `--loop` flag
- loop smoothing in postprocess
- loop intent recorded in exported metadata

### Postprocess pipeline

- silence trimming
- fade-in and fade-out
- peak normalization
- sample rate conversion
- mono/stereo conversion
- loop smoothing

### Engine presets

- Godot preset
- Unity preset
- Unreal preset
- per-engine output directory defaults
- config-based preset overrides

### Inspect and preview

- inspect a single file
- inspect a directory of WAV files
- local playback through default audio device

### Pack export

- build manifest from existing WAV directory
- optional zip archive creation

### Setup and diagnostics

- backend readiness via `info`
- guided backend setup via `setup`
- JSON output for automation

## Deliberate Non-Goals For Current v0

- full music generation
- dialogue generation
- timeline editing
- FMOD or Wwise project authoring
- collaborative review tooling

## Not Yet Implemented

- OGG export
- LUFS measurement and normalization
- tag-aware asset metadata
- backend fallback rules
- richer loop quality validation

## Quality Bar

For current v0, success means:
- short-form sounds are usable quickly
- batches provide enough variation for game use
- outputs are easy to script and integrate
- the command surface is predictable and testable
