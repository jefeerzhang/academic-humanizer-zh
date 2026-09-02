#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_layer7_injection.py — Academic Humanizer Layer 7 injection auditor.

Companion to validate_red_lines.py. Layer 7 (Academic Injection Layer) is
an *additive* layer that allows "cognitive hedging" + "first-person
limiting density" in academic prose; this auditor checks the AFTER text
honors the Layer 7 contract:

  L7.1  First-person count <= 1 (academic: 笔者认为 / 本研究倾向于 /
        我们倾向于), and ONLY in Discussion / Conclusion / Limitations.
  L7.2  Cognitive hedging density 1–3 per 1000 chars (suggested), AND
        must NOT land in Methods / Results / 数据陈述段落.
  L7.3  Anti-human-trap blacklist must have 0 hits (no emoji, no
        小红书体, no 口语第一人称 我觉得/我认为).
  L7.4  Delegates C0–C2 red lines to validate_red_lines.py (exit 0).

Usage:
    # Two files:
    python3 scripts/validate_layer7_injection.py after.md before.md

    # One combined markdown with "## Before" and "## After":
    python3 scripts/validate_layer7_injection.py --combined example.md

Exit codes:
    0  PASS  — Layer 7 contract honored
    1  WARN  — soft warning (hedge density outside suggested range)
    2  FAIL  — Layer 7 violation (first-person abuse, hedge in Results, blacklist hit)

NOTE: Layer 7 is OPTIONAL. If the input does not claim Layer 7 activation
(look for "Layer 7" or "启用注入" markers in the change log), this auditor
emits a single informational message and exits 0. Pass --force to always audit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

# Windows consoles often default to a legacy codepage (e.g. GBK / cp936) that
# cannot encode the FAIL/WARN tags. Force UTF-8 so output never crashes.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

# Academic first-person (compliant)
FIRST_PERSON_ACADEMIC_RE = re.compile(
    r"笔者(?:认为|倾向于|猜测|判断)|"
    r"本研究(?:倾向于|认为|猜测)|"
    r"我们倾向于(?:将|把|对)|"
    r"本文(?:倾向于|猜测)",
)

# Colloquial first-person (blacklisted in academic)
FIRST_PERSON_COLLOQUIAL_RE = re.compile(
    r"(?:^|[^本研笔])我(?:认为|觉得|感觉|想|倾向于|猜测)|"
    r"我个人(?:认为|觉得|感觉)|"
    r"在我看来",
)

# Cognitive hedging — patterns that signal "academic hedging" / "认知边界留白"
HEDGING_PATTERNS = [
    r"样本限制使.{0,15}需谨慎对待",
    r"样本限制使.{0,15}需要谨慎",
    r"目前尚不清楚",
    r"倾向于将.{0,15}归因于",
    r"倾向于把.{0,15}归因于",
    r"倾向于.{0,8}归因于",
    r"这一发现有待.{0,8}验证",
    r"上述结论.{0,8}成立.{0,8}条件",
    r"不能(?:完全|彻底)?排除",
    r"在.{0,15}条件下成立",
    r"需谨慎对待",
    r"有待进一步.{0,4}检验",
    r"有待跨地区.{0,4}验证",
]
HEDGING_RE = re.compile("|".join(HEDGING_PATTERNS))

# Anti-human-trap blacklist (academic version)
BLACKLIST_PATTERNS = [
    r"🔥|💡|👍|✨|🌟|⭐|💯|🎉|🤖",     # emoji
    r"绝绝子|家人们|YYDS|绝美|绝绝",   # 小红书体
    r"(?:^|[^笔本研])我(?:觉得|感觉|想|倾向)",  # 口语第一人称
    r"\b挺(?:好|多|不)|蛮(?:好|不)",     # 学术 register 不兼容
]
BLACKLIST_RE = re.compile("|".join(BLACKLIST_PATTERNS))

# Section markers (Chinese academic conventions). Layer 7 forbids cognitive
# hedging from landing in Methods / Results sections.
SECTION_HEADER_RE = re.compile(
    r"^#{1,6}\s*(?:\d+\.?\s*)?"          # optional numbering
    r"(方法|方法论|研究方法|实验设计|数据与|实证结果|研究结果|结果|发现|结论|讨论|局限|政策含义|摘要|引言|背景|文献综述)\s*$",
    re.MULTILINE,
)

