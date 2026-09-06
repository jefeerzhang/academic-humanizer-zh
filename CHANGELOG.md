# Changelog

All notable changes to this fork are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.6.0] — 2026-09

### Added

- Layer 1 now cites Wikipedia ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup) and [blader/humanizer](https://github.com/blader/humanizer) (MIT) as sources
- `references/layers/layer-1-general-tells.md`: sourced per-pattern working catalog (watch-lists + before/after, 1.1–1.18) with false-positive guard and academic adaptations
- `scripts/audit_tells.py`: Layer 1 residual AI-tell auditor (strict: placeholder / em dash; weak: per-pattern watch-lists with co-occurrence bar; CI job audits all examples) + `scripts/test_audit_tells.py`
- New Layer 1 patterns: placeholder / unfilled template text, formulaic challenges-and-outlook, fake deeper truth, defensive "not X" moves, rejected fake alternatives; era-aware AI-vocabulary watch-list (2023/2024/2025 model eras, Grok quirks)

### Changed

- Elegant variation and em-dash rules calibrated (weak-tell-alone; em-dash rule kept as academic register, not detection)
- Vague connection/association and knowledge-gap speculation documented as academic-nuanced patterns with Layer 3/4 caveats
- Process step 4 (Report) now requires the `audit_tells.py` exit code in the report and a revise-until-PASS loop on residual Layer 1 tells

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
