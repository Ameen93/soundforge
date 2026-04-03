---
project: soundforge
type: todo
status: active
last_updated: 2026-03-29
---

# TODO

This is the current backlog after reconciling the docs with the shipped implementation.

## High Priority

- [ ] Add OGG export support while keeping WAV as the canonical processing format.
- [ ] Decide whether `process` should optionally emit a manifest for processed files.

## Medium Priority

- [ ] Add LUFS analysis and decide whether normalization by LUFS belongs in the next milestone.
- [ ] Add richer inspect output such as more analysis metadata.
- [ ] Add tags or subcategory metadata for assets and manifests.
- [ ] Consider introducing a structured request type if API or service reuse becomes a near-term goal.
- [ ] Improve batch progress reporting with elapsed time or a simple progress indicator.

## Low Priority

- [ ] Consider moving naming helpers into a dedicated module if export responsibilities keep growing.
- [ ] Consider engine-aware default prefixes if that proves useful in practice.
- [ ] Consider a retro or procedural backend once the current workflow is stronger.

## Done Recently

- [x] seed warning for unsupported backends
- [x] duration clamp warnings in backend code
- [x] WAV validation after export
- [x] richer postprocess metadata in manifests
- [x] CLI help examples
- [x] type and engine validation in CLI options
- [x] `process` default output to `processed/`
- [x] engine preset overrides from config
- [x] backend capability preflight validation for loop and duration requests
- [x] README and repo documentation refresh

## Notes

- `README.md` is the user-facing source of truth.
- `docs/ARCHITECTURE.md` is the implementation source of truth.
- `docs/V0_5_EXECUTION_PLAN.md` is the concrete next-phase execution plan.
- This file should stay short and only track real remaining work.
