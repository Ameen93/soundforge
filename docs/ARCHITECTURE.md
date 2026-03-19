---
project: soundforge
type: architecture
status: planning
last_updated: 2026-03-17
tags: soundforge, architecture, audio, cli, backends, gamedev
---

# Architecture

## Architectural Goal
Build SoundForge as a reusable core library with a thin CLI wrapper, so the same core can later power:
- a web app
- an internal API
- editor integrations
- agentic workflows

This should directly inherit the architectural lesson from `pixelforge`: keep the product logic in the core, not in the CLI.

## v0 System Shape

```text
User prompt
   │
   ▼
soundforge CLI
   │
   ├── config resolution
   ├── engine preset resolution
   ├── output path planning
   └── human/JSON formatting
   │
   ▼
soundforge.core
   │
   ├── backend selection
   ├── generation request building
   ├── postprocess pipeline
   ├── analysis / inspection
   ├── export / packaging
   └── preview
   │
   ▼
Backend
   ├── hosted API backend
   └── optional local backend
   │
   ▼
Audio outputs + manifest
```

## Recommended Package Layout

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
│       ├── naming.py
│       ├── pack.py
│       ├── postprocess.py
│       ├── preview.py
│       ├── types.py
│       └── backends/
│           ├── __init__.py
│           ├── api_sfx.py
│           └── local_stable_audio.py
└── .soundforge.toml.example
```

## Core Design Rules

### 1. CLI is orchestration, not business logic
The CLI should do:
- argument parsing
- config loading
- output path decisions
- status printing
- JSON formatting

The core should do:
- prompt shaping
- backend calls
- waveform postprocessing
- audio analysis
- export packaging

### 2. Backends share a stable interface
The backend abstraction should support:
- generate one clip
- generate multiple variations
- report availability
- report capabilities

The interface should not leak provider-specific payload shapes into the rest of the system.

### 3. Postprocessing is a first-class subsystem
For SoundForge, postprocessing is not optional polish. It is the core of the product.

v0 postprocessing should support:
- trimming leading and trailing silence
- fade-in / fade-out
- peak normalization
- optional LUFS normalization if dependency cost is acceptable
- mono/stereo conversion
- sample-rate conversion
- optional loop smoothing for ambience
- optional tail trimming

### 4. Export is structured, not ad hoc
The output system should generate:
- stable file names
- export directories
- manifest metadata
- optional pack archives later

### 5. JSON mode is a product requirement
Every command that produces output should support machine-readable JSON. This is essential for:
- agent workflows
- CI automation
- editor integration
- future SaaS wrapping

## Suggested Core Types

```python
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AudioSpec:
    sample_rate: int
    channels: int
    format: str
    bit_depth: int | None = None


@dataclass
class GenerateRequest:
    prompt: str
    asset_type: str
    duration_seconds: float | None = None
    loop: bool = False
    variations: int = 1
    engine: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AudioAsset:
    path: Path
    duration_seconds: float
    sample_rate: int
    channels: int
    peak_dbfs: float | None = None
    loudness_lufs: float | None = None
    loop_safe: bool | None = None


@dataclass
class GenerateResult:
    assets: list[AudioAsset]
    backend: str
    prompt_used: str
    manifest_path: Path | None = None
```

## Backend Strategy

### Recommended v0 Backend Order
1. Hosted API backend first
2. Local backend second

Rationale:
- Faster to ship
- Less local hardware complexity
- Better first-user experience
- Lets the architecture mature before absorbing large local model costs

### Hosted Backend Expectations
The first hosted backend should support:
- short SFX generation
- variable count / variations
- explicit duration when available
- WAV export or easily convertible output

### Local Backend Expectations
The local backend is strategically valuable, but should be treated as a second-phase feature unless implementation cost is low.

Potential local candidate classes:
- Stable Audio Open-based backend for experimentation
- procedural fallback backend for retro and synthetic SFX later

## Preview Architecture
v0 preview should be intentionally simple:
- play a file
- play a directory as a variation set
- print metadata summary
- optionally show a basic ASCII or textual waveform later

This does not need to become a DAW.

## Config Model
SoundForge should use `.soundforge.toml`, discovered by walking up the directory tree in the current project.

Config categories:
- defaults
- output paths
- engine presets
- backend defaults
- postprocessing defaults
- naming rules

Example:

```toml
[defaults]
backend = "api"
engine = "godot"
type = "sfx"
duration = 1.5
variations = 4
output_dir = "assets/audio"

[postprocess]
trim_silence = true
normalize_peak_dbfs = -1.0
fade_in_ms = 5
fade_out_ms = 25

[export]
format = "wav"
sample_rate = 44100
channels = "mono"
manifest = true
```

## Engine Presets

### Godot
- Prefer WAV or Ogg depending on use case
- Useful defaults: WAV for SFX, Ogg for ambience/music

### Unity
- Import flexibility is broad, so SoundForge should optimize for WAV-first exports and optional Ogg conversion

### Unreal
- Accepts a wide range of import formats, but WAV-first remains the safest universal export default

## Why WAV-First
WAV should be the canonical v0 output because it is:
- simple
- widely supported
- fast to import
- good for further engine-side compression
- easy to analyze and transform without generational loss

Optional Ogg export can be layered on top.

## Non-Goals For The Architecture
The initial design should avoid:
- provider-specific business logic embedded in commands
- custom binary project formats
- complex plugin systems before core abstractions stabilize
- over-optimizing for SaaS before the CLI workflow is proven
