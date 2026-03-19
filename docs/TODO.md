---
project: soundforge
type: todo
status: active
last_updated: 2026-03-19
---

# SoundForge — Comprehensive TODO

Gap analysis between planned docs, BMAD artifacts (37 FRs, 15 NFRs), and the current v0 implementation.

---

## 1. Implementation Gaps (v0 spec vs actual code)

### 1.1 Missing Types from Architecture Spec

The `docs/ARCHITECTURE.md` specifies these core types that were **not implemented**:

- **`AudioSpec`** dataclass — `sample_rate`, `channels`, `format`, `bit_depth`. Used to describe target audio specs independently of config. Currently this is handled implicitly through config resolution, but the type itself doesn't exist.
- **`GenerateRequest`** dataclass — `prompt`, `asset_type`, `duration_seconds`, `loop`, `variations`, `engine`, `tags`. Currently, generation parameters are passed as loose keyword arguments rather than a structured request object.

The architecture doc also specifies `GenerateResult.assets` as `list[AudioAsset]` (plural), but the implementation uses `GenerateResult.asset` (singular). This means the single-generation result type doesn't match the spec — though the implementation choice is reasonable for single generation.

**Impact:** Low for v0. But the structured request type would help with validation, serialization, and future API/web reuse.

### 1.2 Missing `naming.py` Module

The architecture doc and `docs/ARCHITECTURE.md` list `core/naming.py` as a dedicated module for file naming conventions. In the implementation, naming logic lives inline in `export.py` (`sanitize_name()`, `make_single_filename()`, `make_batch_filename()`).

**Impact:** Low. The functions work, just not in their own module.

### 1.3 Seed Not Sent to Backend (FR5 — Partial)

The CLI accepts `--seed` and stores it in the manifest, but the seed is **never sent to the ElevenLabs API**. The ElevenLabs API doesn't appear to support a seed parameter, so this is an API limitation — but the user gets no feedback that their seed had no effect on generation.

**TODO:**
- [ ] Log a warning when `--seed` is used with a backend that doesn't support seeds
- [ ] Check `capabilities()["supports_seed"]` and warn accordingly
- [ ] Still store seed in manifest for metadata tracking

### 1.4 Duration Silently Clamped (NFR8 — Partial)

In `elevenlabs.py`, user-specified duration is silently clamped:
```python
body["duration_seconds"] = max(0.5, min(30.0, duration_seconds))
```

If a user specifies `--duration 50`, they get 30s with no warning. This violates NFR8 ("error messages include the failing parameter and a suggestion for correction").

**TODO:**
- [ ] Warn the user when duration is clamped to backend limits
- [ ] Use `capabilities()["max_duration"]` for validation instead of hardcoded 30

### 1.5 No Pre-Flight Validation Against Backend Capabilities (FR31 — Partial)

The `capabilities()` method exists on backends and is reported by `info`, but **no validation** happens before generation. If the user requests features the backend doesn't support (e.g., loop on a backend without loop support), the request goes through and either fails at the API or gets silently ignored.

**TODO:**
- [ ] Before calling `backend.generate()`, validate duration and loop against `capabilities()`
- [ ] Warn or error if requested features exceed backend capabilities

### 1.6 WAV Files Not Validated Before Writing Manifest (NFR6)

`export.py` writes the WAV file via `soundfile.write()`, then analyzes the **in-memory numpy array** (not the written file) to populate manifest metadata. If the WAV write fails silently or produces a corrupt file, the manifest would still be written with stale metadata.

**TODO:**
- [ ] After writing WAV, read it back with `sf.info()` to verify the file is valid
- [ ] Only write manifest after all WAV files are verified

### 1.7 Postprocess Settings Incomplete in Manifest

The manifest's `postprocess` field only tracks `trim`, `normalize`, `fade_in`, `fade_out`. It does **not** track:
- Loop smoothing applied (yes/no, crossfade duration)
- Sample rate conversion (from → to)
- Channel conversion (from → to)

**TODO:**
- [ ] Add `loop_smooth`, `resample`, `channel_convert` to the postprocess settings dict in `generate.py` and `batch.py`

### 1.8 `loudness_lufs` Field Missing

