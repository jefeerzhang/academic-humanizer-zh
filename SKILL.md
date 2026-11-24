---
name: academic-humanizer-zh
version: 0.7.0
description: |
  Edit AI-assisted academic prose (papers, theses, rebuttals, reviews) and grant
  proposals (NSF Summary/Description, NIH Specific Aims, fellowships) so each claim
  ties to its number, figure, or citation and the voice matches the author's. Never
  alters numbers, results, equations, sample sizes, dates, places, cite keys, or named
  methods/metrics. Not for blogs, marketing, personal essays, or evading AI-use
  disclosure.

  Uses Layer 5 author-sample style comparison (`scripts/compare_author_style.py`) for
  voice calibration instead of fixed-phrase Layer 7 injection (disabled by default).
  C0–C2 red lines dominate. Non-academic Chinese prose (公众号 / 公文 / 商业 / 新闻 / 文学)
  defers to sibling `natural-chinese`.

  TRIGGER: "润色论文" / "润色一下" / "改写学术稿" / "去 AI 味"
  / "academic humanizer" / "polish manuscript" / "edit my draft" / "match my voice"
  / "funding proposal review" / "NSF / NIH aims" / "Specific Aims"
  / "降低 AI 痕迹" / "学术改稿" / "reviewer-proof" / "submit-grade edit"
  / "摘要松一松" / "科普段落自然化".
license: MIT
compatibility: claude-code codex morphmind opencode
allowed-tools: [Read, Write, Edit, Grep, Glob, Bash, WebFetch, WebSearch, AskUserQuestion, NotebookEdit]
metadata:
  sibling_skills:
    - name: natural-chinese
      url: https://github.com/jefeerzhang/natural-chinese
      role: handles non-academic Chinese prose (公众号 / 公文 / 商业 / 新闻 / 文学)
---

# Academic Humanizer

Improve the clarity and voice of AI-assisted *academic* writing while keeping the precise,
evidence-bound voice scholarship requires and matching the author's own style. Preserves
every number, result, and citation; not a tool for evading AI-use disclosure.

## When to use

Editing or reviewing academic prose: paper sections, abstracts, rebuttals, related work,
and **funding proposals** (NSF, NIH Specific Aims, fellowship / foundation proposals;
see Layer 6). **Not** for blogs, marketing, or personal essays. Do **not** inject
colloquial first-person voice (`我觉得`, humor, emoji personality) or stock hedging
templates (`笔者认为`, `样本限制使…需谨慎对待`) into a manuscript. Fixed-phrase
Layer 7 injection is **disabled by default**; preserve whitelisted scholarly `we` / `本研究`,
and calibrate voice against the author's own prior writing sample via Layer 5
(`scripts/compare_author_style.py`). If auditing a legacy draft with Layer 7 enabled,
restrict academic hedging to Discussion / Conclusion / Limitations / 政策含义 only.
For technical writing, neutral and precise *is* the human voice.
Proposals have a different register from papers — ambition language a paper would trim is
appropriate there; apply Layer 6, not the paper layers' stricter trimming, to vision statements.

## Core principle

Academic writing already has a correct human voice: neutral, precise, third-person plural
("we"), every claim tied to its evidence. The job is to (1) strip the AI *tells* without
casualizing, and (2) enforce the discipline a general humanizer misses:
**every claim earns its number, figure, or citation, and no verb is stronger than its evidence.**

## Process

1. **Read** the manuscript and any author writing sample; note the document type
   (paper vs. proposal) and the target venue or funding agency. When the author supplies
   a prior paper or writing sample, extract its baseline first with
   `scripts/compare_author_style.py --sample <sample> --profile-only` (sentence rhythm,
   self-reference convention, connectives, hedging density). For proposals, also apply
   Layer 6 and preserve appropriate vision.
2. **Audit** (do not edit yet): list each detected pattern with its location and proposed
   fix, and each empirical claim's evidence status. Prefer **strong** Layer 1 tells first
   (see `references/layers/layer-1-general-tells.md` Strength); *weak alone* patterns need
   company in the same passage. Look at **paragraph shape** and **sentence-length
   variation** as well as sentences. Do **not** draft a fixed-phrase Layer 7 injection
   plan (disabled by default; never invent new limitations or speculations to add hedging).
3. **Rewrite**: same structure and content, all claims and citations preserved, tells
   removed, over-claims matched to evidence, legitimate hedging kept. Match sentence
   rhythm, self-reference (`本文` / `本研究` / `we`), and connective habits to the
   author's sample when provided. Before rewriting, read
   `examples/before-after-zh-academic.md` to calibrate edit strength and output format
   (English prose: `examples/before-after.md`). Only when auditing legacy Layer 7 drafts,
   read `examples/before-after-zh-academic-injection.md` for boundary reference. After a
   draft, re-check tells that often survive a first pass: negative parallelisms (1.7),
   one-line closers (1.19), rule-of-three (1.8), em dashes (1.17), and flat sentence
   rhythm (L2.rhythm).
