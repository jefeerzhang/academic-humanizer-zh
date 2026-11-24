#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for compare_author_style.py — run: python scripts/test_compare_author_style.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from compare_author_style import compare_texts, extract_style_profile


AUTHOR_SAMPLE_ZH = (
    "本文基于 2012–2023 年沪深 A 股上市公司面板数据，考察机构投资者持股期限对企业颠覆性创新的影响。"
    "结果很清楚。"
    "与短期交易型机构相比，长期稳定持股的机构投资者能够缓解管理层短视压力，进而提升发明专利的前向引用率。"
    "当然，这一效应并不完全由持股比例决定，还受到行业研发周期的约束。"
    "在稳健性检验中，本文替换核心解释变量度量方式，并引入工具变量处理潜在内生性，核心结论依然成立。"
    "可见，资本的长期属性对高风险创新活动具有直接支撑作用。"
)


class TestCompareAuthorStyle(unittest.TestCase):
    def test_aligned_zh_rewrite_passes(self):
        after = (
            "本文利用 2015–2023 年制造业企业数据，检验绿色信贷政策对污染排放强度的影响。"
            "基准结果稳健。"
            "相较于非重污染行业，重污染企业在新政实施后明显压缩了高耗能资本开支，进而降低了单位产值排放。"
            "当然，这一变化并不完全源于信贷额度收紧，也与地方环保执法强化有关。"
            "替换被解释变量并引入双重差分稳健性检验后，本文的核心发现保持不变。"
            "可见，信贷定价约束对企业减排行为产生了实际作用。"
        )
        code, sp, ap, findings = compare_texts(AUTHOR_SAMPLE_ZH, after)
        self.assertEqual(sp.language, "zh")
        self.assertEqual(ap.language, "zh")
        self.assertEqual(code, 0, msg=str(findings))

    def test_foreign_first_person_bi_zhe_triggers_warn(self):
        # Sample uses 本文 only; introducing 笔者认为 (old Layer 7 template) must warn.
        after = (
            "本文利用 2015–2023 年制造业企业数据，检验绿色信贷政策对污染排放强度的影响。"
            "基准结果稳健。"
            "笔者认为，这一差异主要源于企业对碳定价预期的调整，而非短期融资成本上升。"
            "当然，这一变化并不完全源于信贷额度收紧。"
            "可见，信贷定价约束对企业减排行为产生了实际作用。"
        )
        code, _, _, findings = compare_texts(AUTHOR_SAMPLE_ZH, after)
        self.assertEqual(code, 1)
        rules = {f.rule for f in findings}
        self.assertIn("S5.3 self-reference drift", rules)

    def test_rhythm_flattening_triggers_warn(self):
        # All sentences forced into uniform ~25-char blocks -> flattens author CV.
        after = (
            "本文基于沪深主板上市公司连续十年的财务年报数据展开检验。"
            "基准回归控制了企业个体固定效应以及年份时间固定效应指标。"
            "工具变量检验采用地区历史邮电业务总量作为外生冲击代理变量。"
            "异质性分析发现政策红利在民营制造企业样本中表现更为明显。"
            "机制检验显示信息不对称程度的缓解构成了最主要的作用渠道。"
            "稳健性测试通过替换核心变量与剔除特殊年份后结果依然成立。"
        )
        code, _, _, findings = compare_texts(AUTHOR_SAMPLE_ZH, after)
        self.assertEqual(code, 1)
        rules = {f.rule for f in findings}
        self.assertIn("S5.2 rhythm flattening", rules)

    def test_foreign_connectives_trigger_warn(self):
        after = (
            "本文检验绿色信贷政策对污染排放强度的影响。"
            "结果稳健。"
            "然而，重污染企业的资本开支在短期内并未立刻收缩。"
            "此外，地方财政补贴在部分省份抵消了利率上浮压力。"
            "因此，减排效应在第二年才开始显现。"
            "然而，高杠杆企业的调整幅度仍大于低杠杆企业。"
            "此外，国有企业的信贷替代渠道更多。"
        )
        code, _, _, findings = compare_texts(AUTHOR_SAMPLE_ZH, after)
        self.assertEqual(code, 1)
        rules = {f.rule for f in findings}
        self.assertIn("S5.4 connective drift", rules)

    def test_english_profile_and_alignment(self):
        sample_en = (
            "We evaluate online calibration under delayed feedback on three clinical benchmarks. "
            "The baseline fails early. "
            "Because labels arrive hours after prediction, standard temperature scaling drifts "
            "whenever patient mix shifts across shifts or hospitals. "
            "Although reweighting reduces variance, it may not recover calibration under abrupt drift. "
            "We therefore update the scaling parameter with an importance-weighted window."
        )
        after_en = (
            "We test online calibration under delayed labels across three ICU cohorts. "
            "Static baselines degrade quickly. "
            "When outcome labels lag behind bedside alerts, fixed temperature scaling loses "
            "reliability during seasonal shifts in admission severity. "
            "Although sliding-window updates reduce error, they may still lag during sudden surges. "
            "We therefore weight recent observations by inverse arrival delay."
        )
        sp = extract_style_profile(sample_en)
        self.assertEqual(sp.language, "en")
        self.assertEqual(sp.dominant_self_ref, "we")
        code, _, _, findings = compare_texts(sample_en, after_en)
        self.assertEqual(code, 0, msg=str(findings))


if __name__ == "__main__":
    unittest.main()
