---
project: soundforge
type: roadmap
status: current
last_updated: 2026-03-29
tags: soundforge, roadmap, milestones, future
---

# Roadmap

This roadmap assumes the long-term goal is:

**SoundForge should be capable of creating and integrating most or all audio assets needed during game development.**

The sequence matters. The product should deepen workflow quality before widening into every audio domain.

## Roadmap Principle

Build in this order:

1. make SFX and ambience genuinely production-usable
2. make assets searchable, regenerable, and integration-friendly
3. automate engine and middleware workflows
4. expand into dialogue and voice
5. expand into music and adaptive systems

## Current State

Implemented now:
- single generation
- batch generation
- ambience and loop-intended workflows
- postprocess pipeline
- inspection and preview
- engine presets
- pack export
- local and hosted backends

This is a strong v0 for prompt-to-pack short-form audio, but it is not yet a full game-audio pipeline.

## v0.5: Production Fit

Theme:

**Make current SFX and ambience workflows reliable enough for real project usage**

Primary outcomes:
- better export formats
- stronger loudness and loop workflows
- better metadata and asset organization
- better review and regeneration workflows

Target features:
- OGG export
- LUFS analysis and optional normalization
- loop analysis, seam scoring, and repair
- richer `inspect` output
- tags and hierarchical asset taxonomy
- regeneration and selective replacement workflows
- engine import hints in manifests
- improved batch progress feedback
- optional `process` manifest output
- backend capability preflight validation

What success looks like:
- a developer can generate or process a usable pack of SFX and ambience
- the pack can be searched, reviewed, and regenerated without manual file wrangling
- exports include enough metadata to drive engine import decisions

## v1: Library And Workflow Maturity

Theme:

**Turn generated files into a manageable audio library**

Primary outcomes:
- reusable asset library
- semantic pack generation
- stronger authoring ergonomics

Target features:
- searchable local asset library
- asset lineage tracking
- pack metadata editing
- favorites, rejected, and approved states
- semantic pack generators:
  - footsteps by surface
  - UI sets
  - weapon family packs
  - ambience families
- prompt templates and style profiles
- reference-conditioned generation
- “generate more like this” workflows
- richer preview with A/B and randomized audition

What success looks like:
- a team can treat SoundForge as a reusable internal audio asset system, not just a one-off generator

## v1.5: Middleware And Engine Automation

Theme:

**Make SoundForge integration-aware, not just file-aware**

Primary outcomes:
- assets can be pushed into runtime audio systems with structure
- workflow covers event-level authoring, not just exported files

Target features:
- Wwise WAAPI integration
- Wwise import automation
- Wwise Random Container generation
- Wwise Switch Container generation
- Wwise SoundBank build hooks
- FMOD-oriented export manifests
- FMOD event templates for one-shots, loops, and parameterized sets
- engine import helpers or plugin-facing metadata
- project-level audio spec definitions

What success looks like:
- generated packs become ready-to-wire runtime assets, not just organized source files

## v2: Voice And Dialogue

Theme:

**Cover game voice workflows**

Primary outcomes:
- placeholder and production-support voice tooling
- dialogue packs fit into the same manifest and pipeline model

Target features:
- bark and callout generation
- placeholder NPC voice packs
- line variation generation
- transcript and subtitle pairing
- pronunciation and style controls
- dialogue directory conventions
- programmer-sound friendly manifests

What success looks like:
- SoundForge handles the early-stage and iteration-heavy parts of VO production, even if final studio VO remains external

## v2.5: Music And Adaptive Audio

Theme:

**Extend beyond short-form effects into score support**

Primary outcomes:
- short music and adaptive cues join the same workflow

Target features:
- stingers
- menu and combat loops
- intensity variants
- layered cue structures
- stem-aware exports when possible
- transition cue generation

What success looks like:
- SoundForge covers a meaningful subset of practical game music needs without turning into a DAW

## v3: Full Audio Operating Layer

Theme:

**Project-wide audio generation, organization, and integration**

Target features:
- game-design-doc to audio task extraction
- scene or gameplay-capture to audio suggestions
- team review workflows
- project-wide batch planning
- agent-driven end-to-end audio generation and integration
- editor plugins for Godot, Unity, and Unreal

## What To Avoid

- adding music too early
- turning the CLI into a general audio editor
- coupling the architecture too tightly to one backend
- shipping broad but shallow features instead of deep workflow wins

## Immediate Priority Order

If the roadmap is reduced to the next 12 months, the order should be:

1. v0.5 production fit
2. v1 library and semantic pack workflows
3. v1.5 middleware and engine automation

Voice and music should come after those layers unless a very specific user need forces reprioritization.
