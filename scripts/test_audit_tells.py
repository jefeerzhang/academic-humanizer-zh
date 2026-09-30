#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for audit_tells.py — run: python scripts/test_audit_tells.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from audit_tells import (
    PATTERNS,
    audit,
    en_dash_hits,
    scan_pattern,
)


def exit_of(text):
    return audit(text)[0]


def rules_of(text):
    return {f.rule for f in audit(text)[1]}


class TestAuditTells(unittest.TestCase):
    def test_clean_text_passes(self):
        text = (
            "The decoder consumes the feature-alignment stage's output, and the "
            "contrastive loss trains both. We evaluate on ImageNet and CIFAR-100 (Table 3)."
        )
        self.assertEqual(exit_of(text), 0)

    # ----- Strict rules (exit 2) -----

    def test_placeholder_bracket_fails(self):
        self.assertEqual(exit_of("We evaluate on [INSERT_DATASET_NAMES]."), 2)

    def test_placeholder_citation_needed_fails(self):
        self.assertEqual(exit_of("See [citation needed]."), 2)

    def test_placeholder_xx_date_fails(self):
        self.assertEqual(exit_of("Date: 2025-XX-XX"), 2)

    def test_em_dash_fails(self):
        self.assertEqual(exit_of("The method \u2014 though simple \u2014 works."), 2)

    def test_en_dash_range_is_fine(self):
        text = "Accuracy improves by 2\u20136% across the board (2020\u20132025)."
        self.assertEqual(exit_of(text), 0)
        self.assertEqual(en_dash_hits(text), [])

    def test_non_range_en_dash_fails(self):
        self.assertEqual(exit_of("The before\u2013after gap was large."), 2)

    def test_chinese_dash_passes(self):
        # Chinese 破折号 —— is standard punctuation, not an AI-tell dash.
        self.assertEqual(exit_of("样本限制使结论需谨慎对待\u2014\u2014这一发现有待验证。"), 0)

    def test_chinese_dash_with_bold_markers_passes(self):
        # Bold markers (**) around a 破折号 must not break CJK-context detection.
        self.assertEqual(
            exit_of("**需谨慎对待**\u2014\u2014**这一发现**有待验证。"),
            0,
        )

    # ----- Weak rules (exit 1) -----

    def test_single_weak_tell_warns(self):
        self.assertEqual(exit_of("The framework is pivotal for the field."), 1)

    def test_multiple_weak_tells_note_cooccurrence(self):
        text = (
            "Pivotal results pave the way for the field. Experts argue the "
            "framework is a testament to future work."
        )
        code, findings = audit(text)
        self.assertEqual(code, 1)
        self.assertIn("co-occurrence", rules_of(text))

    def test_associated_with_is_weak_not_fail(self):
        # "associated with" is legit calibrated language in empirical prose.
        text = "The outcome is associated with household income in the full sample."
        code, findings = audit(text)
        self.assertEqual(code, 1)
        self.assertFalse(any(f.severity == "fail" for f in findings))

    def test_one_line_closer_warns(self):
        text = "Accuracy rises by 4 points. This shows the importance of metadata."
        self.assertEqual(exit_of(text), 1)
        self.assertTrue(any("1.19" in f.rule for f in audit(text)[1]))

    # ----- Matching mechanics -----

    def test_word_boundary_matches_stems(self):
        text = "The method showcases and underscores robustness, delving into details."
        hits = scan_pattern(next(p for p in PATTERNS if p.pid == "1.5"), text)
        self.assertIn("showcase", hits)
        self.assertIn("underscore", hits)
        # "delving" needs its explicit variant term (delve drops the e).
        self.assertIn("delving", hits)

    def test_placeholder_inline_citation_not_flagged(self):
        # [N]-style inline citations are sacred, not placeholders.
        self.assertEqual(exit_of("Prior work covers this [3, 7]."), 0)


if __name__ == "__main__":
    unittest.main()
