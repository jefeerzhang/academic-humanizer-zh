#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for validate_layer7_injection.py — run: python scripts/test_validate_layer7_injection.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from validate_layer7_injection import (
    FORBIDDEN_SECTIONS,
    audit_pair,
    check_hedging,
    sectionize,
)
from combined_parser import split_combined_all as parse_pairs


class TestSectionize(unittest.TestCase):
    def test_english_results_forbidden(self):
        text = "## Results\nWe found X.\n\n## Discussion\n笔者认为 Y。"
        sections = sectionize(text)
        names = [s[0] for s in sections]
        self.assertIn("结果", names)
        self.assertIn("讨论", names)

    def test_compound_header_results_discussion(self):
        text = "## 结果与讨论\n回归结果显示显著。\n"
        sections = sectionize(text)
        self.assertEqual(sections[0][0], "结果")
        self.assertIn("结果", FORBIDDEN_SECTIONS)

    def test_abstract_forbidden(self):
        text = "## 摘要\n笔者认为结论成立。"
        sections = sectionize(text)
        self.assertEqual(sections[0][0], "摘要")
        report = audit_pair("", text, force=True, no_red_line=True)
        fails = [f for f in report.findings if f.severity == "FAIL"]
        self.assertTrue(any("§摘要" in f.message for f in fails))


class TestHedgingDensity(unittest.TestCase):
    def test_short_text_three_hedges_passes(self):
        after = (
            "在 Discussion 段，**笔者认为**，差异源于认知。"
            "**目前尚不清楚**机制是否普适。"
            "**样本限制使**推广**需谨慎对待**——**这一发现有待**跨地区样本验证。"
        )
        sections = sectionize(after)
        findings, count, density = check_hedging(after, sections)
        warns = [f for f in findings if f.severity == "WARN" and f.rule == "L7.2"]
        self.assertEqual(count, 3)
        self.assertEqual(warns, [])

    def test_hedge_in_results_fails(self):
        after = "## Results\n这一发现有待跨地区样本验证。\n"
        sections = sectionize(after)
        findings, _, _ = check_hedging(after, sections)
        fails = [f for f in findings if f.severity == "FAIL"]
        self.assertTrue(any("§结果" in f.message for f in fails))


class TestCombinedIntegration(unittest.TestCase):
    def test_injection_example_meta_excluded(self):
        path = Path(__file__).parent.parent / "examples" / "before-after-zh-academic-injection.md"
        if not path.exists():
            self.skipTest("example file missing")
        pairs = parse_pairs(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(pairs), 3)
        self.assertNotIn("修改对照", pairs[0][1])
        report = audit_pair(pairs[0][0], pairs[0][1], force=True, no_red_line=True)
        l7_warns = [f for f in report.findings if f.rule.startswith("L7.2") and f.severity == "WARN"]
        self.assertEqual(l7_warns, [], msg=str(l7_warns))


if __name__ == "__main__":
    unittest.main()
