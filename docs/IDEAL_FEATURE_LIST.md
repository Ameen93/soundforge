---
project: soundforge
type: strategy
status: draft
last_updated: 2026-03-29
tags: soundforge, roadmap, feature-list, game-audio
---

# Ideal Feature List

This document defines the ideal product surface for SoundForge if the goal is:

**A developer should be able to create, process, organize, preview, and integrate most or all audio assets needed for a game from one workflow.**

It is intentionally broader than the current v0 scope.

## Research Summary

Current official docs and platforms suggest the real target is not just text-to-sound generation.

The market and engine stack already expect:
- prompt-based sound effect generation with duration, looping, and prompt control
- multiple game-ready import formats
- engine-specific compression and import behavior
- metadata-rich audio workflows
- middleware structures such as events, switches, RTPCs, random containers, and programmer-driven audio

Key signals:
- ElevenLabs positions sound effects around duration, looping, prompt influence, and game-ready usage.
- Stable Audio Open provides local text-to-audio generation up to 47 seconds at 44.1 kHz stereo.
- Godot recommends WAV for short repetitive SFX and OGG for longer audio, and supports looped WAV behavior.
- Unity imports WAV, OGG, MP3, FLAC, and others, then transcodes based on import settings.
- Unreal imports multiple formats, converts internally, and exposes compression choices and Sound Wave workflows.
- Wwise automation is explicitly designed for importing audio, creating objects, generating banks, and setting game parameters and switches through WAAPI.
- Wwise Switch Containers and Random Containers are first-class runtime design patterns for things like footsteps by surface.
- FMOD’s official examples emphasize event parameters, banks, and programmer sounds for dynamic playback.

## Product Principle

To be fully usable for game development, SoundForge should become:

**a game-audio asset pipeline and integration layer**

not merely:

**a prompt-to-WAV generator**

## Ideal Feature Set

## 1. Asset Creation

### 1.1 Sound effect generation

- one-shot SFX generation
- UI sound generation
- impact, weapon, pickup, machine, magic, vehicle, and environment presets
- batch variation generation
- seedable deterministic generation where supported
- reference-audio-conditioned generation
- style transfer from a pack or reference set

### 1.2 Ambience and loops

- ambient bed generation
- seamless loop generation
- loop repair and seam scoring
- long-form ambience assembly from shorter generated layers
- biome or scene presets such as cave, forest, city, spaceship, underwater

### 1.3 Dialogue and voice

- placeholder NPC voice generation
- barks, callouts, and effort sounds
- voice pack generation by character
- line variation generation
- pronunciation or style controls
- subtitle and transcript pairing

### 1.4 Music and adaptive music

- short stingers
- menu and combat loop generation
- tension or intensity variants
- stem generation when model support is good enough
- adaptive cue structures for layered playback

Inference:
This is necessary for the claim “all sound assets needed in a game.” Today SoundForge is strongest on SFX and ambience, but full game coverage eventually implies voice and music surfaces too.

## 2. Postprocess And Repair

### 2.1 Cleanup

- silence trim
- fade-in and fade-out
- peak normalization
- LUFS measurement and optional normalization
- de-click and de-pop repair
- DC offset removal
- noise reduction where useful
- tail trim and release shaping

### 2.2 Format and channel handling

- WAV export
- OGG export
- MP3 export where useful
- mono, stereo, and multichannel handling where engines allow it
- sample-rate conversion presets
- bit-depth control

### 2.3 Loop tooling

- automatic loop-point discovery
- loop quality score
- crossfade repair
- ping-pong loop export where engine supports it
- explicit loop metadata export

### 2.4 Analysis

- peak dBFS
- RMS and LUFS
- crest factor
- duration and silence windows
- transient score
- spectral centroid or brightness proxy
- onset density
- clipping detection

## 3. Asset Library And Search

### 3.1 Local library

- index generated and imported assets
- search by prompt, tags, engine, category, duration, loudness, and source backend
- duplicate and near-duplicate detection
- favorite, reject, shortlist states

### 3.2 Pack and taxonomy support

- tags such as `footstep`, `surface/wood`, `weapon/light`, `ui/confirm`
- hierarchical categories
- per-asset notes
- asset lineage: prompt, seed, backend, reference asset, postprocess chain

### 3.3 Reuse workflows

- regenerate selected variants
- replace one file in a pack without rebuilding everything
- derive a new pack from an approved pack style

## 4. Engine-Aware Export

### 4.1 Import-ready output

- Godot presets
- Unity presets
- Unreal presets
- project-relative output paths
- engine-appropriate defaults for SFX vs ambience vs music vs VO

### 4.2 Format strategy by use case

- short repetitive SFX exported as WAV by default
- long ambience and music optionally exported as OGG
- import recommendations encoded in metadata

Inference:
This follows official engine guidance. Godot explicitly recommends WAV for short repetitive SFX and OGG for longer audio. Unity and Unreal accept multiple formats but still require good import-time choices.

### 4.3 Engine metadata

- manifest with per-file import hints
- loop intent
- voice vs music vs SFX classification
- suggested compression mode
- suggested streaming vs memory load policy
- spatial vs 2D intent

## 5. Middleware Integration

This is the biggest missing layer if SoundForge is meant to be a serious game-audio production tool.

### 5.1 Wwise support

- import audio into Wwise via WAAPI
- create Sound SFX objects
- create Random Containers automatically for variation sets
- create Switch Containers for surface or state families
- assign Switches and States
- generate SoundBanks
- set metadata and object properties

### 5.2 FMOD support

- export FMOD-friendly folder structures and metadata
- generate event manifests
- create event templates for one-shots, loops, and layered events
- parameter-ready pack structures
- programmer-sound friendly dialogue and VO structures

