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

    def test_agents_domain_paths_exist(self):
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        if "docs/adr/" in agents or "docs/adr" in agents:
            adr = REPO_ROOT / "docs" / "adr"
            self.assertTrue(adr.is_dir(), "docs/adr/ missing")

    def test_triage_labels_manifest_matches_docs(self):
        manifest = REPO_ROOT / ".github" / "triage-labels.json"
        self.assertTrue(manifest.is_file(), ".github/triage-labels.json missing")
        import json
        data = json.loads(manifest.read_text(encoding="utf-8"))
        names = {entry["name"] for entry in data["labels"]}
        expected = {
            "needs-triage", "needs-info", "ready-for-agent",
            "ready-for-human", "wontfix",
        }
        self.assertEqual(names, expected)

    def test_license_fork_copyright(self):
        license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("jefeerzhang", license_text.lower())
        self.assertIn("AIScientists-Dev", license_text)

    def test_context_defines_layer7_loaded_vs_injection(self):
        ctx = (REPO_ROOT / "CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Layer 7 loaded", ctx)
        self.assertIn("Layer 7 injection", ctx)

    def test_skill_process_defaults_to_non_injection_example(self):
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        # Default calibration example is C7 academic, not injection.
        self.assertRegex(
            skill,
            r"Before rewriting,\s+read `examples/before-after-zh-academic\.md`",
        )
        # Injection example only when Layer 7 is loaded/active.
        self.assertRegex(
            skill,
            r"(?:[Ww]hen|[Ii]f) Layer 7\s+(?:is\s+)?(?:loaded|active)"
            r".*before-after-zh-academic-injection\.md",
            re.DOTALL,
        )
        # Exit 2 is Layer 7 FAIL, not "red-line only".
        self.assertNotRegex(skill, r"2 red-line violation")
        self.assertRegex(skill, r"2\s*=?\s*(?:FAIL|fail|失败)")

    def test_rules_zh_section9_does_not_claim_deleted_decision_tree(self):
        rules = (REPO_ROOT / "references" / "rules-zh.md").read_text(encoding="utf-8")
        sec9 = rules.split("## §9.")[1] if "## §9." in rules else ""
        self.assertNotIn("决策树", sec9)
        self.assertIn("SKILL.md", sec9)
        self.assertIn("layer-7-academic-injection.md", sec9)

    def test_injection_landing_zones_aligned(self):
        """Process / When to use / README / §7.7 share the same allowed set."""
        allowed = "Discussion / Conclusion / Limitations / 政策含义"
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        layer7 = (REPO_ROOT / "references" / "layers" / "layer-7-academic-injection.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(allowed, skill)
        self.assertIn(allowed, readme)
        self.assertIn("政策含义", layer7)
        # Checklist must mention 政策含义 as allowed landing, not only D/C/L.
        self.assertRegex(layer7, r"Discussion\s*/\s*Conclusion\s*/\s*Limitations\s*/\s*政策含义")

    def test_readme_badge_targets_exist(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for m in re.finditer(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)", readme):
            target = m.group(1)
            if target.startswith("http"):
                continue
            path = REPO_ROOT / target
            self.assertTrue(path.is_file(), f"README links to missing {target}")

    def test_changelog_exists(self):
        self.assertTrue((REPO_ROOT / "CHANGELOG.md").is_file())


if __name__ == "__main__":
    unittest.main()
