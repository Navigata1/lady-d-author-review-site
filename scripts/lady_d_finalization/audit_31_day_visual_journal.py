#!/usr/bin/env python3
"""Deterministic content and image audit for Lady D's concise visual journal."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source/finalization/31-day-visual-journal-v2/visual-journal.json"
SCENES = ROOT / "assets/lady-d-31-visual-journal-v2/scenes"
QUALITY = ROOT / "quality/31-day-visual-journal-v2"
EXPECTED_SIZE = (1800, 2700)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dhash(image: Image.Image, size: int = 16) -> int:
    grayscale = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    pixels = list(grayscale.get_flattened_data())
    value = 0
    for row in range(size):
        offset = row * (size + 1)
        for column in range(size):
            value = (value << 1) | int(pixels[offset + column] > pixels[offset + column + 1])
    return value


def word_count(value: str) -> int:
    return len(value.split())


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    days = payload.get("days", [])
    errors: list[str] = []
    warnings: list[str] = []
    records: list[dict[str, object]] = []

    if len(days) != 31:
        errors.append(f"expected exactly 31 days, found {len(days)}")
    if [day.get("day") for day in days] != list(range(1, 32)):
        errors.append("days are not the complete ordered range 1-31")
    if len({day.get("title") for day in days}) != 31:
        errors.append("titles are not unique")
    if len({day.get("reference") for day in days}) != 31:
        errors.append("Scripture references are not unique")
    if len({day.get("scene") for day in days}) != 31:
        errors.append("scene directions are not unique")
    if len({day.get("sceneFamily") for day in days}) < 15:
        errors.append("scene-family diversity is below the 15-family floor")

    forbidden_visible_labels = ("volume 1", "volume 2", "volume 3", "source day")
    hashes: dict[str, int] = {}
    perceptual: list[tuple[int, int]] = []
    brightness_values: list[float] = []

    for day in days:
        number = int(day["day"])
        label = f"day {number:02d}"
        for field in ("title", "encouragement", "reference", "scriptureExcerpt", "prayer", "affirmation", "scene", "sceneFamily", "textZone"):
            if not str(day.get(field, "")).strip():
                errors.append(f"{label} is missing {field}")

        lengths = {
            "title": word_count(day.get("title", "")),
            "encouragement": word_count(day.get("encouragement", "")),
            "scripture": word_count(day.get("scriptureExcerpt", "")),
            "prayer": word_count(day.get("prayer", "")),
            "affirmation": word_count(day.get("affirmation", "")),
        }
        if not 2 <= lengths["title"] <= 7:
            errors.append(f"{label} title exceeds the concise 2-7 word range")
        if not 12 <= lengths["encouragement"] <= 32:
            errors.append(f"{label} encouragement exceeds the concise 12-32 word range")
        if not 4 <= lengths["scripture"] <= 28:
            errors.append(f"{label} Scripture excerpt exceeds the 4-28 word range")
        if not 12 <= lengths["prayer"] <= 32:
            errors.append(f"{label} prayer exceeds the concise 12-32 word range")
        if not 2 <= lengths["affirmation"] <= 10:
            errors.append(f"{label} affirmation exceeds the concise 2-10 word range")

        visible_copy = " ".join(str(day.get(field, "")) for field in ("title", "encouragement", "scriptureExcerpt", "prayer", "affirmation")).lower()
        for forbidden in forbidden_visible_labels:
            if forbidden in visible_copy:
                errors.append(f"{label} exposes internal source label {forbidden!r}")
        if day.get("translation") != "KJV":
            errors.append(f"{label} is not explicitly KJV")

        scene_path = SCENES / f"day-{number:02d}.jpg"
        if not scene_path.is_file():
            errors.append(f"{label} scene is missing")
            continue
        with Image.open(scene_path) as image:
            if image.size != EXPECTED_SIZE:
                errors.append(f"{label} scene is {image.size}, expected {EXPECTED_SIZE}")
            if image.mode != "RGB":
                errors.append(f"{label} scene mode is {image.mode}, expected RGB")
            reduced = image.convert("L").resize((64, 96), Image.Resampling.LANCZOS)
            brightness = round(ImageStat.Stat(reduced).mean[0], 2)
            image_hash = sha256(scene_path)
            perceptual_hash = dhash(image)
        if image_hash in hashes:
            errors.append(f"{label} is byte-identical to day {hashes[image_hash]:02d}")
        hashes[image_hash] = number
        perceptual.append((number, perceptual_hash))
        brightness_values.append(brightness)
        records.append({
            "day": number,
            "path": str(scene_path.relative_to(ROOT)),
            "width": EXPECTED_SIZE[0],
            "height": EXPECTED_SIZE[1],
            "brightness": brightness,
            "sha256": image_hash,
            "copyWordCounts": lengths,
        })

    nearest_pairs: list[dict[str, int]] = []
    for index, (left_day, left_hash) in enumerate(perceptual):
        for right_day, right_hash in perceptual[index + 1 :]:
            distance = (left_hash ^ right_hash).bit_count()
            if distance < 20:
                errors.append(f"days {left_day:02d} and {right_day:02d} are perceptually too similar ({distance}/256)")
            if distance < 50:
                nearest_pairs.append({"left": left_day, "right": right_day, "distance": distance})

    dark_scenes = [record["day"] for record in records if float(record["brightness"]) < 70]
    if len(dark_scenes) > 4:
        errors.append(f"too many intentionally dark scenes for Lady D's brightness brief: {dark_scenes}")
    elif dark_scenes:
        warnings.append(f"strategic low-light scenes retained for narrative contrast: {dark_scenes}")

    status = "PASS" if not errors else "FAIL"
    report = {
        "schema": "idc.lady_d_31_day_visual_journal_audit/v2",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "product": "concise 31-page visual journal",
        "days": len(days),
        "uniqueTitles": len({day.get("title") for day in days}),
        "uniqueScriptures": len({day.get("reference") for day in days}),
        "uniqueScenes": len({day.get("scene") for day in days}),
        "uniqueSceneFamilies": len({day.get("sceneFamily") for day in days}),
        "imageSize": {"width": EXPECTED_SIZE[0], "height": EXPECTED_SIZE[1]},
        "brightness": {
            "minimum": min(brightness_values, default=0),
            "maximum": max(brightness_values, default=0),
            "average": round(sum(brightness_values) / len(brightness_values), 2) if brightness_values else 0,
            "strategicLowLightDays": dark_scenes,
        },
        "nearestPerceptualPairsUnder50": sorted(nearest_pairs, key=lambda item: item["distance"]),
        "errors": errors,
        "warnings": warnings,
        "records": records,
        "sourceSha256": sha256(SOURCE),
    }
    QUALITY.mkdir(parents=True, exist_ok=True)
    destination = QUALITY / "content-and-scene-audit.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "days", "uniqueTitles", "uniqueScriptures", "uniqueScenes", "uniqueSceneFamilies", "brightness", "errors", "warnings")}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
