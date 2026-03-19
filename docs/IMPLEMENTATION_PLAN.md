---
project: soundforge
type: implementation-plan
status: planning
last_updated: 2026-03-17
tags: soundforge, implementation, v0, cli, audio, backend
---

# Implementation Plan

## Overview
SoundForge v0 should be built as a focused, usable CLI for game sound effect and ambience generation. The implementation should follow a narrow product thesis:

**Ship a clean prompt-to-pack workflow for short game audio first.**

This avoids the trap of trying to solve the entire game audio stack in the first release.

## Phase 0: Foundation Decisions

### Decision 1
Start with `SFX + ambience loops`, not full music.

Reason:
- lower model complexity
- clearer user value
- easier evaluation
- closer alignment with the strongest current market tools

### Decision 2
Build hosted backend support first, but keep the backend abstraction neutral.

Reason:
- fastest path to usable output
- lowest local setup burden
- easier initial testing
- preserves room for self-hosted or local generation later

### Decision 3
Use WAV as the canonical working format.

Reason:
- easy postprocessing
- broad engine compatibility
- no avoidable quality loss during cleanup

## Proposed Milestones

### Milestone 1: Core Scaffolding
Deliver:
- package skeleton
- CLI entrypoint
- config loader
- JSON / human output formatting
- basic type definitions

Acceptance criteria:
- `soundforge info` runs
- `.soundforge.toml` can be discovered
- stdout/stderr separation is in place

### Milestone 2: Hosted Generation Path
Deliver:
- backend interface
- first hosted backend
- single `generate` command
- file saving and manifest writing

Acceptance criteria:
- one prompt produces one WAV file and JSON metadata
- backend capability checks are exposed through `info`

### Milestone 3: Batch Workflow
Deliver:
- `batch` command
- deterministic naming
- pack directory creation
- manifest for grouped outputs

Acceptance criteria:
- one prompt can produce N numbered files
- outputs can be dropped into a game project without manual renaming

### Milestone 4: Postprocessing
Deliver:
- silence trimming
- fade handling
- normalization
- sample-rate conversion
- mono/stereo conversion

Acceptance criteria:
- raw backend output can be transformed into cleaner game-ready audio
- processing works on both generated files and existing files

### Milestone 5: Preview & Inspect
Deliver:
- `preview`
- `inspect`
- directory-level inspection support

Acceptance criteria:
- users can quickly validate results without leaving the CLI workflow

### Milestone 6: Engine Presets
Deliver:
- Godot preset
- Unity preset
- Unreal preset
- export rule resolution

Acceptance criteria:
- `--engine` materially changes export defaults and output organization

## Suggested Command Surface

### v0 Commands
```bash
soundforge generate PROMPT
soundforge batch PROMPT
soundforge process PATH
soundforge preview PATH
soundforge inspect PATH
soundforge pack PATH
soundforge info
soundforge setup
```

### Example CLI Usage
```bash
soundforge generate "stone door grinding open, ancient, heavy" \
  --type sfx \
  --duration 2.5 \
  --engine godot \
  --output assets/audio/doors

soundforge batch "arcade coin pickup, bright and short" \
  --count 8 \
  --prefix sfx_coin \
  --engine unity \
  --output assets/audio/ui

soundforge generate "wind through a ruined canyon" \
  --type ambience \
  --duration 8 \
  --loop \
  --output assets/audio/ambience
```

## Recommended Internal Modules

### `core/config.py`
Responsibilities:
- load `.soundforge.toml`
- resolve defaults
- apply engine preset rules

### `core/types.py`
Responsibilities:
- request/result dataclasses
- backend and asset enums
- manifest structures

### `core/generate.py`
Responsibilities:
- build normalized generation requests
- shape prompts if needed
- call backends

### `core/postprocess.py`
Responsibilities:
- trim
- normalize
- fades
- channel conversion
- resampling
- loop-safe cleanup

### `core/analysis.py`
Responsibilities:
- duration
- sample rate
- channel count
- peak amplitude
- optional loudness
- silence estimates

### `core/export.py`
Responsibilities:
- write files
- convert formats
- write manifests
- enforce naming and folder structure

### `core/pack.py`
Responsibilities:
- assemble sets
- summarize pack metadata
- optional archive export later

### `core/preview.py`
Responsibilities:
- playback helpers
- variation set browsing

## Manifest Design
Every batch or pack should generate a manifest.

Suggested schema:

```json
{
  "name": "coin_pickups",
  "asset_type": "ui",
  "engine": "unity",
  "backend": "api",
  "prompt": "arcade coin pickup, bright and short",
  "generated_at": "2026-03-17T19:00:00Z",
  "files": [
    {
      "path": "sfx_coin_01.wav",
      "duration_seconds": 0.42,
      "sample_rate": 44100,
      "channels": 1,
      "peak_dbfs": -1.0
    }
  ]
}
```

## Dependency Recommendations
The exact set can be finalized during implementation, but the likely stack is:
- `click` for CLI
- `numpy` for signal operations
- `soundfile` for file IO
- `scipy` for resampling utilities if needed
- `pydantic` only if manifest/config validation needs stronger schemas later
- backend-specific SDKs only as optional extras

Avoid making the initial package too heavy if the first backend is hosted.

## Testing Strategy

### v0 Test Layers
1. Unit tests for config, naming, manifest, and postprocessing helpers
2. Smoke tests for CLI command execution
3. Fixture-based tests for `process` and `inspect`
4. Mocked backend tests for generation workflows

### What Not To Depend On For CI
- real API calls by default
- subjective human listening tests as the only quality gate
- fragile waveform snapshots that break on small backend changes

## Biggest Risks

### Risk 1: Backend quality variance
Mitigation:
- keep backend abstraction clean
- preserve prompt shaping in core
- emphasize batch workflows and selection over single perfect outputs

### Risk 2: Cleanup pipeline is too weak
Mitigation:
- make postprocessing a first-class implementation milestone
- treat `process` as a standalone useful command

### Risk 3: Scope drift into music and voice
Mitigation:
- explicit non-goals in docs and milestones
- separate roadmap section for deferred capabilities

### Risk 4: Local backend complexity
Mitigation:
- do not make local inference a blocker for v0
- keep it architecturally possible, not mandatory

## Recommended First Build Order
The practical build sequence should be:

1. CLI shell and config
2. types and manifest schema
3. hosted backend adapter
4. single generate command
5. batch command
6. postprocess command and library
7. inspect/preview
8. engine presets

That order gets the shortest path to a usable product while keeping the architecture clean.
