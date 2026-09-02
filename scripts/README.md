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

The script splits on the first ## Before and the next ## After, and stops
before meta subsections (### 修改对照 / C0–C2 核对 / Layer 7 密度核对) or the
next ## heading. Use --all-pairs to audit every pair in multi-example files.
Parsing logic lives in `scripts/combined_parser.py` (shared with Layer 7 auditor).

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
    python scripts/test_combined_parser.py
    python scripts/test_validate_layer7_injection.py
    python scripts/test_repo_consistency.py

Covers the known failure modes: duplicated numbers halved, Chinese citations,
year-range parsing, combined-parser meta boundaries, Layer 7 checks, and
README / LICENSE / CONTEXT / English-example alignment with CI.

### Smoke test

    python scripts/run_examples.py

Audits every combined example with `validate_red_lines.py --all-pairs` and
`validate_layer7_injection.py --all-pairs` where applicable. Exit 0 required.

### Extending

- Field-specific named terms: append to the NAMED_TERMS list in the script.
- Stricter p-value rule: new p-values in the after text trigger WARN (C0 — do not invent
  statistics). Layer 4 may surface an existing significance statement with notation only
  when the claim was already in the before text.

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
