#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for audit_tells.py — run: python scripts/test_audit_tells.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from audit_tells import (
    PATTERNS,
    ZH_PATTERNS,
    audit,
    en_dash_hits,
    scan_pattern,
    scan_zh_pattern,
    sentence_rhythm_stats,
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

    # ----- Chinese C7 rules (rules-zh.md §1 A-F) + §10 whitelist guards -----

    def test_zh_c7_a_formulaic_opener_and_closer_warn(self):
        text = "近年来，随着外卖规模的迅速发展，本研究为低碳消费开辟了新的路径。"
        code, findings = audit(text)
        self.assertEqual(code, 1)
        rules = {f.rule for f in findings}
        self.assertTrue(any(r.startswith("C7.A") for r in rules))

    def test_zh_c7_b_value_saturation_warns(self):
        text = "本研究对推动低碳消费具有重要意义，发挥了关键作用。"
        self.assertEqual(exit_of(text), 1)
        self.assertTrue(any(r.startswith("C7.B") for r in rules_of(text)))

    def test_zh_c7_c_abstract_subject_warns(self):
        text = "随着时代的发展，消费观念正在发生深刻变化。"
        self.assertEqual(exit_of(text), 1)
        self.assertTrue(any(r.startswith("C7.C") for r in rules_of(text)))

    def test_zh_c7_d_nominalized_verb_warns_but_methods_whitelisted(self):
        bad = "政策制定者应对补贴机制进行优化，并采取措施加以改进。"
        self.assertEqual(exit_of(bad), 1)
        self.assertTrue(any(r.startswith("C7.D") for r in rules_of(bad)))

        # Methodology and §10-A whitelist phrasing must NOT be flagged.
        good = "为确保研究结论的可靠性，本文进行了以下稳健性测试，并对样本进行回归检验。"
        self.assertEqual(exit_of(good), 0)

    def test_zh_c7_e_parallel_triad_and_transition_stack(self):
        triad = "这一机制既是理论创新，也是实践突破，更是方法示范。"
        self.assertTrue(any(r.startswith("C7.E") for r in rules_of(triad)))

        stacked = "首先，样本偏好低碳标签；其次，受访者重视包装；同时，收入差异不显著。"
        self.assertTrue(any(r.startswith("C7.E") for r in rules_of(stacked)))

        # Clean 首先 / 其次 / 最后 without mixed 同时/此外/再者 is whitelisted.
        legit = "首先，本文使用面板数据检验主效应；其次，通过工具变量处理内生性；最后，检验异质性。"
        self.assertEqual(exit_of(legit), 0)

    def test_zh_c7_f_meta_commentary_and_vague_consensus_warn(self):
        text = "诸多研究表明该现象普遍存在，本研究旨在探讨其内在机制。"
        self.assertEqual(exit_of(text), 1)
        self.assertTrue(any(r.startswith("C7.F") for r in rules_of(text)))

    def test_zh_section10_whitelist_phrases_not_flagged(self):
        text = (
            "鉴于此，本文延续学术界关于耐心资本的经典研究，以核心解释变量检验创新效应。"
            "总而言之，需要注意的是，上述结论在稳健性测试后依然成立。"
        )
        self.assertEqual(exit_of(text), 0)

    def test_zh_cooccurrence_across_c7_patterns(self):
        text = (
            "近年来，随着数字经济的迅速发展，诸多研究表明转型具有重要意义。"
            "本研究旨在探讨其机制，并采取措施进行优化，为行业发展贡献了力量。"
        )
        code, findings = audit(text)
        self.assertEqual(code, 1)
        self.assertIn("co-occurrence", {f.rule for f in findings})

    # ----- L2 sentence-length rhythm uniformity -----

    def test_zh_flat_sentence_rhythm_warns(self):
        # 6 consecutive sentences all around 24-26 CJK chars -> very low CV
        text = (
            "本研究考察数字普惠金融对中小微企业融资约束的直接影响效应。"
            "实证样本选取沪深两市主板上市公司连续十年的财务年报数据。"
            "基准回归控制了企业个体固定效应以及年份时间固定效应指标。"
            "工具变量检验采用地区历史邮电业务总量作为外生冲击代理变量。"
            "异质性分析发现政策红利在民营制造企业样本中表现更为明显。"
            "机制检验显示信息不对称程度的缓解构成了最主要的作用渠道。"
        )
        stats = sentence_rhythm_stats(text)
        self.assertEqual(stats["sentence_count"], 6)
        self.assertLess(stats["cv"], 0.18)
        self.assertTrue(stats["flag"])
        self.assertEqual(exit_of(text), 1)
        self.assertIn("L2.rhythm sentence uniformity", rules_of(text))

    def test_zh_varied_sentence_rhythm_passes(self):
        text = (
            "样本来自 2015–2023 年沪深 A 股非金融上市公司，剔除 ST 样本后剩余 18420 条观测。"
            "结果很直接。"
            "核心解释变量系数在 1% 水平上显著为负，表明融资约束下降约 12.4%。"
            "工具变量通过弱识别检验。"
            "进一步分组显示，这一效应集中在非国有企业与低抵押品行业，而在国有企业中不显著。"
        )
        stats = sentence_rhythm_stats(text)
        self.assertGreaterEqual(stats["cv"], 0.18)
        self.assertFalse(stats["flag"])
        self.assertEqual(exit_of(text), 0)


if __name__ == "__main__":
    unittest.main()