# Marker that the user/skill claims Layer 7 was activated in the change log.
LAYER7_ACTIVATION_MARKERS = [
    "Layer 7",
    "启用注入",
    "启用 Layer 7",
    "学术注入层",
    "cognitive hedging",
    "academic injection",
]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    severity: str            # "FAIL" | "WARN" | "INFO"
    rule: str                # "L7.1" | "L7.2" | "L7.3" | "L7.4"
    message: str
    location: str = ""       # line number or section name
    evidence: str = ""       # the offending snippet


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    layer7_active: bool = False
    first_person_count: int = 0
    hedge_count: int = 0
    text_length: int = 0
    hedge_per_1k: float = 0.0

    def exit_code(self) -> int:
        if any(f.severity == "FAIL" for f in self.findings):
            return 2
        if any(f.severity == "WARN" for f in self.findings):
            return 1
        return 0

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "findings": [asdict(f) for f in self.findings],
            "exit_code": self.exit_code(),
        }


# ---------------------------------------------------------------------------
# Section detection — partition the text by academic section headers so we can
# tell where (in Results vs Discussion) a hedge or first-person landed.
# ---------------------------------------------------------------------------

def sectionize(text: str) -> list[tuple[str, str, int]]:
    """Return list of (section_name, body, start_line). Section name is
    'unknown' if no header is found before the first header."""
    matches = list(SECTION_HEADER_RE.finditer(text))
    if not matches:
        return [("unknown", text, 1)]

    sections: list[tuple[str, str, int]] = []
    # Pre-header region (摘要/引言 unnumbered)
    if matches[0].start() > 0:
        pre_body = text[: matches[0].start()].strip()
        if pre_body:
            sections.append(("preamble", pre_body, 1))

    for i, m in enumerate(matches):
        section_name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        start_line = text[: m.start()].count("\n") + 1
        if body:
            sections.append((section_name, body, start_line))
    return sections


# Methods / Results / 数据陈述 are forbidden for Layer 7 injection.
FORBIDDEN_SECTIONS = {"方法", "方法论", "研究方法", "实验设计", "数据与",
                       "实证结果", "研究结果", "结果", "发现", "preamble"}


# ---------------------------------------------------------------------------
# Layer 7 checks
# ---------------------------------------------------------------------------

def check_first_person(after: str, sections: list[tuple[str, str, int]]) -> list[Finding]:
    findings: list[Finding] = []
    academic_hits: list[tuple[str, int, str]] = []   # (section, line, match)
    colloquial_hits: list[tuple[str, int, str]] = []

    for sec_name, body, base_line in sections:
        for m in FIRST_PERSON_ACADEMIC_RE.finditer(body):
            if _is_skippable_context(body, m.start()):
                continue
            line_no = body[: m.start()].count("\n") + base_line
            academic_hits.append((sec_name, line_no, m.group(0)))
        for m in FIRST_PERSON_COLLOQUIAL_RE.finditer(body):
            if _is_skippable_context(body, m.start()):
                continue
            line_no = body[: m.start()].count("\n") + base_line
            colloquial_hits.append((sec_name, line_no, m.group(0)))

    # L7.1a — colloquial first-person: hard fail
    for sec, line, match in colloquial_hits:
        findings.append(Finding(
            severity="FAIL",
            rule="L7.1",
            message=f"口语第一人称 '{match}' 出现在学术段落（section={sec}）；学术 register 禁用。",
            location=f"line {line}, §{sec}",
            evidence=match,
        ))

    # L7.1b — academic first-person count > 1: hard fail
    if len(academic_hits) > 1:
        ev = "; ".join(f"{m}@line {ln}" for _, ln, m in academic_hits)
        findings.append(Finding(
            severity="FAIL",
            rule="L7.1",
            message=f"学术合规第一人称出现 {len(academic_hits)} 次（上限 1 处/全文）。",
            location="全文",
            evidence=ev,
        ))

    # L7.1c — academic first-person landing in Methods/Results/preamble: hard fail
    for sec, line, match in academic_hits:
        if sec in FORBIDDEN_SECTIONS:
            findings.append(Finding(
                severity="FAIL",
                rule="L7.1",
                message=f"第一人称 '{match}' 落在禁用段落 §{sec}（仅 Discussion/Conclusion/Limitations/政策含义 允许）。",
                location=f"line {line}, §{sec}",
                evidence=match,
            ))

    return findings, len(academic_hits)


