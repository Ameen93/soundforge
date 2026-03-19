---
project: soundforge
type: overview
status: planning
last_updated: 2026-03-17
tags: soundforge, game-audio, ai, cli, sfx, ambience, gamedev
---

# SoundForge
> AI-powered game audio asset generator and packaging tool for indie developers.

## What This Is
SoundForge is a planned Python CLI and reusable core library for generating, cleaning, previewing, and packaging game audio assets from natural-language prompts.

The first version should focus on **sound effects** and **ambient loops** rather than full music composition. The product goal is not just text-to-audio generation. It is a complete game-audio workflow:

1. Prompt a sound
2. Generate one or more variations
3. Clean and normalize the result
4. Validate duration, loudness, and loopability
5. Export engine-ready files plus a manifest

The project should mirror the best structural decisions from `pixelforge`:
- Thin CLI wrapper
- Clean core library
- Pluggable generation backends
- Project-level config file
- Agent-friendly stdout/stderr separation
- Deterministic file outputs and JSON mode

## Problem It Solves
Indie game teams routinely stall on audio. The common failure modes are:
- Spending hours searching stock libraries for "almost right" sounds
- Hiring sound design help too late or not at all
- Getting raw generated audio that still needs trimming, fades, normalization, resampling, naming, and organization
- Lack of fast iteration when a game needs 8 small variants instead of 1 perfect hero sound

SoundForge should reduce this to a prompt-and-export workflow designed for actual game integration.

## Core Thesis
The durable product value is not the model alone.

Model quality will keep changing. The moat is the workflow around generation:
- engine-aware export defaults
- variation packs
- loop-safe ambience handling
- loudness and cleanup rules
- naming conventions
- metadata manifests
- fast audition and preview
- agent-friendly automation

This is the same strategic pattern that makes `pixelforge` more interesting than a raw image generator.

## v0 Product Scope
SoundForge v0 should target:
- Single sound effect generation
- Multi-variation sound effect generation
- Ambient one-shots and short ambience loops
- Cleanup and mastering-lite postprocessing
- WAV-first export
- Engine presets for Godot, Unity, and Unreal
- Preview and inspection in the terminal
- Pack export with JSON manifest

## Explicit v0 Non-Goals
To keep the first release coherent, v0 should not try to do all of the following:
- full song generation
- multi-minute adaptive game music
- dialogue / voice acting generation
- DAW-style waveform editing UI
- complex stem mixing
- middleware project editing for FMOD or Wwise
- real-time in-engine procedural synthesis

These may become future features, but they should not define the first implementation.

## Target Users
### Primary
- Indie game developers
- Game jam teams
- Solo developers shipping quickly

### Secondary
- Small studios doing rapid prototyping
- Technical designers who need placeholder or shippable SFX fast
- Developers building with AI coding agents who need CLI automation

### Tertiary
- Video creators and interactive media teams

## Primary Jobs To Be Done
- "Give me 8 usable coin pickup variations with clean names."
- "Generate a sci-fi door open sound and export it for Unity."
- "Create a seamless cave ambience loop."
- "Make a sword hit pack with short, medium, and heavy variants."
- "Produce files plus a manifest so an agent can wire them into the project."

## Product Positioning
SoundForge should be positioned as:

**A game-audio asset pipeline, not just an audio generator.**

The intended differentiation is:
- better workflow than generic AI sound tools
- more automation than stock-library browsing
- better developer ergonomics than browser-only tools
- optional self-hosted/local path in addition to hosted APIs

## Deliverables From v0
At minimum, v0 should be able to emit:
- `.wav` files
- optional `.ogg` conversions
- a `manifest.json`
- predictable file naming
- metadata useful for agentic workflows

## Recommended Repository Shape
```text
soundforge/
├── docs/
├── soundforge/
│   ├── __init__.py
│   ├── cli/
│   └── core/
├── pyproject.toml
└── .soundforge.toml.example
```

## Success Criteria For v0
SoundForge v0 is successful if a developer can:

1. Run one command from a game project directory
2. Generate several usable SFX variations
3. Receive files that do not require manual cleanup first
4. Import those files into a game engine immediately
5. Script the workflow from another tool or AI agent

## Guiding Principle
The product should optimize for **speed to acceptable, game-ready audio**, not perfection in a DAW sense.
