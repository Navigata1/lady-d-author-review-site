#!/usr/bin/env python3
"""Qualify and rank Lady D's August cover candidates."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "source/finalization/cover-prompts.json"
COVER_DIR = ROOT / "public/covers/lady-d-finalization"
QUALITY_DIR = ROOT / "quality/finalization"
DOWNLOAD_DIR = ROOT / "public/downloads/lady-d-finalization"
EVIDENCE_DIR = ROOT / "ops/mission/evidence"


EDITORIAL = {
    "v1-a-her-golden-valley": {
        "genre_fit": 30,
        "thumbnail_clarity": 23,
        "brief_fidelity": 25,
        "distinction": 19,
        "rationale": "Closest to Lady D's emailed composition, with an immediate emotional center and strong shelf brightness.",
    },
    "v1-b-path-into-light": {
        "genre_fit": 29,
        "thumbnail_clarity": 24,
        "brief_fidelity": 23,
        "distinction": 18,
        "rationale": "The clearest journey metaphor and the brightest Volume I option, with slightly less intimacy than her seated reference.",
    },
    "v1-c-held-above-valley": {
        "genre_fit": 29,
        "thumbnail_clarity": 23,
        "brief_fidelity": 24,
        "distinction": 19,
        "rationale": "A dignified, intimate surrender image with excellent river depth and a calm typographic field.",
    },
    "v2-a-footsteps-at-dawn": {
        "genre_fit": 29,
        "thumbnail_clarity": 25,
        "brief_fidelity": 25,
        "distinction": 18,
        "rationale": "The strongest retail read for the Son volume: unmistakable sandal impressions, open road, and luminous olive setting.",
    },
    "v2-b-olive-road": {
        "genre_fit": 29,
        "thumbnail_clarity": 23,
        "brief_fidelity": 24,
        "distinction": 17,
        "rationale": "Elegant and contemplative, with a softer footprint read and especially usable upper title space.",
    },
    "v2-c-beside-open-field": {
        "genre_fit": 28,
        "thumbnail_clarity": 23,
        "brief_fidelity": 23,
        "distinction": 19,
        "rationale": "The distant companion adds narrative warmth; the brighter path is distinctive but less quiet than the other two.",
    },
    "v2-d-carried-on-the-way": {
        "genre_fit": 30,
        "thumbnail_clarity": 25,
        "brief_fidelity": 25,
        "distinction": 20,
        "rationale": "The most complete Son-lane story: two walkers' trails run side by side, one stops at mid-path, and the carried figure resolves why one full trail continues.",
    },
    "v3-a-dove-opening-sky": {
        "genre_fit": 28,
        "thumbnail_clarity": 25,
        "brief_fidelity": 24,
        "distinction": 18,
        "rationale": "An unmistakable Spirit-lane symbol with exceptional brightness, though the radiant center leaves less tonal range.",
    },
    "v3-b-wind-over-field": {
        "genre_fit": 29,
        "thumbnail_clarity": 23,
        "brief_fidelity": 25,
        "distinction": 19,
        "rationale": "The best expression of breath and movement, balancing the dove and flame with a living field.",
    },
    "v3-c-after-rain": {
        "genre_fit": 30,
        "thumbnail_clarity": 24,
        "brief_fidelity": 25,
        "distinction": 20,
        "rationale": "The richest Spirit composition: dove, flame, living water, fresh growth, and radiant after-rain light work as one scene.",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prompt_data = json.loads(PROMPTS.read_text())
    records = []
    failures = []

    for candidate in prompt_data["candidates"]:
        identifier = candidate["id"]
        path = COVER_DIR / f"{identifier}.png"
        if not path.exists():
            failures.append(f"missing:{identifier}")
            continue

        with Image.open(path) as image:
            rgb = image.convert("RGB")
            gray = rgb.convert("L")
            pixels = rgb.width * rgb.height
            luminance = round(ImageStat.Stat(gray).mean[0], 2)
            histogram = gray.histogram()
            dark_mass = round(sum(histogram[:64]) / pixels * 100, 2)
            aspect = round(rgb.width / rgb.height, 6)
            dimensions_ok = (rgb.width, rgb.height) == (1024, 1536)
            aspect_ok = abs(aspect - (2 / 3)) < 0.001

        floor = candidate["luminance_floor"]
        passed = dimensions_ok and aspect_ok and luminance >= floor and dark_mass <= 25
        if not passed:
            failures.append(identifier)

        editorial = EDITORIAL[identifier]
        score = sum(editorial[key] for key in (
            "genre_fit", "thumbnail_clarity", "brief_fidelity", "distinction"
        ))
        records.append({
            **candidate,
            "file": f"/covers/lady-d-finalization/{path.name}",
            "sha256": digest(path),
            "width": 1024,
            "height": 1536,
            "average_luminance": luminance,
            "dark_mass_percent": dark_mass,
            "qualification": "PASS" if passed else "FAIL",
            "score": score,
            **editorial,
        })

    for volume in (1, 2, 3):
        ranked = sorted(
            (record for record in records if record["volume"] == volume),
            key=lambda record: (-record["score"], record["id"]),
        )
        for rank, record in enumerate(ranked, start=1):
            record["volume_rank"] = rank

    result = {
        "schema": "lady-d.cover-qualification/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate": "PASS" if not failures else "FAIL",
        "rubric": {
            "genre_fit": 30,
            "thumbnail_clarity": 25,
            "brief_fidelity": 25,
            "distinction": 20,
        },
        "hard_rules": {
            "dimensions": "1024x1536",
            "aspect_ratio": "2:3",
            "luminance_floor": "165 for Volume I; 160 for Volumes II and III",
            "maximum_dark_mass_percent": 25,
            "dark_pixel_threshold": "luminance < 64",
        },
        "failures": failures,
        "candidates": sorted(records, key=lambda record: (record["volume"], record["volume_rank"])),
        "shortlist": [
            "v1-a-her-golden-valley",
            "v2-d-carried-on-the-way",
            "v3-c-after-rain",
        ],
        "review_boundary": "Editorial scores are an IDC review rubric, not an independent model-family verdict. Lady D selects the final direction.",
    }

    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2) + "\n"
    (QUALITY_DIR / "lady-d-cover-qualification.json").write_text(payload)
    (DOWNLOAD_DIR / "lady-d-cover-qualification.json").write_text(payload)
    (EVIDENCE_DIR / "P3-G1-2026-08-30.json").write_text(payload)

    print(f"Cover qualification: {result['gate']} ({len(records)} candidates)")
    for record in result["candidates"]:
        print(
            f"  {record['id']}: score={record['score']} "
            f"lum={record['average_luminance']} dark={record['dark_mass_percent']}% "
            f"{record['qualification']}"
        )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
