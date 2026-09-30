# Layer 1 — General AI-tell catalog (sourced)

> Loaded by `SKILL.md` Layer 1 when the editor needs per-pattern watch-lists and examples.
> `SKILL.md` carries the compact contract; this file is the working catalog.
> **C0 guard:** numbers in "After" examples must already appear in the author's tables or Before text — never invent magnitudes.
> **Academic guard:** this is the *general* layer. Academic exceptions (Layer 3) and claim↔evidence discipline (Layer 4) always dominate; when a general pattern conflicts with a legitimate scholarly construct, Layer 3 wins.

## Sources

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup (CC BY-SA). The general patterns below track that page, which updates as model behavior changes (era-dependent vocabulary, declining em-dash rates, etc.).
- [blader/humanizer](https://github.com/blader/humanizer) v3.1 (MIT) — same lineage, adapted for academic prose; strength ordering and patterns 1.19–1.20 follow its §2 / §24.

## Strength (edit discipline)

Aligned with blader/humanizer v3.x: a tell counts in proportion to how rarely a careful writer would make it on purpose. Audit **paragraph shape** as well as sentences (a contrast split across two sentences, three parallel examples, or the same closer after every section is one tell at larger scale).

| Strength | Meaning | Patterns here |
| -------- | ------- | ------------- |
| **Strong** | One clear sighting justifies an edit | 1.7, 1.10, 1.13, 1.14, 1.15, 1.19, 1.20 |
| **Weak alone** | Act only when several tells share a passage, or density is high | 1.1–1.6, 1.8, 1.9, 1.11, 1.12, 1.16–1.18 |

Pattern tags: **[W]** wiki-derived · **[B]** blader-derived · **[WB]** both · **[A]** academic adaptation. Strength tags below: **[strong]** / **[weak alone]**.

---

## 1.1 Inflated significance, legacy, broader trends [WB] [weak alone]

**Watch:** stands/serves as, is a testament/reminder, a crucial/pivotal/vital/key role or moment, underscores/highlights its importance, reflects broader, symbolizing, setting the stage for, marking/shaping, key turning point, evolving landscape, focal point, indelibly/deeply rooted.

**Before:** *This work marks a pivotal moment, paving the way for a new paradigm.*
**After:** *This work addresses one failure mode of prior methods: error accumulation under long-horizon rollout (Section 4).*

## 1.2 Superficial "-ing" tails [WB] [weak alone]

**Watch:** highlighting/underscoring/emphasizing…, ensuring…, reflecting/symbolizing…, contributing to…, cultivating/fostering…, encompassing…, enhancing…, valuable insights, align/resonate with.

**Before:** *The model captures long-range dependencies, showcasing a seamless integration that underscores its value.*
**After:** *The model captures long-range dependencies, which the baselines miss (Table 2).*

## 1.3 Promotional / sales language [WB] [weak alone]

**Watch:** boasts, vibrant, rich (figurative), profound, enhancing, showcasing, exemplifies, commitment to, groundbreaking, renowned, featuring, diverse array, in the heart of, nestled.

**Before:** *Our approach boasts a groundbreaking framework grounded in profound theoretical insights.*
**After:** *Our approach combines three ideas: a metadata-aware encoder, a soft-supervision loss, and cross-domain transfer (Section 3).*

## 1.4 Vague attributions [WB] [weak alone]

**Watch:** industry reports, observers have cited, experts argue, some critics argue, several sources (when only one or two are cited).

**Before:** *Experts argue that the method is more robust.*
**After:** *Two recent studies report higher robustness under distribution shift [7, 12].*

## 1.5 AI vocabulary (era-aware) [W] [weak alone]

**Watch (2023–2024 era):** Additionally (sentence-initial), boasts, bolstered, crucial, delve, emphasizing, enduring, garner, intricate/intricacies, interplay, key (adjective), landscape (abstract), meticulous, pivotal, underscore, tapestry, testament, valuable, vibrant.

**Watch (2024–2025 era, GPT-4o):** align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant.

**Watch (2025+ era, GPT-5):** emphasizing, enhance, highlighting, showcasing.

**Model quirks:** Grok overuses *causal*, *empirical*, *correlate*, *underscore*. *Delve* faded sharply after 2024 — still reads as AI in 2023-era drafts, less so in new ones.

**Rule:** these words co-occur; one instance is weak, several in one passage is the tell. Check the After text against these lists before finishing (this is the mechanical audit target).

## 1.6 Copula avoidance [WB] [weak alone]

**Watch:** serves as/stands as/marks/functions as/operates as/represents [a], boasts/features/maintains/offers [a], refers to (for the thing itself).

**Before:** *This module serves as the core encoder and features a gating mechanism.*
**After:** *This module is the core encoder and has a gating mechanism.*

## 1.7 Negative parallelisms [WB] [strong]

**Watch:** not just X but (also) Y, not X but Y, X rather than Y, no X, no Y, just Z.

**Before:** *This isn't merely an optimization trick; it's a paradigm shift.*
**After:** *The update rule is simple, and that is what makes the method stable.*

## 1.8 Rule of three [WB] [weak alone]

**Watch:** three-item lists used to sound complete (adjective, adjective, adjective; short phrase ×3). Also check **paragraph scale**: three parallel examples plus a lesson.

**Before:** *The framework is novel, elegant, and transformative.*
**After:** *The framework is new relative to prior work (Section 2).*

## 1.9 Vague connection / association [W, academic-nuanced] [weak alone]

**Watch:** in connection with, connected with, associated with (when it replaces a relationship the author could name).

**Before:** *The decoder is closely associated with the feature-alignment stage, in connection with the contrastive loss.*
**After:** *The decoder consumes the feature-alignment stage's output, and the contrastive loss trains both.*

**Academic caveat:** "X is associated with Y" is *correct calibrated language* in empirical work (as opposed to "causes"). Flag only the padding use — vague "connection" where the author could name the relationship. Do not "fix" correlational phrasing in Results.

## 1.10 Placeholder / unfilled template text [W] [strong]

**Watch:** [Describe…], [citation needed] left in a draft, INSERT_…, PASTE_…, 202x-xx-xx dates, TODO, <URL>.

**Before:** *We evaluate on three datasets [INSERT_DATASET_NAMES] with the loss in Eq. (XX).*
**After:** *We evaluate on ImageNet, CIFAR-100, and iNaturalist with the loss in Eq. (3).*

Report any placeholder the author must fill in the change log; never invent the missing value yourself (C0).

## 1.11 Formulaic challenges-and-outlook [W, academic-nuanced] [weak alone]

**Watch:** Despite these promising results / Despite these challenges, several challenges remain, future work will, Challenges and Future Directions (as a stock closing).

**Before:** *Despite these promising results, several challenges remain. Future work will address them.*
**After:** *Two limitations remain: encoder runtime on long sequences, and tuning on small corpora.*

**Academic caveat:** limitations / discussion sections are required; the tell is the content-free restatement formula, not the mention of limitations.

## 1.12 Knowledge-gap disclaimer + speculation [W→A] [weak alone]

**Watch:** not extensively documented in the literature, little is known about, not widely available/documented (uncited) + likely/possibly/may reflect (speculative gap-fill).

**Before:** *While specific details are not extensively documented in the literature, this likely reflects the method's novelty.*
**After:** *We found no published evaluation of the method on long-horizon tasks.*

**Academic caveat:** "little is known" is legitimate when true and ideally cited; the tell is the uncited disclaimer followed by an invented "likely" explanation. Ties to Layer 4: soften or cite — never fabricate the gap-fill.

## 1.13 Fake deeper truth [B] [strong]

**Watch:** at its core, what really matters, the real question is, fundamentally, in reality, the heart of the matter.

**Before:** *At its core, what really matters is whether the model can generalize.*
**After:** *The open question is whether the model generalizes beyond its training distribution.*

## 1.14 Defensive "not X" moves (answering unraised objections) [B] [strong]

**Watch:** This is not to say…, To be clear, It should be noted that this does not imply…, Don't get me wrong, I'm not arguing that…, Some might say… but.

**Before:** *This is not to say that pretraining doesn't matter; rather, the issue is the fine-tuning signal.*
**After:** *The issue is the fine-tuning signal.*

Keep the sentence only if the text already raised the objection, or the claim itself is real (Layer 4).

## 1.15 Rejected fake alternatives [B] [strong]

**Watch:** a tempting approach would be, one might be tempted to, an obvious approach would be, it would be easy to just, you might think… but.

**Before:** *A tempting approach would be to retrain the encoder on every update, but that would be too slow. We update in place.*
**After:** *We update the encoder in place.*

Remove the fake option; keep the real constraint.

## 1.16 Filler and qualifier stacking [WB] [weak alone]

**Watch (filler):** in order to, due to the fact that, at this point in time, it is worth noting that, it is important to note that, the fact that (redundant). **Density, not single use:** one "in order to" is ordinary human prose — flag when filler piles up.

**Watch (qualifier stacking):** could potentially possibly, might arguably, to some extent, somewhat, relatively, fairly, quite — stacked in one claim.

**Before:** *It could potentially possibly be argued that the method might have some effect.*
**After:** *The method may improve held-out accuracy.*

**Academic caveat:** calibrated hedging (suggests, may indicate, is consistent with) is Layer 3-protected; cut only the stacking, never the evidence-tied hedge.

## 1.17 Em dashes [WB] [weak alone]

**Rule:** the final rewrite must not contain em dashes (—) or en dashes (–); recast with commas, colons, parentheses, or separate sentences. This is an academic-register rule, not a detection claim: one dash alone is not evidence of AI (human editors use them; ChatGPT's rate has dropped, Claude's has not).

**Before:** *The method — though simple — works well.*
**After:** *The method is simple but works well.*

## 1.18 Elegant variation [WB] [weak alone]

**Watch:** cycling several synonyms for one referent in the same paragraph (the encoder / the feature extractor / the representation module).

**Rule:** flag only when dense (3+ switches for one referent in a paragraph). A single synonym switch is ordinary, and the Wikipedia list treats elegant variation as a weak / historical indicator (non-native writers also avoid repetition).

**Before:** *The encoder improves accuracy. The feature extractor adds stability. The representation module runs fast.*
**After:** *The encoder improves accuracy, adds stability, and runs fast.*

## 1.19 One-line closers and example restatement [B] [strong]

**Watch:** a one-sentence paragraph that only restates the paragraph before it; "That is the real win."; "That distinction matters."; "Let that sink in."; the same closer after several sections; a sentence after an example, scene, or number that *names what it showed* without adding a claim ("This shows the importance of…", "The message was clear:", "It was a lesson in…"); staged run-ups before a routine claim ("Let's dive in", "Here's the thing", "Here's what you need to know").

**Before:** *Accuracy rises by 4 points on ImageNet (Table 2). This shows the importance of metadata-aware encoding.*
**After:** *Accuracy rises by 4 points on ImageNet (Table 2).*

**Before (staged run-up):** *Here's the thing. The encoder fails when feature types are dropped.*
**After:** *The encoder fails when feature types are dropped.*

**Academic caveat:** Keep evidence pointers that name a result already in the text ("Table 2 shows…", "As Figure 3 indicates…"). Cut only the closer that *explains the example the reader just saw* or the run-up that delays the claim. Do not strip a limitations sentence that adds a new constraint.

## 1.20 Heading restated in the first sentence [B] [strong]

**Watch:** a heading followed by a one-line paragraph that only renames the heading before real content begins.

**Before:**
> ## Ablation
>
> We conduct an ablation study.
>
> Removing the type embedding drops AUROC by 3 points (Table 4).

**After:**
> ## Ablation
>
> Removing the type embedding drops AUROC by 3 points (Table 4).

**Academic caveat:** A first sentence that *starts* the content under the heading is fine ("We ablate three components."). Flag only the pure restatement that says the section exists. In Chinese, the same tell: 「## 稳健性检验」后紧跟「本文进行稳健性检验。」→ 删复述句，直接写检验内容。

## False-positive guard (do not over-correct)

From Wikipedia "Signs of AI writing" (Ineffective indicators) + Layer 3:

- **Perfect grammar, polish, or consistent style** — not a tell by itself.
- **Formal or academic prose** — only the *specific* listed words are tells, not formality in general.
- **Transition words in isolation** — one "however" / "moreover" is not a tell; density is.
- **"Bland" or "robust"-sounding prose without specific tells** — that is just dry writing.
- **Curly quotes, a single em dash, a single short sentence** — not proof alone.
- **Deliberate repetition used for rhythm** ("She came. She saw. She conquered.") — keep it.
- **Unsourced claims** — most prose is unsourced; lack of citations is not a tell.
- **Secondhand text** — never rewrite watched phrases inside quotations, titles, proper names, or examples where the phrase is being *discussed* rather than *used*.
- **Chinese register conventions** — 总而言之 / 需要注意的是 / 核心解释变量 / 结论·建议·贡献骨架 are whitelisted for Chinese social-science writing (`references/rules-zh.md` §10); do not flag them via this English catalog.
- **Academic keeps (Layer 3):** evidence-tied hedging, passive voice, "we" / "本研究", semicolons, long attributives.
- **When unsure:** several patterns in one passage are stronger evidence than one pattern anywhere.

## Citation-integrity note (report-only, never fix)

AI-drafted reference lists may contain fabricated DOIs, dangling or unused named references, placeholders (2025-XX-XX, INSERT_URL), or mismatched cite keys. **C0 applies:** never alter, delete, or "repair" a citation. Flag the discrepancy in the change log and let the author verify against the source.
