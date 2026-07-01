#!/usr/bin/env python3
"""Apply proof decision resolutions to Lady D production source files."""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "downloads" / "production"
DECISION_PATH = ROOT / "downloads" / "production" / "kdp" / "proof-decision-resolution" / "proof-decision-resolution.json"
OUT = ROOT / "downloads" / "production" / "kdp" / "proof-decision-application"
PUBLIC_OUT = ROOT / "public" / "downloads" / "production" / "kdp" / "proof-decision-application"
LIBRARY_OUT = Path("/Users/IDC2.5/Documents/LADY D/Production Library/_Shared/KDP Readiness/Proof Decision Application")
GENERATED = "2026-07-01"

MONTH_FOCUS = {
    "January": "First Trust",
    "February": "Holy Courage",
    "March": "Forming Mercy",
    "April": "Renewal Hope",
    "May": "Patient Provision",
    "June": "Settled Peace",
    "July": "Hidden Faithfulness",
    "August": "Sabbath Trust",
    "September": "Harvest Gratitude",
    "October": "Holy Steadiness",
    "November": "Grateful Remembrance",
    "December": "Finishing Hope",
    "Bonus": "Leap-Day Grace",
}

VOLUME_MORNING_FRAMES = {
    1: "Let the Father's love carry {fragment} into one faithful step today.",
    2: "Walk with Jesus through {fragment} in one faithful step today.",
    3: "Let the Spirit carry {fragment} into one faithful step today.",
}

THEOLOGY_REPLACEMENTS = [
    ("fear, rejection, and performance", "fear, rejection, and self-measuring striving"),
    ("I must earn the right to need provision", "I am unworthy of needing provision"),
    ("This protects obedience from becoming performance.", "This protects obedience from becoming self-measuring striving."),
    ("What spiritual practice has become performance?", "What spiritual practice has become self-measuring striving instead of grateful return?"),
    ("Where did Sabbath rest protect obedience from performance?", "Where did Sabbath rest protect obedience from self-measuring striving?"),
    ("visibility or performance?", "visibility or outward achievement?"),
    ("performance religion", "self-managed religion"),
    ("religious performance", "religious self-measuring"),
    ("frantic performance", "frantic striving"),
    ("spiritual performance", "spiritual self-display"),
    ("beneath performance", "beneath self-display"),
    ("platform, or performance", "platform, or self-display"),
    ("pride, confusion, and performance", "pride, confusion, and self-display"),
]


@dataclass(frozen=True)
class EntryRef:
    file: Path
    volume: int
    heading: str
    title: str
    scripture: str
    title_span: tuple[int, int]
    impact: str
    impact_span: tuple[int, int] | None
    month: str
    day_number: int | None


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def manuscript_files() -> list[Path]:
    return sorted(PRODUCTION.glob("volume-*-days-*-manuscript.md")) + sorted(PRODUCTION.glob("volume-1-leap-day-bonus-manuscript.md"))


def journal_files() -> list[Path]:
    return sorted(PRODUCTION.glob("volume-*-*journal.md"))


def volume_from_path(path: Path) -> int:
    match = re.search(r"volume-(\d+)", path.name)
    if not match:
        raise ValueError(f"Cannot infer volume from {path}")
    return int(match.group(1))


def parse_entries(path: Path) -> list[EntryRef]:
    text = read(path)
    matches = list(re.finditer(r"(?m)^## (?P<head>(?:Day (?P<day>\d{3}) - (?P<date>[^\n]+))|(?:Bonus(?: / Leap Day)? - (?P<bonus_date>[^\n]+)))$", text))
    entries: list[EntryRef] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        chunk = text[start:end]
        title_match = re.search(r"(?m)^### (?P<title>.+)$", chunk)
        scripture_match = re.search(r"(?m)^\*\*Scripture Reference:\*\*\s*(?P<scripture>.+)$", chunk)
        impact_match = re.search(r"(?m)^\*\*Morning impact:\*\*\s*(?P<impact>.+)$", chunk)
        if not title_match:
            continue
        day_number = int(match.group("day")) if match.group("day") else None
        date_value = match.group("date") or match.group("bonus_date") or "Bonus"
        month = "Bonus" if match.group("bonus_date") else date_value.split()[0]
        title_span = (start + title_match.start("title"), start + title_match.end("title"))
        impact_span = None
        if impact_match:
            impact_span = (start + impact_match.start("impact"), start + impact_match.end("impact"))
        entries.append(
            EntryRef(
                file=path,
                volume=volume_from_path(path),
                heading=match.group("head"),
                title=title_match.group("title").strip(),
                scripture=scripture_match.group("scripture").strip() if scripture_match else "",
                title_span=title_span,
                impact=impact_match.group("impact").strip() if impact_match else "",
                impact_span=impact_span,
                month=month,
                day_number=day_number,
            )
        )
    return entries


