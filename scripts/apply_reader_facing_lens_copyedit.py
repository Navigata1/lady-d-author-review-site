#!/usr/bin/env python3
"""Convert internal production-lens notes into reader-facing context lenses."""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "downloads" / "production"
PUBLIC_PRODUCTION = ROOT / "public" / "downloads" / "production"
OUT = ROOT / "downloads" / "production" / "kdp" / "author-voice-copyedit"
PUBLIC_OUT = ROOT / "public" / "downloads" / "production" / "kdp" / "author-voice-copyedit"
LIBRARY_OUT = Path("/Users/IDC2.5/Documents/LADY D/Production Library/_Shared/KDP Readiness/Author Voice Copyedit")
GENERATED = "2026-07-01"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in content.rstrip().splitlines())
    path.write_text(cleaned + "\n", encoding="utf-8")


def source_files() -> list[Path]:
    return sorted(PRODUCTION.glob("volume-*-days-*-manuscript.md")) + sorted(PRODUCTION.glob("volume-1-leap-day-bonus-manuscript.md"))


def volume_from_path(path: Path) -> int:
    match = re.search(r"volume-(\d+)", path.name)
    if not match:
        raise ValueError(f"Cannot infer volume from {path}")
    return int(match.group(1))


def clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = text.replace("the production lens", "this lens")
    text = text.replace("The production lens", "This lens")
    text = text.replace("the devotional focus", "the devotional focus")
    text = text.replace("This better matches the passage and prevents decorative language use.", "The passage points to inward covenant renewal rather than decorative language.")
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def convert_lens_text(original: str) -> tuple[str, str]:
    text = original.strip()
    text = re.sub(r"^The architecture assigns? [^;]+;\s*", "", text)
    text = re.sub(r"^the architecture assigns? [^;]+;\s*", "", text)
    route = "unknown"

    replacements = [
        ("the production lens is corrected to ", ""),
        ("the production lens uses ", ""),
        ("the production lens keeps ", "This lens keeps "),
        ("the production lens handles ", "This lens reads "),
        ("the production lens treats ", "This lens treats "),
        ("the production lens opens ", "This lens opens "),
    ]
    for prefix, replacement in replacements:
        if text.startswith(prefix):
            route = prefix.strip()
            text = replacement + text[len(prefix) :]
            break

    text = clean_sentence(text)
    return text, route


