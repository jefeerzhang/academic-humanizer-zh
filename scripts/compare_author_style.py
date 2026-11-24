#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_author_style.py — Academic Humanizer Layer 5 author-sample style comparator.

Replaces fixed-phrase Layer 7 injection with empirical voice calibration against
the author's own prior writing sample (accepted papers / drafts). Extracts and
compares four measurable prose dimensions in Chinese or English:

  S5.1  Sentence length distribution (mean, stdev, CV, short/long ratios)
  S5.2  Sentence rhythm preservation (warns if rewrite flattens author variance)
  S5.3  Self-reference convention (本文 / 本研究 / 笔者 / 我们; we / this paper / this study)
  S5.4  Connective profile (flags foreign connectives introduced by the rewrite)
  S5.5  Natural hedging & punctuation density (warns on over-stripping or over-stuffing)

Usage:
    # Compare an author sample against a cleaned draft:
    python3 scripts/compare_author_style.py --sample prior_paper.md --after edited.md

    # Compare an author sample against the ## After span(s) of a combined file:
    python3 scripts/compare_author_style.py --sample prior_paper.md --combined examples/before-after-zh-academic.md

    # Inspect a single sample's style profile (no diff):
    python3 scripts/compare_author_style.py --sample prior_paper.md --profile-only

Exit codes:
    0  PASS  — rewrite stays within the author sample's style envelope
    1  WARN  — measurable style drift detected (review dimensions in report)
    2  FAIL  — invalid arguments or empty input
    3  Unexpected crash — never conflated with WARN
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from audit_tells import _clean_prose_text, sentence_rhythm_stats
from combined_parser import split_combined_all

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

_CJK = "\u4e00-\u9fff"

ZH_SELF_REFS: dict[str, re.Pattern[str]] = {
    "本文": re.compile(r"本文"),
    "本研究": re.compile(r"本研究"),
    "笔者": re.compile(r"笔者"),
    "我们": re.compile(r"我们"),
}

EN_SELF_REFS: dict[str, re.Pattern[str]] = {
    "we": re.compile(r"\b(?:we|our|us)\b", re.IGNORECASE),
    "this paper": re.compile(r"\bthis paper\b", re.IGNORECASE),
    "this study": re.compile(r"\bthis study\b", re.IGNORECASE),
    "the authors": re.compile(r"\bthe authors?\b", re.IGNORECASE),
}

ZH_CONNECTIVES: tuple[str, ...] = (
    "因此", "故而", "由此", "然而", "但是", "不过", "尽管", "虽然", "即便",
    "此外", "同时", "进一步", "一方面", "另一方面", "综上", "可见", "换言之",
    "相反", "当然", "而", "进而",
)

EN_CONNECTIVES: tuple[str, ...] = (
    "however", "therefore", "thus", "although", "whereas", "yet", "instead",
    "moreover", "furthermore", "additionally", "in contrast", "by contrast",
    "in addition", "meanwhile", "nonetheless", "nevertheless",
)

ZH_HEDGES: tuple[str, ...] = (
    "可能", "倾向于", "尚不", "一定程度上", "并非", "难以", "往往", "有待", "谨慎", "或许",
)

EN_HEDGES: tuple[str, ...] = (
    "may", "might", "suggest", "appear", "consistent with", "likely",
    "unlikely", "seem", "tend to", "potentially",
)

_EN_ABBREV_RE = re.compile(
    r"\b(?:e\.g|i\.e|et al|vs|Fig|Eq|Sec|No|Dr|Mr|Ms|Prof|Inc|Ltd)\.",
    re.IGNORECASE,
)


@dataclass
class StyleProfile:
    language: str
    unit_count: int
    sentence_count: int
    mean_sent_len: float
    sent_variance: float
    sent_stdev: float
    sent_cv: float
    short_ratio: float
    long_ratio: float
    self_refs: dict[str, int] = field(default_factory=dict)
    dominant_self_ref: str = ""
    connectives: dict[str, int] = field(default_factory=dict)
    connective_per_1k: float = 0.0
    hedges_per_1k: float = 0.0
    semicolon_per_1k: float = 0.0
    quote_pairs_per_1k: float = 0.0


@dataclass
class Finding:
    rule: str
    severity: str   # "warn" | "info" | "fail"
    message: str
    detail: dict = field(default_factory=dict)


