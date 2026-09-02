#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync GitHub triage labels from .github/triage-labels.json (requires gh CLI + auth).

Usage:
    python scripts/sync_triage_labels.py
    python scripts/sync_triage_labels.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / ".github" / "triage-labels.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print gh commands only")
    args = ap.parse_args()

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    labels = data.get("labels", [])
    if not labels:
        print("sync_triage_labels: no labels in manifest", file=sys.stderr)
        return 1

    for entry in labels:
        name = entry["name"]
        color = entry.get("color", "ededed").lstrip("#")
        desc = entry.get("description", "")
        cmd = [
            "gh", "label", "create", name,
            "--color", color,
            "--description", desc,
            "--force",
        ]
        if args.dry_run:
            print(" ".join(cmd))
        else:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0 and "already exists" not in (proc.stderr or "").lower():
                print(proc.stderr or proc.stdout, file=sys.stderr)
                return proc.returncode
            print(f"ok: {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