The `docs/ARCHITECTURE.md` specifies `AudioAsset.loudness_lufs` as a field, and the implementation plan mentions "optional LUFS normalization". The current `AudioAsset` type has no `loudness_lufs` field, and no LUFS measurement is performed.

This was listed as a deferred decision ("whether LUFS normalization belongs in v0 or v0.5").

**TODO:**
- [ ] Decide: add LUFS to v0 or defer to v0.5
- [ ] If added: use `pyloudnorm` library for measurement, add `loudness_lufs` to `AudioAsset`

### 1.9 Optional Ogg Conversion

`docs/PROJECT_OVERVIEW.md` lists "optional `.ogg` conversions" in v0 deliverables. The implementation only supports WAV. This was also listed as a deferred decision.

**TODO:**
- [ ] Decide: add Ogg export to v0 or defer to v0.5
- [ ] If added: use `soundfile` with `format='OGG'` subtype, add `--format` flag to CLI

### 1.10 Asset Type Subtags Not Implemented

`docs/FEATURES.md` lists optional subtags: `footstep`, `impact`, `weapon`, `magic`, `pickup`, `door`, `machine`, `environment`. These are not implemented in v0 — the `--type` flag only accepts the 4 primary types (sfx, ui, ambience, loop).

**Impact:** Low. Subtags are described as "optional" in the docs. But they'd be useful for prompt shaping and manifest metadata.

**TODO:**
- [ ] Add optional `--tags` flag (comma-separated) for subtag metadata
- [ ] Store tags in manifest alongside asset_type

### 1.11 Backend File Naming Mismatch

The `docs/ARCHITECTURE.md` package layout lists `api_sfx.py` and `local_stable_audio.py` as backend files. The implementation uses `elevenlabs.py`. This is fine — the docs describe a generic structure, and the implementation names the actual provider.

**Impact:** None. Documentation artifact.

---

## 2. Test Coverage

Current state: **181 tests passing, 86% overall coverage.** All core modules exceed the 70% NFR target.

### 2.1 Test Files (all present)

- [x] **`test_generate.py`** (200 LOC) — generation pipeline with mocked backend
- [x] **`test_batch.py`** (147 LOC) — batch generation, deterministic naming
- [x] **`test_pack.py`** (108 LOC) — pack assembly, zip, manifest
- [x] **`test_preview.py`** (86 LOC) — playback mocking, sounddevice import error
- [x] **`test_backends.py`** (191 LOC) — ElevenLabs with mocked httpx, factory, errors
- [x] **`test_stable_audio.py`** (280 LOC) — Stable Audio with mocked torch/diffusers, config integration
- [x] **`test_cli.py`** (170 LOC) — Click CliRunner smoke tests

### 2.2 Remaining Coverage Gaps

- [ ] `test_config.py` — Missing: config file discovery walk-up behavior (`_find_config`), global config fallback
- [ ] `test_export.py` — Missing: `export_single()`, `export_batch()`, manifest relative path resolution
- [ ] `test_postprocess.py` — Missing: stereo audio paths for trim/fade/normalize, `run_pipeline` with resampling and channel conversion together

### 2.3 Coverage by Module

| Module | Coverage | Target |
|--------|----------|--------|
| types.py | 100% | ✅ |
| generate.py | 100% | ✅ |
| analysis.py | 100% | ✅ |
| pack.py | 100% | ✅ |
| preview.py | 100% | ✅ |
| backends/elevenlabs.py | 98% | ✅ |
| backends/__init__.py | 95% | ✅ |
| batch.py | 92% | ✅ |
| config.py | 91% | ✅ |
| export.py | 91% | ✅ |
| postprocess.py | 91% | ✅ |
| backends/stable_audio.py | 75% | ✅ (uncovered lines require GPU) |
| cli/commands.py | 70% | ✅ (CLI layer) |

---

## 3. CLI Polish & UX

### 3.1 Help Text Lacks Usage Examples (NFR7)

Click generates `--help` from docstrings, but the current docstrings are minimal:
```
Generate a single sound effect from a text prompt.
```

The spec calls for usage examples in help output.