def check_hedging(after: str, sections: list[tuple[str, str, int]]) -> tuple[list[Finding], int, float]:
    findings: list[Finding] = []
    total_len = len(after)
    if total_len == 0:
        return findings, 0, 0.0

    all_hits: list[tuple[str, int, str]] = []
    for sec_name, body, base_line in sections:
        for m in HEDGING_RE.finditer(body):
            if _is_skippable_context(body, m.start()):
                continue
            line_no = body[: m.start()].count("\n") + base_line
            all_hits.append((sec_name, line_no, m.group(0)))

    hedge_count = len(all_hits)
    # Density is computed against the *full* text length (including skipped
    # table cells); that's intentional — the contract is per-1000-chars of
    # editable prose, and skipped tokens don't count as prose.
    density = hedge_count / max(total_len, 1) * 1000.0

    # L7.2a — hedge density outside 1–3 per 1000 chars → soft warn
    if hedge_count > 0 and not (1.0 <= density <= 3.0):
        findings.append(Finding(
            severity="WARN",
            rule="L7.2",
            message=f"认知边界留白密度 {density:.2f}/千字（建议 1.0–3.0）。",
            location="全文",
            evidence=f"{hedge_count} hits in {total_len} chars",
        ))

    # L7.2b — hedge landing in Methods/Results/preamble: hard fail
    for sec, line, match in all_hits:
        if sec in FORBIDDEN_SECTIONS:
            findings.append(Finding(
                severity="FAIL",
                rule="L7.2",
                message=f"认知边界留白 '{match}' 落在禁用段落 §{sec}（仅 Discussion/Conclusion/Limitations 允许）。",
                location=f"line {line}, §{sec}",
                evidence=match,
            ))

    return findings, hedge_count, density


def check_blacklist(after: str) -> list[Finding]:
    findings: list[Finding] = []
    for m in BLACKLIST_RE.finditer(after):
        if _is_skippable_context(after, m.start()):
            continue
        line_no = after[: m.start()].count("\n") + 1
        findings.append(Finding(
            severity="FAIL",
            rule="L7.3",
            message=f"反人味陷阱黑名单命中：'{m.group(0)}'。",
            location=f"line {line_no}",
            evidence=m.group(0),
        ))
    return findings


def _is_skippable_context(text: str, offset: int) -> bool:
    """Return True if the position at `offset` lies inside a region that should
    NOT be audited: fenced code blocks (``` ... ```), inline code spans
    (`...`), or markdown table rows (lines starting with `|`). This lets
    documentation files that *discuss* the patterns (示例 + 修改对照 tables)
    be audited without false positives.

    The function walks backwards to the start of the current line, checks the
    line for table/code-fence markers, and walks forwards looking for an
    enclosing code span.
    """
    # 1. Inside a fenced code block?
    line_start = text.rfind("\n", 0, offset) + 1
    # Count ``` fences above the line
    fence_count = text[:line_start].count("```")
    if fence_count % 2 == 1:
        return True

    # 2. Inside a markdown table row? (line starts with `|` after whitespace)
    line_end = text.find("\n", offset)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        return True

    # 3. Inside an inline code span? (count of unescaped backticks on the line
    #    to the left of offset is odd)
    backtick_count = line[: offset - line_start].count("`")
    if backtick_count % 2 == 1:
        return True

    return False


def detect_layer7_active(before: str, after: str) -> bool:
    """Layer 7 is OPTIONAL. We activate this auditor only if the change log
    or before/after pair indicates Layer 7 was used. Heuristic: any
    activation marker in before/after, OR > 0 first-person academic hits,
    OR > 0 cognitive hedging hits."""
    text = before + "\n" + after
    if any(m in text for m in LAYER7_ACTIVATION_MARKERS):
        return True
    if FIRST_PERSON_ACADEMIC_RE.search(after):
        return True
    if HEDGING_RE.search(after):
        return True
    return False


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def parse_combined(md: str) -> tuple[str, str]:
    """Split a combined markdown into (before, after) by '## Before' / '## After'."""
    md_low = md
    m_before = re.search(r"^##\s*Before\b.*?$", md_low, re.MULTILINE | re.IGNORECASE)
    m_after = re.search(r"^##\s*After\b.*?$", md_low, re.MULTILINE | re.IGNORECASE)
    if not (m_before and m_after):
        return "", md
    body = md[m_after.end():]
    m_after_end = re.search(r"^##\s", body, re.MULTILINE)
    after = body[: m_after_end.start()] if m_after_end else body
    before = md[m_before.end(): m_after.start()]
    return before.strip(), after.strip()


