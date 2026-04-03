---
project: soundforge
type: execution-plan
status: current
last_updated: 2026-03-29
tags: soundforge, v0.5, epics, implementation
---

# v0.5 Execution Plan

This document turns the `v0.5` roadmap phase into concrete epics and tickets.

Goal:

**Make SoundForge production-usable for SFX and ambience workflows before expanding into larger audio domains.**

## v0.5 Scope

In scope:
- OGG export
- LUFS analysis and optional normalization
- loop analysis and repair
- richer inspect output
- tags and taxonomy
- selective regeneration
- engine import hints in manifests
- backend capability preflight validation
- better progress and process manifests

Out of scope:
- middleware integration
- local asset library
- voice workflows
- music workflows

## Recommended Delivery Order

1. core validation and schema groundwork
2. export and analysis upgrades
3. loop intelligence
4. tags and regeneration
5. CLI polish and manifest enrichment

## Epic 1: Core Validation And Manifest Foundation

Purpose:

Create the schema and validation base needed for everything else.

### Ticket 1.1: Add backend capability preflight validation

Problem:
- unsupported requests are not consistently rejected or warned before backend calls

Changes:
- add central validation in `soundforge/core/generate.py`
- add central validation in `soundforge/core/batch.py`
- validate duration against `capabilities()["max_duration"]`
- validate loop intent against `capabilities()["supports_loop"]`
- define consistent warn-vs-error rules

Acceptance criteria:
- invalid requests fail or warn before provider call
- validation behavior is consistent across backends
- CLI output and JSON mode both expose useful errors

Testing criteria:
- unit tests cover duration validation against backend capability limits
- unit tests cover loop validation for backends that do and do not support loops
- tests verify provider generate methods are not called when requests should fail early
- CLI tests verify human-readable and JSON error paths

### Ticket 1.2: Version the manifest schema

Problem:
- manifest surface is growing but has no explicit versioning

Changes:
- add `manifest_version`
- document schema fields in README or architecture docs
- keep existing readers working where practical

Acceptance criteria:
- new manifests declare a version
- schema additions do not silently break future readers

Testing criteria:
- export tests verify `manifest_version` is present for single, batch, and pack outputs
- backward-compatibility tests verify existing readers tolerate the new field
- snapshot-style tests verify manifest structure remains stable

### Ticket 1.3: Add import-hint section to manifests

Problem:
- engine-ready export metadata is not explicit enough

Changes:
- add per-file import hints:
  - format
  - sample rate
  - channels
  - loop intent
  - suggested engine usage
  - suggested compression or streaming hint

Acceptance criteria:
- manifests carry actionable import guidance for engines

Testing criteria:
- export tests verify import hints are emitted for generated and processed assets
- tests cover Godot, Unity, and Unreal preset differences
- JSON contract tests verify hints remain machine-readable and predictable

## Epic 2: Export And Analysis Upgrade

Purpose:

Improve the practical quality and portability of exported assets.

### Ticket 2.1: Add OGG export path

Changes:
- support OGG export in `core/export.py`
- add CLI format selection for generation and processing
- keep WAV as canonical internal processing format

Acceptance criteria:
- `generate`, `batch`, and `process` can emit OGG
- manifests record actual exported formats
- pack workflows handle non-WAV exports intentionally

Testing criteria:
- export tests verify OGG files are written and readable by `soundfile`
- generation and processing tests verify format selection for WAV and OGG
- manifest tests verify exported format metadata is correct
- pack tests verify OGG-containing packs behave as designed for the chosen v0.5 rule

Open design question:
- should mixed-format packs be allowed in v0.5, or should each run emit one target format only?

Recommended answer:
- one target format per run in v0.5

### Ticket 2.2: Add LUFS measurement

Changes:
- extend `core/analysis.py`
- extend `AudioAsset` and `InspectResult`
- add optional dependency for loudness measurement

Acceptance criteria:
- inspect output can report LUFS for generated and processed assets
- manifest metadata can include LUFS

Testing criteria:
- analysis tests verify LUFS is computed for representative mono and stereo fixtures
- tests cover missing-optional-dependency behavior if loudness support is not installed
- inspect CLI tests verify LUFS appears in human and JSON output

### Ticket 2.3: Add optional LUFS normalization

Changes:
- extend `core/postprocess.py`
- add CLI/config support for loudness normalization mode
- keep peak normalization available

Acceptance criteria:
- user can choose peak or LUFS normalization
- output behavior is documented and test-covered

Testing criteria:
- postprocess tests verify normalization mode selection
- audio fixture tests verify output loudness moves toward target LUFS within an acceptable tolerance
- CLI tests verify config and flag precedence for normalization mode

### Ticket 2.4: Richer inspect output

Changes:
- extend human and JSON inspect output
- include loudness, loop-intent metadata, and format details

Acceptance criteria:
- `inspect` is useful for audio QA, not just basic file metadata

Testing criteria:
- CLI tests verify new inspect fields appear in human output
- JSON tests verify new inspect payload fields and names
- directory inspect tests verify multi-file reporting remains aligned and readable

## Epic 3: Loop Intelligence

Purpose:

Make ambience and loop-intended assets safer without forcing DAW cleanup.

### Ticket 3.1: Add loop analysis helpers

Changes:
- measure boundary similarity
- estimate seam quality
- store loop score in metadata

Acceptance criteria:
- loop-intended assets include a machine-readable loop-quality signal

Testing criteria:
- analysis tests verify loop score output for known good and known bad loop fixtures
- manifest tests verify loop metadata is written for loop-intended assets
- inspect tests verify loop-quality information is surfaced consistently