**TODO:**
- [ ] Add `\b` + example blocks to Click command docstrings:
  ```
  Generate a single sound effect from a text prompt.

  Examples:
    soundforge generate "coin pickup" --engine godot
    soundforge generate "sword clash" --type sfx --duration 2.5
    soundforge generate "cave ambience" --type ambience --loop
  ```

### 3.2 Error Messages Could Be More Actionable (NFR8)

Some error paths produce helpful messages (missing API key), but others are raw exceptions:
- HTTP errors show status code + truncated response body
- Network errors show generic "could not connect" messages

**TODO:**
- [ ] HTTP 401 → "Invalid API key. Check your key at elevenlabs.io/app/settings/api-keys"
- [ ] HTTP 429 → "Rate limit exceeded. Wait and retry, or check your plan at elevenlabs.io"
- [ ] HTTP 500 → "ElevenLabs server error. Try again in a few minutes."

### 3.3 No `--type` Validation in Generate/Batch

The `--type` flag accepts any string. If a user types `--type sfxx`, it passes through without error and gets used as-is in naming and manifest.

**TODO:**
- [ ] Add `type=click.Choice(["sfx", "ui", "ambience", "loop"])` to the `--type` option
- [ ] Same for `--engine`: `type=click.Choice(["godot", "unity", "unreal"])`

### 3.4 No Progress Feedback During Batch Generation

The batch command shows "Generating variation 1/8..." but there's no timing estimate or progress bar. For 8 variations at ~10s each, users wait ~80s with minimal feedback.

**TODO:**
- [ ] Show elapsed time per variation: "Generating variation 3/8... (12.3s elapsed)"
- [ ] Or use a simple progress indicator

### 3.5 Process Command Overwrites Input Files

When `--output` is not specified, `soundforge process file.wav` writes the processed file back to the same path, overwriting the original.

**TODO:**
- [ ] Warn before overwriting input files (or require `--in-place` flag)
- [ ] Or default to a `processed/` subdirectory

---

## 4. Architecture & Code Quality

### 4.1 No README.md

The project has no README. For an open-source tool, this is essential.

**TODO:**
- [ ] Create README.md with: project description, installation, quick start, all commands with examples, configuration, engine presets, contributing

### 4.2 No Git Repository

The project has no `.git` directory or `.gitignore`.

**TODO:**
- [ ] `git init`
- [ ] Create `.gitignore` (Python standard: `__pycache__`, `.venv`, `*.egg-info`, `.coverage`, `dist/`, `.pytest_cache/`)
- [ ] Initial commit

### 4.3 Config File Engine Preset Overrides

The `.soundforge.toml.example` has `[engine.godot]`, `[engine.unity]`, `[engine.unreal]` sections, but the config loader **does not parse these** — engine presets are hardcoded in `ENGINE_PRESETS` dict. Users can't customize engine presets via config file.

**TODO:**
- [ ] Parse `[engine.*]` sections from TOML and merge with hardcoded defaults
- [ ] Allow users to override sample_rate, channels, output_dir per engine

### 4.4 The `process` Command Doesn't Write Manifest

When running `soundforge process`, processed files are written but no manifest is generated. For consistency with `generate` and `batch` (which always produce manifests), `process` could optionally write one.

**TODO:**
- [ ] Add `--manifest` flag to `process` command to optionally write a manifest for processed files

### 4.5 Batch Doesn't Infer Prefix from Engine + Type

