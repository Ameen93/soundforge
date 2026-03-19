---
project: soundforge
type: features
status: planning
last_updated: 2026-03-17
tags: soundforge, features, v0, roadmap, audio, gamedev
---

# Features & Capabilities

## v0 Feature Set

### 1. Single Asset Generation
Command concept:
```bash
soundforge generate "metal sword hit with bright impact" -o assets/audio/sfx
```

Capabilities:
- Generate one sound effect from text
- Set target duration when supported by the backend
- Choose asset category
- Export as WAV
- Emit metadata and JSON output

### 2. Variation Batch Generation
Command concept:
```bash
soundforge batch "retro coin pickup" --count 8 --prefix sfx_coin
```

Capabilities:
- Produce multiple variations from one prompt
- Save files with deterministic numbering
- Generate a manifest describing the set
- Support lightweight pack creation for immediate engine import

This should be treated as a primary feature, not a bonus feature. Games rarely need one perfect sound. They need sets.

### 3. Ambient Loop Generation
Command concept:
```bash
soundforge generate "cave ambience with dripping water" --type ambience --loop
```

Capabilities:
- Generate short ambience clips
- Mark output as intended for looping
- Run loop-safety heuristics or smoothing postprocessing
- Export metadata indicating loop intent

### 4. Cleanup / Postprocess Pipeline
Command concept:
```bash
soundforge process assets/audio/raw/*.wav
```

Capabilities:
- Trim leading/trailing silence
- Fade edges
- Normalize output
- Convert sample rate and channel count
- Prepare assets for engine import

### 5. Engine Presets
Command concept:
```bash
soundforge generate "ui click, soft" --engine godot
```

Capabilities:
- Resolve format defaults
- Resolve sample-rate defaults
- Resolve output directories
- Resolve naming conventions where configured

### 6. Preview / Inspect
Command concepts:
```bash
soundforge preview assets/audio/sfx_coin_01.wav
soundforge inspect assets/audio/sfx_coin_01.wav --output-json
```

Capabilities:
- Play or audition output locally
- Print duration, sample rate, channels, peak information
- Inspect a whole directory of variations

### 7. Pack Export
Command concept:
```bash
soundforge pack assets/audio/coin_pickups/ --name coin_pickups
```

Capabilities:
- Build manifest file
- Group related files
- Prepare game-ready asset bundles
- Enable later zip export if desired

### 8. Setup / Info
Command concepts:
```bash
soundforge setup
soundforge info --output-json
```

Capabilities:
- Check configured backend readiness
- Report installed capabilities
- Confirm dependency availability
- Confirm config discovery path

## v0 Asset Types
Recommended initial types:
- `sfx`
- `ui`
- `ambience`
- `loop`

Optionally define subtype tags rather than separate hardcoded classes:
- `footstep`
- `impact`
- `weapon`
- `magic`
- `pickup`
- `door`
- `machine`
- `environment`

## v0 Non-Goals
The following should be explicitly deferred:
- full-length music tracks
- adaptive music systems
- voice acting and dialogue pipelines
- beat syncing for music systems
- stem separation or remix tools
- timeline editing
- scene-aware video-to-sound workflows
- middleware-native project generation for FMOD/Wwise

## Future Features

### Near-Term v1 Features
- Better loop validation and automatic seam-repair
- Ogg export and engine-specific presets
- More detailed manifest schema
- bulk regeneration and selective replacement
- tagging and searchable local library
- prompt templates per asset type
- backend fallback rules

### v1.5 Features
- procedural retro SFX backend for 8-bit / arcade sounds
- richer audio analysis including LUFS, crest factor, transient score
- preset libraries such as `platformer`, `sci-fi`, `fantasy`, `survival-horror`
- prompt-to-pack workflows like `footstep pack on gravel`

### v2 Features
- music-loop generation
- layered stem output
- FMOD/Wwise export helpers
- editor plugins
- web app / hosted API
- shared team library and approval workflow
- regeneration from reference audio

### Experimental Future Features
- scene-to-sound generation from video or gameplay capture
- in-engine procedural runtime generation
- reference-conditioned generation
- adaptive music cue generation
- event taxonomy generation from a game design document

## Quality Bar For v0
For v0, "good" means:
- short sounds are immediately usable
- batches contain enough variation to avoid repetition fatigue
- output files are clean enough to ship in indie projects
- the command line experience is stable and scriptable

It does not mean:
- the system replaces a senior sound designer
- every output is studio-mastered
- music generation is solved
