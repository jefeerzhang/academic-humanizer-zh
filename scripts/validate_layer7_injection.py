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
    python3 scripts/validate_layer7_injection.py before.md after.md
    python3 scripts/validate_layer7_injection.py --combined example.md
    python3 scripts/validate_layer7_injection.py --combined --all-pairs example.md

Exit codes:
    0  PASS  — Layer 7 contract honored
    1  WARN  — soft warning (hedge density outside suggested range)
    2  FAIL  — Layer 7 violation (first-person abuse, hedge in Results, blacklist hit)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from combined_parser import split_combined, split_combined_all

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


FIRST_PERSON_ACADEMIC_RE = re.compile(
    r"笔者(?:认为|倾向于|猜测|判断)|"
    r"本研究(?:倾向于|认为|猜测)|"
    r"我们倾向于(?:将|把|对)|"
    r"本文(?:倾向于|猜测)",
)

FIRST_PERSON_COLLOQUIAL_RE = re.compile(
    r"(?:^|[^本研笔])我(?:认为|觉得|感觉|想|倾向于|猜测)|"
    r"我个人(?:认为|觉得|感觉)|"
    r"在我看来",
)

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
    r"有待跨地区.{0,4}验证",
]
HEDGING_RE = re.compile("|".join(HEDGING_PATTERNS))

BLACKLIST_PATTERNS = [
    r"🔥|💡|👍|✨|🌟|⭐|💯|🎉|🤖",
    r"绝绝子|家人们|YYDS|绝美|绝绝",
    r"(?:^|[^笔本研])我(?:觉得|感觉|想|倾向)",
    # no \b: CJK has no word boundary, so a leading \b misses 挺 after a CJK char.
    # Match complete tokens only (avoid fragmenting 蛮不错 / false-flagging 蛮不讲理).
    r"挺(?:好|多|不错)|蛮(?:好|不错)",
]
BLACKLIST_RE = re.compile("|".join(BLACKLIST_PATTERNS))

SECTION_HEADER_RE = re.compile(
    r"^#{1,6}\s*(?:\d+\.?\s*)?"
    r"("
    r"方法|方法论|研究方法|实验设计|数据与|实证结果|研究结果|结果|发现|"
    r"结果与讨论|讨论|局限|局限性|政策含义|摘要|引言|背景|文献综述|"
    r"Methods?|Results?(?:\s+and\s+Discussion)?|Discussion|Limitations?|"
    r"Conclusions?|Introduction|Abstract|Background|Literature\s+Review"
    r")\s*$",
    re.MULTILINE | re.IGNORECASE,
)

SECTION_NORMALIZE: dict[str, str] = {
    "方法": "方法", "方法论": "方法论", "研究方法": "研究方法",
    "实验设计": "实验设计", "数据与": "数据与", "实证结果": "实证结果",
    "研究结果": "研究结果", "结果": "结果", "发现": "发现",
    "结果与讨论": "结果与讨论", "讨论": "讨论", "局限": "局限", "局限性": "局限",
    "政策含义": "政策含义", "摘要": "摘要", "引言": "引言", "背景": "背景",
    "文献综述": "文献综述", "methods": "方法", "method": "方法",
    "results": "结果", "result": "结果",
    "results and discussion": "结果与讨论",
    "discussion": "讨论", "limitations": "局限", "limitation": "局限",
    "conclusions": "结论", "conclusion": "结论", "introduction": "引言",
    "abstract": "摘要", "background": "背景", "literature review": "文献综述",
}

COMPOUND_RESULTS_DISCUSSION = frozenset({"结果与讨论"})

DISCUSSION_SPLIT_RE = re.compile(
    r"^(?:"
    r"#{1,6}\s*讨论\s*$|讨论[：:]|"
    r"#{1,6}\s*Discussion\s*$|Discussion[.:]"
    r")",
    re.MULTILINE | re.IGNORECASE,
)

LAYER7_ACTIVATION_MARKERS = [
    "Layer 7", "启用注入", "启用 Layer 7", "学术注入层",
    "cognitive hedging", "academic injection",
]

FORBIDDEN_SECTIONS = {
    "方法", "方法论", "研究方法", "实验设计", "数据与",
    "实证结果", "研究结果", "结果", "发现", "摘要", "preamble",
}


@dataclass
class Finding:
    severity: str
    rule: str
    message: str
    location: str = ""
    evidence: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    layer7_active: bool = False
    first_person_count: int = 0
    hedge_count: int = 0
    text_length: int = 0
    prose_length: int = 0
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


def _normalize_section(raw: str) -> str:
    key = raw.strip()
    return SECTION_NORMALIZE.get(key, SECTION_NORMALIZE.get(key.lower(), key))