### Ticket 3.2: Add selectable loop repair modes

Changes:
- keep current smoothing as default
- add repair mode options if simple enough
- record chosen repair mode in manifest

Acceptance criteria:
- users can choose repair behavior for loop workflows

Testing criteria:
- postprocess tests verify each repair mode changes output as intended
- CLI tests verify repair mode selection and invalid mode handling
- manifest tests verify selected repair mode is recorded

### Ticket 3.3: Surface loop quality in inspect and generate output

Acceptance criteria:
- users can immediately see if a loop is likely acceptable

Testing criteria:
- generate CLI tests verify loop-quality output is shown when relevant
- inspect CLI tests verify loop score visibility for loop-intended assets
- JSON tests verify loop-quality fields are included in structured results

## Epic 4: Tags, Taxonomy, And Regeneration

Purpose:

Make packs reusable instead of disposable.

### Ticket 4.1: Add asset tags

Changes:
- add CLI tags input
- store tags in manifest
- support tags on generate, batch, and pack

Acceptance criteria:
- assets can be categorized beyond the coarse `asset_type`

Testing criteria:
- manifest tests verify tags persist for generate, batch, pack, and process flows where supported
- CLI tests verify tag parsing and serialization
- tests cover empty, repeated, and malformed tag input behavior

### Ticket 4.2: Define a lightweight taxonomy model

Changes:
- support conventions such as:
  - `category:footstep`
  - `surface:wood`
  - `intensity:light`
- keep taxonomy open-ended, not hardcoded into enums

Acceptance criteria:
- taxonomy is expressive enough for later semantic packs and Wwise/FMOD mapping

Testing criteria:
- tests verify taxonomy fields remain open-ended rather than enum-locked
- manifest tests verify taxonomy values serialize predictably
- validation tests verify malformed taxonomy input is handled cleanly

### Ticket 4.3: Selective regeneration

Changes:
- regenerate a specific file or manifest entry
- preserve pack naming and manifest integrity
- support replace-in-place workflow

Acceptance criteria:
- user can replace one bad variation without rebuilding an entire pack manually

Testing criteria:
- integration-style tests verify a selected asset can be regenerated in place
- tests verify unchanged pack members keep their filenames and metadata
- manifest tests verify replaced entries remain coherent after regeneration

### Ticket 4.4: Add process-manifest support

Changes:
- optional manifest output for processed files
- preserve source-to-output lineage where possible

Acceptance criteria:
- processed asset sets can participate in the same metadata workflows as generated packs

Testing criteria:
- process command tests verify optional manifest emission
- tests verify lineage metadata is present when source information is available
- manifest tests verify processed outputs conform to the documented schema

## Epic 5: CLI And Workflow Polish

Purpose:

Close usability gaps that make the tool feel unfinished in longer runs.

### Ticket 5.1: Better batch progress reporting

Changes:
- elapsed time display
- current item indicator
- clearer export-phase messaging

Acceptance criteria:
- long-running batch jobs show meaningful progress

Testing criteria:
- CLI tests verify progress messages include the expected phases and counters
- tests verify `--quiet` suppresses progress output cleanly
- tests verify JSON mode is not polluted by progress text

### Ticket 5.2: Improve JSON consistency

Changes:
- ensure new metadata appears in JSON mode cleanly
- standardize error payload shapes where possible

Acceptance criteria:
- automation consumers do not need command-specific parsing hacks

Testing criteria:
- CLI JSON tests verify stable top-level keys across commands
- error-path tests verify structured error payload shape
- regression tests verify human-readable stderr does not leak into stdout

### Ticket 5.3: Documentation updates for new schema and flags

Changes:
- update `README.md`
- update `docs/ARCHITECTURE.md`
- update `docs/TODO.md`

Acceptance criteria:
- docs and implementation land together

Testing criteria:
- every merged feature changes the relevant docs in the same change set
- command examples in docs are verified against current CLI options
- schema documentation is checked against emitted JSON examples before release

## Suggested Milestones

## Milestone A

Ship:
- backend validation
- manifest versioning
- import hints

Outcome:
- stronger request safety and schema foundation

Milestone test gate:
- all new validation and manifest tests pass
- no regression in existing generate, batch, pack, and CLI suites

## Milestone B

Ship:
- OGG export
- LUFS measurement
- richer inspect

Outcome:
- materially better export and QA workflows

Milestone test gate:
- WAV and OGG export tests pass
- loudness analysis and inspect tests pass
- optional-dependency behavior is covered in CI

## Milestone C

Ship:
- loop scoring
- loop repair options

Outcome:
- ambience workflows become safer and more informative

Milestone test gate:
- loop analysis fixtures produce stable scores
- repair-mode tests and CLI visibility tests pass

## Milestone D

Ship:
- tags
- taxonomy conventions
- selective regeneration
- process manifests

Outcome:
- packs become maintainable units instead of one-off outputs

Milestone test gate:
- tag and taxonomy serialization tests pass
- selective regeneration integration tests pass
- process-manifest tests pass

## Milestone E

Ship:
- progress polish
- JSON cleanup
- final docs alignment

Outcome:
- v0.5 feels cohesive and automation-friendly

Milestone test gate:
- JSON contract tests pass across command suite
- progress-output tests pass
- docs are updated and verified against CLI behavior

## Recommended First Build

If starting implementation immediately, do this first:

1. Ticket 1.1 backend capability validation
2. Ticket 1.2 manifest versioning
3. Ticket 2.1 OGG export

Reason:
- these unblock later metadata and export work
- they improve the current user experience fastest
- they do not require a larger architectural jump