When `--prefix` is not provided, the batch command derives it from `{asset_type}_{sanitized_prompt}`. But when an engine preset is active, a more useful default might include the engine context (e.g., for Godot's `audio/sfx/` directory).

**TODO:**
- [ ] Consider whether prefix should be engine-aware when no explicit prefix is given

---

## 5. Deferred Decisions (from DECISIONS.md)

These were explicitly left open during planning:

| Decision | Options | Status |
|----------|---------|--------|
| LUFS normalization | v0 or v0.5 | Deferred to v0.5 |
| Ogg export | v0 or v0.5 | Deferred to v0.5 |
| Local backend candidate | Stable Audio Open vs others | **Done** — Stable Audio Open 1.0 implemented |
| Retro/procedural synthesis | v1 or v1.5 | Deferred to v1.5 per roadmap |

---

## 6. Roadmap Items (from ROADMAP.md)

### v0.5 — "Better production fit"
- [ ] Ogg export alongside WAV
- [ ] Richer inspect command (waveform visualization, spectral info)
- [ ] Improved loop validation (automatic seam detection, loop quality score)
- [ ] Genre/preset templates (platformer, sci-fi, fantasy, survival-horror)
- [ ] More robust naming and folder conventions
- [ ] Backend fallback configuration (try backend A, fall back to backend B)

### v1 — "Library and workflow maturity"
- [ ] Searchable local asset library (index generated files, search by prompt/type/tags)
- [ ] Regeneration and replace workflows (regenerate a specific file in a pack)
- [ ] Pack-level metadata editing (rename, retag, re-describe after generation)
- [ ] Tagging and categorization system
- [ ] Retro/procedural SFX backend (sfxr-style synthesis for 8-bit/arcade sounds)
- [ ] Better preview UX (waveform display, A/B comparison, variation cycling)

### v1.5 — "Game-audio specialization"
- [ ] Footstep pack generators (by surface: grass, stone, wood, metal, sand)
- [ ] Weapon family generators (light/medium/heavy variants per weapon type)
- [ ] UI set generators (click, hover, confirm, cancel, error — cohesive sets)
- [ ] Environment ambience set builders (forest, cave, city, space, underwater)
- [ ] Reference-audio conditioning (generate "similar to this reference")
- [ ] First FMOD/Wwise middleware export helpers

### v2 — "Expanded creative surface"
- [ ] Loopable music cues
- [ ] Layered stem output
- [ ] Adaptive/layered music primitives
- [ ] FMOD/Wwise helper exports
- [ ] Web app or hosted API
- [ ] Team libraries and review workflows

### Long-term — "Game-audio operating layer"
- [ ] Editor plugins for Godot/Unity/Unreal
- [ ] GDD-to-audio task extraction
- [ ] Agent-assisted project-wide audio generation
- [ ] Scene/gameplay capture to sound suggestions
- [ ] Runtime procedural hybrids

---

## 7. Priority Summary

### Must Fix (v0 polish before "done")

| # | Item | Status |
|---|------|--------|
| 1 | Warn when `--seed` is used with unsupported backend | ✅ Done (generate.py) |
| 2 | Warn when duration is clamped to backend limits | ✅ Done (both backends) |
| 3 | Add `click.Choice` validation for `--type` and `--engine` | ✅ Done (commands.py) |
| 4 | Validate WAV file after writing, before manifest | Open |
| 5 | Track loop_smooth/resample/channel_convert in manifest | ✅ Done (generate.py, batch.py) |
| 6 | Add usage examples to command help text | ✅ Done (commands.py) |
| 7 | Create `.gitignore` and initialize git repo | Open |
| 8 | Warn before overwriting input in `process` command | ✅ Done (defaults to processed/ subdir) |

### Should Do (v0 quality bar)

| # | Item | Status |
|---|------|--------|
| 9 | Write `test_generate.py` | ✅ Done (200 LOC) |
| 10 | Write `test_batch.py` | ✅ Done (147 LOC) |
| 11 | Write `test_pack.py` | ✅ Done (108 LOC) |
| 12 | Write `test_backends.py` | ✅ Done (191 LOC) |
| 13 | Write `test_cli.py` | ✅ Done (170 LOC) |
| 14 | Parse `[engine.*]` config sections | ✅ Done (config.py) |
| 15 | Better HTTP error messages (401/429/500) | ✅ Done (elevenlabs.py) |
| 16 | Create README.md | ✅ Done |
| 17 | Local GPU backend (Stable Audio Open) | ✅ Done (stable_audio.py + test_stable_audio.py) |
| 18 | Setup command for local backend | ✅ Done (HuggingFace auth flow) |

### Nice to Have (v0.5 candidates)

| # | Item | Effort |
|---|------|--------|
| 19 | Add `--tags` flag for asset subtags | Small |
| 20 | Add `GenerateRequest` dataclass for structured requests | Medium |
| 21 | LUFS normalization with `pyloudnorm` | Medium |
| 22 | Ogg export with `--format` flag | Medium |
| 23 | Batch progress with elapsed time | Small |
| 24 | Process command `--manifest` flag | Small |
