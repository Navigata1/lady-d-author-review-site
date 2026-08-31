#!/usr/bin/env python3
"""Audit Lady D's 31-day shared devotional corpus and scene-production readiness."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source/finalization/31-day/visual-devotional.json"
SCENES = ROOT / "assets/lady-d-31-day/scenes"
DRAFTS = ROOT / "assets/lady-d-31-day/drafts"
QUALITY = ROOT / "quality/31-day"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    days = payload.get("days", [])
    errors: list[str] = []
    warnings: list[str] = []
    if len(days) != 31:
        errors.append(f"expected 31 days, found {len(days)}")
    if [day.get("day") for day in days] != list(range(1, 32)):
        errors.append("target days are not the complete ordered range 1-31")
    counts = Counter(day.get("volume") for day in days)
    if counts != Counter({1: 10, 2: 10, 3: 10, 0: 1}):
        errors.append(f"volume split is wrong: {dict(counts)}")
    source_pairs = [(day.get("volume"), day.get("sourceDay")) for day in days if day.get("volume")]
    if len(source_pairs) != len(set(source_pairs)):
        errors.append("a trilogy source day was selected more than once")
    for day in days:
        label = f"day {day.get('day')}"
        scripture = day.get("scripture", {})
        if scripture.get("translation") != "KJV":
            errors.append(f"{label} is not KJV")
        if not scripture.get("reference") or not scripture.get("text"):
            errors.append(f"{label} is missing visible Scripture")
        if len(day.get("body", [])) != 4:
            errors.append(f"{label} does not have the four-paragraph Lady D reading anatomy")
        for field in ("title", "closing", "prayer", "journalReflect", "journalAct", "selectionReason"):
            if not str(day.get(field, "")).strip():
                errors.append(f"{label} is missing {field}")
        visual = day.get("visual", {})
        prompt = visual.get("prompt", "").lower()
        if not visual.get("environment") or not visual.get("motion") or not prompt:
            errors.append(f"{label} has an incomplete visual or motion spec")
        if "no text" not in prompt and "do not render typography" not in prompt:
            errors.append(f"{label} prompt does not prohibit baked typography")
    day31 = days[-1] if days else {}
    if day31.get("scripture", {}).get("reference") != "Ephesians 3:19":
        errors.append("day 31 is not the intended trinitarian Ephesians 3 culmination")

    scene_records = []
    for day in days:
        scene = SCENES / f"day-{day['day']:02d}.png"
        draft = DRAFTS / f"day-{day['day']:02d}-v1.png"
        if scene.exists():
            scene_records.append({"day": day["day"], "status": "present-unqualified", "sha256": digest(scene)})
        elif draft.exists():
            scene_records.append({"day": day["day"], "status": "draft-print-hold", "sha256": digest(draft)})
        else:
            scene_records.append({"day": day["day"], "status": "pending-generation"})
    missing_scenes = sum(1 for item in scene_records if item["status"] != "final-qualified")
    draft_scenes = sum(1 for item in scene_records if item["status"] == "draft-print-hold")
    if missing_scenes:
        warnings.append(f"{missing_scenes} final scene renders remain pending; movement key art is directional fallback only")
    if draft_scenes:
        warnings.append(f"{draft_scenes} creative-direction draft is available but remains outside the print-final asset path")

    QUALITY.mkdir(parents=True, exist_ok=True)
    content_report = {
        "schema": "idc.lady_d_31_day_content_audit/v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not errors else "FAIL",
        "days": len(days),
        "volumeCounts": dict(sorted(counts.items())),
        "errors": errors,
        "warnings": warnings,
        "sourceSha256": digest(SOURCE),
    }
    scene_report = {
        "schema": "idc.lady_d_31_day_scene_gauntlet/v1",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING_ASSETS" if missing_scenes else "READY_FOR_VISUAL_SCORING",
        "threshold": 88,
        "rubric": {
            "scriptureAndMessageFidelity": 20,
            "visualStorytelling": 20,
            "LadyDBrightnessAndWarmth": 15,
            "TypographySafeComposition": 10,
            "AnatomyAndHistoricalCoherence": 10,
            "DistinctiveBeauty": 10,
            "MotionLayerPotential": 5,
            "TechnicalQuality": 10,
        },
        "hardRejects": [
            "baked text, watermark, or malformed lettering",
            "scene contradicts the selected Scripture or devotional message",
            "distorted anatomy, demeaning depiction, or careless historical treatment",
            "no clean typography zone",
            "darkness overwhelms the intended light without narrative purpose",
            "scene cannot be separated into foreground, subject, atmosphere, and light layers for motion",
        ],
        "records": scene_records,
    }
    (QUALITY / "content-audit.json").write_text(json.dumps(content_report, indent=2) + "\n", encoding="utf-8")
    (QUALITY / "scene-gauntlet.json").write_text(json.dumps(scene_report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(content_report, indent=2))
    print(json.dumps({"sceneStatus": scene_report["status"], "missingScenes": missing_scenes, "draftScenes": draft_scenes}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
