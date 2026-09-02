#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_red_lines.py — Academic Humanizer C0–C2 red-line auditor.

Given a before / after pair (files or stdin), assert that the editing pass did NOT
violate the contract:

  C0  Numbers, p-values, statistics, citations, equations, dates, places
      are sacred. Never invent, drop, or alter.
  C1  Claims are not deleted, merged, or altered.
  C2  Terminology and named methods / metrics stay verbatim.

Usage:
    # Two files:
    python3 scripts/validate_red_lines.py before.md after.md

    # One combined markdown with "## Before" and "## After" sections:
    python3 scripts/validate_red_lines.py --combined examples/before-after-zh-academic.md

    # Two text blobs via stdin (separated by line "<<<AFTER>>>"):
    python3 scripts/validate_red_lines.py -

Exit codes:
    0  PASS  — all red lines preserved
    1  WARN  — some warnings, no hard fails
    2  FAIL  — at least one red line violated
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Union

from combined_parser import split_combined, split_combined_all

# Windows consoles often default to a legacy codepage (e.g. GBK / cp936) that
# cannot encode the FAIL/WARN tags. Force UTF-8 so output never crashes.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Extractors: each returns a sorted list of (match, value, line_no) tuples.
# ---------------------------------------------------------------------------

# Numbers: integers, decimals, percentages, scientific notation, ranges "2–6%"
NUM_RE = re.compile(
    r"(?<![A-Za-z\u4e00-\u9fff\d])"           # not preceded by letter / CJK / digit
    r"(\d{4}(?:[–—\-]\d{2,4})?"              # year or year range (2020–2025)
    r"|\d{1,3}(?:,\d{3})+(?:\.\d+)?"         # grouped integer (1,234.56)
    r"|\d+\.\d+"                             # decimal
    r"|\d{1,3})"                              # short integer (avoid slicing years)
    r"(?:%|\s*[–—\-]\s*\d+%)?"           # optional percent or percent range
    r"(?![A-Za-z\d])"
)

# p-values and statistics
PVAL_RE = re.compile(
    r"\*?p\*?\s*[<≤>]\s*0?\.\d+|"
    r"\bn\s*=\s*\d+|"
    r"\b(?:t|F|chi-square|χ²|χ2|r|R²|R\^2)\s*=\s*[\d.]+|"
    r"\bCI\s*[=:]|"
    r"\bAUROC\s*=\s*[\d.]+",
    re.IGNORECASE,
)

# Inline citations:
#   numeric: [1], [12], [1-3], [1, 2, 5]
#   author-year in parens: (Smith, 2020), (Smith et al., 2019)
#   author-year as sentence clause: Smith (2020), Smith et al. (2019)
#   Chinese full-width forms: 李聪（2021）指出 / （李聪，2021）/ （李聪等，2021）
_AUTHOR = r"[A-Z][A-Za-zÀ-ſ'\-]+"
_CN_AUTHOR = r"[\u4e00-\u9fff]{2,4}"
_CN_AUTHOR_SEP = r"\s*[、,，和]\s*"
CITE_RE = re.compile(
    r"\\(?:cite|citep|citet)(?:\[[^\]]*\])?\{[^}]+\}"
    r"|\[\d+(?:\s*[,–-]\s*\d+)*\]"
    r"|(?:^|\s)\(" + _AUTHOR + r"(?:\s+et\s+al\.?)?\s*,\s*\d{4}[a-z]?\)"
    r"|(?:^|\s)" + _AUTHOR + r"(?:\s+et\s+al\.?)?\s*\(\d{4}[a-z]?\)"
    r"|(?:" + _CN_AUTHOR + _CN_AUTHOR_SEP + r")*" + _CN_AUTHOR + r"[（(]\d{4}[a-z]?[）)]"
    r"|[（(](?:" + _CN_AUTHOR + _CN_AUTHOR_SEP + r")*" + _CN_AUTHOR + r"(?:等)?(?:\s*et\s+al\.?)?\s*[，,]\s*\d{4}[a-z]?[）)]",
)
# Math / equations: $...$, $$...$$, \( \), \[ \], \begin{...}
MATH_RE = re.compile(
    r"\$\$.+?\$\$|"           # $$...$$
    r"\$.+?\$|"                 # $...$
    r"\\\(.+?\\\)|"         # \(...\)
    r"\\\[.+?\\\]|"         # \[…\]
    r"\\begin\{[a-zA-Z*]+\}.+?\\end\{[a-zA-Z*]+\}",
    re.DOTALL,
)

