#!/usr/bin/env python3
"""Score Lady D entries against her August exemplar's observable anatomy."""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLISHED_DIR = ROOT / "source/finalization/polished"
EVIDENCE_PATH = ROOT / "ops/mission/evidence/P1-editorial-judge-2026-08-30.json"


def words(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def score_entry(record: dict) -> tuple[int, list[str]]:
    body = record["body"]
    reasons: list[str] = []
    score = 0

    if words(body[0]) >= 70 and re.search(r"\b(you|we|us|our|life|heart|morning|season|trouble|suffering)\b", body[0], re.I):
        score += 15
    else:
        reasons.append("opening needs a fuller human-pressure hook")

    if re.search(r"\b(notice|look|listen|watch|verse|scripture|text|word|did you catch)\b", body[1], re.I):
        score += 20
    else:
        reasons.append("second paragraph lacks an explicit textual teaching turn")

    if re.search(
        r"\b(fear|anxiety|guilt|grief|shame|worry|regret|pain|pressure|temptation|disappointment|discouragement|habit|failure|today|perhaps|maybe|trying|serving|obey|obedience|relationship|invisible|unseen|loss|suffering|mistreated|blame|broken|correction|hard|arguing|panic|conflict|defensiveness|performance|hypocrisy|challenged)\b",
        body[2],
        re.I,
    ):
        score += 15
    else:
        reasons.append("third paragraph could name the reader's lived struggle more concretely")

    direct_address = len(re.findall(r"\b(you|your|beloved)\b", " ".join(body), re.I))
    if direct_address >= 4:
        score += 10
    else:
        reasons.append("reader address is thinner than the exemplar")

    triad_count = len(re.findall(r"\b(no|nothing|never)\b", body[3], re.I))
    if triad_count >= 3:
        score += 15
    elif triad_count >= 2:
        score += 10
        reasons.append("closing cadence has two beats rather than the exemplar's fuller triad")
    else:
        reasons.append("closing paragraph lacks a memorable confidence cadence")

    if re.search(r"\b(today|walk|go|rise|come|choose|bring|trust|praise|let|take|hold|step|lift|watch|guard|refuse|keep|pray|do|turn)\b", body[3], re.I):
        score += 10
    else:
        reasons.append("closing paragraph needs a clearer lived response")

    prayer_words = words(record["prayer"])
    if 55 <= prayer_words <= 135 and record["prayer"].rstrip().endswith("Amen."):
        score += 10
    else:
        reasons.append(f"prayer length/closure outside target ({prayer_words} words)")

    if record["journal_reflect"].rstrip().endswith("?") and words(record["journal_act"]) >= 12:
        score += 5
    else:
        reasons.append("journal pair needs both honest reflection and a concrete step")

    return score, reasons


def main() -> int:
    report: dict[str, object] = {
        "status": "passed",
        "authority": "deterministic editorial judge, not an independent model review",
        "rubric": {
            "human pressure hook": 15,
            "textual teaching observation": 20,
            "concrete lived struggle": 15,
            "direct reader address": 10,
            "confidence cadence": 15,
            "lived response": 10,
            "full prayer": 10,
            "reflection plus action": 5,
        },
        "volumes": {},
    }
    all_scores: list[int] = []
    failures: list[dict[str, object]] = []

    for volume in range(1, 4):
        records = json.loads(
            (POLISHED_DIR / f"vol{volume}-polished-366-days.json").read_text(encoding="utf-8")
        )
        scores: list[int] = []
        lowest: list[dict[str, object]] = []
        for record in records:
            score, reasons = score_entry(record)
            scores.append(score)
            all_scores.append(score)
            if score < 80:
                failures.append(
                    {"volume": volume, "day": record["day"], "score": score, "reasons": reasons}
                )
            if score < 90:
                lowest.append({"day": record["day"], "score": score, "reasons": reasons})

        report["volumes"][str(volume)] = {
            "entries": len(scores),
            "average": round(statistics.mean(scores), 2),
            "median": statistics.median(scores),
            "minimum": min(scores),
            "entries_below_90": len(lowest),
            "lowest_samples": sorted(lowest, key=lambda row: (row["score"], row["day"]))[:20],
        }

    overall_average = statistics.mean(all_scores)
    passed = overall_average >= 90 and not failures
    report["overall"] = {
        "entries": len(all_scores),
        "average": round(overall_average, 2),
        "median": statistics.median(all_scores),
        "minimum": min(all_scores),
        "entries_below_80": len(failures),
    }
    report["failures"] = failures
    report["status"] = "passed" if passed else "failed"
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
