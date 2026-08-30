#!/usr/bin/env python3
"""Verify the immutable Lady D finalization source inventory."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_HASHES = {
    "source/finalization/voice/vol1-voice-366-days.json": "659a474f29abfc6c1fcbab37bd17c19cc2a1785a313ea12bb887c6ac90e97c37",
    "source/finalization/voice/vol2-voice-366-days.json": "03883c9e6bf3d0b9ed2605beed3e08acc831d62fdc4461ae16673b7f70b03880",
    "source/finalization/voice/vol3-voice-366-days.json": "d4b477537c40af43cb242f9b7777b75949bb1a56634cb8d8ee4595dbb283db53",
    "source/finalization/enrichment/vol1-enrichment-366-days.json": "ca55701878e398281d00fb20dd0503b35c0eff32d436432f5ad6784aad30456f",
    "source/finalization/enrichment/vol2-enrichment-366-days.json": "67af0d65478734ddb6be567bda18f995c005ac44bcadbd8dc4dc106a592b3ae1",
    "source/finalization/enrichment/vol3-enrichment-366-days.json": "fada6806a60a36d822776c6b88da6936b5a0b923ad64531d52f583f4ed385257",
    "source/finalization/templates/vol1-devotional-source.html": "736f920f3ce3494313cbd0150db77de5461e9a6a63d7a5ae8e696dc5db7d1512",
    "source/finalization/templates/vol1-journal-source.html": "747d23a72ace494d4234c4fda4eb366e76360e3d68a9cc92886700566927e31c",
    "source/finalization/templates/vol2-devotional-source.html": "5fc022431f13eb35b1cd71414d5a2238d11c68f2ee3124d25b09499330bb0006",
    "source/finalization/templates/vol2-journal-source.html": "146157f91b3121a76c68c8995aa60c8432644c220c73a90e92a092f7543338f7",
    "source/finalization/templates/vol3-devotional-source.html": "4d24dfff181547a71af01001a57898ccc240d4e1da8d07968ed0fba5da8d8ee4",
    "source/finalization/templates/vol3-journal-source.html": "7b371e1aad8cbb27d93621b062fb3fbff6f498f2d33515bc850f08c05251e84d",
    "source/finalization/evidence/Lady-D-Cover-Codex-Handoff.md": "f8b90ec2e6df90f233287a1ca766055608bc68b50f56850a33838afe23a3166b",
    "source/finalization/evidence/Lady-D-Cover-Design-Studio.html": "01fbaaa52c7088f53d2a8376c9746a8bc702aba92bcbf50db290ee3b6f4a1f48",
    "source/finalization/evidence/Lady-D-Cover-Vision-Brief.html": "ba7d8d55ee135272eb8888258aa44e7dbc5b3e9d6928653d6e75076740dce56f",
    "source/finalization/kimi/master-sample.html": "88540004d563303ab00afea418afb51eb85042c3991007f56c90941de3773ecc",
    "source/finalization/kimi/plan-of-attack.html": "16a426def752fedccacbf46a2952cf199a25196f135481c282c5d9ad434ad54c",
    "source/finalization/kimi/prompt-pack-31day.html": "f7c604176f2bb8e7de226337e179fc510ac70a5afc11325b21e02fc665a97dfb",
}

VOICE_FIELDS = {
    "day",
    "title",
    "body",
    "closing",
    "prayer",
    "journal_reflect",
    "journal_act",
}
ENRICHMENT_FIELDS = {
    "day",
    "thread_ref",
    "note_title",
    "note_body",
    "lens_translit",
    "lens_script",
    "lens_lang",
    "lens_gloss",
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(relative: str) -> list[dict]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def check_corpus(relative: str, fields: set[str], errors: list[str]) -> None:
    records = load_json(relative)
    if len(records) != 366:
        errors.append(f"{relative}: expected 366 records, found {len(records)}")
        return

    days = [record.get("day") for record in records]
    if sorted(days) != list(range(366)):
        errors.append(f"{relative}: day keys must be unique integers 0 through 365")

    for index, record in enumerate(records):
        missing = fields - set(record)
        if missing:
            errors.append(f"{relative}[{index}]: missing {sorted(missing)}")
        if "body" in fields:
            body = record.get("body")
            if not isinstance(body, list) or len(body) != 4 or not all(body):
                errors.append(f"{relative}[{index}]: body must contain four non-empty paragraphs")
            if not str(record.get("prayer", "")).rstrip().endswith("Amen."):
                errors.append(f"{relative}[{index}]: prayer must end with Amen.")


def main() -> int:
    errors: list[str] = []
    verified: dict[str, str] = {}

    for relative, expected in EXPECTED_HASHES.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing source: {relative}")
            continue
        actual = digest(path)
        verified[relative] = actual
        if actual != expected:
            errors.append(f"hash mismatch: {relative}\n  expected {expected}\n  actual   {actual}")

    for volume in range(1, 4):
        check_corpus(
            f"source/finalization/voice/vol{volume}-voice-366-days.json",
            VOICE_FIELDS,
            errors,
        )
        check_corpus(
            f"source/finalization/enrichment/vol{volume}-enrichment-366-days.json",
            ENRICHMENT_FIELDS,
            errors,
        )

    exemplar = ROOT / "source/finalization/evidence/lady-d-august-03-voice-exemplar.md"
    exemplar_text = exemplar.read_text(encoding="utf-8") if exemplar.exists() else ""
    for marker in (
        "The God Who Drowns Our Enemies",
        "Notice that Moses did not sing this song before the sea parted",
        "fear, anxiety, guilt, disappointment, temptation, or discouragement",
    ):
        if marker not in exemplar_text:
            errors.append(f"voice exemplar missing marker: {marker}")

    day_two = next(
        item
        for item in load_json("source/finalization/voice/vol1-voice-366-days.json")
        if item["day"] == 2
    )
    if day_two["title"] != "The Love That Sank Pharaoh's Best":
        errors.append("Volume I Day 2 calibration title changed unexpectedly")
    if "Notice the verse" not in day_two["body"][1]:
        errors.append("Volume I Day 2 lost its textual teaching observation")

    report = {
        "status": "failed" if errors else "passed",
        "source_count": len(verified),
        "voice_records": 1098,
        "enrichment_records": 1098,
        "protected_fields": [
            "anchor Scripture text and reference",
            "translation label",
            "original-language lens",
            "correlative thread reference and teaching note",
            "Volume I Day 2 calibration entry",
        ],
        "hashes": verified,
        "errors": errors,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    evidence_path = ROOT / "ops/mission/evidence/P0-G1-2026-08-30.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