# Dates: "2023年8月", "August 2023", "2023-08", "2023/8/15"
DATE_RE = re.compile(
    r"\d{4}\s*年\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*日?)?|"  # 2023 年 8 月
    r"\d{4}\s*[\-\/]\s*\d{1,2}(?:\s*[\-\/]\s*\d{1,2})?|"  # 2023-08 / 2023-08-15
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s*\d{4}|"
    r"\b\d{4}\b",
)

# Named methods / metrics (extend as your field needs). Lowercased match.
NAMED_TERMS = [
    "discrete choice experiment", "discrete choice model",
    "conditional logit", "mixed logit", "latent class", "latent class model",
    "auroc", "auprc", "rmse", "mae", "mse",
    "t-test", "t test", "paired test",
    "ols", "wls", "gls", "did", "twfe", "psm", "iv", "rd", "rdid",
    "resnet", "vit", "bert", "gpt", "llm",
    "选择实验", "离散选择", "条件 logit", "混合 logit", "潜在类别",
    "双重差分", "倾向得分匹配",
    "碳标签", "碳标识",
]

# Single-word English terms that need word-boundary + negation-context awareness.
# Multi-word terms (e.g. "discrete choice experiment") and Chinese terms are
# unaffected: spaces and CJK characters provide natural boundaries.
_SHORT_TERMS = {
    "auroc", "auprc", "rmse", "mae", "mse",
    "ols", "wls", "gls", "did", "twfe", "psm", "iv", "rd", "rdid",
    "resnet", "vit", "bert", "gpt", "llm",
}

# Words/patterns that, when FOLLOWING a short term, signal English common usage
# (verbs / particles / pronouns) rather than a named method. The check is
# applied to text AFTER the term, because English "did" + verb is verb usage
# ("did observe", "did not", "did so"), while "did" as a method name stands
# alone or is followed by methodology tokens ("DID was used", "applied DID").
_NEGATION_SUFFIXES = (
    # Negation / auxiliary
    "not ", "n't", "n't ",
    # Pronouns / particles that follow "did"
    " so", " it", " this", " that",
    " you", " we", " i ", " they", " he ", " she ",
    # Common academic verbs that "did" can take
    " observe", " see", " find", " show", " suggest",
    " indicate", " demonstrate", " note ", " mention",
)


def extract_numbers(text: str) -> list[str]:
    # Mask citations so that years / digits inside \cite{...}, cite keys, or
    # author-year parentheses do not register as standalone numbers.
    masked = list(text)
    for m in CITE_RE.finditer(text):
        for i in range(m.start(), m.end()):
            masked[i] = " "
    masked_text = "".join(masked)
    return [m.group(0).replace(" ", "") for m in NUM_RE.finditer(masked_text)]


