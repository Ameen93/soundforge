---
project: soundforge
type: decisions
status: planning
last_updated: 2026-03-17
tags: soundforge, decisions, architecture, scope
---

# Decision Log

## Product Decisions

### Focus v0 on SFX and ambience
Decision:
SoundForge v0 should target short-form game audio, especially sound effects and ambience loops.

Why:
- clearer user need
- stronger current model fit
- lower evaluation complexity
- easier packaging story than music

### Treat variations as a core feature
Decision:
Batch generation should be a first-class feature, not an extra.

Why:
- games need variation to avoid repetition fatigue
- one hero sound is less useful than a small set
- this aligns with competitor messaging and real game workflows

### Position as workflow, not pure generation
Decision:
SoundForge should be framed as a game-audio asset pipeline.

Why:
- model quality is not enough to differentiate
- cleanup, naming, manifests, and engine export are where workflow value accumulates

## Architecture Decisions

### Core library + thin CLI
Decision:
Keep the CLI thin and move business logic into a reusable core.

Why:
- mirrors the strongest design choice in `pixelforge`
- enables future API and web reuse
- improves testability

### Backend abstraction from day one
Decision:
Design around interchangeable backends immediately.

Why:
- providers will change
- local support remains strategically valuable
- prevents lock-in to a single vendor payload shape

### WAV-first canonical pipeline
Decision:
Use WAV as the internal and default export format.

Why:
- safest for processing
- broadest import support
- simplest first implementation

## Workflow Decisions

### JSON mode is mandatory
Decision:
All relevant commands should support structured JSON output.

Why:
- agent compatibility
- CI automation
- editor and tooling integrations

### Project-level config discovery
Decision:
Use `.soundforge.toml` discovered by walking up from the current directory.

Why:
- matches how game projects are organized
- aligns with the proven `pixelforge` model
- supports team conventions and shared defaults

### Engine presets early
Decision:
Include Godot, Unity, and Unreal presets in v0.

Why:
- they are practical target engines
- export defaults are meaningful product value
- they reduce friction in real adoption

## Deferred Decisions

These remain open for later implementation:
- exact first hosted backend
- exact local backend candidate
- whether LUFS normalization belongs in v0 or v0.5
- whether Ogg export belongs in v0 or v0.5
- whether retro/procedural synthesis joins v1 or v1.5
