#!/usr/bin/env python3
"""Build book-level master assemblies from Lady D production batches."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "downloads" / "production"
MASTER = PRODUCTION / "master"
PUBLIC_MASTER = ROOT / "public" / "downloads" / "production" / "master"
LIBRARY = ROOT.parents[0] / "Production Library"

TODAY = date(2026, 7, 1).isoformat()


@dataclass(frozen=True)
class Volume:
    number: int
    title: str
    folder: str
    spiritual_lane: str

    @property
    def slug(self) -> str:
        return f"volume-{self.number}"

    @property
    def file_title(self) -> str:
        return self.title.replace("'", "").replace(" ", "-")


VOLUMES = [
    Volume(1, "Surrendering to God's Love", "01 Surrendering to God's Love", "God the Father"),
    Volume(2, "Walking with Jesus", "02 Walking with Jesus", "Jesus the Son"),
    Volume(3, "Filled with the Holy Spirit", "03 Filled with the Holy Spirit", "The Holy Spirit"),
]

MONTHS = {
    "january": 1,
    "february": 2,
    "leap-day": 2.9,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def strip_batch_front_matter(text: str) -> str:
    parts = re.split(r"(?m)^---\s*$", text, maxsplit=1)
    body = parts[1] if len(parts) == 2 else text
    return body.strip()


def manuscript_sort_key(path: Path) -> tuple[float, str]:
    name = path.name
    if "leap-day-bonus" in name:
        return (59.5, name)
    match = re.search(r"days-(\d{3})", name)
    if not match:
        return (9999, name)
    return (int(match.group(1)), name)


def journal_sort_key(path: Path) -> tuple[float, float, str]:
    name = path.name.lower()
    month_rank = 99.0
    for month, rank in MONTHS.items():
        if month in name:
            month_rank = float(rank)
            break
    if "closeout" in name or "-close-" in name or "close-" in name:
        week_rank = 5.5
    elif "transition" in name:
        week_rank = 5.0
    else:
        week_match = re.search(r"week-(\d+)", name)
        week_rank = float(week_match.group(1)) if week_match else 4.9
    if "leap-day" in name:
        month_rank = 2.9
        week_rank = 1.0
    return (month_rank, week_rank, name)


def batch_manuscripts(volume: Volume) -> list[Path]:
    paths = sorted(
        PRODUCTION.glob(f"{volume.slug}-days-*-manuscript.md"),
        key=manuscript_sort_key,
    )
    if volume.number == 1:
        leap = PRODUCTION / "volume-1-leap-day-bonus-manuscript.md"
        if leap.exists():
            paths.append(leap)
            paths = sorted(paths, key=manuscript_sort_key)
    return paths


def batch_journals(volume: Volume) -> list[Path]:
    return sorted(
        PRODUCTION.glob(f"{volume.slug}-*-companion-journal.md"),
        key=journal_sort_key,
    )


def master_header(volume: Volume, kind: str) -> str:
    return f"""# {volume.title}

Susan "Lady D" Damon

IDC Publishing {kind}

Spiritual lane: {volume.spiritual_lane}

Assembly date: {TODAY}

Status: Review master assembled from approved production batches. This is a KDP-oriented assembly artifact, not the final upload file.

Scripture note: Scripture references are included without full quoted Bible text until translation permissions are finalized.

