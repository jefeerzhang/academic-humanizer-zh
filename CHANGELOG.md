# Changelog

All notable changes to this fork are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.5.0] — 2026-09

### Added

- Layer 7 academic injection (cognitive hedging + ≤1 academic first-person) with auditor
- Chinese C7 ruleset (`references/rules-zh.md`) and shipped before/after examples
- Shared `combined_parser.py`; CI unit tests + `run_examples.py`
- `CONTEXT.md`, `docs/adr/`, `.github/triage-labels.json`

### Fixed

- Combined-markdown After spans no longer include `### 修改对照` meta
- Compound `结果与讨论` / `Results and Discussion` split so Discussion hedges are not false-failed
- CJK colloquial intensifier blacklist (`挺好` / `蛮不错` / …) without unreliable `\b`
- Process loop: default calibration on C7 example; injection example only when Layer 7 loaded

### Changed

- Document SOT: routing in `SKILL.md`; density/blacklist/checklist in `layer-7-academic-injection.md`
- Allowed injection landing: Discussion / Conclusion / Limitations / 政策含义; 引言 forbidden