def extract_pvals(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", m.group(0)).strip() for m in PVAL_RE.finditer(text)]


def canonicalize_citation(raw: str) -> Union[str, list[str]]:
    r"""Collapse surface variation of one citation to a stable key.

    Two failure modes this absorbs (both were real bugs):
    - Prose glues onto the front of a Chinese author-year clause ("正如
      李聪（2021）"), so the raw matched name is unstable. Canonicalize to
      the last two CJK chars before the paren plus the year span.
    - A parenthetical -> narrative reflow ("(Smith et al., 2019)" ->
      "Smith et al. (2019)") is legitimate editing, not an alteration, so
      English author-year citations collapse to "name|year".
    - LaTeX cite commands (r"\cite{smith2020}", r"\citep{...}") keep the cite key
      verbatim because the key is the sacred identifier.
    - Chinese multi-author citations ("（张三、李四，2021）") collapse all
      author names so the key remains stable across listing styles.
    """
    c = re.sub(r"\s+", " ", raw).strip()

    latex = re.match(r"\\(?:cite|citep|citet)(?:\[[^\]]*\])?\{([^}]+)\}$", c)
    if latex:
        keys = [k.strip() for k in latex.group(1).split(",") if k.strip()]
        if len(keys) == 1:
            return keys[0]
        return keys

    # Chinese narrative / prose-prefix author-year: 李聪（2021）/ 正如李聪（2021）
    cm = re.match(r"([\u4e00-\u9fff]+)[（(](\d{4}[a-z]?)[）)]$", c)
    if cm:
        authors = cm.group(1)
        year = cm.group(2)
        if re.search(r"[、,，和]", authors):
            authors = re.sub(r"\s*[、,，和]\s*", "", authors)
        else:
            authors = authors[-2:]
        return f"{authors}（{year}）"

    # Chinese parenthetical multi-author: （张三、李四，2021）
    cpm = re.match(
        r"[（(]([\u4e00-\u9fff]+(?:[、,，和]\s*[\u4e00-\u9fff]+)*?)(?:等)?(?:\s*et\s+al\.?)?\s*[，,]\s*(\d{4}[a-z]?)[）)]$",
        c,
    )
    if cpm:
        authors = re.sub(r"\s*[、,，和]\s*", "", cpm.group(1))
        return f"{authors}（{cpm.group(2)}）"

    em = re.match(
        r"\(?([A-Z][A-Za-zÀ-ſ'\-]+(?:\s+et\s+al\.?)?)\s*,?\s*\(?(\d{4}[a-z]?)\)?$",
        c,
    )
    if em:
        return f"{em.group(1).lower().replace(' ', '').rstrip('.')}|{em.group(2)}"
    return c


def extract_citations(text: str) -> list[str]:
    out: list[str] = []
    for m in CITE_RE.finditer(text):
        canon = canonicalize_citation(m.group(0))
        if isinstance(canon, list):
            out.extend(canon)
        else:
            out.append(canon)
    return out



def extract_math(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", m.group(0)).strip() for m in MATH_RE.finditer(text)]


def extract_dates(text: str) -> list[str]:
    return [re.sub(r"\s+", "", m.group(0)) for m in DATE_RE.finditer(text)]


def extract_named_terms(text: str) -> list[str]:
    """Extract named methods/metrics with word-boundary + negation-context awareness.

    - Multi-word English terms (e.g. "discrete choice experiment") are matched
      as phrases — internal spaces give natural boundaries.
    - Chinese terms are matched literally — CJK characters provide boundaries.
    - Single-word English terms (did, ols, gpt, etc.) use \\b word boundaries
      AND are skipped when preceded by an English negation or auxiliary verb
      ("did not", "didn't", "is not", etc.) so common verbs do not trigger
      false C2 red-line violations.
    """
    found: list[str] = []
    for term in NAMED_TERMS:
        if term not in _SHORT_TERMS:
            # Multi-word phrase or Chinese term: simple substring match.
            if term.lower() in text.lower():
                found.append(term)
            continue
        # Short single-word English term: word-boundary + suffix-context.
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", flags=re.IGNORECASE)
        accepted = False
        for m in pattern.finditer(text):
            following = text[m.end():m.end() + 14].lower()
            following = " " + following  # ensure leading space so "so" doesn't match in "used"
            if any(suf in following for suf in _NEGATION_SUFFIXES):
                continue
            accepted = True
            break  # one hit per term is enough
        if accepted:
            found.append(term)
    return found


def extract_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def extract_sentences(text: str) -> list[str]:
    # Chinese terminators split regardless of following whitespace; Chinese
    # prose has no space after 。 English keeps the ". " convention.
    parts = re.split(r"(?<=[。！？!?])|(?<=[^\s。]\.)\s+", text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]


def _missing(before: list[str], after: list[str]) -> list[str]:
    """Multiset difference: elements of before whose count exceeds after.

    Membership checks miss duplicated items being halved (before has two
    occurrences of a number/citation, after only one) — Counter catches them.
    """
    return sorted((Counter(before) - Counter(after)).elements())


# ---------------------------------------------------------------------------
# Feature extraction: text -> FeatureSet. All regex / normalization knowledge
# lives behind this seam; compare() consumes FeatureSets and never sees raw text.
# ---------------------------------------------------------------------------

@dataclass
class FeatureSet:
    numbers: list[str]
    stats: list[str]
    citations: list[str]
    math: list[str]
    dates: list[str]
    terms: list[str]
    paragraphs: int
    sentences: int


def extract_features(text: str) -> FeatureSet:
    return FeatureSet(
        numbers=sorted(extract_numbers(text)),
        stats=sorted(extract_pvals(text)),
        citations=sorted(extract_citations(text)),
        math=sorted(extract_math(text)),
        dates=sorted(extract_dates(text)),
        terms=sorted(set(extract_named_terms(text))),
        paragraphs=len(extract_paragraphs(text)),
        sentences=len(extract_sentences(text)),
    )


# ---------------------------------------------------------------------------
# Diff audit
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    rule: str
    severity: str   # "fail" | "warn" | "info"
    message: str
    detail: dict = field(default_factory=dict)


def compare(before: FeatureSet, after: FeatureSet) -> list[Finding]:
    """Pure diff of two FeatureSets — no regex, no text access."""
    findings: list[Finding] = []

    # ----- C0.1 Numbers -----
    before_nums = before.numbers
    after_nums = after.numbers
    missing_nums = _missing(before_nums, after_nums)
    if missing_nums:
        findings.append(Finding(
            "C0.1 numbers", "fail",
            f"{len(missing_nums)} number(s) from before are missing or altered in after.",
            {"missing": missing_nums[:20], "missing_count": len(missing_nums)},
        ))
    # Suspicious: new numbers in after that weren't in before
    new_nums = [n for n in after_nums if n not in before_nums]
    # Filter trivial: dates and 4-digit year-only numbers are checked separately
    real_new = []
    for n in new_nums:
        if re.fullmatch(r"\d{4}", n):            # year
            continue
        if re.fullmatch(r"0?\.\d+", n):         # p-value-ish (e.g. .05, 0.05)
            continue
        if re.fullmatch(r"\d{1,2}", n):          # tiny integers likely from table row numbers
            continue
        real_new.append(n)
    if real_new:
        findings.append(Finding(
            "C0.1 numbers (new)", "warn",
            f"{len(real_new)} new number(s) appeared in after — verify not hallucinated.",
            {"new": real_new[:20], "new_count": len(real_new)},
        ))

    # ----- C0.2 p-values / statistics -----
    missing_p = _missing(before.stats, after.stats)
    if missing_p:
        findings.append(Finding(
            "C0.2 stats", "fail",
            f"{len(missing_p)} statistical expression(s) lost or altered.",
            {"missing": missing_p},
        ))

    # ----- C0.3 Citations -----
    missing_cites = _missing(before.citations, after.citations)
    if missing_cites:
        findings.append(Finding(
            "C0.3 citations", "fail",
            f"{len(missing_cites)} citation(s) lost or altered.",
            {"missing": missing_cites[:30], "missing_count": len(missing_cites)},
        ))

    # ----- C0.4 Math / equations -----
    missing_math = _missing(before.math, after.math)
    if missing_math:
        findings.append(Finding(
            "C0.4 math", "fail",
            f"{len(missing_math)} equation(s) / math environment(s) lost or altered.",
            {"missing_count": len(missing_math)},
        ))

    # ----- C0.5 Dates -----
    missing_dates = _missing(before.dates, after.dates)
    # Filter trivial year-only matches that often appear in citations
    real_missing_dates = [d for d in missing_dates if not re.fullmatch(r"\d{4}", d)]
    if real_missing_dates:
        findings.append(Finding(
            "C0.5 dates", "warn",
            f"{len(real_missing_dates)} date(s) lost or altered.",
            {"missing": real_missing_dates[:20]},
        ))

    # ----- C1 Structure -----
    bp, ap = before.paragraphs, after.paragraphs
    if abs(bp - ap) > max(1, bp * 0.2):
        findings.append(Finding(
            "C1 paragraphs", "warn",
            f"Paragraph count drifted: before={bp}, after={ap}.",
            {"before": bp, "after": ap},
        ))
    bs, as_ = before.sentences, after.sentences
    if bs > 0 and abs(bs - as_) > max(2, bs * 0.25):
        findings.append(Finding(
            "C1 sentences", "warn",
            f"Sentence count drifted >25%: before={bs}, after={as_}.",
            {"before": bs, "after": as_},
        ))

    # ----- C2 Named methods / metrics -----
    missing_terms = [t for t in before.terms if t not in after.terms]
    if missing_terms:
        findings.append(Finding(
            "C2 named terms", "fail",
            f"{len(missing_terms)} named method(s) / metric(s) lost or paraphrased.",
            {"missing": missing_terms},
        ))

    if not findings:
        findings.append(Finding(
            "summary", "info",
            "All red lines preserved (C0 numbers, C0 stats, C0 cites, "
            "C0 math, C0 dates, C1 structure, C2 named terms).",
        ))
    return findings


def compare_texts(before: str, after: str) -> list[Finding]:
    """Convenience path text -> features -> diff, for CLI and tests."""
    return compare(extract_features(before), extract_features(after))


# ---------------------------------------------------------------------------
# I/O helpers — split_combined / split_combined_all live in combined_parser.py
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("combined", nargs="?", help="Single file with ## Before / ## After (positional alias of --combined)")
    p.add_argument("--combined", dest="combined_flag", nargs="?", const=None, default=None, help="Single file with ## Before / ## After. Without a value, falls back to the positional combined argument.")
    p.add_argument("--all-pairs", action="store_true", help="When using a combined file, audit every ## Before / ## After pair (default: first pair only)")
    p.add_argument("--before", help="Before text file")
    p.add_argument("--after", help="After text file")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of human report")
    p.add_argument("--quiet", action="store_true", help="Suppress info-level findings in human mode")
    args = p.parse_args()

    combined_path = args.combined_flag or args.combined

    if args.before and args.after:
        before = Path(args.before).read_text(encoding="utf-8")
        after = Path(args.after).read_text(encoding="utf-8")
        pairs = [(before, after)]
    elif combined_path == "-":
        text = sys.stdin.read()
        pairs = list(split_combined_all(text))
    elif combined_path:
        text = Path(combined_path).read_text(encoding="utf-8")
        pairs = list(split_combined_all(text))
    else:
        p.error("Provide a combined file (positional or --combined), or --before / --after pair.")

    if not pairs:
        print("validate_red_lines: no ## Before / ## After pairs found", file=sys.stderr)
        return 3

    if not args.all_pairs and len(pairs) > 1:
        # Backward-compatible: silently audit only the first pair unless --all-pairs is passed
        pairs = pairs[:1]

    all_findings: list[Finding] = []
    for idx, (before, after) in enumerate(pairs, start=1):
        findings = compare_texts(before, after)
        if len(pairs) > 1:
            for f in findings:
                f.rule = f"{f.rule}#{idx}"
        all_findings.extend(findings)

    if args.json:
        print(json.dumps([asdict(f) for f in all_findings], ensure_ascii=False, indent=2))
    else:
        for f in all_findings:
            if args.quiet and f.severity == "info":
                continue
            tag = {"fail": "❌ FAIL", "warn": "⚠️  WARN", "info": "✅ INFO"}.get(f.severity, f.severity)
            print(f"[{tag}] {f.rule}: {f.message}")
            if f.detail:
                detail = {k: v for k, v in f.detail.items() if v}
                if detail:
                    print(f"        {json.dumps(detail, ensure_ascii=False)}")

    has_fail = any(f.severity == "fail" for f in all_findings)
    has_warn = any(f.severity == "warn" for f in all_findings)
    return 2 if has_fail else (1 if has_warn else 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # crash must never masquerade as exit 0/1/2
        print(f"validate_red_lines: unexpected crash: {exc}", file=sys.stderr)
        sys.exit(3)
