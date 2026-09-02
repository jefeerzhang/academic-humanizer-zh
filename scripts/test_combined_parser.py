#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for combined_parser.py — run: python scripts/test_combined_parser.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from combined_parser import split_combined_all


SAMPLE = """\
## Before
> before prose one

## After
> after prose one

### 修改对照
| col | val |
|---|---|
| x | y |

## 示例 2

## Before
> before prose two

## After
> after prose two

### C0–C2 红线核对
| item | ok |
|---|---|
| 692 | yes |
"""


class TestCombinedParser(unittest.TestCase):
    def test_meta_h3_stops_after_span(self):
        pairs = split_combined_all(SAMPLE)
        self.assertEqual(len(pairs), 2)
        self.assertIn("after prose one", pairs[0][1])
        self.assertNotIn("修改对照", pairs[0][1])
        self.assertIn("after prose two", pairs[1][1])
        self.assertNotIn("红线核对", pairs[1][1])

    def test_before_body_excludes_heading(self):
        pairs = split_combined_all(SAMPLE)
        self.assertNotIn("## Before", pairs[0][0])
        self.assertIn("before prose one", pairs[0][0])


if __name__ == "__main__":
    unittest.main()
