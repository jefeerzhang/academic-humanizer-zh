# Academic Humanizer (Chinese Fork)

> *「AI 起草的论文你敢直接投稿吗？——每个数字、引用、术语必须一字不动。」*

[![license](https://img.shields.io/badge/license-MIT-2f8f57?style=flat-square)](LICENSE)
&nbsp;[![version](https://img.shields.io/badge/version-0.5.0-2f8f57?style=flat-square)](CHANGELOG.md)
&nbsp;[![skill](https://img.shields.io/badge/skill-papers_and_grant_proposals-1c1a15?style=flat-square)](SKILL.md)
&nbsp;![built by](https://img.shields.io/badge/built_by-NSF,_CAREER,_NIH_R01-555?style=flat-square)
&nbsp;[![skills.sh](https://img.shields.io/badge/skills.sh-jefeerzhang%2Facademic--humanizer--zh-2f8f57?style=flat-square)](https://skills.sh/jefeerzhang/academic-humanizer-zh)
&nbsp;[![audit](https://github.com/jefeerzhang/academic-humanizer-zh/actions/workflows/audit.yml/badge.svg)](../../actions/workflows/audit.yml)

> ⚠️ **场景分工**：本 skill 负责学术场景（论文 / 摘要 / 学位稿 / grant proposal / 科普段落）。
> 通用中文（公众号 / 公文 / 商业 / 新闻 / 新媒体 / 文学）请走兄弟技能 **[`natural-chinese`](https://github.com/jefeerzhang/natural-chinese)**。

**5 秒价值陈述**

- **14 类**中文学术 AI 痕迹 · **6 段** grant proposal 模式 · **7 条** C0–C2 红线契约
- `scripts/validate_red_lines.py` 把「数字没动」从口头承诺变成 CI 退出码 `0/1/2/3`
- 每个改动都附 before/after 对照 + diff + unchanged-claim declaration

## Why we built this

Some of us write a lot of papers and grant proposals, and our team started using AI to help with
drafts. The problem is that AI-assisted drafts come out generic and verbose, with "In recent years..."
openers, inflated phrasing, and over-long sentences. They also drift from the author's own voice and
lose the precision scholarship depends on.

There are tools called "humanizers," but they are built for blogs and marketing. Run one on a paper or
an NSF proposal and it flattens the precision along with everything else. The careful wording academic
writing depends on is the first thing to go.

So we put together our own. To calibrate it, we had the AI compare its own drafts with our team's
accepted papers and funded proposals, and we went through the differences by hand. It is nothing fancy,
and it is not about gaming review, defeating detectors, or adding fake novelty. We wanted AI-assisted
drafts to read clearly and in the author's own voice, with the numbers, citations, and claims left
exactly as written.

## Ethics and disclosure

This is an editing aid for clarity and voice, calibrated to an author's own prior accepted work. It does
not generate findings, invent data, or change citations, and it is not designed to evade AI-use
detection. Using it does not remove your obligation to disclose AI assistance: always follow the
disclosure policy of the venue you submit to.

## See it work

> [!CAUTION]
> **Before** (a generic AI draft):
>
> In recent years, continual learning has attracted increasing attention and achieved remarkable
> success. However, existing methods still face crucial challenges. In this proposal, we propose a novel
> framework that leverages cutting-edge techniques to delve into these intricate problems, paving the way
> for a transformative paradigm that will revolutionize the field.

> [!TIP]
> **After** (clear, in the author's voice, with claims tied to evidence):
>
> Continual learning matters, but today's methods stay empirical and their principles are unclear. That
> limits reliability and progress. This proposal builds a principled framework on three fronts:
> adaptation, soft supervision, and cross-domain knowledge. We demonstrate it on autonomous driving and
> network management.

**More before/after passes** are in [`examples/before-after.md`](examples/before-after.md): a general
example, an NIH Specific Aims page, and a funded NSF CAREER summary.

---

## What it does

- **Sharpens clarity and voice:** trims generic AI phrasing ("paves the way", "extensive experiments",
  "to the best of our knowledge", "In recent years...", delve/underscore/tapestry, rule-of-three, very
  long sentences, em-dashes) and brings the draft closer to the author's own style.
- **Keeps claims tied to evidence:** no verb stronger than the data (`prove` → `show empirically`),
  and vague magnitudes become attributed ranges.
- **Leaves real scholarship alone:** evidence-tied hedging, passive voice where it fits, `we`,
  definitions, symbols, and every citation. It doesn't change a number or a reference.
- **Has a separate mode for grant proposals (NSF, NIH):** it keeps the vision a paper would trim, and
  spends most of the effort on the first pages, since that's what reviewers score.
- **Returns a diff and an unchanged-claim declaration**, so the author can verify that no number,
  citation, or claim was altered.
- **Has an executable red-line auditor** (`scripts/validate_red_lines.py`) that mechanically checks
  C0–C2 (numbers, statistics, citations, math, dates, structure, named terms) on a before / after
  pair and exits with code 0 / 1 / 2 for CI integration. See `scripts/README.md`.

## 中文扩展（Chinese Academic Extension）

This fork adds Chinese academic writing support on top of the upstream `AIScientists-Dev/academic-humanizer`:

- **`references/rules-zh.md`** — Chinese-language local rules. Routes automatically when the editable
  prose is **structured as continuous Chinese paragraphs** (not just by raw CJK ratio, to avoid
  mis-routing an English manuscript with a Chinese abstract). Covers six typical AI-tells (套话开头/
  过渡/收尾、价值判断词饱和、抽象主语、名词化动词、排比三件套、假中立元评论) and explicitly
  protects academic conventions that must not be changed (passive voice, "本研究/本文", long
  attributives, statistical notation, references, project numbers). v0.5.0 adds §9 — the academic
  injection (Layer 7) exemption table.
- **`references/layers/layer-7-academic-injection.md`** — v0.5.0 bridge from sibling skill
  [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese). Loads only when the input
  matches "学术 + 口语化段落 / 科普段 / 社科摘要 / humanistic introduction" branch (see
  "Document-style routing" in `SKILL.md`). Activates cognitive hedging + first-person density
  limiting only; other "立人味" tools remain closed in academic register.
- **`examples/before-after-zh-academic.md`** — a submission-grade before/after using a real Chinese
  social-science abstract, with each edit mapped to a specific rule.
- **`examples/before-after-zh-academic-injection.md`** — v0.5.0 example. Three paragraph types
  (social-science abstract / 科普段 / 引言人文叙述) showing Layer 7 **loaded vs injection disabled**
  (example 3: C7 only, no hedging injection in intro), with C0–C2 + Layer 7 density checks.
- **`examples/before-after-tri-research-report-zh.md`** — a real-world before/after on a
  `tri-research` deep-research report (30 references, 30 inline `[N]` citations, 7 fixed sections),
  demonstrating that the C0–C2 red lines (references / citations / structure / numbers untouched)
  hold on structured research reports, not just paper abstracts.
- **`scripts/validate_layer7_injection.py`** — v0.5.0 companion to `validate_red_lines.py`. Audits
  first-person count (≤1), cognitive hedging density (1–3 / 千字), forbidden-section drops (no
  hedging in Methods/Results), anti-human-trap blacklist (no emoji, no 小红书体, no 口语第一人称),
  and delegates C0–C2 to `validate_red_lines.py`. Exit codes 0/1/2 for CI integration.

The English rules and contracts (C0–C7) live in `SKILL.md` (~280 lines: core layers + routing).
Heavy catalogs (Layer 2, Layer 6, Layer 7) live under `references/layers/` and load on demand.

---

## Install

```bash
# Claude Code / Codex / OpenCode / Cline / Cursor / Windsurf — pick one:
npx skills add jefeerzhang/academic-humanizer-zh --global    # or:
git clone https://github.com/jefeerzhang/academic-humanizer-zh ~/.claude/skills/academic-humanizer-zh
```

It is a plain `SKILL.md` plus examples, so it also runs as a skill or system prompt for **Codex** and
**MorphMind**. Point your agent at `SKILL.md`.

## Use

```
/academic-humanizer-zh
[paste a section, or point at main.tex]
# optionally: "match my voice from prior_paper.pdf; target venue: ICLR"
```

## Repository layout

```
.
├── CONTEXT.md                        # Domain glossary (layers, C0–C2, routing terms)
├── SKILL.md                          # Core contract + Layers 1, 3–5 (~280 lines) + Document-style routing
├── references/
│   ├── rules-zh.md                   # C7 Chinese local rules (load on routing) — §9 Layer 7 exemption table
│   └── layers/
│       ├── layer-2-academic-tells.md # 2.1–2.11 detailed catalog
│       ├── layer-6-proposals.md      # NSF / NIH structure + claim↔feasibility
│       └── layer-7-academic-injection.md  # v0.5.0: academic-filtered 破+立双轨 (cognitive hedging + 第一人称限密度)
├── examples/
│   ├── before-after.md               # English (paper, NIH Aims, NSF CAREER) — CI-audited pairs
│   ├── before-after-zh-academic.md   # Chinese social-science abstract
│   ├── before-after-zh-academic-injection.md  # v0.5.0: Layer 7 enabled/disabled comparisons
│   └── before-after-tri-research-report-zh.md  # Real tri-research report (30 cites)
├── scripts/
│   ├── validate_red_lines.py         # C0-C2 mechanical auditor (CI-friendly exit codes)
│   ├── validate_layer7_injection.py  # v0.5.0: Layer 7 injection-density auditor
│   └── README.md                     # how to use the auditors
└── assets/                           # README banners
```

## Make it yours

The rules here reflect one group's voice. Fork the repo and adapt them to your own: point it at a few of
your past papers, keep the checks that fit your field, and adjust the rest. It is meant to be
personalized, not a one-size-fits-all filter.

## How it works

Seven layers: general AI-tell catalog → academic-specific tells → preserve scholarly conventions →
claim↔evidence matching → voice/venue calibration → funding-proposal mode (NSF/NIH) → optional Layer 7
academic injection (Chinese 社科摘要 / 科普段 / humanities intro). The audit→rewrite loop is defined in
[`SKILL.md`](SKILL.md). Chinese ruleset **C7** loads on continuous-Chinese routing; heavy catalogs
(Layer 2, Layer 6, Layer 7) live under `references/layers/` and load on demand.

Layer 7 (`references/layers/layer-7-academic-injection.md`) loads only for matching document
signatures. It adds cognitive hedging + first-person density limiting — the academic-filtered subset of
sibling skill [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese)'s "破+立双轨".
C0–C2 red lines remain the dominant contract.

## Scenario routing

The skill picks its layer stack by **document-style signature**:

| Input signature | Routes to |
|---|---|
| Hard academic markers (`\cite{}`, `p < 0.0x`, `n = xxx`, `.bib`, equations) | Layer 1–6 + C7 (full pass); **Layer 7 NOT activated** |
| Grant proposal markers (NIH Aims / NSF Project Summary / fellowship) | Layer 1–6 + Layer 6 grant mode + C7; **Layer 7 NOT activated** |
| Continuous Chinese with academic cues (摘要 / 本文提出 / 研究方法 / 政策含义), no hard markers | Layer 1–5 + C7 + **Layer 7 loaded** (inject hedging/first-person only in Discussion / Conclusion / Limitations / 政策含义) |
| User says "摘要松一松 / 科普段落自然化 / 不要太死板" | **Force-activate Layer 7** |
| Non-academic Chinese (公众号 / 公文 / 商业 / 新闻 / 文学) | Defer to sibling skill [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese) |

Full routing logic and edge cases in [`SKILL.md`](SKILL.md) → "Document-style routing".

## Sibling skills

- [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese) (MIT) — general-purpose
  Chinese "破+立双轨" protocol covering 6 scenarios (公文 / 学术 / 商业 / 新闻 / 新媒体 / 文学).
  Layer 7 of this skill borrows the academic-filtered subset of `natural-chinese`'s 5 "立人味"
  tools. For non-academic Chinese prose, defer to `natural-chinese`.

## Document-type fallbacks

If the input is a `.bib` / `.bbl`, a `.tex` mostly equations, or non-academic text, the skill
**does not edit** and reports why. **Rebuttal / response-to-reviewers letters** use **rebuttal mode**
(politeness + point-by-point structure) — they are edited, not treated as a no-edit fallback.
Cover letters keep professional register; do not strip "we respectfully" politeness as AI fluff.

## References

Layer 6 distills the *stable* structure of NSF and NIH proposals. For current, binding requirements
(page limits, formatting, deadlines), consult the source:

- NSF: [Proposal & Award Policies & Procedures Guide (PAPPG)](https://www.nsf.gov/policies/pappg)
- NSF: [CAREER program](https://new.nsf.gov/funding/opportunities/career-faculty-early-career-development-program)
- NIH: [Write Your Application](https://grants.nih.gov/grants/how-to-apply-application-guide/format-and-write/write-your-application.htm) (Specific Aims, Significance, Innovation, Approach)

## Acknowledgments

- **[blader/humanizer](https://github.com/blader/humanizer)** (MIT). *Focus:* removing general
  AI-writing patterns for blog, casual, and encyclopedic text. This skill reuses its general AI-tell
  catalog (Layer 1) and extends it for academic prose.
- **[koaeraser/ARMS](https://github.com/koaeraser/ARMS)**. *Focus:* an autonomous pipeline for
  statistics/methodology research papers (idea → validated, revised manuscript). A complementary,
  broader-scope project that informed the claim-evidence and numerical-precision emphasis here.

This skill is the narrower piece: a single-purpose **editing pass** that sharpens clarity and matches
claims to evidence while preserving the author's scholarly voice.

## License

MIT.