def apply_file(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    applications: list[dict[str, object]] = []

    def replace_correction(match: re.Match[str]) -> str:
        original = match.group("body").strip()
        replacement, route = convert_lens_text(original)
        applications.append(
            {
                "file": str(path.relative_to(ROOT)),
                "line": text[: match.start()].count("\n") + 1,
                "volume": volume_from_path(path),
                "route": route,
                "old_label": match.group("label"),
                "old_text": original,
                "new_text": replacement,
            }
        )
        return f"**Context and language lens:** {replacement}"

    def replace_text_note(match: re.Match[str]) -> str:
        original = match.group("body").strip()
        replacement = (
            "Matthew 18:11 has textual-placement differences across Bible editions. "
            "Treat this day as rescue-focused while final wording and placement are confirmed during translation and permissions review."
        )
        applications.append(
            {
                "file": str(path.relative_to(ROOT)),
                "line": text[: match.start()].count("\n") + 1,
                "volume": volume_from_path(path),
                "route": "production text note",
                "old_label": match.group("label"),
                "old_text": original,
                "new_text": replacement,
            }
        )
        return f"**Translation review note:** {replacement}"

    new_text = re.sub(
        r"(?m)^\*\*(?P<label>Production lens correction|Production lens note|Production lens):\*\*\s*(?P<body>.+)$",
        replace_correction,
        text,
    )
    new_text = re.sub(
        r"(?m)^\*\*(?P<label>Production text note):\*\*\s*(?P<body>.+)$",
        replace_text_note,
        new_text,
    )
    if new_text != text:
        write(path, new_text)
    return applications


def audit_sources(paths: list[Path]) -> dict[str, object]:
    totals: dict[str, object] = {
        "production_lens_labels": 0,
        "architecture_mentions": 0,
        "context_lens_labels": 0,
        "entries": 0,
        "by_volume": {str(volume): {"entries": 0, "context_lens_labels": 0, "production_lens_labels": 0} for volume in (1, 2, 3)},
    }
    for path in paths:
        text = path.read_text(encoding="utf-8")
        volume = str(volume_from_path(path))
        production = len(re.findall(r"\*\*(?:Production lens correction|Production lens note|Production lens|Production text note):\*\*", text))
        context = len(re.findall(r"\*\*Context and language lens:\*\*", text))
        translation_notes = len(re.findall(r"\*\*Translation review note:\*\*", text))
        entries = len(re.findall(r"(?m)^## (?:Day \d{3}|Bonus)", text))
        totals["production_lens_labels"] += production
        totals["architecture_mentions"] += len(re.findall(r"\barchitecture assigns?\b", text, flags=re.IGNORECASE))
        totals["context_lens_labels"] += context
        totals["entries"] += entries
        totals["by_volume"][volume]["entries"] += entries
        totals["by_volume"][volume]["context_lens_labels"] += context
        totals["by_volume"][volume]["production_lens_labels"] += production
        totals["by_volume"][volume]["translation_review_notes"] = totals["by_volume"][volume].get("translation_review_notes", 0) + translation_notes
    return totals


def markdown_report(payload: dict[str, object]) -> str:
    route_counts = Counter(item["route"] for item in payload["applications"])
    volume_rows = "\n".join(
        f"| Volume {volume} | {row['entries']} | {row['context_lens_labels']} | {row['production_lens_labels']} |"
        for volume, row in payload["post_audit"]["by_volume"].items()
    )
    route_lines = "\n".join(f"- {route}: {count}" for route, count in route_counts.most_common())
    sample_lines = "\n".join(
        f"- `{item['file']}` line {item['line']}: {item['new_text']}"
        for item in payload["applications"][:20]
    )
    return f"""# Lady D Reader-Facing Lens Application

Generated: {GENERATED}

Status: Source-level copyedit applied. Internal production-lens labels were converted into reader-facing context/language lenses.

## Summary

- Source files touched: {len(payload['source_files_touched'])}
- Lines converted in this run: {len(payload['applications'])}
- Remaining internal production labels: {payload['post_audit']['production_lens_labels']}
- Remaining architecture-assigned mentions: {payload['post_audit']['architecture_mentions']}
- Reader-facing context/language lens labels: {payload['post_audit']['context_lens_labels']}
- Source entries checked: {payload['post_audit']['entries']}
- Public mirror remaining internal production labels: {payload['public_audit']['production_lens_labels']}
- Public mirror remaining architecture-assigned mentions: {payload['public_audit']['architecture_mentions']}

## By Volume

| Volume | Entries | Context/language lens labels | Remaining production labels |
| --- | ---: | ---: | ---: |
{volume_rows}

## Conversion Routes

{route_lines}

## Sample Reader-Facing Lens Lines

{sample_lines}

## Release Boundary

This pass removes internal production wording from reader-facing manuscript sources. It does not replace the full author-voice copyedit, Scripture permissions decision, final front/back matter approval, locked page-count cover regeneration, KDP Previewer, or physical proof review.
"""


def sync_artifacts(paths: list[Path]) -> None:
    PUBLIC_OUT.mkdir(parents=True, exist_ok=True)
    LIBRARY_OUT.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, PUBLIC_OUT / path.name)
        shutil.copy2(path, LIBRARY_OUT / path.name)


def sync_public_manuscripts(paths: list[Path]) -> list[Path]:
    mirrored: list[Path] = []
    PUBLIC_PRODUCTION.mkdir(parents=True, exist_ok=True)
    for path in paths:
        target = PUBLIC_PRODUCTION / path.name
        shutil.copy2(path, target)
        mirrored.append(target)
    return mirrored


def main() -> None:
    paths = source_files()
    applications: list[dict[str, object]] = []
    for path in paths:
        applications.extend(apply_file(path))
    public_paths = sync_public_manuscripts(paths)
    touched = sorted({item["file"] for item in applications})
    payload = {
        "generated": GENERATED,
        "status": "reader_facing_lens_copyedit_applied_not_final_upload",
        "applications": applications,
        "source_files_touched": touched,
        "post_audit": audit_sources(paths),
        "public_audit": audit_sources(public_paths),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "reader-facing-lens-application.json"
    md_path = OUT / "reader-facing-lens-application.md"
    write(json_path, json.dumps(payload, indent=2))
    write(md_path, markdown_report(payload))
    sync_artifacts([json_path, md_path])
    print(
        json.dumps(
            {
                "status": payload["status"],
                "converted": len(applications),
                "source_files_touched": len(touched),
                "remaining_production_lens_labels": payload["post_audit"]["production_lens_labels"],
                "remaining_architecture_assigned_mentions": payload["post_audit"]["architecture_mentions"],
                "public_remaining_production_lens_labels": payload["public_audit"]["production_lens_labels"],
                "public_remaining_architecture_assigned_mentions": payload["public_audit"]["architecture_mentions"],
                "report": str(md_path.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