Adventist guardrail: Sabbath language is reserved for the seventh-day/Saturday Sabbath. Obedience is framed as a response to grace, not a way to earn God's love.
"""


def assemble_manuscript(volume: Volume) -> tuple[Path, dict]:
    paths = batch_manuscripts(volume)
    pieces = [master_header(volume, "Master Interior Manuscript")]
    pieces.append("\n## Reader Orientation\n")
    pieces.append(
        "This master gathers the complete daily devotional production batches in calendar order, including the February 29 bonus entry. Final typography, front matter, copyright language, ISBN data, and KDP trim-specific pagination still need the publishing pass.\n"
    )
    pieces.append("\n---\n")
    for path in paths:
        pieces.append(f"\n<!-- Source: {path.name} -->\n")
        pieces.append(strip_batch_front_matter(read(path)))
        pieces.append("\n---\n")

    text = "\n".join(pieces)
    out = MASTER / f"{volume.slug}-master-interior-manuscript.md"
    write(out, text)
    stats = {
        "volume": volume.number,
        "title": volume.title,
        "source_files": [p.name for p in paths],
        "source_file_count": len(paths),
        "day_entries": len(re.findall(r"(?m)^## Day \d{3}\b", text)),
        "bonus_entries": len(re.findall(r"(?m)^## Bonus", text)),
        "scripture_references": len(re.findall(r"(?m)^\*\*Scripture Reference:\*\*", text)),
        "sabbath_mentions": len(re.findall(r"\bSabbath\b", text)),
        "sunday_mentions": len(re.findall(r"\bSunday\b", text)),
        "words": len(text.split()),
        "output": str(out.relative_to(ROOT)),
    }
    return out, stats


def assemble_journal(volume: Volume) -> tuple[Path, dict]:
    paths = batch_journals(volume)
    pieces = [master_header(volume, "Master Companion Journal")]
    pieces.append("\n## Journal Orientation\n")
    pieces.append(
        "This master gathers the companion journal production batches in approximate calendar order for review and future trim-specific design. Final page rhythm, response lines, and KDP interior formatting still need the publishing pass.\n"
    )
    pieces.append("\n---\n")
    for path in paths:
        pieces.append(f"\n<!-- Source: {path.name} -->\n")
        pieces.append(strip_batch_front_matter(read(path)))
        pieces.append("\n---\n")

    text = "\n".join(pieces)
    out = MASTER / f"{volume.slug}-master-companion-journal.md"
    write(out, text)
    stats = {
        "volume": volume.number,
        "title": volume.title,
        "source_files": [p.name for p in paths],
        "source_file_count": len(paths),
        "reflection_sections": len(re.findall(r"(?m)^### .*Reflection\b", text)),
        "sabbath_mentions": len(re.findall(r"\bSabbath\b", text)),
        "sunday_mentions": len(re.findall(r"\bSunday\b", text)),
        "words": len(text.split()),
        "output": str(out.relative_to(ROOT)),
    }
    return out, stats


def copy_to_library(volume: Volume, manuscript: Path, journal: Path) -> None:
    dest = LIBRARY / volume.folder / "06 Master Assembly"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manuscript, dest / manuscript.name)
    shutil.copy2(journal, dest / journal.name)


def copy_to_public(path: Path) -> None:
    target = PUBLIC_MASTER / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def build_audit(manuscript_stats: list[dict], journal_stats: list[dict]) -> Path:
    all_good = all(s["day_entries"] == 365 and s["bonus_entries"] == 1 and s["scripture_references"] == 366 for s in manuscript_stats)
    audit = {
        "assembly_date": TODAY,
        "result": "pass" if all_good else "review",
        "manuscripts": manuscript_stats,
        "journals": journal_stats,
        "requirements": {
            "three_book_folders": "Production Library contains a 06 Master Assembly folder under each book folder.",
            "complete_day_count": "Each master manuscript must contain 365 dated day entries plus one February 29 bonus entry.",
            "scripture_permissions": "References only; no full Bible text is added by this assembler.",
            "adventist_guardrail": "Sabbath wording remains source text only and is not introduced into non-Saturday closeout batches.",
        },
    }
    json_path = MASTER / "master-assembly-audit.json"
    write(json_path, json.dumps(audit, indent=2))

    lines = [
        "# Lady D Master Assembly Audit",
        "",
        f"Audit date: {TODAY}",
        "",
        f"Result: {'Pass' if all_good else 'Needs review'}",
        "",
        "## Manuscript Counts",
        "",
    ]
    for s in manuscript_stats:
        lines.extend(
            [
                f"### Volume {s['volume']} - {s['title']}",
                "",
                f"- Source batch files: {s['source_file_count']}",
                f"- Day entries: {s['day_entries']}",
                f"- Bonus entries: {s['bonus_entries']}",
                f"- Scripture references: {s['scripture_references']}",
                f"- Sabbath mentions: {s['sabbath_mentions']}",
                f"- Sunday mentions: {s['sunday_mentions']}",
                f"- Word count: {s['words']}",
                f"- Output: `{s['output']}`",
                "",
            ]
        )
    lines.extend(["## Companion Journal Counts", ""])
    for s in journal_stats:
        lines.extend(
            [
                f"### Volume {s['volume']} - {s['title']}",
                "",
                f"- Source journal files: {s['source_file_count']}",
                f"- Reflection sections: {s['reflection_sections']}",
                f"- Sabbath mentions: {s['sabbath_mentions']}",
                f"- Sunday mentions: {s['sunday_mentions']}",
                f"- Word count: {s['words']}",
                f"- Output: `{s['output']}`",
                "",
            ]
        )
    md_path = MASTER / "master-assembly-audit.md"
    write(md_path, "\n".join(lines))
    return md_path


def main() -> None:
    MASTER.mkdir(parents=True, exist_ok=True)
    PUBLIC_MASTER.mkdir(parents=True, exist_ok=True)

    manuscript_stats: list[dict] = []
    journal_stats: list[dict] = []
    generated: list[Path] = []

    for volume in VOLUMES:
        manuscript, m_stats = assemble_manuscript(volume)
        journal, j_stats = assemble_journal(volume)
        copy_to_library(volume, manuscript, journal)
        copy_to_public(manuscript)
        copy_to_public(journal)
        manuscript_stats.append(m_stats)
        journal_stats.append(j_stats)
        generated.extend([manuscript, journal])

    audit_md = build_audit(manuscript_stats, journal_stats)
    generated.extend([audit_md, MASTER / "master-assembly-audit.json"])
    for path in [audit_md, MASTER / "master-assembly-audit.json"]:
        copy_to_public(path)
        shared = LIBRARY / "_Shared" / "Release Evidence"
        shared.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, shared / path.name)

    print(json.dumps({"generated": [str(p.relative_to(ROOT)) for p in generated], "manuscripts": manuscript_stats}, indent=2))


if __name__ == "__main__":
    main()
