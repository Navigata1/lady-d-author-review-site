#!/usr/bin/env python3
"""Audit polished Lady D voice files against source invariants and style gates."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "source/finalization/voice"
POLISHED_DIR = ROOT / "source/finalization/polished"
EVIDENCE_PATH = ROOT / "ops/mission/evidence/P1-G1-2026-08-30.json"

MECHANICAL_PATTERNS = {
    "surrender_to_his_love_means": r"Surrender to His love means",
    "as_you_surrender_to_his_love": r"As you surrender to His love",
    "when_pronoun_surrenders_to_his_love": r"When (?:we|you|I) surrender to His love",
    "surrender_to_his_love_by": r"Surrender to His love by",
    "residual_surrender_to_his_love": r"surrender to His love",
    "our_part_is_to_surrender": r"Our part is to surrender",
}


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def all_text(records: list[dict]) -> str:
    values: list[str] = []
    for record in records:
        values.extend(record["body"])
        values.extend(
            [
                record["closing"],
                record["prayer"],
                record["journal_reflect"],
                record["journal_act"],
            ]
        )
    return "\n".join(values)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    volumes: dict[str, object] = {}
    corpus_before = ""
    corpus_after = ""

    for volume in range(1, 4):
        source_path = SOURCE_DIR / f"vol{volume}-voice-366-days.json"
        polished_path = POLISHED_DIR / f"vol{volume}-polished-366-days.json"
        if not polished_path.exists():
            errors.append(f"missing polished corpus: {polished_path.relative_to(ROOT)}")
            continue

        source = json.loads(source_path.read_text(encoding="utf-8"))
        polished = json.loads(polished_path.read_text(encoding="utf-8"))
        if len(source) != 366 or len(polished) != 366:
            errors.append(f"Volume {volume}: source and polished files must each have 366 records")
            continue

        source_by_day = {record["day"]: record for record in source}
        polished_by_day = {record["day"]: record for record in polished}
        if set(source_by_day) != set(polished_by_day):
            errors.append(f"Volume {volume}: day keys changed")

        changed_entries = 0
        length_ratios: list[float] = []
        for day in sorted(source_by_day):
            before = source_by_day[day]
            after = polished_by_day[day]
            if before["title"] != after["title"]:
                errors.append(f"Volume {volume} day {day}: title changed")
            if len(after.get("body", [])) != 4 or not all(after["body"]):
                errors.append(f"Volume {volume} day {day}: body structure changed")
            if not after.get("prayer", "").rstrip().endswith("Amen."):
                errors.append(f"Volume {volume} day {day}: prayer no longer closes with Amen.")
            if before != after:
                changed_entries += 1

            before_length = sum(len(item) for item in before["body"])
            after_length = sum(len(item) for item in after["body"])
            ratio = after_length / before_length if before_length else 1.0
            length_ratios.append(ratio)
            if ratio < 0.94 or ratio > 1.06:
                warnings.append(f"Volume {volume} day {day}: body length ratio {ratio:.3f}")

            if "  " in all_text([after]):
                errors.append(f"Volume {volume} day {day}: doubled space introduced")

        if volume == 1 and sha(source_by_day[2]) != sha(polished_by_day[2]):
            errors.append("Volume I Day 2 calibration entry changed")

        before_text = all_text(source)
        after_text = all_text(polished)
        corpus_before += before_text
        corpus_after += after_text
        pattern_counts = {
            label: len(re.findall(pattern, after_text, flags=re.IGNORECASE))
            for label, pattern in MECHANICAL_PATTERNS.items()
        }
        for label, count in pattern_counts.items():
            if count:
                errors.append(f"Volume {volume}: {label} still appears {count} time(s)")

        surrender_before = len(re.findall(r"\bsurrender\w*\b", before_text, flags=re.IGNORECASE))
        surrender_after = len(re.findall(r"\bsurrender\w*\b", after_text, flags=re.IGNORECASE))
        if surrender_after < max(250, int(surrender_before * 0.65)):
            errors.append(
                f"Volume {volume}: surrender theology was over-edited "
                f"({surrender_before} before, {surrender_after} after)"
            )

        volumes[str(volume)] = {
            "entries": 366,
            "changed_entries": changed_entries,
            "title_hash_before": sha([record["title"] for record in source]),
            "title_hash_after": sha([record["title"] for record in polished]),
            "day_two_protected": volume != 1 or sha(source_by_day[2]) == sha(polished_by_day[2]),
            "mechanical_pattern_counts": pattern_counts,
            "surrender_word_count_before": surrender_before,
            "surrender_word_count_after": surrender_after,
            "body_length_ratio_min": min(length_ratios),
            "body_length_ratio_max": max(length_ratios),
        }

    before_exact = len(re.findall(r"surrender to His love", corpus_before, flags=re.IGNORECASE))
    after_exact = len(re.findall(r"surrender to His love", corpus_after, flags=re.IGNORECASE))
    report = {
        "status": "failed" if errors else "passed",
        "volumes": volumes,
        "exact_phrase_before": before_exact,
        "exact_phrase_after": after_exact,
        "errors": errors,
        "warnings": warnings,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
