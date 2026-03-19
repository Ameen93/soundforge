---
project: soundforge
type: roadmap
status: planning
last_updated: 2026-03-17
tags: soundforge, roadmap, milestones, future
---

# Roadmap

## Guiding Rule
Each phase should deepen the same workflow rather than widening the product into unrelated audio domains too early.

## v0
Theme: **Prompt-to-pack game SFX**

Target outcomes:
- generate one-shot SFX
- generate variation packs
- support ambience loops
- clean and normalize outputs
- export engine-ready files and manifests
- expose a scriptable CLI

Notable exclusions:
- music
- voice
- editor plugins
- collaboration features

## v0.5
Theme: **Better production fit**

Candidate additions:
- Ogg export
- richer inspect command
- improved loop validation
- preset templates by genre
- more robust naming and folder conventions
- backend fallback configuration

## v1
Theme: **Library and workflow maturity**

Candidate additions:
- searchable local asset library
- regeneration and replace workflows
- pack-level metadata editing
- tagging and categorization
- retro/procedural SFX backend
- better preview UX

## v1.5
Theme: **Game-audio specialization**

Candidate additions:
- footstep packs by surface
- weapon family generators
- UI set generators
- environment ambience set builders
- reference-audio conditioning
- first middleware export helpers

## v2
Theme: **Expanded creative surface**

Candidate additions:
- loopable music cues
- stem output
- adaptive / layered music primitives
- FMOD / Wwise helper exports
- lightweight web app or hosted API
- team libraries and review workflows

## Long-Term
Theme: **Game-audio operating layer**

Possible destinations:
- editor plugins for Godot / Unity / Unreal
- GDD-to-audio task extraction
- agent-assisted project-wide audio generation
- scene or gameplay capture to sound suggestions
- runtime procedural hybrids

## What To Protect Against
The roadmap should explicitly resist these common failures:
- adding music too early
- turning the CLI into a DAW
- making the first release backend-dependent in its architecture
- widening scope before the core SFX workflow is solid