def _extract_sentences(prose: str, is_zh: bool) -> list[int]:
    body_lines = [
        ln for ln in prose.splitlines()
        if ln.strip() and not re.match(r"^\s*[-*+]\s+", ln)
    ]
    body = "\n".join(body_lines)
    if is_zh:
        raw_sents = re.split(r"[。！？!?]+|\n+", body)
        lengths = [
            len(re.findall(f"[{_CJK}]", s)) + len(re.findall(r"[A-Za-z0-9]+", s))
            for s in raw_sents
            if s.strip()
        ]
        return [n for n in lengths if n >= 5]
    masked = _EN_ABBREV_RE.sub(lambda m: m.group(0).replace(".", ""), body)
    raw_sents = re.split(r"(?<=[.!?])\s+|\n+", masked)
    lengths = [
        len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", s))
        for s in raw_sents
        if s.strip()
    ]
    return [n for n in lengths if n >= 4]


def _count_terms(prose: str, terms: tuple[str, ...], is_zh: bool) -> dict[str, int]:
    counts: dict[str, int] = {}
    if is_zh:
        for term in terms:
            n = len(re.findall(re.escape(term), prose))
            if n:
                counts[term] = n
    else:
        lower = prose.lower()
        for term in terms:
            rx = re.escape(term) if " " in term else r"\b" + re.escape(term) + r"\b"
            n = len(re.findall(rx, lower))
            if n:
                counts[term] = n
    return counts


def extract_style_profile(text: str) -> StyleProfile:
    """Extract a language-aware prose style profile from *text*."""
    prose = _clean_prose_text(text)
    rhythm = sentence_rhythm_stats(text)
    is_zh = rhythm["language"] == "zh"

    if is_zh:
        unit_count = len(re.findall(f"[{_CJK}]", prose)) + len(re.findall(r"[A-Za-z0-9]+", prose))
        short_cut, long_cut = 18, 45
        ref_map = ZH_SELF_REFS
        conn_terms = ZH_CONNECTIVES
        hedge_terms = ZH_HEDGES
    else:
        unit_count = len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", prose))
        short_cut, long_cut = 12, 28
        ref_map = EN_SELF_REFS
        conn_terms = EN_CONNECTIVES
        hedge_terms = EN_HEDGES

    lengths = _extract_sentences(prose, is_zh)
    n_sents = len(lengths)
    short_ratio = round(sum(1 for x in lengths if x <= short_cut) / n_sents, 3) if n_sents else 0.0
    long_ratio = round(sum(1 for x in lengths if x >= long_cut) / n_sents, 3) if n_sents else 0.0

    self_refs = {k: len(rx.findall(prose)) for k, rx in ref_map.items()}
    self_refs = {k: v for k, v in self_refs.items() if v > 0}
    dominant_self_ref = max(self_refs, key=lambda k: self_refs[k]) if self_refs else ""

    connectives = _count_terms(prose, conn_terms, is_zh)
    hedges = _count_terms(prose, hedge_terms, is_zh)

    scale = 1000.0 / max(unit_count, 1)
    conn_per_1k = round(sum(connectives.values()) * scale, 2) if unit_count else 0.0
    hedges_per_1k = round(sum(hedges.values()) * scale, 2) if unit_count else 0.0
    semicolons = prose.count("；") + prose.count(";")
    semicolon_per_1k = round(semicolons * scale, 2) if unit_count else 0.0
    quote_pairs = (
        len(re.findall(r"“[^”\n]{1,30}”", prose))
        + len(re.findall(r"「[^」\n]{1,30}」", prose))
        + len(re.findall(r'"[^"\n]{1,30}"', prose))
    )
    quote_pairs_per_1k = round(quote_pairs * scale, 2) if unit_count else 0.0

    return StyleProfile(
        language=rhythm["language"],
        unit_count=unit_count,
        sentence_count=rhythm["sentence_count"],
        mean_sent_len=rhythm["mean"],
        sent_variance=rhythm["variance"],
        sent_stdev=rhythm["stdev"],
        sent_cv=rhythm["cv"],
        short_ratio=short_ratio,
        long_ratio=long_ratio,
        self_refs=self_refs,
        dominant_self_ref=dominant_self_ref,
        connectives=connectives,
        connective_per_1k=conn_per_1k,
        hedges_per_1k=hedges_per_1k,
        semicolon_per_1k=semicolon_per_1k,
        quote_pairs_per_1k=quote_pairs_per_1k,
    )


