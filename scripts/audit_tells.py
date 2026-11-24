#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_tells.py — Academic Humanizer Layer 1 + C7 residual AI-tell auditor.

After an editing pass, scan the After text for:
  - English Layer 1 general AI tells (`references/layers/layer-1-general-tells.md`)
  - Chinese C7 academic AI tells A–F (`references/rules-zh.md` §1) with §10 whitelist guards
  - L2 sentence-length rhythm uniformity (variance / stdev / CV across prose sentences)

Strict rules (the skill removes these outright in academic register):
  1.10 placeholder / unfilled template text
  1.17 em dashes, and en dashes outside numeric ranges (2–6%, 2020–2025 are fine)

Weak rules (context-dependent; several patterns together are the tell, per the
catalog's false-positive guard):
  - Layer 1 (English): 1.1–1.16, 1.19
  - C7 (Chinese): C7.A (formulaic openers/transitions/closers), C7.B (value-judgment
    saturation), C7.C (abstract subjects), C7.D (nominalized empty verbs),
    C7.E (rule-of-three / stacked transitions), C7.F (meta-commentary / vague consensus)
  - L2.rhythm: flat sentence-length uniformity (low CV or 5+ consecutive uniform-length sentences)

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
    1  WARN  — weak tells or flat sentence rhythm present (review)
    2  FAIL  — strict tell present (placeholder, em dash, or non-range en dash)
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


@dataclass(frozen=True)
class RegexTellPattern:
    pid: str
    name: str
    regexes: tuple[re.Pattern[str], ...]
    whitelist: tuple[re.Pattern[str], ...] = ()


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

# Chinese C7 academic AI-tell patterns (`references/rules-zh.md` §1 A–F).
# Whitelist guards follow `references/rules-zh.md` §0, §2, §10 (do not flag
# 总而言之 / 需要注意的是 / 核心解释变量 / 鉴于此，本文延续 / 方法论 进行检验·回归·稳健性测试).
ZH_PATTERNS: tuple[RegexTellPattern, ...] = (
    RegexTellPattern(
        "C7.A",
        "中文套话开头/过渡/收尾",
        (
            re.compile(r"随着[^。！？\n]{1,20}的(?:不断|迅速|快速|蓬勃|持续)?发展"),
            re.compile(r"在[^。！？\n]{1,18}背景下"),
            re.compile(r"近年来[，,]?[^。！？\n]{0,28}(?:日益|广泛关注|受到关注|蓬勃发展|迅速扩大|迅速发展)"),
            re.compile(r"众所周知|不言而喻|自工业革命以来"),
            re.compile(r"基于以上分析|通过以上讨论|概括而言|有鉴于此"),
            re.compile(r"(?<!有)鉴于此(?![，,]\s*本文延续)"),
            re.compile(r"为[^。！？\n]{1,22}提供了新的思路"),
            re.compile(r"为[^。！？\n]{1,22}开辟了"),
            re.compile(r"对[^。！？\n]{1,20}具有重要(?:的)?参考价值"),
            re.compile(r"具有重要(?:的)?理论意义和实践价值"),
            re.compile(r"为[^。！？\n]{1,26}贡献了力量"),
            re.compile(r"未来值得进一步深入研究|有待后续研究进一步验证|未来依然可期|前景广阔"),
            re.compile(r"这正是[^。！？\n]{1,18}的意义所在"),
        ),
        whitelist=(
            re.compile(r"鉴于此[，,]\s*本文延续"),
        ),
    ),
    RegexTellPattern(
        "C7.B",
        "中文价值判断词饱和",
        (
            re.compile(r"具有重要意义"),
            re.compile(r"发挥(?:了)?关键作用|起到(?:了)?重要作用"),
            re.compile(r"揭示了[^。！？\n]{1,28}的关键作用"),
            re.compile(r"不可忽视|日益显著|深刻变化|深远影响|开创性的|前所未有的"),
            re.compile(r"明确下一步|系统性缺陷|广泛落地"),
        ),
    ),
    RegexTellPattern(
        "C7.C",
        "中文抽象主语代替施动者",
        (
            re.compile(r"(?:时代|社会|科技|行业)的发展"),
            re.compile(r"消费观念正在发生|人类社会经历了"),
        ),
    ),
    RegexTellPattern(
        "C7.D",
        "中文名词化虚化动词",
        (
            re.compile(r"进行(?:优化|调整|改进|探讨|提升|完善|推进)"),
            re.compile(r"做出(?:选择|判断|贡献|决策)"),
            re.compile(r"实现(?:增长|突破|提升|跨越)"),
            re.compile(r"采取措施|加以改进|给予支持|提供保障"),
            re.compile(r"(?:起到|发挥)[^。！？\n]{0,4}作用"),
        ),
        whitelist=(
            re.compile(r"进行(?:了)?(?:以下)?(?:稳健性)?(?:分析|检验|回归|测试|估计)"),
        ),
    ),
    RegexTellPattern(
        "C7.E",
        "中文排比三件套/过渡词堆叠",
        (
            re.compile(r"既是[^。！？\n]{1,22}也是[^。！？\n]{1,22}更是"),
            re.compile(r"不仅[^。！？\n]{1,22}而且[^。！？\n]{1,22}更"),
            re.compile(r"理论意义、实践意义、方法论意义"),
        ),
    ),
    RegexTellPattern(
        "C7.F",
        "中文假客观/元评论",
        (
            re.compile(r"(?:本研究|本文)(?:试图|旨在)探讨"),
            re.compile(r"下面我们来看|接下来我们将"),
            re.compile(r"诸多研究表明|大量研究证实|学界普遍认为|计量学界形成共识"),
            re.compile(r"存在一些局限性"),
        ),
    ),
)

_EN_ABBREV_RE = re.compile(
    r"\b(?:e\.g|i\.e|et al|vs|Fig|Eq|Sec|No|Dr|Mr|Ms|Prof|Inc|Ltd)\.",
    re.IGNORECASE,
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


def _clean_prose_text(text: str) -> str:
    """Extract editable prose, skipping fenced code blocks and markdown tables."""
    in_fence = False
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith("|") or stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            line = re.sub(r"^\s*>\s?", "", line)
        lines.append(line)
    return _dash_clean("\n".join(lines))


def scan_zh_pattern(pattern: RegexTellPattern, text: str) -> list[str]:
    """Return deduped Chinese C7 matches in *text* (max 6), respecting whitelists."""
    prose = _clean_prose_text(text)
    if not re.search(f"[{_CJK}]", prose):
        return []
    hits: list[str] = []
    for rx in pattern.regexes:
        for m in rx.finditer(prose):
            window_start = max(0, m.start() - 8)
            window_end = min(len(prose), m.end() + 12)
            window = prose[window_start:window_end]
            if any(wl.search(window) for wl in pattern.whitelist):
                continue
            snippet = m.group(0).strip()
            if snippet and snippet not in hits:
                hits.append(snippet)
            if len(hits) >= 6:
                return hits
    return hits


def scan_zh_transition_stack(text: str) -> list[str]:
    """Flag C7.E mixed transition stacking within one paragraph:
    首先 + 其次 + (同时|此外|再者). Pure 首先/其次/最后 is whitelisted."""
    prose = _clean_prose_text(text)
    hits: list[str] = []
    for para in re.split(r"\n\s*\n", prose):
        if "首先" in para and "其次" in para:
            extra = [w for w in ("同时", "此外", "再者") if w in para]
            if extra:
                tag = f"首先+其次+{'/'.join(extra)}"
                if tag not in hits:
                    hits.append(tag)
    return hits


def _sentence_unit_length(sentence: str, is_zh: bool) -> int:
    if is_zh:
        cjk_chars = len(re.findall(f"[{_CJK}]", sentence))
        latin_tokens = len(re.findall(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*", sentence))
        return cjk_chars + latin_tokens
    return len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", sentence))


def sentence_rhythm_stats(text: str) -> dict:
    """Compute sentence-length variance / stdev / CV on prose paragraphs.

    Detects L2 flat sentence rhythm (low CV or 5+ consecutive uniform-length
    sentences, matching `references/rules-zh.md` §4).
    """
    prose = _clean_prose_text(text)
    # Skip bullet-list-only lines (e.g. partial diff summaries) from rhythm stats
    body_lines = [
        ln for ln in prose.splitlines()
        if ln.strip() and not re.match(r"^\s*[-*+]\s+", ln)
    ]
    body = "\n".join(body_lines)
    cjk_count = len(re.findall(f"[{_CJK}]", body))
    latin_count = len(re.findall(r"[A-Za-z]+", body))
    is_zh = cjk_count >= latin_count

    if is_zh:
        raw_sents = re.split(r"[。！？!?]+|\n+", body)
        min_len = 5
    else:
        masked = _EN_ABBREV_RE.sub(lambda m: m.group(0).replace(".", ""), body)
        raw_sents = re.split(r"(?<=[.!?])\s+|\n+", masked)
        min_len = 4

    lengths = [
        _sentence_unit_length(s.strip(), is_zh)
        for s in raw_sents
        if s.strip()
    ]
    lengths = [n for n in lengths if n >= min_len]
    n = len(lengths)
    if n == 0:
        return {
            "language": "zh" if is_zh else "en",
            "sentence_count": 0,
            "mean": 0.0,
            "variance": 0.0,
            "stdev": 0.0,
            "cv": 0.0,
            "min": 0,
            "max": 0,
            "uniform_window": False,
            "flag": False,
        }

    mean = sum(lengths) / n
    variance = sum((x - mean) ** 2 for x in lengths) / n
    stdev = math.sqrt(variance)
    cv = (stdev / mean) if mean > 0 else 0.0

    # Window check: 5 consecutive sentences within a narrow band
    band_lo, band_hi, max_span = (20, 35, 8) if is_zh else (15, 28, 6)
    uniform_window = False
    if n >= 5:
        for i in range(n - 4):
            win = lengths[i:i + 5]
            if all(band_lo <= x <= band_hi for x in win) and (max(win) - min(win)) <= max_span:
                uniform_window = True
                break

    min_mean = 15.0 if is_zh else 10.0
    flag = n >= 5 and mean >= min_mean and (cv < 0.18 or uniform_window)

    return {
        "language": "zh" if is_zh else "en",
        "sentence_count": n,
        "mean": round(mean, 2),
        "variance": round(variance, 2),
        "stdev": round(stdev, 2),
        "cv": round(cv, 3),
        "min": min(lengths),
        "max": max(lengths),
        "uniform_window": uniform_window,
        "flag": flag,
    }


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

    # ----- Weak rules: Layer 1 (English) + C7 (Chinese) -----
    weak: dict[str, list[str]] = {}
    pattern_names: dict[str, str] = {}
    for pat in PATTERNS:
        if pat.pid in ("1.10", "1.17"):
            continue
        pattern_names[pat.pid] = pat.name
        hits = scan_pattern(pat, text)
        if hits:
            weak[pat.pid] = hits

    for zpat in ZH_PATTERNS:
        pattern_names[zpat.pid] = zpat.name
        hits = scan_zh_pattern(zpat, text)
        if zpat.pid == "C7.E":
            for stack_hit in scan_zh_transition_stack(text):
                if stack_hit not in hits:
                    hits.append(stack_hit)
        if hits:
            weak[zpat.pid] = hits

    for pid, hits in sorted(weak.items()):
        findings.append(Finding(
            f"{pid} {pattern_names[pid]}", "warn",
            f"{len(hits)} weak-tell match(es) — verify context before deciding.",
            {"matches": hits},
        ))
    if len(weak) >= 3:
        patterns = ", ".join(
            f"{pid} {pattern_names[pid]}"
            for pid in sorted(weak)
        )
        findings.append(Finding(
            "co-occurrence", "warn",
            f"{len(weak)} weak-tell patterns co-occur — the catalog's 'several patterns together' bar. Likely residual AI text.",
            {"patterns": patterns},
        ))

    # ----- L2 sentence-length rhythm uniformity -----
    rhythm = sentence_rhythm_stats(text)
    if rhythm["flag"]:
        findings.append(Finding(
            "L2.rhythm sentence uniformity", "warn",
            (
                f"Sentence lengths are unusually uniform "
                f"(n={rhythm['sentence_count']}, mean={rhythm['mean']}, "
                f"stdev={rhythm['stdev']}, cv={rhythm['cv']}). Vary sentence length."
            ),
            rhythm,
        ))

    if not findings:
        findings.append(Finding(
            "summary", "info",
            "No Layer 1 / C7 residual AI tells detected in After text.",
            {"rhythm": rhythm} if rhythm["sentence_count"] > 0 else {},
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
