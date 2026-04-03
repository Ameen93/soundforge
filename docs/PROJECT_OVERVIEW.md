---
project: soundforge
type: overview
status: current
last_updated: 2026-03-29
tags: soundforge, game-audio, ai, cli, sfx, ambience, gamedev
---

# SoundForge

SoundForge is a game-audio asset pipeline for developers. It combines text-to-audio generation with postprocessing, inspection, preview, deterministic export, and pack manifests.

## Product Thesis

The durable value is not the model alone. The value is the workflow around generation:
- engine-aware defaults
- variation packs
- cleanup and mastering-lite steps
- deterministic naming
- machine-readable manifests
- agent-friendly CLI behavior

This makes SoundForge more useful than a raw prompt-to-audio endpoint for actual game integration work.

## Current Scope

Implemented now:
- single asset generation
- batch variation generation
- ambience and loop-intended workflows
- WAV-first export
- trim, fade, normalize, resample, channel conversion, loop smoothing
- inspection and preview
- manifest and pack export
- backend readiness reporting

Out of scope for the current release:
- full music generation
- dialogue and voice workflows
- DAW-style editing
- middleware-native authoring
- collaborative asset review flows

## Primary Users

- indie game developers
- solo developers
- game jam teams
- technical designers
- developers building agent-driven asset pipelines

## Primary Jobs

- generate one usable SFX quickly
- generate several variations with predictable naming
- normalize and resample assets for engine import
- preview and inspect assets without leaving the terminal
- bundle a directory into a manifest-backed pack

## Maintainer Brief

If you are new to the repo, read in this order:

1. `README.md`
2. `soundforge/cli/commands.py`
3. `soundforge/core/generate.py`
4. `soundforge/core/batch.py`
5. `soundforge/core/config.py`
6. `docs/ARCHITECTURE.md`
7. `docs/TODO.md`

Mental model:
- the CLI is orchestration
- the core owns workflow logic
- backends only generate arrays plus sample rate
- export turns processed arrays into files and manifests

## Success Criteria

SoundForge is successful when a developer can:

1. run it from a game project directory
2. generate usable short-form audio with one command
3. receive outputs that need little or no manual cleanup
4. import the results into a game engine immediately
5. automate the workflow from scripts or other agents
