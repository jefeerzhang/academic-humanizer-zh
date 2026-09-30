#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_tells.py — Academic Humanizer Layer 1 residual AI-tell auditor.

After an editing pass, scan the After text for general AI tells from the
sourced Layer 1 catalog (`references/layers/layer-1-general-tells.md`), so the
skill's "what still sounds AI-generated" step has a mechanical counterpart,
not just prose.

Strict rules (the skill removes these outright in academic register):
  1.10 placeholder / unfilled template text
  1.17 em dashes, and en dashes outside numeric ranges (2–6%, 2020–2025 are fine)

Weak rules (context-dependent; several patterns together are the tell, per the
catalog's false-positive guard): 1.1 inflated significance, 1.2 -ing tails,
1.3 promotional language, 1.4 vague attributions, 1.5 AI vocabulary,
1.6 copula avoidance, 1.7 negative parallelisms, 1.9 vague connection,
1.11 formulaic challenges-and-outlook, 1.12 knowledge-gap speculation,
  1.13 fake deeper truth, 1.14 defensive "not X" moves, 1.15 rejected fake
  alternatives, 1.16 filler, 1.19 one-line closers / example restatement.
  (1.20 heading restatement is structural and not mechanically scanned.)

Usage:
    # One combined markdown with "## Before" / "## After" sections
    # (audits every After span):
    python3 scripts/audit_tells.py --combined examples/before-after-zh-academic.md

    # A plain file (scans the whole file):
    python3 scripts/audit_tells.py --after after.md

    # Combined markdown via stdin:
    python3 scripts/audit_tells.py - < combined.md

Exit codes:
    0  PASS  — no strict hits, no weak-tell patterns with hits
    1  WARN  — weak tells present (review; a single instance is often legit)
    2  FAIL  — strict tell present (placeholder, em dash, or non-range en dash)
    3  Unexpected crash — never conflated with WARN
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from combined_parser import split_combined_all

# Windows consoles often default to a legacy codepage (e.g. GBK / cp936) that
# cannot encode the FAIL/WARN tags. Force UTF-8 so output never crashes.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class TellPattern:
    pid: str
    name: str
    strict: bool
    terms: tuple[str, ...]


# Literal phrases: single tokens match as word prefixes (\bterm\w*), phrases as
# substrings. All case-insensitive. Watch-lists mirror
# `references/layers/layer-1-general-tells.md`.
PATTERNS: tuple[TellPattern, ...] = (
    TellPattern("1.1", "inflated significance", False, (
        "paving the way", "pave the way", "setting the stage for",
        "key turning point", "evolving landscape", "focal point",
        "indelible mark", "deeply rooted", "stands as a testament",
        "is a testament", "testament to", "marks a pivotal",
        "marks a significant shift",
    )),
    TellPattern("1.2", "superficial -ing tails", False, (
        "highlighting the", "underscoring the", "emphasizing the",
        "showcasing the", "reflecting the", "symbolizing the",
        "fostering the", "cultivating the", "encompassing the",
        "enhancing the", "contributing to the",
    )),
    TellPattern("1.3", "promotional / sales language", False, (
        "boasts", "vibrant", "exemplifies", "commitment to", "nestled",
        "in the heart of", "groundbreaking", "renowned", "diverse array",
        "breathtaking", "must-visit", "cutting-edge",
    )),
    TellPattern("1.4", "vague attributions", False, (
        "experts argue", "experts believe", "experts claim",
        "some critics argue", "observers have cited", "industry reports",
        "several sources suggest",
    )),
    TellPattern("1.5", "AI vocabulary", False, (
        "delve", "delving", "underscore", "intricate", "tapestry", "testament",
        "pivotal", "showcase", "foster", "leverage", "realm", "seamless",
        "bolster", "garner", "meticulous", "vibrant", "crucial",
        "emphasize", "highlight", "align with", "deep dive",
    )),
    TellPattern("1.6", "copula avoidance", False, (
        "serves as", "stands as", "functions as", "operates as",
        "boasts a", "features a", "maintains a", "offers a",
    )),
    TellPattern("1.7", "negative parallelisms", False, (
        "not just", "not merely", "not only",
    )),
    TellPattern("1.9", "vague connection / association", False, (
        "in connection with", "connected with", "closely associated",
        "associated with",
    )),
    TellPattern("1.10", "placeholder / unfilled template", True, ()),
    TellPattern("1.11", "formulaic challenges-and-outlook", False, (
        "despite these promising results", "despite these challenges",
        "despite its success", "several challenges remain",
        "future work will", "challenges and future", "future outlook",
        "continues to thrive",
    )),
    TellPattern("1.12", "knowledge-gap disclaimer + speculation", False, (
        "not extensively documented", "little is known",
        "not widely documented", "not publicly available",
        "based on available information", "maintains a low profile",
        "likely due to",
    )),
    TellPattern("1.13", "fake deeper truth", False, (
        "at its core", "what really matters", "the real question is",
        "the heart of the matter", "in reality",
    )),
    TellPattern("1.14", "defensive 'not X' moves", False, (
        "this is not to say", "to be clear", "don't get me wrong",
        "i'm not arguing", "i am not arguing", "some might say",
        "this isn't mainly about", "it should be noted that this does not imply",
    )),
    TellPattern("1.15", "rejected fake alternatives", False, (
        "a tempting approach would be", "one might be tempted to",
        "an obvious approach would be", "it would be easy to just",
        "you might think", "some would suggest",
    )),
    TellPattern("1.16", "filler / qualifier stacking", False, (
        "in order to", "due to the fact that", "at this point in time",
        "it is worth noting that", "it is important to note that",
        "could potentially possibly",
    )),
    TellPattern("1.17", "em / en dashes", True, ()),
    TellPattern("1.19", "one-line closers / example restatement", False, (
        "that is the real win", "that distinction matters", "let that sink in",
        "this shows the importance", "the message was clear",
        "here's the thing", "here's what you need to know", "let's dive in",
        "let's explore", "without further ado",
    )),
)

# 1.10 placeholders: bracket drafting-notes, INSERT_/PASTE_ tokens, <URL>,
# and XX dates. `[N]`-style inline citations and bare "[...]" are NOT flagged.
PLACEHOLDER_RES = (
    re.compile(
        r"\[[^\]]{0,60}"
        r"(?:describe|insert|todo|placeholder|citation needed|\bxx\b|xxx)"
        r"[^\]]{0,60}\]",
        re.IGNORECASE,
    ),
    re.compile(r"\binsert_[a-z_]{1,20}\b", re.IGNORECASE),
    re.compile(r"\bpaste_[a-z_]{1,20}\b", re.IGNORECASE),
    re.compile(r"<url>", re.IGNORECASE),
    re.compile(r"20\d\d\s*[-/]\s*[xX]{2}\s*[-/]\s*[xX]{2}"),
)

EN_DASH = "\u2013"
EM_DASH = "\u2014"
_CJK = "\u4e00-\u9fff"


def _cjk_adjacent(text: str, start: int, end: int) -> bool:
    """True when the dash sits next to a CJK char — Chinese 破折号, not an
    English AI-tell dash. Layer 1's dash rule is an English-register rule;
    Chinese prose legitimately uses —— (C7 does not ban it)."""
    prev = text[start - 1] if start > 0 else ""
    nxt = text[end] if end < len(text) else ""
    return bool(re.match(f"[{_CJK}]", prev) or re.match(f"[{_CJK}]", nxt))


# Inline markdown markers (bold / italic / code) can sit between a 破折号 and
# the CJK chars around it ("**待**——**这**"), breaking _cjk_adjacent. Strip
# them for dash-context evaluation only; significance asterisks on p-values
# survive because a bare `*p < 0.05` loses only the markers, not the letter.
_DASH_TEXT_CLEAN = re.compile(r"\*\*|(?<!\*)\*(?!\*)|\x60|(?<!_)_(?!_)")


def _dash_clean(text: str) -> str:
    return _DASH_TEXT_CLEAN.sub("", text)


def scan_pattern(pattern: TellPattern, text: str) -> list[str]:
    """Return the deduped watch-list terms that hit in *text* (max 6)."""
    hits: list[str] = []
    lower = text.lower()
    for term in pattern.terms:
        if " " in term:
            m = re.search(re.escape(term), lower)
        else:
            m = re.search(r"\b" + re.escape(term) + r"\w*", lower)
        if m and term not in hits:
            hits.append(term)
            if len(hits) >= 6:
                break
    return hits


def scan_placeholders(text: str) -> list[str]:
    hits: list[str] = []
    for rx in PLACEHOLDER_RES:
        for m in rx.finditer(text):
            snippet = m.group(0)
            if snippet not in hits:
                hits.append(snippet)
            if len(hits) >= 6:
                return hits
    return hits


def en_dash_hits(text: str) -> list[str]:
    """En dashes NOT forming a numeric range (2–6%, 2020–2025 are fine)."""
    out: list[str] = []
    for m in re.finditer(EN_DASH, text):
        if _cjk_adjacent(text, m.start(), m.end()):
            continue
        before = text[max(0, m.start() - 2):m.start()]
        after = text[m.end():m.end() + 2]
        if re.search(r"\d\s*$", before) and re.search(r"^\s*\d", after):
            continue
        snippet = text[max(0, m.start() - 10):m.end() + 10].replace("\n", " ")
        if snippet not in out:
            out.append(snippet)
        if len(out) >= 6:
            break
    return out


@dataclass
class Finding:
    rule: str
    severity: str   # "fail" | "warn" | "info"
    message: str
    detail: dict = field(default_factory=dict)


def audit(text: str) -> tuple[int, list[Finding]]:
    """Scan one After text. Returns (exit_code, findings)."""
    findings: list[Finding] = []

    # ----- Strict rules: unconditional in academic register -----
    dash_text = _dash_clean(text)
    em_count = len([
        m for m in re.finditer(EM_DASH, dash_text)
        if not _cjk_adjacent(dash_text, m.start(), m.end())
    ])
    if em_count:
        findings.append(Finding(
            "1.17 em dash", "fail",
            f"{em_count} em dash(es) in After text (Layer 1 rule: remove entirely in academic register).",
        ))
    en = en_dash_hits(dash_text)
    if en:
        findings.append(Finding(
            "1.17 en dash", "fail",
            f"{len(en)} non-range en dash(es) in After text.",
            {"examples": en[:3]},
        ))
    ph = scan_placeholders(text)
    if ph:
        findings.append(Finding(
            "1.10 placeholder", "fail",
            f"{len(ph)} placeholder / unfilled template hit(s) in After text.",
            {"examples": ph[:5]},
        ))

    # ----- Weak rules: context-dependent, several together are the tell -----
    weak: dict[str, list[str]] = {}
    for pat in PATTERNS:
        if pat.pid in ("1.10", "1.17"):
            continue
        hits = scan_pattern(pat, text)
        if hits:
            weak[pat.pid] = hits

    for pid, hits in sorted(weak.items()):
        pat = next(p for p in PATTERNS if p.pid == pid)
        findings.append(Finding(
            f"{pid} {pat.name}", "warn",
            f"{len(hits)} weak-tell match(es) — verify context before deciding.",
            {"matches": hits},
        ))
    if len(weak) >= 3:
        patterns = ", ".join(
            f"{pid} {next(p for p in PATTERNS if p.pid == pid).name}"
            for pid in sorted(weak)
        )
        findings.append(Finding(
            "co-occurrence", "warn",
            f"{len(weak)} weak-tell patterns co-occur — the catalog's 'several patterns together' bar. Likely residual AI text.",
            {"patterns": patterns},
        ))

    if not findings:
        findings.append(Finding(
            "summary", "info",
            "No Layer 1 residual AI tells detected in After text.",
        ))

    has_fail = any(f.severity == "fail" for f in findings)
    has_warn = any(f.severity == "warn" for f in findings)
    return (2 if has_fail else 1 if has_warn else 0), findings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("combined", nargs="?", help="Combined markdown file with ## Before / ## After (positional alias of --combined)")
    p.add_argument("--combined", dest="combined_flag", nargs="?", const=None, default=None, help="Combined markdown file; '-' reads stdin")
    p.add_argument("--after", help="Plain text/markdown file to audit (whole file)")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of human report")
    p.add_argument("--quiet", action="store_true", help="Suppress info-level findings in human mode")
    args = p.parse_args()

    combined_path = args.combined_flag or args.combined
    if args.after:
        texts = [Path(args.after).read_text(encoding="utf-8")]
    elif combined_path == "-":
        texts = [after for _, after in split_combined_all(sys.stdin.read())]
    elif combined_path:
        texts = [after for _, after in split_combined_all(Path(combined_path).read_text(encoding="utf-8"))]
    else:
        p.error("Provide a combined file (positional or --combined), or --after FILE.")

    if not texts:
        print("audit_tells: no ## After spans found", file=sys.stderr)
        return 3

    all_findings: list[Finding] = []
    max_exit = 0
    for idx, text in enumerate(texts, start=1):
        code, findings = audit(text)
        if len(texts) > 1:
            for f in findings:
                f.rule = f"{f.rule}#{idx}"
        all_findings.extend(findings)
        max_exit = max(max_exit, code)

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
    return max_exit


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # crash must never masquerade as exit 0/1/2
        print(f"audit_tells: unexpected crash: {exc}", file=sys.stderr)
        sys.exit(3)
