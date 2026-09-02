#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repo documentation truth tests — run: python scripts/test_repo_consistency.py

Ensures README / AGENTS / LICENSE / examples do not contradict what CI audits.
"""

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestRepoConsistency(unittest.TestCase):
    def test_readme_describes_seven_layers_not_six(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Six layers:", readme)
        self.assertIn("Seven layers", readme)

    def test_readme_skill_line_count_not_stale_230(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotRegex(readme, r"[~≈]?\s*230\s*lines")
        skill_lines = len((REPO_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines())
        # README should cite a line count within ±15 of actual SKILL.md
        m = re.search(r"SKILL\.md.*?(\d{2,3})\s*lines", readme)
        if m:
            claimed = int(m.group(1))
            self.assertGreaterEqual(claimed, skill_lines - 15)
            self.assertLessEqual(claimed, skill_lines + 15)

    def test_english_example_uses_combined_before_after_format(self):
        path = REPO_ROOT / "examples" / "before-after.md"
        text = path.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r"^##\s+Before\b", text, re.MULTILINE))
        self.assertIsNotNone(re.search(r"^##\s+After\b", text, re.MULTILINE))

    def test_run_examples_audits_english_example(self):
        from run_examples import audit_example

        path = REPO_ROOT / "examples" / "before-after.md"
        result = audit_example(path)
        self.assertNotIn("skipped", result.red_lines_summary.lower())
        self.assertEqual(result.red_lines_exit, 0, result.red_lines_summary)

    def test_agents_context_reference_exists(self):
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        if "CONTEXT.md" in agents:
            self.assertTrue(
                (REPO_ROOT / "CONTEXT.md").is_file(),
                "AGENTS.md references CONTEXT.md but file is missing",
            )

    def test_license_fork_copyright(self):
        license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("jefeerzhang", license_text.lower())
        self.assertIn("AIScientists-Dev", license_text)


if __name__ == "__main__":
    unittest.main()