def read_input(path: str | None, combined: bool) -> tuple[str, str]:
    if path is None or path == "-":
        raw = sys.stdin.read()
        if "<<<AFTER>>>" in raw:
            before, after = raw.split("<<<AFTER>>>", 1)
        else:
            before, after = "", raw
        return before.strip(), after.strip()
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if combined:
        return parse_combined(raw)
    # Two-file mode expected via CLI args
    return "", ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*", help="after.md [before.md] (omit if --combined or stdin)")
    ap.add_argument("--combined", action="store_true", help="parse single markdown with ## Before / ## After")
    ap.add_argument("--force", action="store_true", help="audit even if Layer 7 activation markers absent")
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    ap.add_argument("--no-red-line", action="store_true", help="skip C0–C2 red-line delegation")
    args = ap.parse_args()

    if args.combined:
        if not args.files:
            print("ERROR: --combined requires a file path", file=sys.stderr)
            return 2
        before, after = read_input(args.files[0], combined=True)
    elif len(args.files) == 2:
        after = Path(args.files[0]).read_text(encoding="utf-8")
        before = Path(args.files[1]).read_text(encoding="utf-8")
    elif len(args.files) == 1:
        # Single file = the AFTER text. Audit it as-is.
        after = Path(args.files[0]).read_text(encoding="utf-8")
        before = ""
    else:
        before, after = read_input(None, combined=False)

    sections = sectionize(after)
    report = Report(text_length=len(after))

    if not args.force and not detect_layer7_active(before, after):
        report.findings.append(Finding(
            severity="INFO",
            rule="L7.0",
            message="未检测到 Layer 7 启用标记（academic injection marker / 第一人称 / cognitive hedging）。"
                    "默认 Layer 7 未激活，跳过审计（用 --force 强制审计）。",
        ))
        report.layer7_active = False
        _emit(report, args)
        return 0

    report.layer7_active = True

    fp_findings, fp_count = check_first_person(after, sections)
    report.findings.extend(fp_findings)
    report.first_person_count = fp_count

    h_findings, hedge_count, density = check_hedging(after, sections)
    report.findings.extend(h_findings)
    report.hedge_count = hedge_count
    report.hedge_per_1k = round(density, 2)

    bl_findings = check_blacklist(after)
    report.findings.extend(bl_findings)

    # L7.4 — delegate C0–C2 to validate_red_lines.py
    if not args.no_red_line and before:
        script = Path(__file__).parent / "validate_red_lines.py"
        if script.exists():
            try:
                proc = subprocess.run(
                    [sys.executable, str(script), "-"],
                    input=f"{before}\n<<<AFTER>>>\n{after}",
                    capture_output=True, text=True, timeout=30,
                )
                if proc.returncode == 2:
                    report.findings.append(Finding(
                        severity="FAIL",
                        rule="L7.4",
                        message="validate_red_lines.py 报告 C0–C2 红线被破坏（exit 2）。",
                        location="全文",
                        evidence=proc.stdout.strip().splitlines()[-1] if proc.stdout else "",
                    ))
                elif proc.returncode == 1:
                    report.findings.append(Finding(
                        severity="WARN",
                        rule="L7.4",
                        message="validate_red_lines.py 报告 C0–C2 警告（exit 1）。",
                        location="全文",
                        evidence=proc.stdout.strip().splitlines()[-1] if proc.stdout else "",
                    ))
            except Exception as exc:  # pragma: no cover
                report.findings.append(Finding(
                    severity="WARN",
                    rule="L7.4",
                    message=f"无法调用 validate_red_lines.py：{exc}",
                ))

    _emit(report, args)
    return report.exit_code()


def _emit(report: Report, args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    code = report.exit_code()
    label = {0: "PASS", 1: "WARN", 2: "FAIL"}.get(code, "?")
    print(f"[{label}] Layer 7 injection audit")
    print(f"  layer7_active     : {report.layer7_active}")
    print(f"  text_length       : {report.text_length}")
    print(f"  first_person_count: {report.first_person_count} (limit <=1)")
    print(f"  hedge_count       : {report.hedge_count}")
    print(f"  hedge_per_1k      : {report.hedge_per_1k} (suggested 1.0–3.0)")
    if not report.findings:
        print("  no findings — Layer 7 contract honored")
        return
    for f in report.findings:
        loc = f" @ {f.location}" if f.location else ""
        ev = f"  evidence: {f.evidence}" if f.evidence else ""
        print(f"  [{f.severity}] {f.rule}: {f.message}{loc}")
        if ev:
            print(ev)


if __name__ == "__main__":
    sys.exit(main())