def _split_compound_results_discussion(
    body: str, base_line: int,
) -> list[tuple[str, str, int]]:
    """Split 结果与讨论 / Results and Discussion into Results + Discussion spans."""
    m = DISCUSSION_SPLIT_RE.search(body)
    if not m:
        return [("结果", body, base_line)]
    parts: list[tuple[str, str, int]] = []
    before = body[: m.start()].strip()
    after = body[m.end():].strip()
    if before:
        parts.append(("结果", before, base_line))
    if after:
        disc_line = base_line + body[: m.start()].count("\n")
        parts.append(("讨论", after, disc_line))
    return parts


def sectionize(text: str) -> list[tuple[str, str, int]]:
    matches = list(SECTION_HEADER_RE.finditer(text))
    if not matches:
        return [("unknown", text, 1)]

    sections: list[tuple[str, str, int]] = []
    if matches[0].start() > 0:
        pre_body = text[: matches[0].start()].strip()
        if pre_body:
            sections.append(("preamble", pre_body, 1))

    for i, m in enumerate(matches):
        section_name = _normalize_section(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        start_line = text[: m.start()].count("\n") + 1
        if not body:
            continue
        if section_name in COMPOUND_RESULTS_DISCUSSION:
            sections.extend(_split_compound_results_discussion(body, start_line))
        else:
            sections.append((section_name, body, start_line))
    return sections


def _editable_prose_length(text: str) -> int:
    in_fence = False
    length = 0
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith("|"):
            continue
        length += len(line)
    return length


def _is_skippable_context(text: str, offset: int) -> bool:
    line_start = text.rfind("\n", 0, offset) + 1
    if text[:line_start].count("```") % 2 == 1:
        return True
    line_end = text.find("\n", offset)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        return True
    if line[: offset - line_start].count("`") % 2 == 1:
        return True
    return False


def check_first_person(
    sections: list[tuple[str, str, int]],
) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    academic_hits: list[tuple[str, int, str]] = []
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

    for sec, line, match in colloquial_hits:
        findings.append(Finding(
            severity="FAIL", rule="L7.1",
            message=f"口语第一人称 '{match}' 出现在学术段落（section={sec}）；学术 register 禁用。",
            location=f"line {line}, §{sec}", evidence=match,
        ))

    if len(academic_hits) > 1:
        ev = "; ".join(f"{m}@line {ln}" for _, ln, m in academic_hits)
        findings.append(Finding(
            severity="FAIL", rule="L7.1",
            message=f"学术合规第一人称出现 {len(academic_hits)} 次（上限 1 处/全文）。",
            location="全文", evidence=ev,
        ))

    for sec, line, match in academic_hits:
        if sec in FORBIDDEN_SECTIONS:
            findings.append(Finding(
                severity="FAIL", rule="L7.1",
                message=f"第一人称 '{match}' 落在禁用段落 §{sec}（仅 Discussion/Conclusion/Limitations/政策含义 允许）。",
                location=f"line {line}, §{sec}", evidence=match,
            ))

    return findings, len(academic_hits)


def check_hedging(
    after: str, sections: list[tuple[str, str, int]],
) -> tuple[list[Finding], int, float]:
    findings: list[Finding] = []
    prose_len = _editable_prose_length(after)
    if prose_len == 0:
        return findings, 0, 0.0

    all_hits: list[tuple[str, int, str]] = []
    for sec_name, body, base_line in sections:
        for m in HEDGING_RE.finditer(body):
            if _is_skippable_context(body, m.start()):
                continue
            line_no = body[: m.start()].count("\n") + base_line
            all_hits.append((sec_name, line_no, m.group(0)))

    hedge_count = len(all_hits)
    density = hedge_count / max(prose_len, 1) * 1000.0

    if hedge_count > 0:
        if prose_len < 1000:
            if hedge_count > 3:
                findings.append(Finding(
                    severity="WARN", rule="L7.2",
                    message=f"短文本（{prose_len} 字）认知边界留白 {hedge_count} 处（建议 ≤3）。",
                    location="全文",
                    evidence=f"{hedge_count} hits in {prose_len} prose chars",
                ))
        elif not (1.0 <= density <= 3.0):
            findings.append(Finding(
                severity="WARN", rule="L7.2",
                message=f"认知边界留白密度 {density:.2f}/千字（建议 1.0–3.0）。",
                location="全文",
                evidence=f"{hedge_count} hits in {prose_len} prose chars",
            ))

    for sec, line, match in all_hits:
        if sec in FORBIDDEN_SECTIONS:
            findings.append(Finding(
                severity="FAIL", rule="L7.2",
                message=f"认知边界留白 '{match}' 落在禁用段落 §{sec}（仅 Discussion/Conclusion/Limitations 允许）。",
                location=f"line {line}, §{sec}", evidence=match,
            ))

    return findings, hedge_count, density


def check_blacklist(after: str) -> list[Finding]:
    findings: list[Finding] = []
    for m in BLACKLIST_RE.finditer(after):
        if _is_skippable_context(after, m.start()):
            continue
        line_no = after[: m.start()].count("\n") + 1
        findings.append(Finding(
            severity="FAIL", rule="L7.3",
            message=f"反人味陷阱黑名单命中：'{m.group(0)}'。",
            location=f"line {line_no}", evidence=m.group(0),
        ))
    return findings


def detect_layer7_active(before: str, after: str) -> bool:
    text = before + "\n" + after
    if any(m in text for m in LAYER7_ACTIVATION_MARKERS):
        return True
    if FIRST_PERSON_ACADEMIC_RE.search(after):
        return True
    if HEDGING_RE.search(after):
        return True
    return False


def audit_pair(before: str, after: str, *, force: bool, no_red_line: bool) -> Report:
    sections = sectionize(after)
    report = Report(
        text_length=len(after),
        prose_length=_editable_prose_length(after),
    )

    if not force and not detect_layer7_active(before, after):
        report.findings.append(Finding(
            severity="INFO", rule="L7.0",
            message="未检测到 Layer 7 启用标记。默认 Layer 7 未激活，跳过审计（用 --force 强制审计）。",
        ))
        return report

    report.layer7_active = True

    fp_findings, fp_count = check_first_person(sections)
    report.findings.extend(fp_findings)
    report.first_person_count = fp_count

    h_findings, hedge_count, density = check_hedging(after, sections)
    report.findings.extend(h_findings)
    report.hedge_count = hedge_count
    report.hedge_per_1k = round(density, 2)

    report.findings.extend(check_blacklist(after))

    if not no_red_line and before:
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
                        severity="FAIL", rule="L7.4",
                        message="validate_red_lines.py 报告 C0–C2 红线被破坏（exit 2）。",
                        location="全文",
                        evidence=proc.stdout.strip().splitlines()[-1] if proc.stdout else "",
                    ))
                elif proc.returncode == 1:
                    report.findings.append(Finding(
                        severity="WARN", rule="L7.4",
                        message="validate_red_lines.py 报告 C0–C2 警告（exit 1）。",
                        location="全文",
                        evidence=proc.stdout.strip().splitlines()[-1] if proc.stdout else "",
                    ))
            except Exception as exc:  # pragma: no cover
                report.findings.append(Finding(
                    severity="WARN", rule="L7.4",
                    message=f"无法调用 validate_red_lines.py：{exc}",
                ))

    return report


