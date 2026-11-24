# CONTEXT.md — academic-humanizer-zh domain glossary

Single-context repo. Read this before naming concepts in issues, ADRs, or agent output.

## What this repo is

A **skill + auditors** package for editing AI-assisted **academic** prose (papers, theses, rebuttals, grant proposals) and **Chinese academic extensions** (C7 rules, author-sample style comparison via Layer 5). Not for blogs, marketing, or general Chinese prose (`natural-chinese` sibling skill).

## Layer stack (English + shared)

| Term | Meaning |
|------|---------|
| **Layer 1** | General AI-tell catalog (inline in `SKILL.md`; sourced working catalog → `references/layers/layer-1-general-tells.md`, 1.1–1.20 with strong/weak strength tags; sources: Wikipedia "Signs of AI writing" + blader/humanizer v3.1) |
| **Layer 2** | Academic-specific tells → `references/layers/layer-2-academic-tells.md` |
| **Layer 3** | Preserve scholarly constructs (hedging, passive, `we`) |
| **Layer 4** | Claim↔evidence discipline — surface existing numbers, never invent |
| **Layer 5** | Voice / venue matching — author-sample style calibration via `scripts/compare_author_style.py` |
| **Layer 6** | Funding-proposal mode (NSF / NIH) → `references/layers/layer-6-proposals.md` |
| **Layer 7** | Legacy Chinese academic injection (fixed-phrase injection **disabled by default** in v0.7.0; safety-guard reference only) → `references/layers/layer-7-academic-injection.md` |
| **C7** | Chinese local-style rules → `references/rules-zh.md` (audited by `scripts/audit_tells.py` C7.A–F + L2.rhythm) |

## Red-line contract (C0–C2)

| Term | Rule |
|------|------|
| **C0** | Numbers, stats, citations, equations, dates — sacred |
| **C1** | Claims not deleted or altered |
| **C2** | Terminology and named methods verbatim |

Mechanical checks: `scripts/validate_red_lines.py` (C0–C2), `scripts/audit_tells.py` (Layer 1 + C7 A–F + L2 sentence rhythm), `scripts/compare_author_style.py` (Layer 5 author-sample voice calibration), `scripts/validate_layer7_injection.py` (legacy Layer 7 safety guard).

## Routing (do not confuse)

- **Layer 5 author-sample calibration** — active whenever the author supplies prior papers/drafts; compares sentence rhythm, self-reference, connectives, and hedging via `scripts/compare_author_style.py`
- **Layer 7 loaded** — disabled by default in v0.7.0 (no longer auto-loaded on Chinese academic cues; see SKILL.md "Document-style routing")
- **Layer 7 injection** — fixed-phrase injection retired; legacy guard restricts any existing hedging/first-person to Discussion / Conclusion / Limitations / 政策含义 and blocks meta-label leaks (`references/layers/layer-7-academic-injection.md`)
- **Rebuttal mode** — edits rebuttals (politeness + point-by-point; lead with decision, then only agreement-changing evidence); not a no-edit fallback

## ADRs

Architecture decisions live in `docs/adr/` when recorded. None required for day-to-day skill edits.

## Maintainer

Fork: [jefeerzhang/academic-humanizer-zh](https://github.com/jefeerzhang/academic-humanizer-zh). Upstream: [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer).
