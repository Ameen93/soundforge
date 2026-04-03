---
project: soundforge
type: decisions
status: current
last_updated: 2026-03-29
tags: soundforge, decisions, architecture, scope
---

# Decision Log

## Product Decisions

### Focus on short-form game audio

Decision:
SoundForge targets SFX, UI sounds, ambience, and loop-intended clips rather than music.

Why:
- clearer product wedge
- better fit for current models
- easier evaluation and packaging
- stronger CLI workflow story

### Treat workflow as the differentiator

Decision:
SoundForge is positioned as a game-audio pipeline, not just a text-to-audio wrapper.

Why:
- cleanup and export matter more than raw generation alone
- deterministic manifests help developers and agents
- engine-aware defaults are real product value

### Treat batch generation as a first-class feature

Decision:
Variation packs are core, not optional polish.

Why:
- games need repeated small variations
- one perfect hero sound is less useful than a usable set

## Architecture Decisions

### Keep the CLI thin

Decision:
The CLI owns parsing and presentation. The core owns workflow logic.

Why:
- improves testability
- preserves reusability
- reduces command-layer drift

### Keep backend abstraction stable

Decision:
Backends must share a common interface and return arrays plus sample rate.

Why:
- avoids provider lock-in
- keeps postprocessing and export backend-agnostic

### Use WAV as the canonical processing format

Decision:
WAV remains the default working format even when source backends return encoded audio. Export may emit WAV or OGG at the boundary.

Why:
- broad engine compatibility
- simple and reliable processing
- lower quality-risk in the pipeline

### Keep JSON mode mandatory

Decision:
Relevant commands must support machine-readable JSON output.

Why:
- agent compatibility
- CI and scripting support
- future API/editor integration

### Discover project config by walking upward

Decision:
Use `.soundforge.toml` discovery from the working directory, with a global fallback.

Why:
- fits game project layout
- allows team defaults
- works well for terminal and agent workflows

## Decisions That Are Now Resolved

### First hosted backend

Resolved:
ElevenLabs is implemented as the hosted backend.

### First local backend

Resolved:
Stable Audio Open 1.0 is implemented as the local GPU backend.

## Open Decisions

- whether LUFS belongs in the next milestone
- whether to introduce structured request types now or wait for API reuse pressure
- whether retro procedural synthesis should become a backend in v1 or later
