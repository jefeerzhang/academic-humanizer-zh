#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_examples.py — Audit every shipped example in `examples/` directory.

A thin wrapper that iterates all `examples/*.md` files. Every example uses `## Before` / `## After`
pairs (including English `before-after.md`) so CI audits the same contract the README promises.
both validate_red_lines.py and validate_layer7_injection.py as appropriate:

  - All examples: validate_red_lines.py --all-pairs
  - Examples whose filename or frontmatter mentions "Layer 7" or
    "academic-injection": also validate_layer7_injection.py --combined

Exit codes (CI-friendly):
    0  PASS  — every shipped example audits clean
    1  WARN  — soft warnings only
    2  FAIL  — at least one example has red-line / injection violation
    3  Unexpected crash

Usage:
    python scripts/run_examples.py                 # audit all examples/*.md
    python scripts/run_examples.py --json         # emit JSON report
    python scripts/run_examples.py path/to/foo.md  # audit a single file
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Windows consoles often default to a legacy codepage that cannot encode
# emoji FAIL/WARN tags. Force UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
RED_LINES = REPO_ROOT / "scripts" / "validate_red_lines.py"
LAYER7 = REPO_ROOT / "scripts" / "validate_layer7_injection.py"

# Examples that exercise Layer 7 — by filename marker or by content sniff.
LAYER7_HINTS = ("injection", "layer-7", "layer7")


@dataclass
class AuditResult:
    file: str
    red_lines_exit: int = -1
    red_lines_summary: str = ""
    layer7_exit: int = -1
    layer7_summary: str = ""

    @property
    def is_fail(self) -> bool:
        return (
            self.red_lines_exit in (2, 3) or self.layer7_exit in (2, 3)
        )

    @property
    def is_warn(self) -> bool:
        return (self.red_lines_exit == 1) or (self.layer7_exit == 1)


@dataclass
class RunReport:
    results: list[AuditResult] = field(default_factory=list)

    def exit_code(self) -> int:
        if any(r.is_fail for r in self.results):
            return 2
        if any(r.is_warn for r in self.results):
            return 1
        return 0


def _needs_layer7(path: Path) -> bool:
    name = path.name.lower()
    if any(h in name for h in LAYER7_HINTS):
        return True
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
    except Exception:
        return False
    return ("Layer 7" in head) or ("academic injection" in head.lower())


def _run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode, (proc.stdout or proc.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 3, "timeout"
    except Exception as exc:
        return 3, f"crash: {exc}"


def _summarize(output: str) -> str:
    """Extract the most severe line from the audit output for the report."""
    if not output:
        return "(no output)"
    for line in output.splitlines():
        if "[❌ FAIL]" in line:
            return line[:200]
    for line in output.splitlines():
        if "[⚠️  WARN]" in line or "[⚠️ WARN]" in line:
            return line[:200]
    for line in output.splitlines():
        if "[✅ INFO]" in line or "[✅ PASS]" in line:
            return line[:200]
    return output.splitlines()[0][:200] if output.splitlines() else "(empty)"


def audit_example(path: Path) -> AuditResult:
    result = AuditResult(file=str(path.relative_to(REPO_ROOT)))

    # All shipped examples use ## Before / ## After (see test_repo_consistency.py).
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:4000]
    except Exception:
        return result
    if not re.search(r"^##\s+Before\b", head, flags=re.MULTILINE):
        result.red_lines_exit = 0
        result.red_lines_summary = "skipped (no ## Before / ## After format)"
        return result

    # Red-lines audit (always; --all-pairs catches every ## Before/## After pair)
    rc, out = _run(
        [sys.executable, str(RED_LINES), "--combined", "--all-pairs", str(path)],
        timeout=60,
    )
    result.red_lines_exit = rc
    result.red_lines_summary = _summarize(out)

    # Layer 7 audit (only for examples that exercise Layer 7)
    if _needs_layer7(path):
        rc7, out7 = _run(
            [sys.executable, str(LAYER7), "--combined", "--all-pairs", str(path)],
            timeout=60,
        )
        result.layer7_exit = rc7
        result.layer7_summary = _summarize(out7)

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("files", nargs="*", help="Specific files to audit (default: all examples/*.md)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human report")
    args = ap.parse_args()

    if args.files:
        targets = [Path(f).resolve() for f in args.files]
    else:
        if not EXAMPLES_DIR.exists():
            print(f"run_examples: examples dir missing: {EXAMPLES_DIR}", file=sys.stderr)
            return 3
        targets = sorted(EXAMPLES_DIR.glob("*.md"))

    if not targets:
        print("run_examples: no example files found", file=sys.stderr)
        return 3

    report = RunReport()
    for path in targets:
        report.results.append(audit_example(path))

    if args.json:
        print(json.dumps(
            {
                "exit_code": report.exit_code(),
                "results": [asdict(r) for r in report.results],
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        label = {0: "PASS", 1: "WARN", 2: "FAIL"}.get(report.exit_code(), "?")
        print(f"[{label}] {len(report.results)} shipped example(s) audited")
        for r in report.results:
            tags = []
            for name, rc in [("C0–C2", r.red_lines_exit), ("Layer7", r.layer7_exit)]:
                if rc < 0:
                    continue
                tag = {0: "✅", 1: "⚠️ ", 2: "❌", 3: "💥"}.get(rc, "?")
                tags.append(f"{name}={tag}{rc}")
            print(f"  {r.file}")
            for t in tags:
                print(f"    {t}")
            for label, summ in (("C0–C2", r.red_lines_summary), ("Layer7", r.layer7_summary)):
                if summ and "no output" not in summ and "(empty)" not in summ:
                    print(f"      {label}: {summ}")

    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())