def merge_reports(reports: list[Report]) -> Report:
    if len(reports) == 1:
        return reports[0]
    merged = Report(layer7_active=any(r.layer7_active for r in reports))
    active = [r for r in reports if r.layer7_active]
    if active:
        merged.text_length = sum(r.text_length for r in active)
        merged.prose_length = sum(r.prose_length for r in active)
        merged.first_person_count = max(r.first_person_count for r in active)
        merged.hedge_count = max(r.hedge_count for r in active)
        if merged.prose_length:
            merged.hedge_per_1k = round(
                merged.hedge_count / merged.prose_length * 1000.0, 2
            )
    for idx, rep in enumerate(reports, start=1):
        for f in rep.findings:
            merged.findings.append(Finding(
                severity=f.severity,
                rule=f"{f.rule}#{idx}" if len(reports) > 1 else f.rule,
                message=f.message,
                location=f.location,
                evidence=f.evidence,
            ))
    return merged


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--combined", action="store_true")
    ap.add_argument("--all-pairs", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-red-line", action="store_true")
    args = ap.parse_args()

    pairs: list[tuple[str, str]] = []

    if args.combined:
        if not args.files:
            print("ERROR: --combined requires a file path", file=sys.stderr)
            return 2
        text = Path(args.files[0]).read_text(encoding="utf-8")
        pairs = list(split_combined_all(text))
        if not pairs:
            print("validate_layer7_injection: no ## Before / ## After pairs found", file=sys.stderr)
            return 3
        if not args.all_pairs and len(pairs) > 1:
            pairs = pairs[:1]
    elif len(args.files) == 2:
        pairs = [
            (
                Path(args.files[0]).read_text(encoding="utf-8"),
                Path(args.files[1]).read_text(encoding="utf-8"),
            )
        ]
    elif len(args.files) == 1:
        pairs = [(Path(args.files[0]).read_text(encoding="utf-8"), "")]
    else:
        raw = sys.stdin.read()
        if "<<<AFTER>>>" in raw:
            b, a = raw.split("<<<AFTER>>>", 1)
            pairs = [(b.strip(), a.strip())]
        else:
            pairs = [("", raw.strip())]

    reports = [
        audit_pair(b, a, force=args.force, no_red_line=args.no_red_line)
        for b, a in pairs
    ]
    report = merge_reports(reports)
    _emit(report, args)
    if any(r.exit_code() == 2 for r in reports):
        return 2
    if any(r.exit_code() == 1 for r in reports):
        return 1
    return 0


def _emit(report: Report, args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return
    code = report.exit_code()
    label = {0: "PASS", 1: "WARN", 2: "FAIL"}.get(code, "?")
    print(f"[{label}] Layer 7 injection audit")
    print(f"  layer7_active     : {report.layer7_active}")
    print(f"  text_length       : {report.text_length}")
    print(f"  prose_length      : {report.prose_length}")
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