def build_entry_index(paths: list[Path]) -> dict[tuple[int, str], EntryRef]:
    index: dict[tuple[int, str], EntryRef] = {}
    for path in paths:
        for entry in parse_entries(path):
            index[(entry.volume, entry.heading)] = entry
    return index


def apply_replacements(path: Path, replacements: list[tuple[int, int, str]]) -> None:
    if not replacements:
        return
    text = read(path)
    for start, end, value in sorted(replacements, reverse=True):
        text = text[:start] + value + text[end:]
    write(path, text)


def strip_title_action(title: str) -> str:
    patterns = [
        r"^Let Fire Refine\s+",
        r"^Let Grace Form\s+",
        r"^Let Hope Rise\s+",
        r"^Let Love Teach\s+",
        r"^Let Mercy Speak\s+",
        r"^Let Peace Lead\s+",
        r"^Come Home to\s+",
        r"^Hold Fast to\s+",
        r"^Lean Into\s+",
        r"^Return to\s+",
        r"^Surrender to\s+",
        r"^Wake Up to\s+",
        r"^Walk in\s+",
        r"^(?:Anchor|Awaken|Behold|Breathe|Carry|Choose|Discover|Embrace|Follow|Practice|Receive|Remember|Rest in|See Again|Stand in|Trust|Yield to|Listen for)\s+",
    ]
    fragment = title
    for pattern in patterns:
        fragment = re.sub(pattern, "", fragment)
        if fragment != title:
            break
    fragment = fragment.strip()
    fragment = re.sub(r"\bPerformance\b", "Striving", fragment)
    fragment = re.sub(r"\bperformance\b", "striving", fragment)
    fragment = re.sub(r"\bEarn\b", "Receive", fragment)
    fragment = re.sub(r"\bearn\b", "receive", fragment)
    return fragment or title


def new_morning_impact(volume: int, title: str) -> str:
    fragment = title.strip()
    fragment = re.sub(r"\bPerformance\b", "Striving", fragment)
    fragment = re.sub(r"\bperformance\b", "striving", fragment)
    fragment = re.sub(r"\bEarn\b", "Receive", fragment)
    fragment = re.sub(r"\bearn\b", "receive", fragment)
    return VOLUME_MORNING_FRAMES[volume].format(fragment=fragment)