Inference:
Wwise WAAPI and FMOD event workflows indicate that “game-ready” audio is often not just files in a folder. It is files plus event structures, switch logic, parameter hooks, and bank/build automation.

## 6. Runtime-Oriented Authoring

### 6.1 Semantic asset families

- footsteps by surface
- weapons by class and intensity
- UI sets by action type
- elemental magic families
- material interaction sets such as wood, metal, stone, cloth

### 6.2 Parameterized sets

- intensity variants
- speed variants
- size variants
- material variants
- damaged or healthy state variants
- indoor vs outdoor ambience variants

### 6.3 Dynamic audio structures

- event packs with randomization metadata
- state-based ambience sets
- layer groups for adaptive mixing
- transition sounds and stingers

## 7. Prompting And Creative Controls

### 7.1 Prompt UX

- prompt templates by category
- guided prompting fields such as material, motion, environment, perspective, intensity
- negative prompts where backend supports them
- prompt linting and improvement suggestions

### 7.2 Consistency controls

- style locks per project
- reusable style profiles
- pack-level coherence controls
- “generate more like this” workflows

### 7.3 Hybrid generation

- AI generation plus procedural synthesis for retro or synthetic SFX
- layering generated audio with user-supplied source layers
- combine generated transient with procedural tail or vice versa

## 8. Preview, Review, And Approval

### 8.1 Audition tools

- instant preview
- A/B compare
- random cycle through a pack
- preview at different playback speeds
- waveform and spectrogram views

### 8.2 Review workflow

- accept or reject variants
- compare by loudness-normalized playback
- annotate reasons for rejection
- shortlist best-of pack exports

### 8.3 Agent and team workflows

- JSON everywhere
- machine-readable review state
- CI-safe noninteractive mode
- deterministic artifact directories

## 9. Automation And Pipeline APIs

### 9.1 CLI and core API

- stable CLI command surface
- reusable Python API
- structured request objects
- structured result objects

### 9.2 Batch automation

- generate from CSV or JSON spec
- generate from a game design audio sheet
- regenerate all missing variants
- partial reruns and resume support

### 9.3 Integration hooks

- Wwise WAAPI support
- engine plugin or importer hooks
- local web UI or API later

## 10. Asset Sources Beyond Generation

If SoundForge is supposed to cover all game audio needs, it should not assume every asset must be generated from text.

- import external WAV, OGG, MP3, FLAC assets
- process recorded Foley
- process vendor packs into a normalized taxonomy
- use existing packs as style references
- merge generated and recorded assets into one manifest system

## Recommended Product Tiers

## Tier 1: Must-have to become a strong game-audio tool

- OGG export
- LUFS analysis
- stronger loop tooling
- tags and taxonomy
- richer inspect and preview
- regeneration and replacement workflows
- better pack metadata
- engine import hints in manifests

## Tier 2: Must-have to become truly game-development ready

- Wwise automation
- FMOD-oriented export and event templates
- semantic pack generators such as footsteps by surface and UI sets
- reference-conditioned generation
- searchable local library
- review and approval workflow

## Tier 3: Needed for the “all game audio assets” claim

- dialogue and bark workflows
- voice pack generation
- short music and stinger workflows
- adaptive or layered music support
- hybrid AI plus procedural synthesis

## Recommended Roadmap Direction

If the goal is serious usefulness rather than flashy breadth, the ideal order is:

1. deepen SFX and ambience production quality
2. add library, taxonomy, and regeneration workflows
3. add middleware and engine automation
4. expand into voice workflows
5. expand into music and adaptive systems

## Suggested Next Concrete Features

If choosing the next 10 features only, the best list is:

1. OGG export
2. LUFS measurement and normalization
3. loop analysis and repair
4. tags and hierarchical asset taxonomy
5. searchable local asset library
6. regeneration and selective replacement
7. semantic pack generators such as footsteps by surface and UI sets
8. engine import hints in manifests
9. Wwise WAAPI integration for import plus random and switch containers
10. FMOD event-template export for one-shots, loops, and parameterized sets

## Sources

- ElevenLabs sound effects docs: https://elevenlabs.io/docs/capabilities/sound-effects
- ElevenLabs sound effects quickstart: https://elevenlabs.io/docs/eleven-api/guides/cookbooks/sound-effects
- Stable Audio diffusers docs: https://huggingface.co/docs/diffusers/en/api/pipelines/stable_audio
- Stable Audio Open model card: https://huggingface.co/stabilityai/stable-audio-open-1.0
- Godot importing audio samples: https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_audio_samples.html
- Godot AudioStreamWAV: https://docs.godotengine.org/en/4.4/classes/class_audiostreamwav.html
- Unity audio file format compatibility: https://docs.unity3d.com/jp/current/Manual/AudioFiles-compatibility.html
- Unity audio compression: https://docs.unity3d.com/ja/current/Manual/AudioFiles-compression.html
- Unreal importing audio files: https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-audio-files
- Wwise WAAPI overview: https://www.audiokinetic.com/en/library/edge/?id=waapi.html&source=SDK
- Wwise audio import example: https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?id=ak_wwise_core_audio_import_example_importing_audio_files_to_create_sound_sfx_and_audio_file_sources.html&source=SDK
- Wwise switch containers: https://blog.audiokinetic.com/en/library/edge/?id=defining_contents_and_behavior_of_switch_containers&source=Help
- Wwise object creation on import: https://www.audiokinetic.com/library/edge/?id=creating_wwise_objects_on_import&source=Help
- FMOD Studio API examples: https://www.fmod.com/assets/html5/studio_api/demo.html
- FMOD programmer sound example: https://www.fmod.com/assets/html5/studio_api/programmer_sound.html
