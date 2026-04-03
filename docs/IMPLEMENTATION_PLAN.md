---
project: soundforge
type: implementation-plan
status: current
last_updated: 2026-03-29
tags: soundforge, implementation, roadmap, audio, backend
---

# Implementation Plan

This plan translates the roadmap into concrete execution phases. It is biased toward shipping the highest-leverage workflow improvements first.

## Planning Assumptions

- keep the CLI thin
- keep `soundforge/core/` reusable
- preserve deterministic outputs and JSON mode
- keep WAV as the canonical processing format
- add broader workflow surfaces only after current SFX workflows are stronger

## Phase 1: v0.5 Production Fit

Goal:

Make current SFX and ambience workflows production-usable for real game projects.

### Workstream 1: Export and analysis

Deliver:
- OGG export support
- LUFS measurement
- optional LUFS normalization
- richer inspect output

Implementation notes:
- extend `core/export.py` to support multi-format export
- keep postprocess in WAV-space, convert at export boundary
- extend `core/analysis.py` and `core/types.py` with loudness metadata
- add CLI flags only after manifest schema is defined

Dependencies:
- decide manifest schema for format variants
- choose optional dependency strategy for loudness measurement

Acceptance criteria:
- generated and processed assets can export as WAV and OGG
- inspect output includes loudness-oriented metadata
- manifests reflect format and loudness information

### Workstream 2: Loop quality

Deliver:
- loop-point analysis
- seam quality score
- loop repair strategy options

Implementation notes:
- keep `loop_smooth()` as the basic repair path
- add analysis helpers before adding complex CLI UX
- record loop scores and repair decisions in manifests

Acceptance criteria:
- ambience workflows provide a useful signal for loopability
- users can tell whether a loop is safe without manual DAW inspection

### Workstream 3: Metadata and regeneration

Deliver:
- asset tags
- hierarchical taxonomy
- selective regeneration
- replace-one-variant workflow

Implementation notes:
- add tags to manifest schema first
- then add CLI affordances for reading and rewriting packs
- avoid coupling taxonomy directly to backend prompt shape

Acceptance criteria:
- a user can regenerate a single asset inside a pack without manual rename or manifest repair

### Workstream 4: Core reliability and ergonomics

Deliver:
- backend capability preflight validation
- better progress reporting
- optional `process` manifest generation

Acceptance criteria:
- invalid generation requests fail early and consistently
- long-running commands provide useful progress

## Phase 2: v1 Library And Semantic Workflow

Goal:

Turn generated output into a reusable, queryable local audio system.

### Workstream 1: Local library

Deliver:
- library index
- search by prompt, tags, type, engine, duration, backend
- lineage tracking

Implementation notes:
- introduce a local metadata store
- keep manifests as source artifacts, not the sole query mechanism
- add import support for externally created assets

Acceptance criteria:
- users can find past generated assets without browsing folders manually

### Workstream 2: Review state

Deliver:
- accepted, rejected, favorite, shortlisted states
- notes and curation metadata
- compare and audition workflows

Acceptance criteria:
- users can review packs and preserve decisions machine-readably

### Workstream 3: Semantic pack generators

Deliver first:
- footsteps by surface
- UI sets
- weapon family packs

Implementation notes:
- these should be higher-level workflows built on top of current generation primitives
- prompts should be templated, not fully opaque

Acceptance criteria:
- one command can create a coherent multi-asset family with useful naming and metadata

## Phase 3: v1.5 Middleware And Engine Automation

Goal:

Make SoundForge integration-aware.

### Workstream 1: Wwise

Deliver:
- WAAPI connection layer
- import existing generated assets into Wwise
- create Sound SFX objects
- create Random Containers from variation packs
- create Switch Containers from tagged families
- build SoundBanks

Implementation notes:
- create a separate integration module rather than bloating `core/export.py`
- model Wwise object mapping from manifest metadata
- start with import and container creation before deeper property automation

Dependencies:
- tags and taxonomy from earlier phases
- stable manifest schema

Acceptance criteria:
- a generated pack can be turned into a usable Wwise object structure with one workflow

### Workstream 2: FMOD

Deliver:
- FMOD-oriented export manifests
- event templates
- loop and one-shot event mapping
- parameter-oriented pack metadata

Implementation notes:
- start with file and manifest structure
- add event scaffold generation before attempting more dynamic authoring

Acceptance criteria:
- generated packs map naturally into FMOD authoring workflows with minimal manual setup

### Workstream 3: Engine import hints

Deliver:
- manifest-level import recommendations for Godot, Unity, Unreal
- optional helper commands or plugin-facing outputs

Acceptance criteria:
- exported metadata is strong enough to drive import tooling later

## Phase 4: v2 Voice And Dialogue

Goal:

Cover placeholder and iterative VO workflows.

### Deliver

- bark and callout generation
- character voice profiles
- line-variation generation
- transcript and subtitle metadata
- programmer-sound friendly export structures

### Dependencies

- stronger library and metadata model
- likely new backend abstractions or capability flags

### Acceptance criteria

- dialogue assets fit the same pack, manifest, and integration patterns as current SFX workflows

## Phase 5: v2.5 Music And Adaptive Audio

Goal:

Expand into practical music support without collapsing into DAW features.

### Deliver

- stingers
- menu and combat loops
- intensity-layer variants
- transition cue workflows
- stem-aware metadata if supported

### Acceptance criteria

- short-form music workflows are scriptable and organized, not just generated ad hoc

## Cross-Cutting Technical Work

These should happen throughout the roadmap.

### Manifest evolution

- version the schema once it expands meaningfully
- document changes in `README.md`
- keep backward-compatible readers where possible

### Testing

- add fixture-driven audio tests for new analysis features
- keep backend behavior mocked in CI
- add integration-test layers for middleware if practical

### Optional dependencies

- keep heavyweight or niche capabilities behind extras
- maintain a clean base install for CLI-only workflows

### Developer UX

- preserve `--output-json`
- preserve deterministic outputs
- preserve noninteractive automation paths

## Suggested Execution Order

The most pragmatic order from here is:

1. backend capability validation
2. OGG export
3. LUFS analysis
4. loop analysis and repair
5. tags and taxonomy
6. regeneration workflows
7. local asset library
8. semantic pack generators
9. Wwise integration
10. FMOD integration

## Recommended Immediate Epics

If starting implementation now, the next three epics should be:

### Epic 1: Export and analysis upgrade

Scope:
- OGG export
- loudness metrics
- richer inspect

### Epic 2: Loop and pack intelligence

Scope:
- loop scoring
- tags
- replace/regenerate workflows

### Epic 3: Asset library foundation

Scope:
- local index
- searchable metadata
- review states

## Execution Docs

Detailed execution breakdown for the next phase:

- `docs/V0_5_EXECUTION_PLAN.md`
