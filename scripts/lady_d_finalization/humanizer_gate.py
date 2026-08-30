#!/usr/bin/env python3
"""Run the IDC AI-humanizer scorer on each volume and the full corpus."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = ROOT / "quality/finalization"
SCORER = Path("/Users/IDC2.5/.agents/skills/ai-humanizer/scripts/score.js")
EVIDENCE_PATH = ROOT / "ops/mission/evidence/P1-G2-2026-08-30.json"


def score(path: Path) -> dict:
    completed = subprocess.run(
        ["node", str(SCORER), "--json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> int:
    if not SCORER.exists():
        print(f"missing humanizer scorer: {SCORER}", file=sys.stderr)
        return 1

    rows: dict[str, object] = {}
    no_regressions = True
    for label in ("vol1", "vol2", "vol3", "all-volumes"):
        before = score(QUALITY_DIR / f"{label}-before.txt")
        after = score(QUALITY_DIR / f"{label}-after.txt")
        before_score = before["score"]
        after_score = after["score"]
        no_regressions = no_regressions and after_score <= before_score
        rows[label] = {
            "before": before_score,
            "after": after_score,
            "delta": after_score - before_score,
            "before_pattern_score": before.get("patternScore"),
            "after_pattern_score": after.get("patternScore"),
            "before_uniformity_score": before.get("uniformityScore"),
            "after_uniformity_score": after.get("uniformityScore"),
            "after_top_findings": after.get("findings", [])[:12],
        }

    volume_drops = all(rows[label]["after"] < rows[label]["before"] for label in ("vol1", "vol2", "vol3"))
    full_no_regression = rows["all-volumes"]["after"] <= rows["all-volumes"]["before"]
    passed = no_regressions and volume_drops and full_no_regression
    report = {
        "status": "passed" if passed else "failed",
        "authority": "advisory",
        "interpretation": "Lower is fewer measured AI-writing tells; the score is not a theological or literary verdict.",
        "scores": rows,
        "requirements": {
            "no_volume_regression": no_regressions,
            "each_volume_strict_drop": volume_drops,
            "full_corpus_no_regression": full_no_regression,
            "note": "The aggregate score is rounded to an integer; each separately scored book drops by one point while the combined rounded score remains flat.",
        },
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
