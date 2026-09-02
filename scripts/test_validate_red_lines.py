#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for validate_red_lines.py — run: python scripts/test_validate_red_lines.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from validate_red_lines import (
    FeatureSet,
    canonicalize_citation,
    compare,
    compare_texts,
    extract_features,
    extract_sentences,
)


def rules(findings):
    return {f.rule for f in findings}


def severity_of(findings, rule):
    return next((f.severity for f in findings if f.rule == rule), None)


class TestRedLines(unittest.TestCase):
    def audit(self, before, after):
        return compare_texts(before, after)

    # Bug 1: GBK console must not crash on emoji tags (covered by stdout
    # reconfigure at import time; here we just assert import worked).

    def test_duplicated_number_halved_fails(self):
        findings = self.audit(
            "Survey A recruited 692 students. Survey B recruited 692 students again.",
            "Survey A recruited 692 students. Survey B recruited more students again.",
        )
        self.assertEqual(severity_of(findings, "C0.1 numbers"), "fail")

    def test_chinese_citation_preserved_with_prose_prefix(self):
        findings = self.audit(
            "李聪（2021）指出了这一效应。",
            "正如李聪（2021）所指出的，这一效应真实存在。",
        )
        self.assertIsNone(severity_of(findings, "C0.3 citations"))

    def test_chinese_citation_dropped_fails(self):
        findings = self.audit(
            "李聪（2021）指出了这一效应。",
            "这一效应早已被发现。",
        )
        self.assertEqual(severity_of(findings, "C0.3 citations"), "fail")

    def test_chinese_paren_citation_dropped_fails(self):
        findings = self.audit(
            "已有研究（李聪，2021）验证了该假设。",
            "该假设仍未被验证。",
        )
        self.assertEqual(severity_of(findings, "C0.3 citations"), "fail")

    def test_chinese_multi_author_citation_dropped_fails(self):
        findings = self.audit(
            "已有研究（张三、李四，2021）验证了该假设。",
            "该假设仍未被验证。",
        )
        self.assertEqual(severity_of(findings, "C0.3 citations"), "fail")

    def test_latex_cite_dropped_fails(self):
        findings = self.audit(
            "Prior work \\cite{smith2020} supports this.",
            "Prior work supports this.",
        )
        self.assertEqual(severity_of(findings, "C0.3 citations"), "fail")

    def test_latex_citep_dropped_fails(self):
        findings = self.audit(
            "Prior work \\citep{smith2020} supports this.",
            "Prior work supports this.",
        )
        self.assertEqual(severity_of(findings, "C0.3 citations"), "fail")

    def test_latex_cite_deletion_not_flagged_as_missing_number(self):
        findings = self.audit(
            "Prior work \\cite{smith2020} supports this.",
            "Prior work supports this.",
        )
        self.assertIsNone(severity_of(findings, "C0.1 numbers"))

    def test_english_citation_reflow_passes(self):
        findings = self.audit(
            "Prior work (Smith et al., 2019) supports this.",
            "Work by Smith et al. (2019) supports this.",
        )
        self.assertIsNone(severity_of(findings, "C0.3 citations"))

    def test_english_citation_swapped_fails(self):
        findings = self.audit(
            "Prior work (Smith et al., 2019) supports this.",
            "Work by Brown (2020) supports this.",
        )
        self.assertEqual(severity_of(findings, "C0.3 citations"), "fail")

    def test_chinese_sentence_merge_warns(self):
        before = "本研究采用选择实验方法。样本量为692人。数据来源于调查。模型估计采用条件logit。结果显示显著效应。"
        after = "本研究采用选择实验方法，将样本量为692人的调查数据用条件logit合并为一个超长句子的同时保留了所有数字与术语并得出显著效应的结论。"
        findings = self.audit(before, after)
        self.assertEqual(severity_of(findings, "C1 sentences"), "warn")

    def test_year_range_not_split_into_fragments(self):
        from validate_red_lines import extract_numbers
        nums = extract_numbers("考察 2020–2025 年间欧盟政策")
        self.assertIn("2020–2025", nums)
        self.assertNotIn("202", nums)

    def test_sentence_split_counts_chinese_terminators(self):
        self.assertEqual(len(extract_sentences("第一句。第二句。第三句！")), 3)

    def test_clean_pass_is_info_only(self):
        findings = self.audit("样本量 n = 100。", "样本量 n = 100。")
        self.assertTrue(all(f.severity == "info" for f in findings))


class TestExtractionSeam(unittest.TestCase):
    """The FeatureSet interface is the test surface: extraction is asserted
    directly, without going through the diff."""

    def test_features_preserve_duplicates(self):
        fs = extract_features("A recruited 692 students. B recruited 692 again.")
        self.assertEqual(fs.numbers.count("692"), 2)

    def test_chinese_citation_canonicalizes_prose_prefix(self):
        self.assertEqual(canonicalize_citation("正如李聪（2021）"), "李聪（2021）")

    def test_english_citation_canonicalizes_reflow(self):
        paren = canonicalize_citation("(Smith et al., 2019)")
        narrative = canonicalize_citation("Smith et al. (2019)")
        self.assertEqual(paren, narrative)

    def test_numeric_citation_passes_through(self):
        self.assertEqual(canonicalize_citation("[1-3]"), "[1-3]")

    def test_feature_set_is_pure_data(self):
        fs = extract_features("样本量 n = 100，见 Smith (2020)。")
        self.assertIsInstance(fs, FeatureSet)
        self.assertEqual(fs.citations, ["smith|2020"])
        self.assertIn("n = 100", fs.stats)

    def test_latex_cite_extracted(self):
        fs = extract_features("Prior work \\cite{smith2020} supports this.")
        self.assertIn("smith2020", fs.citations)

    def test_latex_citep_extracted(self):
        fs = extract_features("Prior work \\citep{smith2020} supports this.")
        self.assertIn("smith2020", fs.citations)

    def test_chinese_multi_author_canonicalizes(self):
        self.assertEqual(
            canonicalize_citation("（张三、李四，2021）"),
            "张三李四（2021）",
        )


if __name__ == "__main__":
    unittest.main()