def new_title(old_title: str, month: str, used: set[str], day_number: int | None) -> str:
    focus = MONTH_FOCUS.get(month, "Faithful Response")
    if old_title.startswith("Let Fire Refine "):
        candidate = "Let " + focus + " Refine " + old_title.removeprefix("Let Fire Refine ")
    elif old_title.startswith("Let Grace Form "):
        candidate = "Let " + focus + " Form " + old_title.removeprefix("Let Grace Form ")
    elif old_title.startswith("Let Hope Rise "):
        candidate = "Let " + focus + " Lift " + old_title.removeprefix("Let Hope Rise ")
    elif old_title.startswith("Let Love Teach "):
        candidate = "Let " + focus + " Teach " + old_title.removeprefix("Let Love Teach ")
    elif old_title.startswith("Let Mercy Speak "):
        candidate = "Let " + focus + " Speak " + old_title.removeprefix("Let Mercy Speak ")
    elif old_title.startswith("Let Peace Lead "):
        candidate = "Let " + focus + " Lead " + old_title.removeprefix("Let Peace Lead ")
    elif old_title.startswith("Come Home to "):
        candidate = "Come Home to " + focus + " Through " + old_title.removeprefix("Come Home to ")
    elif old_title.startswith("Hold Fast to "):
        candidate = "Hold Fast to " + focus + " Through " + old_title.removeprefix("Hold Fast to ")
    elif old_title.startswith("Lean Into "):
        candidate = "Lean Into " + focus + " Through " + old_title.removeprefix("Lean Into ")
    elif old_title.startswith("Return to "):
        candidate = "Return to " + focus + " Through " + old_title.removeprefix("Return to ")
    elif old_title.startswith("Surrender to "):
        candidate = "Surrender to " + focus + " Through " + old_title.removeprefix("Surrender to ")
    elif old_title.startswith("Wake Up to "):
        candidate = "Wake Up to " + focus + " Through " + old_title.removeprefix("Wake Up to ")
    elif old_title.startswith("Yield to "):
        candidate = "Yield to " + focus + " Through " + old_title.removeprefix("Yield to ")
    else:
        parts = old_title.split(maxsplit=1)
        candidate = f"{parts[0]} {focus} in {parts[1]}" if len(parts) == 2 else f"{focus} {old_title}"

    candidate = candidate.replace("Performance", "Striving")
    candidate = candidate.replace("performance", "striving")
    base = candidate
    if candidate in used:
        suffix = f" for Day {day_number:03d}" if day_number else f" for {month}"
        candidate = base + suffix
    counter = 2
    while candidate in used:
        candidate = f"{base} {counter}"
        counter += 1
    used.add(candidate)
    return candidate


def apply_title_decisions(resolution: dict[str, object], paths: list[Path]) -> list[dict[str, object]]:
    index = build_entry_index(paths)
    used_titles = {entry.title for entry in index.values()}
    replacements_by_file: dict[Path, list[tuple[int, int, str]]] = {}
    applied: list[dict[str, object]] = []
    for decision in resolution["title_decisions"]:
        for location in decision["locations"][1:]:
            key = (int(decision["volume"]), str(location["heading"]))
            entry = index.get(key)
            if not entry:
                applied.append({"id": decision["id"], "status": "missing_heading", "heading": location["heading"]})
                continue
            if entry.title != decision["repeated_title"]:
                applied.append(
                    {
                        "id": decision["id"],
                        "status": "already_changed_or_mismatch",
                        "heading": entry.heading,
                        "current_title": entry.title,
                    }
                )
                continue
            replacement = new_title(entry.title, entry.month, used_titles, entry.day_number)
            replacements_by_file.setdefault(entry.file, []).append((*entry.title_span, replacement))
            applied.append(
                {
                    "id": decision["id"],
                    "status": "applied",
                    "file": str(entry.file.relative_to(ROOT)),
                    "heading": entry.heading,
                    "old_title": entry.title,
                    "new_title": replacement,
                }
            )
    for path, replacements in replacements_by_file.items():
        apply_replacements(path, replacements)
    return applied


def apply_morning_impacts(paths: list[Path]) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for path in paths:
        replacements: list[tuple[int, int, str]] = []
        for entry in parse_entries(path):
            if not entry.impact_span:
                applied.append({"status": "missing_impact", "file": str(path.relative_to(ROOT)), "heading": entry.heading})
                continue
            replacement = new_morning_impact(entry.volume, entry.title)
            if entry.impact == replacement:
                applied.append({"status": "already_current", "file": str(path.relative_to(ROOT)), "heading": entry.heading})
                continue
            replacements.append((*entry.impact_span, replacement))
            applied.append(
                {
                    "status": "applied",
                    "file": str(path.relative_to(ROOT)),
                    "heading": entry.heading,
                    "title": entry.title,
                    "old_morning_impact": entry.impact,
                    "new_morning_impact": replacement,
                }
            )
        apply_replacements(path, replacements)
    return applied


def apply_theology_replacements(paths: list[Path]) -> list[dict[str, object]]:
    applied: list[dict[str, object]] = []
    for path in paths:
        text = read(path)
        original = text
        for old, new in THEOLOGY_REPLACEMENTS:
            count = text.count(old)
            if count:
                text = text.replace(old, new)
                applied.append({"file": str(path.relative_to(ROOT)), "old": old, "new": new, "count": count})
        if text != original:
            write(path, text)
    return applied