def compare_profiles(sample: StyleProfile, after: StyleProfile) -> tuple[int, list[Finding]]:
    """Compare an edited text profile against the author's historical sample."""
    findings: list[Finding] = []

    if sample.language != after.language:
        findings.append(Finding(
            "S5.0 language mismatch", "warn",
            f"Author sample language ({sample.language}) differs from After text ({after.language}).",
            {"sample_language": sample.language, "after_language": after.language},
        ))
        return 1, findings

    is_zh = sample.language == "zh"

    # ----- S5.1 Mean sentence length drift -----
    if sample.sentence_count >= 4 and after.sentence_count >= 4 and sample.mean_sent_len > 0:
        rel_diff = abs(after.mean_sent_len - sample.mean_sent_len) / sample.mean_sent_len
        abs_diff = abs(after.mean_sent_len - sample.mean_sent_len)
        min_abs = 8.0 if is_zh else 6.0
        if rel_diff > 0.35 and abs_diff >= min_abs:
            direction = "longer" if after.mean_sent_len > sample.mean_sent_len else "shorter"
            findings.append(Finding(
                "S5.1 sentence length drift", "warn",
                (
                    f"After sentences are substantially {direction} than the author sample "
                    f"(sample mean={sample.mean_sent_len}, after mean={after.mean_sent_len})."
                ),
                {
                    "sample_mean": sample.mean_sent_len,
                    "after_mean": after.mean_sent_len,
                    "relative_diff": round(rel_diff, 3),
                },
            ))

    # ----- S5.2 Sentence rhythm flattening -----
    if (
        sample.sentence_count >= 4
        and after.sentence_count >= 4
        and sample.sent_cv >= 0.22
        and after.sent_cv < min(0.18, sample.sent_cv * 0.65)
    ):
        findings.append(Finding(
            "S5.2 rhythm flattening", "warn",
            (
                f"After flattened the author's sentence-length variation "
                f"(sample CV={sample.sent_cv}, after CV={after.sent_cv})."
            ),
            {
                "sample_cv": sample.sent_cv,
                "after_cv": after.sent_cv,
                "sample_stdev": sample.sent_stdev,
                "after_stdev": after.sent_stdev,
            },
        ))

    # ----- S5.3 Self-reference drift -----
    if sample.self_refs and after.self_refs:
        foreign_refs = {
            k: v for k, v in after.self_refs.items()
            if k not in sample.self_refs
        }
        # Flag introducing 笔者 when the author sample never uses 笔者,
        # or switching the dominant self-reference entirely.
        if "笔者" in foreign_refs or (
            sample.dominant_self_ref
            and after.dominant_self_ref
            and sample.dominant_self_ref != after.dominant_self_ref
            and sample.dominant_self_ref not in after.self_refs
        ):
            findings.append(Finding(
                "S5.3 self-reference drift", "warn",
                (
                    f"After introduced self-reference style absent from the author sample "
                    f"(sample={sample.self_refs}, after={after.self_refs})."
                ),
                {
                    "sample_self_refs": sample.self_refs,
                    "after_self_refs": after.self_refs,
                    "foreign_self_refs": foreign_refs,
                },
            ))

    # ----- S5.4 Foreign connective drift -----
    if sample.unit_count >= 80 and after.connectives:
        foreign_conns = {
            k: v for k, v in after.connectives.items()
            if k not in sample.connectives
        }
        repeated_foreign = {k: v for k, v in foreign_conns.items() if v >= 2}
        if repeated_foreign or len(foreign_conns) >= 3:
            findings.append(Finding(
                "S5.4 connective drift", "warn",
                "After introduced connectives not observed in the author sample.",
                {
                    "foreign_connectives": foreign_conns,
                    "sample_connectives": sample.connectives,
                },
            ))

    # ----- S5.5 Hedging density drift -----
    min_units = 150 if is_zh else 80
    if sample.unit_count >= min_units and after.unit_count >= min_units:
        if sample.hedges_per_1k >= 3.0 and after.hedges_per_1k == 0.0:
            findings.append(Finding(
                "S5.5 hedging stripped", "warn",
                (
                    f"After stripped all natural hedging present in the author sample "
                    f"(sample={sample.hedges_per_1k}/1k, after=0.0/1k)."
                ),
                {"sample_hedges_per_1k": sample.hedges_per_1k, "after_hedges_per_1k": 0.0},
            ))
        elif (
            after.hedges_per_1k > max(sample.hedges_per_1k * 2.5, sample.hedges_per_1k + 6.0)
            and after.hedges_per_1k >= 6.0
        ):
            findings.append(Finding(
                "S5.5 hedging over-stuffed", "warn",
                (
                    f"After has much denser hedging than the author sample "
                    f"(sample={sample.hedges_per_1k}/1k, after={after.hedges_per_1k}/1k)."
                ),
                {
                    "sample_hedges_per_1k": sample.hedges_per_1k,
                    "after_hedges_per_1k": after.hedges_per_1k,
                },
            ))

    if not findings:
        findings.append(Finding(
            "summary", "info",
            "After text aligns with the author sample's sentence rhythm, self-reference, and connective profile.",
        ))

    has_fail = any(f.severity == "fail" for f in findings)
    has_warn = any(f.severity == "warn" for f in findings)
    return (2 if has_fail else 1 if has_warn else 0), findings


