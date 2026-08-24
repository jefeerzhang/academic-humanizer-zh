# Scripts

## validate_red_lines.py

Mechanical auditor for the C0-C2 red lines in SKILL.md. Confirms that an
editing pass did not alter numbers, statistics, citations, equations, dates,
named methods/metrics, or paragraph structure between a before and after
text pair.

Use it as the executable counterpart of the "unchanged-claim declaration" the
skill promises in its Output section: instead of trusting the editor's prose
account, run this script on the actual diff.

### Red lines audited

| Rule                  | Severity on violation                              | What is extracted                                                        |
| --------------------- | -------------------------------------------------- | ------------------------------------------------------------------------ |
| C0.1 numbers          | FAIL if missing, WARN if new                       | Integers, decimals, percentages, ranges                                  |
| C0.2 stats            | FAIL if missing                                    | p < 0.05, n = 692, t = 2.3, AUROC = 0.91, CI =, etc.                     |
| C0.3 citations        | FAIL if missing                                    | [1], [1-3], (Smith, 2020), Smith et al. (2019), 李聪（2021）, （李聪，2021） |
| C0.4 math             | FAIL if missing                                    | $...$$, $...$, [...], begin{...}...end{...}                              |
| C0.5 dates            | WARN if missing                                    | 2023 nian 8 yue, 2023-08, August 2023, bare year                         |
| C1 structure          | WARN if drift > 20% paragraphs / 25% sentences     | paragraph and sentence counts                                            |
| C2 named terms        | FAIL if missing                                    | curated list of common methods/metrics (DCE, AUROC, t-test, OLS, ...)    |

### Usage

Two files:

    python3 scripts/validate_red_lines.py --before before.md --after after.md

One combined markdown with ## Before / ## After headings:

    python3 scripts/validate_red_lines.py examples/before-after-zh-academic.md

The script splits on the first ## Before and the next ## After, and only
audits the editable prose span between them. Meta sections (场景假设 /
修改对照 / 合规清单 / 总结) are skipped automatically.

Stdin, two blobs separated by <<<AFTER>>>:

    cat before.md > /tmp/in.md
    echo "<<<AFTER>>>" >> /tmp/in.md
    cat after.md >> /tmp/in.md
    python3 scripts/validate_red_lines.py - < /tmp/in.md

### Output

- Human-readable by default (one line per finding with a FAIL/WARN/INFO tag).
- --json emits a JSON array for CI / programmatic consumption.
- --quiet suppresses the INFO summary.

### Exit codes (CI-friendly)

- 0  All red lines preserved.
- 1  Only WARN-level findings (e.g. structure drift, new dates). Human review recommended.
- 2  One or more FAIL findings (numbers, stats, citations, math, or named terms lost).
- 3  Unexpected crash (e.g. unreadable input) — never conflated with WARN.

### Regression tests

    python scripts/test_validate_red_lines.py

Covers the known failure modes: duplicated numbers halved, Chinese full-width
citations（李聪（2021）/ （李聪，2021）), citation reflow vs swap, and
Chinese sentence-merge drift.

### Smoke test

    python3 scripts/validate_red_lines.py examples/before-after-zh-academic.md
    python3 scripts/validate_red_lines.py examples/before-after-tri-research-report-zh.md

Both shipped examples should exit 0.

### Extending

- Field-specific named terms: append to the NAMED_TERMS list in the script.
- Stricter p-value rule: by default, the script allows new p-values in the
  after (because adding a missing *p* < 0.05 is the kind of legitimate
  enhancement SKILL.md Layer 4 calls for). If your venue forbids this, tighten
  `extract_pvals()` — it lives behind the `extract_features()` seam;
  `compare()` diffs FeatureSets and never sees text.

### Limitations

- The script is mechanical, not semantic. It catches lost citations and
  altered numbers; it does not catch a paraphrased claim that happens to
  preserve all numbers but inverts a sign. Always combine with a human
  review of the diff.
- The named-terms list is curated for the academic fields the upstream skill
  targets (CS / ML / econometrics / social science). Add field-specific terms
  before running on, e.g., a chemistry manuscript.
- Numbers that appear inside a citation (Smith 2020 -> year 2020) are
  filtered to reduce noise, but very short abstracts may still produce
  false-positive structure-drift warnings.
- The stats extractor matches comparisons (`p < 0.05`, `p ≤`, `p >`) and
  right-side forms like `n = 692`; a bare equality `p = 0.03` is caught only
  indirectly, via the numbers audit.
