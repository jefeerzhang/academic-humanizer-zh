#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared parser for combined markdown files with ## Before / ## After pairs.

Strips frontmatter and meta sections (修改对照 / 合规清单 / C0–C2 核对 / Layer 7 密度核对)
from the audited After span so validators compare editable prose only.
"""

from __future__ import annotations

import re

BEFORE_HEADING_RE = re.compile(r"^##\s+Before\b", re.MULTILINE)
AFTER_HEADING_RE = re.compile(r"^##\s+After\b", re.MULTILINE)

# Headings that mark the end of editable After prose (h2 section breaks or h3+ meta blocks).
META_HEADING_RE = re.compile(
    r"^#{2,6}\s*(?:"
    r"修改对照|合规清单|红线核对|注入密度核对|综合验证|场景假设|"
    r"C0[\s–—-]*C2|Layer\s*7|Example notes|Change notes"
    r")",
    re.MULTILINE | re.IGNORECASE,
)

NEXT_H2_RE = re.compile(r"^##\s", re.MULTILINE)


def _find_after_end(text: str, after_heading_end: int) -> int:
    """Return index in *text* where the After body ends (exclusive)."""
    tail = text[after_heading_end:]
    candidates: list[int] = []

    m_h2 = NEXT_H2_RE.search(tail)
    if m_h2:
        candidates.append(after_heading_end + m_h2.start())

    m_meta = META_HEADING_RE.search(tail)
    if m_meta:
        candidates.append(after_heading_end + m_meta.start())

    if not candidates:
        return len(text)
    return min(candidates)


def split_combined_all(text: str) -> list[tuple[str, str]]:
    """Return ALL (before, after) pairs from a combined markdown file."""
    if "<<<AFTER>>>" in text:
        before, after = text.split("<<<AFTER>>>", 1)
        return [(before.strip(), after.strip())]

    pairs: list[tuple[str, str]] = []
    before_matches = list(BEFORE_HEADING_RE.finditer(text))
    after_matches = list(AFTER_HEADING_RE.finditer(text))

    for bm in before_matches:
        am = next((m for m in after_matches if m.start() > bm.start()), None)
        if am is None:
            continue

        before_body = text[bm.start(): am.start()]
        before_body = re.sub(
            r"^##\s+Before.*$", "", before_body, count=1, flags=re.MULTILINE
        ).strip()

        after_end = _find_after_end(text, am.end())
        after_body = text[am.start(): after_end]
        after_body = re.sub(
            r"^##\s+After.*$", "", after_body, count=1, flags=re.MULTILINE
        ).strip()

        pairs.append((before_body, after_body))
    return pairs


def split_combined(text: str) -> tuple[str, str]:
    """Return the first (before, after) pair; raises ValueError if none found."""
    pairs = list(split_combined_all(text))
    if not pairs:
        raise ValueError(
            "Could not find both '## Before' and '## After' headings. "
            "Use --before/--after, or separate stdin with a line "
            "containing '<<<AFTER>>>'."
        )
    return pairs[0]