def compare_texts(sample_text: str, after_text: str) -> tuple[int, StyleProfile, StyleProfile, list[Finding]]:
    sample_profile = extract_style_profile(sample_text)
    after_profile = extract_style_profile(after_text)
    code, findings = compare_profiles(sample_profile, after_profile)
    return code, sample_profile, after_profile, findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--sample", required=True, help="Author's historical writing sample file")
    ap.add_argument("--after", help="Edited text file to compare against --sample")
    ap.add_argument("--combined", help="Combined markdown file with ## Before / ## After spans")
    ap.add_argument("--profile-only", action="store_true", help="Only print the author sample's style profile")
    ap.add_argument("--json", action="store_true", help="Emit JSON report")
    args = ap.parse_args()

    sample_path = Path(args.sample)
    if not sample_path.is_file():
        print(f"compare_author_style: sample file not found: {sample_path}", file=sys.stderr)
        return 2
    sample_text = sample_path.read_text(encoding="utf-8")
    sample_profile = extract_style_profile(sample_text)

    if args.profile_only:
        if args.json:
            print(json.dumps(asdict(sample_profile), ensure_ascii=False, indent=2))
        else:
            print(f"[INFO] Author style profile ({sample_profile.language})")
            print(f"  sentences        : {sample_profile.sentence_count} (mean={sample_profile.mean_sent_len}, stdev={sample_profile.sent_stdev}, cv={sample_profile.sent_cv})")
            print(f"  short/long ratio : short={sample_profile.short_ratio}, long={sample_profile.long_ratio}")
            print(f"  self_refs        : {sample_profile.self_refs} (dominant={sample_profile.dominant_self_ref or 'none'})")
            print(f"  connectives/1k   : {sample_profile.connective_per_1k} {sample_profile.connectives}")
            print(f"  hedges/1k        : {sample_profile.hedges_per_1k}")
            print(f"  punct/1k         : semicolon={sample_profile.semicolon_per_1k}, quotes={sample_profile.quote_pairs_per_1k}")
        return 0

    if args.after:
        after_path = Path(args.after)
        if not after_path.is_file():
            print(f"compare_author_style: after file not found: {after_path}", file=sys.stderr)
            return 2
        after_texts = [after_path.read_text(encoding="utf-8")]
    elif args.combined:
        comb_path = Path(args.combined)
        if not comb_path.is_file():
            print(f"compare_author_style: combined file not found: {comb_path}", file=sys.stderr)
            return 2
        after_texts = [after for _, after in split_combined_all(comb_path.read_text(encoding="utf-8"))]
        if not after_texts:
            print("compare_author_style: no ## After spans found", file=sys.stderr)
            return 2
    else:
        ap.error("Provide --after FILE, --combined FILE, or --profile-only.")

    max_exit = 0
    all_reports: list[dict] = []
    for idx, after_text in enumerate(after_texts, start=1):
        after_profile = extract_style_profile(after_text)
        code, findings = compare_profiles(sample_profile, after_profile)
        if len(after_texts) > 1:
            for f in findings:
                f.rule = f"{f.rule}#{idx}"
        max_exit = max(max_exit, code)
        all_reports.append({
            "pair": idx,
            "exit_code": code,
            "sample_profile": asdict(sample_profile),
            "after_profile": asdict(after_profile),
            "findings": [asdict(f) for f in findings],
        })

    if args.json:
        payload = all_reports[0] if len(all_reports) == 1 else {"exit_code": max_exit, "reports": all_reports}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for rep in all_reports:
            sp = rep["sample_profile"]
            ap_prof = rep["after_profile"]
            label = {0: "PASS", 1: "WARN", 2: "FAIL"}.get(rep["exit_code"], "?")
            suffix = f" #{rep['pair']}" if len(all_reports) > 1 else ""
            print(f"[{label}] Author style comparison{suffix} ({sp['language']})")
            print(f"  sentence mean : sample={sp['mean_sent_len']} vs after={ap_prof['mean_sent_len']} (cv {sp['sent_cv']} vs {ap_prof['sent_cv']})")
            print(f"  self_refs     : sample={sp['self_refs']} vs after={ap_prof['self_refs']}")
            print(f"  hedges/1k     : sample={sp['hedges_per_1k']} vs after={ap_prof['hedges_per_1k']}")
            for f in rep["findings"]:
                tag = {"fail": "❌ FAIL", "warn": "⚠️  WARN", "info": "✅ INFO"}.get(f["severity"], f["severity"])
                print(f"  [{tag}] {f['rule']}: {f['message']}")
    return max_exit


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"compare_author_style: unexpected crash: {exc}", file=sys.stderr)
        sys.exit(3)