4. **Report**: cleaned text plus a short change log + a **diff** + an **unchanged-claim
   declaration**. Cover everything the original covered. Whenever an edit is finalized:
   - Run `scripts/audit_tells.py` on the result (`--combined` on the before/after file, or
     `--after` on the cleaned text; scans Layer 1 English tells, C7 Chinese A–F tells, and
     L2 sentence-length uniformity) and report its exit code; if exit ≥ 1 (WARN / FAIL),
     revise the residual tells before finalizing.
   - When an author sample was supplied, run
     `scripts/compare_author_style.py --sample <sample> --after <cleaned>` and report its
     exit code (0 = PASS / 1 = WARN on rhythm, self-reference, connective, or hedging drift).
   - If auditing a legacy draft with Layer 7 markers, run
     `scripts/validate_layer7_injection.py` and report its exit code (0 = PASS / 1 = WARN /
     2 = FAIL for first-person abuse, forbidden-section hedge, blacklist hit, meta-label
     leak, or C0–C2 red-line break).
   **Completion:** every numbered item 1–4 is present, the unchanged-claim declaration is
   explicit on each C0/C1/C2 category — not just a blanket "no changes" — and the
   `audit_tells.py` exit code is reported.

---

## Language routing and the C0–C7 contract

This skill is language-aware. Route by the **dominant language of the editable prose**,
not by raw character ratio (a single English paragraph with one Chinese abstract line
should not be re-routed to the Chinese ruleset):

- **Default**: English ruleset (Layers 1–6 in the references/ tree).
- **Switch to Chinese** (`references/rules-zh.md`, layer C7) when **both** hold:
  (a) the editable prose is **structured as continuous Chinese paragraphs** (not isolated
  CJK strings inside English prose), and
  (b) the author has marked the target language as Chinese **or** the venue is a
  Chinese-language journal.
- When in doubt: ask the author before routing. Wrong routing is worse than a brief pause.

**The C0–C7 contract (never violated):**

- **C0 — Numbers, equations, p-values, statistics, citations are sacred.** Never invent,
  drop, or alter a number, equation, citation, sample size, date, or place. Preserve
  every cite key.
- **C1 — Claims are not deleted, merged, or altered.** Same structure and content;
  rewrite only the surface (claim↔evidence matching stays in Layer 4 / 6.5).
- **C2 — Terminology and named methods stay verbatim.** Formal definitions, method /
  metric names, technical terms, symbols.
- **C3 — Preserve legitimate scholarly constructs** (evidence-tied hedging, passive
  voice, "we"/"本研究", semicolons). See Layer 3.
- **C4 — Claim↔evidence discipline.** Every claim earns its number/figure/citation; no
  verb stronger than its evidence (Layer 4; proposals: claim↔feasibility, Layer 6.5).
- **C5 — Voice and venue matching** (Layer 5).
- **C6 — Funding-proposal mode** when the text is a grant proposal (Layer 6).
- **C7 — Chinese local-style fixes**, loaded from `references/rules-zh.md` when the
  routing rule above holds: 套话开头/过渡/收尾, 价值判断词饱和, 抽象主语, 名词化动词,
  排比三件套, 假客观元评论, 句式冗余 — subject to the same red lines in C0–C2.

---

## Document-style routing (voice calibration & legacy Layer 7)

Beyond language, route by **document style** — the layer that should run.

| Input signature | Routes to |
|---|---|
| Hard academic markers (`\cite{}` / `\citep{}` / `\begin{equation}` / `p < 0.0x` / `n = xxx` / `.bib` pointer) | **Layer 1–5 + C7** (full academic pass); **Layer 7 disabled** |
| Grant proposal markers (NIH Aims / NSF Project Summary / fellowship structure) | **Layer 1–6 + C7** (grant mode); **Layer 7 disabled** |
| Author supplies prior paper / writing sample (any academic genre, or user asks "摘要松一松" / "科普段落自然化" / "match my voice") | **Layer 1–5 + C7 + `scripts/compare_author_style.py`** — calibrate sentence rhythm, self-reference, connectives, and natural hedging to the author's own sample |
| Continuous Chinese academic prose without an author sample | **Layer 1–5 + C7** — clean A–F tells and vary sentence rhythm; **do NOT inject stock Layer 7 phrases** |
| Non-academic Chinese (公众号 / 公文 / 商业 / 新闻 / 文学) | **Defer to sibling skill [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese)** — this skill does not edit |