def markdown_report(payload: dict[str, object]) -> str:
    title_count = Counter(item["status"] for item in payload["title_applications"])
    impact_count = Counter(item["status"] for item in payload["morning_impact_applications"])
    theology_total = sum(int(item["count"]) for item in payload["theology_applications"])
    post_check = payload["post_source_repetition_check"]
    post_title_dups = sum(int(item["duplicate_title_groups"]) for item in post_check.values())
    post_impact_dups = sum(int(item["duplicate_morning_impact_groups"]) for item in post_check.values())
    touched = sorted(payload["source_files_touched"])
    return f"""# Lady D Proof Decision Source Application

Generated: {GENERATED}

Status: Source edits applied before master/proof regeneration.

## Summary

- Title decisions applied: {title_count.get("applied", 0)}
- Title decisions skipped/already changed: {sum(v for k, v in title_count.items() if k != "applied")}
- Title decisions resolved in current source state: {len(payload["title_applications"])}
- Morning-impact lines applied: {impact_count.get("applied", 0)}
- Morning-impact lines already current: {impact_count.get("already_current", 0)}
- Morning-impact lines current in source state: {len(payload["morning_impact_applications"])}
- Theology phrase replacements applied: {theology_total}
- Source files touched: {len(touched)}
- Post-source duplicate title groups: {post_title_dups}
- Post-source duplicate morning-impact groups: {post_impact_dups}

## Source Files Touched

{chr(10).join(f"- `{path}`" for path in touched)}

## Resolution Policy

- Later duplicate day titles were retitled using the local month lens while preserving the original devotional angle.
- Repeated morning-impact refrains were individualized per entry so the daily close now reflects the day title and volume lane.
- Priority grace/obedience watch phrases were clarified so obedience remains response to grace, never a way to earn God's love.
"""


def source_repetition_check(paths: list[Path]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for volume in (1, 2, 3):
        titles: list[str] = []
        impacts: list[str] = []
        for path in paths:
            if volume_from_path(path) != volume:
                continue
            for entry in parse_entries(path):
                titles.append(entry.title)
                impacts.append(entry.impact)
        title_dups = sum(1 for count in Counter(titles).values() if count > 1)
        impact_dups = sum(1 for count in Counter(impacts).values() if count > 1)
        result[str(volume)] = {
            "titles": len(titles),
            "morning_impacts": len(impacts),
            "duplicate_title_groups": title_dups,
            "duplicate_morning_impact_groups": impact_dups,
        }
    return result


def sync_artifacts(paths: list[Path]) -> None:
    PUBLIC_OUT.mkdir(parents=True, exist_ok=True)
    LIBRARY_OUT.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, PUBLIC_OUT / path.name)
        shutil.copy2(path, LIBRARY_OUT / path.name)


def main() -> None:
    resolution = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    m_paths = manuscript_files()
    j_paths = journal_files()

    title_applications = apply_title_decisions(resolution, m_paths)
    morning_impact_applications = apply_morning_impacts(m_paths)
    theology_applications = apply_theology_replacements(m_paths + j_paths)

    touched = set()
    for item in title_applications:
        if item.get("status") == "applied":
            touched.add(item["file"])
    for item in morning_impact_applications:
        if item.get("status") == "applied":
            touched.add(item["file"])
    for item in theology_applications:
        touched.add(item["file"])

    payload = {
        "generated": GENERATED,
        "source_decision_file": str(DECISION_PATH.relative_to(ROOT)),
        "title_applications": title_applications,
        "morning_impact_applications": morning_impact_applications,
        "theology_applications": theology_applications,
        "source_files_touched": sorted(touched),
        "post_source_repetition_check": source_repetition_check(m_paths),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "proof-decision-source-application.json"
    md_path = OUT / "proof-decision-source-application.md"
    write(json_path, json.dumps(payload, indent=2))
    write(md_path, markdown_report(payload))
    sync_artifacts([json_path, md_path])
    print(
        json.dumps(
            {
                "title_applied": sum(1 for item in title_applications if item.get("status") == "applied"),
                "morning_impacts_applied": sum(1 for item in morning_impact_applications if item.get("status") == "applied"),
                "theology_replacements": sum(int(item["count"]) for item in theology_applications),
                "source_files_touched": len(touched),
                "report": str(md_path.relative_to(ROOT)),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
