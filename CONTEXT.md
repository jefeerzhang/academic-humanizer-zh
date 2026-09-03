# CONTEXT.md — academic-humanizer-zh domain glossary

Single-context repo. Read this before naming concepts in issues, ADRs, or agent output.

## What this repo is

A **skill + auditors** package for editing AI-assisted **academic** prose (papers, theses, rebuttals, grant proposals) and **Chinese academic extensions** (C7 rules, optional Layer 7 injection). Not for blogs, marketing, or general Chinese prose (`natural-chinese` sibling skill).

## Layer stack (English + shared)

| Term | Meaning |
|------|---------|
| **Layer 1** | General AI-tell catalog (inline in `SKILL.md`) |
| **Layer 2** | Academic-specific tells → `references/layers/layer-2-academic-tells.md` |
| **Layer 3** | Preserve scholarly constructs (hedging, passive, `we`) |
| **Layer 4** | Claim↔evidence discipline — surface existing numbers, never invent |
| **Layer 5** | Voice / venue matching |
| **Layer 6** | Funding-proposal mode (NSF / NIH) → `references/layers/layer-6-proposals.md` |
| **Layer 7** | Optional Chinese academic injection (hedging + ≤1 academic first-person) → `references/layers/layer-7-academic-injection.md` |
| **C7** | Chinese local-style rules → `references/rules-zh.md` |

## Red-line contract (C0–C2)

| Term | Rule |
|------|------|
| **C0** | Numbers, stats, citations, equations, dates — sacred |
| **C1** | Claims not deleted or altered |
| **C2** | Terminology and named methods verbatim |

Mechanical check: `scripts/validate_red_lines.py`. Layer 7 check: `scripts/validate_layer7_injection.py`.

## Routing (do not confuse)

- **Rebuttal mode** — edits rebuttals (politeness + point-by-point); not a no-edit fallback
- **Layer 7** — see SKILL.md "Document-style routing" + `references/layers/layer-7-academic-injection.md`; **加载 ≠ 注入**

## ADRs

Architecture decisions live in `docs/adr/` when recorded. None required for day-to-day skill edits.

## Maintainer

Fork: [jefeerzhang/academic-humanizer-zh](https://github.com/jefeerzhang/academic-humanizer-zh). Upstream: [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer).