**Why Layer 7 fixed-phrase injection is disabled by default (v0.7.0):** injecting stock phrases (`笔者认为`, `样本限制使…需谨慎对待`, `目前尚不清楚`) creates a new template-AI tell and risks inventing limitations absent from the source (violating C1). `references/layers/layer-7-academic-injection.md` and `scripts/validate_layer7_injection.py` remain as a legacy safety guard (exit 0/1/2; forbids meta-label leaks, blacklist hits, and hedging outside Discussion / Conclusion / Limitations / 政策含义).

---

## Layer 1: General AI-tell catalog (inline)

Scan for and fix the general patterns, subject to the academic exceptions in Layer 3.
**Strong** tells (edit on one clear sighting): negative parallelisms ("not just X, but Y");
placeholder / unfilled template text; fake deeper truth ("at its core", "what really
matters"); defensive "not X" moves that answer an objection no one raised; rejected fake
alternatives ("A tempting approach would be…, but…"); **one-line closers and example
restatement** ("This shows the importance of…", "That distinction matters.", staged
run-ups like "Here's the thing"); **heading restated in the first sentence** (heading +
a line that only renames it).
**Weak alone** (need company or density): inflated significance ("marking a pivotal
moment"); superficial "-ing" tails; promotional / figurative language; vague attributions;
AI vocabulary (*delve, underscore, intricate, tapestry, testament, landscape (abstract),
pivotal, showcase, foster, leverage (filler), realm, seamless, bolster, garner,
meticulous, align with, gate/gated (figurative), vibrant, crucial, emphasize/emphasizing,
highlight (verb)*); copula avoidance ("serves as" → "is"); rule-of-three padding; elegant
variation (flag only when several synonyms cycle for one referent in a paragraph); filler
("it is worth noting that", "in order to" — density, not single use); formulaic
challenges-and-outlook; knowledge-gap speculation; **em-dashes** (remove entirely; recast
with commas, colons, parentheses, or separate sentences — an academic-register rule, not a
detection claim: one dash alone is not evidence).
Also fix **overlong, clause-stacked sentences** (split them; see 2.11).

**Before:** *Additionally, an enduring testament to the method's value is its ability to
delve into intricate dependencies, showcasing a seamless integration that underscores its
pivotal role.*
**After:** *The method also captures higher-order dependencies, which the baselines miss
(Table 2).*

> Full Layer 1 working catalog — per-pattern watch-lists, before/after pairs, strength
> table, false-positive guard, and academic adaptations — lives in
> `references/layers/layer-1-general-tells.md` and is loaded on demand (1.1–1.20). Sources:
> Wikipedia ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
> (WikiProject AI Cleanup) and [blader/humanizer](https://github.com/blader/humanizer) v3.1
> (MIT). When a "After" example here or in the catalog shows a number, it must already exist
> in the author's tables or Before text — never invent magnitudes (C0).

---

## Layer 2: Academic AI tells (full catalog → reference)

Load `references/layers/layer-2-academic-tells.md` for the 11 academic-specific
patterns — the highest-frequency are over-claiming verbs and overlong, clause-stacked
sentences. The contract is the same as the inline Layer 1 catalog: detect → match the
rule → rewrite without changing evidence.

---

## Layer 3: Preserve these (do NOT over-correct)

A general humanizer flattens legitimate scholarly constructs. Keep them.

- **Evidence-tied hedging is correct and required.** Keep "suggests", "is consistent
  with", "we hypothesize that", "may indicate", "appears to" when the claim is genuinely
  uncertain. *Wrong fix:* turning *"the results suggest X"* into *"the results prove X"*:
  this manufactures over-claiming. Keep the calibrated verb.
- **Passive voice** is fine when the actor is irrelevant: *"Samples were normalized to
  total protein."*
- **First-person plural "we"** is standard; do not rewrite to avoid it.
- **Semicolons and an occasional triple** are fine in moderation. Em-dashes are the
  exception: remove them entirely (Layer 1), recasting with commas, colons, parentheses,
  or separate sentences.
- Numbers, citations, named methods/metrics, and formal definitions stay verbatim,
  subject to the C0–C2 red lines above; this layer adds nothing to them.

---

## Layer 4: Claim–evidence discipline

For every empirical claim, check (a) is it backed by a number, figure, table, or citation
in the text, and (b) does the verb match the strength of that evidence?

**C0 boundary:** Layer 4 may **surface numbers already present** in the manuscript (text,
tables, figures, cited work). If no number exists → **soften the verb** or **add an evidence
pointer** (`Table 2`, `Figure 3`), never fabricate a magnitude.

- **Unbacked claim → add the evidence pointer or soften.**
  *Before:* *Our method is more robust.*  *After:* *Our method's accuracy is more stable
  under distribution shift than the baseline (Figure 3).* (Figure 3 must already exist.)
- **Verb stronger than evidence → downgrade.**
  *Before:* *This demonstrates that our method is universally superior.*
  *After:* *On these three datasets, our method matches or exceeds the strongest baseline
  (Table 2).*
- **Vague magnitude when a number already appears elsewhere → surface it with attribution.**
  *Before:* *a large improvement* (Table 2 reports 2–6%).  *After:* *a 2–6% improvement
  in balanced accuracy over the strongest baseline (Table 2).* Prefer ranges over single
  averaged values unless the averaging method is stated.

---

## Layer 5: Voice and venue matching (author-sample calibration)

Voice calibration replaces fixed-phrase injection. When the author supplies prior papers
or drafts, run `scripts/compare_author_style.py --sample <sample> --profile-only` before
rewriting to measure their actual baseline across four dimensions: (1) sentence-length
mean, standard deviation, and CV (short/long mix); (2) self-reference convention
(`本文` / `本研究` / `笔者` / `我们` or `we` / `this paper`); (3) connective vocabulary
and density; (4) natural hedging and punctuation habits. After rewriting, run
`scripts/compare_author_style.py --sample <sample> --after <cleaned>` (exit 0 = aligned,
1 = drift warning) and fix flagged drifts (e.g., flattened rhythm or foreign connectives).
Match the venue's register too (e.g., ICLR / NeurIPS: terse, direct, results-forward;
Nature / PNAS: more expository). Absent a sample, default to clean, precise,
venue-appropriate prose without injecting stock first-person or hedging templates.

---

## Layer 6: Funding-proposal mode (NSF, NIH)

A proposal is not a paper. It is sold on **vision plus feasibility**, not on finished
results, and reviewers score it. The register shift matters: ambition language that the
paper layers would trim ("long-term goal", "pioneer", "transformative", "establish a
foundation") is *appropriate and expected* here, provided a credible plan and evidence
back it. So in proposal mode, **do not flatten the vision**; enforce a different
discipline instead: **claim ↔ feasibility**.

> Full Layer 6 (NSF / NIH structure, first-3-pages primacy, claim↔feasibility, proposal-
> specific weak moves) lives in `references/layers/layer-6-proposals.md` and is loaded
> on demand.

---

## Document-type fallbacks (run BEFORE editing)

The skill is for **editable prose**. If the input is something else, fall back instead
of editing the wrong thing:

- **Plain `.bib` / `.bbl` / only a references list** → say so and stop. Don't rewrite
  bibliography entries; cite keys are sacred.
- **`.tex` with mostly equations and macros** → edit only the prose inside the document
  text regions; never touch math environments, `\cite{}`, `\ref{}`, `\label{}`.
- **Reviewer comments / rebuttal letter** → switch to **rebuttal mode**: politeness +
  point-by-point structure; **lead with the decision / answer**, then keep only the
  evidence or constraint that would change whether the reviewer agrees — do not rebuild
  the full diagnosis, restated problem, or proof-of-plan the reviewer already has from
  their comment and the manuscript (blader/humanizer §26, adapted). Do not apply paper
  tightening or Layer 7 injection. Preserve author `we` / `本研究`; edit for clarity and
  tone only.
- **Cover letter, response-to-reviewers, conference summary** → keep professional
  register; do not strip "we respectfully" politeness as AI fluff.
- **Non-academic text (blog, marketing, README, chat)** → refuse and explain why.
- **Empty input or single paragraph under 30 words** → ask the author whether to proceed
  (often the author meant a different file).

When any fallback triggers, **report it** in the change log: "Input was X; skill Y was
not applied because Z."

---

## Output

Return, in this order:

1. **Cleaned text** (full, same structure, every claim preserved).
2. **Diff** (paragraph-level or sentence-level before/after), so the author can review.
3. **Change log**: patterns removed (by type and count), claims softened or given
   evidence pointers, voice / venue notes, routing decision (English / Chinese / N/A),
   any fallback triggered.
4. **Unchanged-claim declaration**: confirm that no number, equation, citation, sample
   size, date, place, or named method / metric was altered. If any of those *had* to
   change for a reason, list it explicitly with the reason.

   For an **executable** check of C0–C2 (numbers, stats, citations, math, dates,
   structure, named terms), run `scripts/validate_red_lines.py` on the before /
   after pair. Exit code 0 = pass; 1 = warnings; 2 = red-line violation. See
   `scripts/README.md` for details.

If the author only asked for a "show me the diff" version, return the diff + change log
without rewriting inline.
