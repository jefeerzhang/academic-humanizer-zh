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
    check_blacklist,
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

    def test_compound_header_splits_results_and_discussion(self):
        text = (
            "## 结果与讨论\n"
            "回归结果显示显著正向偏好。\n\n"
            "### 讨论\n"
            "笔者认为这一差异源于认知差异。目前尚不清楚机制是否普适。\n"
        )
        sections = sectionize(text)
        names = [s[0] for s in sections]
        self.assertIn("结果", names)
        self.assertIn("讨论", names)
        report = audit_pair("", text, force=True, no_red_line=True)
        fails = [f for f in report.findings if f.severity == "FAIL"]
        self.assertEqual(fails, [], msg=str(fails))

    def test_compound_header_results_part_still_forbidden(self):
        text = "## 结果与讨论\n这一发现有待跨地区样本验证。\n"
        sections = sectionize(text)
        self.assertEqual(sections[0][0], "结果")
        findings, _, _ = check_hedging(text, sections)
        fails = [f for f in findings if f.severity == "FAIL"]
        self.assertTrue(any("§结果" in f.message for f in fails))

    def test_compound_header_english_discussion_split(self):
        text = (
            "## Results and Discussion\n"
            "Accuracy improved on all benchmarks.\n\n"
            "Discussion: We attribute the gain to better calibration.\n"
            "目前尚不清楚 whether this holds on OOD data.\n"
        )
        sections = sectionize(text)
        names = [s[0] for s in sections]
        self.assertIn("结果", names)
        self.assertIn("讨论", names)
        findings, _, _ = check_hedging(text, sections)
        fails = [f for f in findings if f.severity == "FAIL" and "§结果" in f.message]
        self.assertEqual(fails, [])

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


class TestBlacklist(unittest.TestCase):
    """L7.3 blacklist: CJK has no word boundary, so \b before 挺 is unreliable."""

    def _fails(self, text: str) -> list:
        return [f for f in check_blacklist(text) if f.severity == "FAIL"]

    def test_ting_after_cjk_still_matched(self):
        # 挺好 preceded by a CJK char must still be caught (no \b boundary in CJK).
        self.assertEqual(len(self._fails("这挺好")), 1, msg="这挺好 not flagged")
        self.assertEqual(len(self._fails("效果挺好")), 1)
        self.assertEqual(len(self._fails("都挺好")), 1)

    def test_ting_common_forms(self):
        for s in ["挺好", "挺多", "挺不错", "挺不好"]:
            self.assertEqual(len(self._fails(s)), 1, msg=s)

    def test_man_common_forms_full_token(self):
        # 蛮不错 must match as the full token, not a fragment "蛮不".
        for s in ["蛮好", "蛮不错", "这蛮不错", "蛮不好"]:
            fails = self._fails(s)
            self.assertEqual(len(fails), 1, msg=s)
            self.assertTrue(
                any(fails[0].evidence.startswith(p) for p in ("蛮好", "蛮不错", "蛮不好")),
                msg=fails[0].evidence,
            )

    def test_man_bi_jiang_li_not_false_positive(self):
        # 蛮不讲理 uses 蛮=willful (蛮横), not the casual intensifier => NOT a trap.
        self.assertEqual(self._fails("蛮不讲理"), [])

    def test_ting_shen_er_chu_not_false_positive(self):
        self.assertEqual(self._fails("挺身而出"), [])

    def test_non_colloquial_not_flagged(self):
        for s in ["还不错", "很好", "相当好"]:
            self.assertEqual(self._fails(s), [], msg=s)

    def test_intro_hedge_fails(self):
        after = "## 引言\n目前尚不清楚这段是否该注入。\n"
        findings, _, _ = check_hedging(after, sectionize(after))
        fails = [f for f in findings if f.severity == "FAIL"]
        self.assertTrue(any("§引言" in f.message for f in fails))


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
