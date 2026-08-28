---
name: academic-humanizer-zh
version: 0.4.0
description: |
  Edit AI-assisted academic prose (papers, theses, rebuttals, reviews) and grant
  proposals (NSF Project Summary/Description, NIH Specific Aims, fellowship/foundation
  applications) so each claim is tied to its number, figure, or citation, and the voice
  matches the author's own. Never alters numbers, results, equations, sample sizes,
  dates, places, cite keys, or named methods/metrics. Not for blogs, marketing, or
  personal essays, and not for evading AI-use disclosure.

  TRIGGER on any of: "润色论文" / "润色一下" / "改写学术稿" / "去 AI 味"
  / "academic humanizer" / "polish manuscript" / "edit my draft" / "match my voice"
  / "funding proposal review" / "NSF / NIH aims" / "Specific Aims"
  / "降低 AI 痕迹" / "学术改稿" / "reviewer-proof" / "submit-grade edit".
license: MIT
compatibility: claude-code codex morphmind opencode
allowed-tools: [Read, Write, Edit, Grep, Glob, Bash, WebFetch, WebSearch, AskUserQuestion, NotebookEdit]
---

# Academic Humanizer

Improve the clarity and voice of AI-assisted *academic* writing while keeping the precise,
evidence-bound voice scholarship requires and matching the author's own style. Preserves
every number, result, and citation; not a tool for evading AI-use disclosure.

## When to use

Editing or reviewing academic prose: paper sections, abstracts, rebuttals, related work,
and **funding proposals** (NSF, NIH Specific Aims, fellowship / foundation proposals;
see Layer 6). **Not** for blogs, marketing, or personal essays, and **never** injects
opinion, humor, or first-person "personality" into a manuscript. For technical writing,
neutral and precise *is* the human voice. Proposals have a different register from papers
— ambition language a paper would trim is appropriate there; apply Layer 6, not the
paper layers' stricter trimming, to vision statements.

## Core principle

Academic writing already has a correct human voice: neutral, precise, third-person plural
("we"), every claim tied to its evidence. The job is to (1) strip the AI *tells* without
casualizing, and (2) enforce the discipline a general humanizer misses:
**every claim earns its number, figure, or citation, and no verb is stronger than its evidence.**

## Process

1. **Read** the manuscript and any author writing sample; note the document type
   (paper vs. proposal) and the target venue or funding agency. For proposals, also apply
   Layer 6 and preserve appropriate vision.
2. **Audit** (do not edit yet): list each detected pattern with its location and proposed
   fix, and each empirical claim's evidence status.
3. **Rewrite**: same structure and content, all claims and citations preserved, tells
   removed, over-claims matched to evidence, legitimate hedging kept. Before rewriting,
   read `examples/before-after-zh-academic.md` to calibrate edit strength and output
   format (English prose: `examples/before-after.md`).
4. **Report**: cleaned text plus a short change log + a **diff** + an **unchanged-claim
   declaration**. Cover everything the original covered.

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

Layers 1–6 are language-agnostic and apply to all text; C7 adds the Chinese-specific
patterns on top.

---

## Layer 1: General AI-tell catalog (inline)

Scan for and fix the general patterns, subject to the academic exceptions in Layer 3:
inflated significance ("marking a pivotal moment"); superficial "-ing" tails that fake
depth ("..., highlighting..."); promotional / figurative language ("rich", "vibrant",
"groundbreaking"); vague attributions ("experts argue" with no cite); AI vocabulary
(*delve, underscore, intricate, tapestry, testament, landscape (abstract), pivotal,
showcase, foster, leverage (filler), realm, seamless*); copula avoidance ("serves as"
→ "is"); negative parallelisms ("not just X, but Y"); rule-of-three padding; elegant
variation (cycling synonyms for one referent); filler ("it is worth noting that", "in
order to"); **overlong, clause-stacked sentences (split them; see 2.11)**;
and **em-dashes (remove entirely; recast with commas, colons, parentheses, or
separate sentences)**.

> Full Layer 2 (academic-specific tells, 2.1–2.11) lives in
> `references/layers/layer-2-academic-tells.md` and is loaded on demand.

**Before:** *Additionally, an enduring testament to the method's value is its ability to
delve into intricate dependencies, showcasing a seamless integration that underscores its
pivotal role.*
**After:** *The method also captures higher-order dependencies, which the baselines miss
(Table 2).*

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

- **Unbacked claim → add the evidence pointer or soften.**
  *Before:* *Our method is more robust.*  *After:* *Our method's accuracy drops by 2
  points under distribution shift, versus 11 points for the baseline (Figure 3).*
- **Verb stronger than evidence → downgrade.**
  *Before:* *This demonstrates that our method is universally superior.*
  *After:* *On these three datasets, our method matches or exceeds the strongest baseline
  (Table 2).*
- **Vague magnitude → a number or RANGE, attributed.**
  *Before:* *a large improvement.*  *After:* *a 2–6% improvement in balanced accuracy
  over the strongest baseline.* Prefer ranges (e.g., "2–6%") over single averaged values
  unless the averaging method is stated, and attribute each number to its method, metric,
  and baseline. When comparing, lead with the comparison against the strongest competitor,
  not the trivial baseline.

---

## Layer 5: Voice and venue matching

If the author supplies prior papers, read a sample first and note sentence rhythm,
connective habits, level and placement of hedging, how they open sections, notation, and
recurring phrasings, then match them. Match the venue's register too (e.g., ICLR /
NeurIPS: terse, direct, results-forward; Nature / PNAS: more expository). Absent a
sample, default to clean, precise, venue-appropriate prose, not the casual, opinionated
voice of a general-purpose humanizer.

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
- **Reviewer comments / rebuttal letter** → switch to **rebuttal mode** (politeness +
  point-by-point structure); do not apply paper tightening.
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
