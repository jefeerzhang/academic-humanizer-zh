# Changelog

All notable changes to this fork are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.6.2] — 2026-10-01

### Fixed

- frontmatter `description` trimmed 1114 → 999 chars to fit the pi loader's 1024-char limit; wording only, no content dropped — all 15 TRIGGER keywords, the C0–C2 red-line clause, and the `natural-chinese` bridge scope are preserved verbatim

## [0.6.1] — 2026-09

### Added

- Layer 1 patterns **1.19** (one-line closers / example restatement / staged run-up) and **1.20** (heading restated in the first sentence), adapted from [blader/humanizer](https://github.com/blader/humanizer) v3.1 §2 / §24 with academic caveats
- Layer 1 **Strength** table (strong vs weak-alone) and paragraph-scale audit note
- Rebuttal mode: lead with the decision, then only agreement-changing evidence ([blader/humanizer](https://github.com/blader/humanizer) §26 adapted)
- `audit_tells.py` weak watch-list for 1.19

### Changed

- README: blader/humanizer pattern count 35 → **26** (v3.1)
- Process audit/rewrite steps: prefer strong tells first; re-check closers / parallelisms / triads / dashes after draft
- `CONTEXT.md`: Layer 1 range 1.1–1.20; rebuttal mode wording updated

## [0.6.0] — 2026-09

### Added

- Layer 1 now cites Wikipedia ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup) and [blader/humanizer](https://github.com/blader/humanizer) (MIT) as sources
- `references/layers/layer-1-general-tells.md`: sourced per-pattern working catalog (watch-lists + before/after, 1.1–1.18) with false-positive guard and academic adaptations
- `references/rules-zh.md` §10: 别乱改清单（作者领域校准白名单：高频表达 + 结论/建议/承接/边际贡献骨架，优先于病灶 A–F 与 §7）；病灶 A「总而言之 / 鉴于此」与 §7「值得注意的是」的冲突已对齐到白名单
- `references/rules-zh.md` §10-C: 第 3 批文献综述与概念界定骨架（29 条，含匹配注意 + 7 条人味信号标注）
- `rules-zh.md` §10 与 README：白名单提炼来源署名（余泳泽等 2025《中国工业经济》· 张大永等 2023《财贸研究》，C 组出自第 1 篇的综述段）
- `scripts/audit_tells.py`: Layer 1 residual AI-tell auditor (strict: placeholder / em dash; weak: per-pattern watch-lists with co-occurrence bar; CI job audits all examples) + `scripts/test_audit_tells.py`
- New Layer 1 patterns: placeholder / unfilled template text, formulaic challenges-and-outlook, fake deeper truth, defensive "not X" moves, rejected fake alternatives; era-aware AI-vocabulary watch-list (2023/2024/2025 model eras, Grok quirks)

### Changed

- Elegant variation and em-dash rules calibrated (weak-tell-alone; em-dash rule kept as academic register, not detection)
- Vague connection/association and knowledge-gap speculation documented as academic-nuanced patterns with Layer 3/4 caveats
- Process step 4 (Report) now requires the `audit_tells.py` exit code in the report and a revise-until-PASS loop on residual Layer 1 tells
- README: new「别乱改清单：AI 白名单」selling-point section (56 whitelisted entries from 3 published papers + 7 human-voice signals) and value-statement bullet; added whitelist-in-action before/after example (house-style 效果示例); section redesigned for impact (centered hero + GitHub alerts + 7/20/29 stats table + humanizer comparison table)

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
