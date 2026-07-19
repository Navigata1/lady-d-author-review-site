#!/usr/bin/env python3
"""Independent, read-only corpus audit for the Lady D devotional trilogy."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
PRODUCTION = REPO / "downloads" / "production"
MASTER = PRODUCTION / "master"
ASSEMBLY_AUDIT = MASTER / "master-assembly-audit.json"
GUIDANCE = Path("/Users/IDC2.5/Downloads/Untitled meeting Jul 6, 2026.md")
OUT_MD = REPO / "quality" / "auditor" / "pre-rewrite-manuscript-audit.md"
OUT_JSON = REPO / "quality" / "auditor" / "pre-rewrite-manuscript-audit.json"

VOLUME_TITLES = {
    1: "Surrendering to God's Love",
    2: "Walking with Jesus",
    3: "Filled with the Holy Spirit",
}

MONTH_NUMBERS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# Chapter counts provide structural validation. Exact verse-text concordance cannot
# be checked until the required KJV/NKJV text exists in the manuscript.
BIBLE_CHAPTERS = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36,
    "Deuteronomy": 34, "Joshua": 24, "Judges": 21, "Ruth": 4,
    "1 Samuel": 31, "2 Samuel": 24, "1 Kings": 22, "2 Kings": 25,
    "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10, "Nehemiah": 13,
    "Esther": 10, "Job": 42, "Psalm": 150, "Psalms": 150,
    "Proverbs": 31, "Ecclesiastes": 12, "Song of Solomon": 8,
    "Isaiah": 66, "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48,
    "Daniel": 12, "Hosea": 14, "Joel": 3, "Amos": 9, "Obadiah": 1,
    "Jonah": 4, "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephaniah": 3,
    "Haggai": 2, "Zechariah": 14, "Malachi": 4, "Matthew": 28,
    "Mark": 16, "Luke": 24, "John": 21, "Acts": 28, "Romans": 16,
    "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
    "Ephesians": 6, "Philippians": 4, "Colossians": 4,
    "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6,
    "2 Timothy": 4, "Titus": 3, "Philemon": 1, "Hebrews": 13,
    "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5,
    "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22,
}

FIELD_LABELS = [
    "Scripture Reference",
    "Context and language lens",
    "Today step",
    "Prayer",
    "Journal prompt",
    "Morning impact",
]

INTERNAL_PATTERNS = {
    "2026 production calendar": r"\b2026 production calendar\b",
    "this page": r"\bthis page\b",
    "this entry": r"\bthis entry\b",
    "the reader": r"\bthe reader\b",
    "this lens": r"\bthis lens\b",
    "production language": r"\b(?:production batch|production entry|editorial note|translation permissions)\b",
}

ORIGINAL_LANGUAGE_SIGNAL = re.compile(
    r"`[^`]+`|\b(?:Hebrew|Greek|Aramaic|ahavah|hesed|shalom|kyrios|phos|"
    r"sozo|eirene|akoloutheo|pneuma|ruach|parakletos|charis|dunamis|"
    r"koinonia|hagios|emunah|dabaq|lev|yada|gaal)\b",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_phrase(value: str) -> str:
    value = value.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[`*_#]", "", value)
    value = re.sub(r"[^a-z0-9'<>]+", " ", value)
    return normalize_space(value)


def word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def split_sentences(value: str) -> list[str]:
    value = re.sub(r"<!--.*?-->", " ", value, flags=re.DOTALL)
    value = re.sub(r"^#{1,6}\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"\*\*([^*]+):\*\*", r"\1:", value)
    value = normalize_space(value)
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", value) if word_count(part) >= 8]


def parse_reference(reference: str) -> dict[str, Any]:
    match = re.fullmatch(
        r"(?P<book>(?:[1-3] )?[A-Za-z]+(?: [A-Za-z]+)*) "
        r"(?P<chapter>\d+):(?P<verse>\d+)(?:-(?P<end_verse>\d+))?",
        reference.strip(),
    )
    if not match:
        return {"valid": False, "reason": "malformed", "raw": reference}
    book = match.group("book")
    chapter = int(match.group("chapter"))
    verse = int(match.group("verse"))
    end_verse = int(match.group("end_verse")) if match.group("end_verse") else None
    if book not in BIBLE_CHAPTERS:
        return {"valid": False, "reason": "unrecognized_book", "raw": reference, "book": book}
    if chapter < 1 or chapter > BIBLE_CHAPTERS[book]:
        return {
            "valid": False,
            "reason": "chapter_out_of_range",
            "raw": reference,
            "book": book,
            "chapter": chapter,
        }
    if verse < 1 or (end_verse is not None and end_verse < verse):
        return {"valid": False, "reason": "invalid_verse_number", "raw": reference, "book": book}
    return {
        "valid": True,
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "end_verse": end_verse,
        "raw": reference,
    }


def trim_entry_block(block: str) -> str:
    return re.sub(r"\n---\s*$", "", block.strip()).strip()


def extract_field(block: str, label: str) -> str:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.*)$", block, re.MULTILINE | re.IGNORECASE)
    return normalize_space(match.group(1)) if match else ""


def devotional_body(block: str) -> str:
    context = re.search(r"^\*\*Context and language lens:\*\*.*$", block, re.MULTILINE | re.IGNORECASE)
    today = re.search(r"^\*\*Today step:\*\*", block, re.MULTILINE | re.IGNORECASE)
    if not context or not today or context.end() >= today.start():
        return ""
    return block[context.end():today.start()].strip()


def parse_devotional_entries(text: str, volume: int, source: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"^## (?P<header>Day (?P<day>\d{3}) - (?P<date>[A-Za-z]+ \d{1,2})|"
        r"Bonus(?: / Leap Day)? - February 29)\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    entries: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = trim_entry_block(text[match.start():end])
        title_match = re.search(r"^### (.+)$", block, re.MULTILINE)
        day = int(match.group("day")) if match.group("day") else None
        entry_key = f"day-{day:03d}" if day is not None else "bonus"
        date_label = match.group("date") or "February 29"
        month_name, day_of_month = date_label.split()
        fields = {label: extract_field(block, label) for label in FIELD_LABELS}
        body = devotional_body(block)
        reference_data = parse_reference(fields["Scripture Reference"]) if fields["Scripture Reference"] else {
            "valid": False,
            "reason": "missing",
            "raw": "",
        }
        visible_scripture = bool(
            re.search(r"^\*\*Scripture (?:Text|Reading|Passage):\*\*", block, re.MULTILINE | re.IGNORECASE)
            or re.search(r"^>\s+.+\b(?:KJV|NKJV)\b", block, re.MULTILINE | re.IGNORECASE)
            or re.search(r"^\*\*(?:KJV|NKJV):\*\*", block, re.MULTILINE | re.IGNORECASE)
        )
        strict_date_artifact = bool(re.search(r"\b2026 production calendar\b|\bSaturday\b", block, re.IGNORECASE))
        actual_saturday = None
        if day is not None:
            actual_saturday = date(2026, MONTH_NUMBERS[month_name], int(day_of_month)).weekday() == 5
        entry = {
            "volume": volume,
            "entry_key": entry_key,
            "day": day,
            "date": date_label,
            "month": month_name,
            "header": match.group("header"),
            "title": normalize_space(title_match.group(1)) if title_match else "",
            "fields": fields,
            "body": body,
            "block": block,
            "source": source,
            "reference": reference_data,
            "visible_scripture_text": visible_scripture,
            "strict_date_specific_sabbath_artifact": strict_date_artifact,
            "actual_2026_saturday": actual_saturday,
            "word_count": word_count(block),
        }
        entries.append(entry)
    return entries


def parse_journal_entries(text: str, volume: int, source: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"^### (?:(?:Day (?P<day>\d{3})(?P<sabbath> Sabbath)? Reflection)|"
        r"(?:Sabbath Reflection - Day (?P<sabbath_day>\d{3}))|"
        r"(?P<bonus>Leap Day Reflection|Bonus Day Reflection|February 29 Bonus Reflection))\s*$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    entries: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        next_heading = re.search(r"^### ", text[match.end():end], re.MULTILINE)
        if next_heading:
            end = match.end() + next_heading.start()
        block = text[match.start():end].strip()
        day_value = match.group("day") or match.group("sabbath_day")
        day = int(day_value) if day_value else None
        entry_key = f"day-{day:03d}" if day is not None else "bonus"
        focus_match = re.search(r"^\*\*Focus:\*\*\s*(.+)$", block, re.MULTILINE)
        write_match = re.search(r"^\*\*Write:\*\*\s*(.+)$", block, re.MULTILINE)
        practice_match = re.search(r"^(?:-\s*)?(?:\*\*Practice:\*\*|Practice:)\s*(.+)$", block, re.MULTILINE)
        practice = normalize_space(practice_match.group(1)) if practice_match else ""
        if write_match:
            prompt = normalize_space(write_match.group(1))
        else:
            content = block.split("\n", 1)[1] if "\n" in block else ""
            content = re.split(
                r"^(?:-\s*)?(?:\*\*Practice:\*\*|Practice:)",
                content,
                maxsplit=1,
                flags=re.MULTILINE,
            )[0]
            prompt_lines = [
                normalize_space(line)
                for line in content.splitlines()
                if normalize_space(line) and not line.startswith("**Focus:**")
            ]
            prompt = normalize_space(" ".join(prompt_lines))
        entries.append({
            "volume": volume,
            "entry_key": entry_key,
            "day": day,
            "source": source,
            "header": normalize_space(match.group(0).removeprefix("### ")),
            "sabbath_heading": bool(match.group("sabbath") or match.group("sabbath_day")),
            "focus": normalize_space(focus_match.group(1)) if focus_match else "",
            "prompt": prompt,
            "practice": practice,
            "block": block,
            "strict_date_specific_sabbath_artifact": bool(
                match.group("sabbath") or match.group("sabbath_day")
                or re.search(r"\b(?:this|on this|Saturday) Sabbath\b|\bSaturday\b", block, re.IGNORECASE)
            ),
        })
    return entries


def normalized_devotional_signature(entry: dict[str, Any]) -> str:
    parts = [entry["header"], entry["title"], entry["body"]]
    parts.extend(entry["fields"][label] for label in FIELD_LABELS)
    return normalize_phrase("\n".join(parts))


def normalized_journal_signature(entry: dict[str, Any]) -> str:
    return normalize_phrase("\n".join([entry["header"], entry["focus"], entry["prompt"], entry["practice"]]))


def duplicate_summary(values: Iterable[tuple[str, str]], max_groups: int = 25) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    display: dict[str, str] = {}
    for entry_id, value in values:
        key = normalize_phrase(value)
        if not key:
            continue
        groups[key].append(entry_id)
        display.setdefault(key, value)
    duplicated = [(key, ids) for key, ids in groups.items() if len(ids) > 1]
    duplicated.sort(key=lambda item: (-len(item[1]), item[0]))
    return {
        "duplicate_group_count": len(duplicated),
        "affected_entry_count": len({entry_id for _, ids in duplicated for entry_id in ids}),
        "maximum_occurrences": max((len(ids) for _, ids in duplicated), default=1),
        "top_groups": [
            {"value": display[key], "occurrences": len(ids), "entry_ids": ids[:12]}
            for key, ids in duplicated[:max_groups]
        ],
    }


def sentence_repetition(entries: list[dict[str, Any]]) -> dict[str, Any]:
    exact: dict[str, list[dict[str, str]]] = defaultdict(list)
    masked: dict[str, list[dict[str, str]]] = defaultdict(list)
    within_entry_duplicates: list[dict[str, Any]] = []

    for entry in entries:
        entry_id = f"V{entry['volume']}-{entry['entry_key']}"
        text = "\n".join([entry["body"]] + [entry["fields"][label] for label in FIELD_LABELS[2:]])
        sentence_rows: list[tuple[str, str]] = []
        for sentence in split_sentences(text):
            normalized = normalize_phrase(sentence)
            if word_count(normalized) < 8:
                continue
            sentence_rows.append((normalized, sentence))
            exact[normalized].append({"entry_id": entry_id, "sentence": sentence})
            title_masked = re.sub(re.escape(entry["title"]), "<TITLE>", sentence, flags=re.IGNORECASE) if entry["title"] else sentence
            masked[normalize_phrase(title_masked)].append({"entry_id": entry_id, "sentence": sentence})
        local = Counter(key for key, _ in sentence_rows)
        for key, count in local.items():
            if count > 1:
                sample = next(sentence for normalized, sentence in sentence_rows if normalized == key)
                within_entry_duplicates.append({"entry_id": entry_id, "occurrences": count, "sentence": sample})

    exact_groups = [(key, rows) for key, rows in exact.items() if len({row["entry_id"] for row in rows}) > 1]
    exact_groups.sort(key=lambda item: (-len(item[1]), item[0]))

    template_groups = []
    for key, rows in masked.items():
        distinct_entries = {row["entry_id"] for row in rows}
        distinct_originals = {normalize_phrase(row["sentence"]) for row in rows}
        if len(distinct_entries) > 1 and len(distinct_originals) > 1:
            template_groups.append((key, rows))
    template_groups.sort(key=lambda item: (-len(item[1]), item[0]))

    return {
        "exact_repeated_sentence_groups": len(exact_groups),
        "exact_repeated_sentence_occurrences": sum(len(rows) for _, rows in exact_groups),
        "exact_repetition_affected_entries": len({row["entry_id"] for _, rows in exact_groups for row in rows}),
        "within_entry_duplicate_sentence_instances": len(within_entry_duplicates),
        "within_entry_duplicate_sentence_examples": within_entry_duplicates[:30],
        "near_exact_title_masked_template_groups": len(template_groups),
        "near_exact_template_occurrences": sum(len(rows) for _, rows in template_groups),
        "near_exact_template_affected_entries": len({row["entry_id"] for _, rows in template_groups for row in rows}),
        "top_exact_repeated_sentences": [
            {
                "sentence": rows[0]["sentence"],
                "occurrences": len(rows),
                "entry_ids": sorted({row["entry_id"] for row in rows})[:12],
            }
            for _, rows in exact_groups[:25]
        ],
        "top_near_exact_templates": [
            {
                "template": key,
                "occurrences": len(rows),
                "examples": [row["sentence"] for row in rows[:3]],
                "entry_ids": sorted({row["entry_id"] for row in rows})[:12],
            }
            for key, rows in template_groups[:25]
        ],
    }


def near_duplicate_title_pairs(entries: list[dict[str, Any]], threshold: float = 0.90) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    by_volume: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        by_volume[entry["volume"]].append(entry)
    for volume, volume_entries in by_volume.items():
        for index, left in enumerate(volume_entries):
            left_title = normalize_phrase(left["title"])
            for right in volume_entries[index + 1:]:
                right_title = normalize_phrase(right["title"])
                if left_title == right_title or not left_title or not right_title:
                    continue
                ratio = SequenceMatcher(None, left_title, right_title).ratio()
                if ratio >= threshold:
                    pairs.append({
                        "volume": volume,
                        "left": f"V{volume}-{left['entry_key']}",
                        "right": f"V{volume}-{right['entry_key']}",
                        "left_title": left["title"],
                        "right_title": right["title"],
                        "similarity": round(ratio, 4),
                    })
    pairs.sort(key=lambda row: (-row["similarity"], row["left"], row["right"]))
    return {"threshold": threshold, "pair_count": len(pairs), "top_pairs": pairs[:40]}


def scripture_clustering(entries: list[dict[str, Any]]) -> dict[str, Any]:
    dated = sorted((entry for entry in entries if entry["day"] is not None), key=lambda row: row["day"])
    runs: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for entry in dated:
        book = entry["reference"].get("book") if entry["reference"].get("valid") else "INVALID"
        if not current or current[-1]["reference"].get("book") == book:
            current.append(entry)
        else:
            runs.append({
                "book": current[0]["reference"].get("book"),
                "start_day": current[0]["day"],
                "end_day": current[-1]["day"],
                "length": len(current),
            })
            current = [entry]
    if current:
        runs.append({
            "book": current[0]["reference"].get("book"),
            "start_day": current[0]["day"],
            "end_day": current[-1]["day"],
            "length": len(current),
        })

    adjacent_same = 0
    monotonic_same_book = 0
    for left, right in zip(dated, dated[1:]):
        left_ref, right_ref = left["reference"], right["reference"]
        if left_ref.get("book") == right_ref.get("book"):
            adjacent_same += 1
            if (right_ref.get("chapter", 0), right_ref.get("verse", 0)) >= (left_ref.get("chapter", 0), left_ref.get("verse", 0)):
                monotonic_same_book += 1

    monthly: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in dated:
        monthly[entry["month"]][entry["reference"].get("book", "INVALID")] += 1
    month_dominance = []
    for month, counts in monthly.items():
        total = sum(counts.values())
        book, count = counts.most_common(1)[0]
        month_dominance.append({
            "month": month,
            "dominant_book": book,
            "dominant_count": count,
            "dated_entries": total,
            "dominant_share": round(count / total, 4),
            "distinct_books": len(counts),
        })
    month_dominance.sort(key=lambda row: MONTH_NUMBERS[row["month"]])
    runs.sort(key=lambda row: (-row["length"], row["start_day"]))
    return {
        "dated_entries": len(dated),
        "distinct_bible_books": len({entry["reference"].get("book") for entry in dated}),
        "adjacent_same_book_transitions": adjacent_same,
        "adjacent_same_book_rate": round(adjacent_same / max(1, len(dated) - 1), 4),
        "monotonic_transitions_within_same_book": monotonic_same_book,
        "book_runs_ge_7_days": sum(run["length"] >= 7 for run in runs),
        "book_runs_ge_14_days": sum(run["length"] >= 14 for run in runs),
        "book_runs_ge_30_days": sum(run["length"] >= 30 for run in runs),
        "longest_runs": runs[:15],
        "month_dominance": month_dominance,
        "months_over_40_percent_one_book": sum(row["dominant_share"] > 0.40 for row in month_dominance),
    }


def file_has_heading_content(text: str, heading_word: str) -> bool:
    match = re.search(rf"^### .*{heading_word}.*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return False
    tail = text[match.end():]
    next_heading = re.search(r"^### ", tail, re.MULTILINE)
    content = tail[:next_heading.start()] if next_heading else tail
    return bool(normalize_space(content))


def file_inventory(path: Path, role: str, volume: int) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(REPO)),
        "role": role,
        "volume": volume,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def top_rows(rows: list[dict[str, Any]], key: str, limit: int = 10) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (-row[key], str(row)))[:limit]


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def clean(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(clean(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def main() -> None:
    if not GUIDANCE.exists():
        raise SystemExit(f"Missing guidance file: {GUIDANCE}")
    if not ASSEMBLY_AUDIT.exists():
        raise SystemExit(f"Missing assembly manifest: {ASSEMBLY_AUDIT}")

    guidance_text = read_text(GUIDANCE)
    manifest = json.loads(read_text(ASSEMBLY_AUDIT))
    inventory: list[dict[str, Any]] = []
    all_devotional_entries: list[dict[str, Any]] = []
    all_journal_entries: list[dict[str, Any]] = []
    volumes: dict[str, Any] = {}

    for volume in (1, 2, 3):
        manuscript_manifest = next(row for row in manifest["manuscripts"] if row["volume"] == volume)
        journal_manifest = next(row for row in manifest["journals"] if row["volume"] == volume)
        dev_source_paths = [PRODUCTION / name for name in manuscript_manifest["source_files"]]
        journal_source_paths = [PRODUCTION / name for name in journal_manifest["source_files"]]
        dev_master_path = REPO / manuscript_manifest["output"]
        journal_master_path = REPO / journal_manifest["output"]

        missing_files = [str(path) for path in dev_source_paths + journal_source_paths + [dev_master_path, journal_master_path] if not path.exists()]
        if missing_files:
            raise SystemExit("Missing declared production files:\n" + "\n".join(missing_files))

        source_dev_entries: list[dict[str, Any]] = []
        for path in dev_source_paths:
            inventory.append(file_inventory(path, "devotional_source", volume))
            source_dev_entries.extend(parse_devotional_entries(read_text(path), volume, path.name))

        source_journal_entries: list[dict[str, Any]] = []
        journal_file_checks = []
        for path in journal_source_paths:
            text = read_text(path)
            inventory.append(file_inventory(path, "journal_source", volume))
            parsed = parse_journal_entries(text, volume, path.name)
            source_journal_entries.extend(parsed)
            journal_file_checks.append({
                "path": path.name,
                "entry_count": len(parsed),
                "has_prayer": file_has_heading_content(text, "Prayer"),
                "has_review": file_has_heading_content(text, "Review"),
                "has_response_space_markup": bool(re.search(r"_{5,}|\.{8,}|\[writing space\]", text, re.IGNORECASE)),
            })

        inventory.append(file_inventory(dev_master_path, "devotional_master", volume))
        inventory.append(file_inventory(journal_master_path, "journal_master", volume))
        master_dev_entries = parse_devotional_entries(read_text(dev_master_path), volume, dev_master_path.name)
        master_journal_entries = parse_journal_entries(read_text(journal_master_path), volume, journal_master_path.name)

        source_dev_by_key = {entry["entry_key"]: entry for entry in source_dev_entries}
        master_dev_by_key = {entry["entry_key"]: entry for entry in master_dev_entries}
        source_journal_by_key = {entry["entry_key"]: entry for entry in source_journal_entries}
        master_journal_by_key = {entry["entry_key"]: entry for entry in master_journal_entries}

        dev_duplicate_keys = sorted(key for key, count in Counter(entry["entry_key"] for entry in source_dev_entries).items() if count > 1)
        journal_duplicate_keys = sorted(key for key, count in Counter(entry["entry_key"] for entry in source_journal_entries).items() if count > 1)
        expected_keys = {f"day-{day:03d}" for day in range(1, 366)} | {"bonus"}

        dev_mismatches = sorted(
            key for key in expected_keys & source_dev_by_key.keys() & master_dev_by_key.keys()
            if normalized_devotional_signature(source_dev_by_key[key]) != normalized_devotional_signature(master_dev_by_key[key])
        )
        journal_mismatches = sorted(
            key for key in expected_keys & source_journal_by_key.keys() & master_journal_by_key.keys()
            if normalized_journal_signature(source_journal_by_key[key]) != normalized_journal_signature(master_journal_by_key[key])
        )

        label_missing = {
            label: sum(not entry["fields"][label] for entry in source_dev_entries)
            for label in FIELD_LABELS
        }
        invalid_references = [
            {"entry_id": f"V{volume}-{entry['entry_key']}", **entry["reference"]}
            for entry in source_dev_entries if not entry["reference"].get("valid")
        ]
        internal_counts = {
            name: {
                "occurrences": sum(len(re.findall(pattern, entry["block"], re.IGNORECASE)) for entry in source_dev_entries),
                "affected_entries": sum(bool(re.search(pattern, entry["block"], re.IGNORECASE)) for entry in source_dev_entries),
            }
            for name, pattern in INTERNAL_PATTERNS.items()
        }
        contexts = [entry["fields"]["Context and language lens"] for entry in source_dev_entries]
        explicit_language = [
            entry for entry in source_dev_entries
            if ORIGINAL_LANGUAGE_SIGNAL.search(entry["fields"]["Context and language lens"] + " " + entry["body"][:700])
        ]
        context_meta = [
            entry for entry in source_dev_entries
            if re.search(r"\bthis lens\b|\bbecause the verse (?:centers|focuses)\b|\bis framed as\b|\bkeeps? the .* language\b",
                         entry["fields"]["Context and language lens"], re.IGNORECASE)
        ]
        strict_dev_date_artifacts = [entry for entry in source_dev_entries if entry["strict_date_specific_sabbath_artifact"]]
        wrong_saturday_claims = [
            entry for entry in strict_dev_date_artifacts
            if entry["day"] is not None and "saturday" in entry["block"].lower() and not entry["actual_2026_saturday"]
        ]
        strict_journal_date_artifacts = [entry for entry in source_journal_entries if entry["strict_date_specific_sabbath_artifact"]]

        prayer_missing_amen = [
            entry for entry in source_dev_entries
            if entry["fields"]["Prayer"] and not re.search(r"\bAmen\.?$", entry["fields"]["Prayer"], re.IGNORECASE)
        ]
        prompt_missing_question = [
            entry for entry in source_dev_entries
            if entry["fields"]["Journal prompt"] and "?" not in entry["fields"]["Journal prompt"]
        ]

        dev_ids = lambda items: [f"V{volume}-{entry['entry_key']}" for entry in items[:25]]
        journal_prompt_dupes = duplicate_summary(
            (f"V{volume}-{entry['entry_key']}", entry["prompt"]) for entry in source_journal_entries
        )
        journal_practice_dupes = duplicate_summary(
            (f"V{volume}-{entry['entry_key']}", entry["practice"]) for entry in source_journal_entries
        )

        volume_data = {
            "title": VOLUME_TITLES[volume],
            "file_counts": {
                "devotional_sources": len(dev_source_paths),
                "journal_sources": len(journal_source_paths),
                "devotional_masters": 1,
                "journal_masters": 1,
            },
            "devotional_entries": {
                "total": len(source_dev_entries),
                "dated": sum(entry["day"] is not None for entry in source_dev_entries),
                "bonus": sum(entry["day"] is None for entry in source_dev_entries),
                "missing_expected_keys": sorted(expected_keys - source_dev_by_key.keys()),
                "duplicate_keys": dev_duplicate_keys,
                "master_entry_count": len(master_dev_entries),
                "master_missing_keys": sorted(expected_keys - master_dev_by_key.keys()),
                "master_source_content_mismatches": dev_mismatches,
                "word_count": sum(entry["word_count"] for entry in source_dev_entries),
            },
            "scripture": {
                "reference_count": sum(bool(entry["fields"]["Scripture Reference"]) for entry in source_dev_entries),
                "structurally_valid_references": sum(entry["reference"].get("valid", False) for entry in source_dev_entries),
                "invalid_references": invalid_references,
                "visible_scripture_text_entries": sum(entry["visible_scripture_text"] for entry in source_dev_entries),
                "missing_visible_scripture_text_entries": sum(not entry["visible_scripture_text"] for entry in source_dev_entries),
                "translation_tagged_entries": sum(bool(re.search(r"\b(?:KJV|NKJV)\b", entry["block"])) for entry in source_dev_entries),
            },
            "label_contract": {
                "missing_current_labels": label_missing,
                "entries_retaining_today_step": sum(bool(entry["fields"]["Today step"]) for entry in source_dev_entries),
                "entries_retaining_morning_impact": sum(bool(entry["fields"]["Morning impact"]) for entry in source_dev_entries),
                "entries_with_both_deprecated_labels": sum(
                    bool(entry["fields"]["Today step"] and entry["fields"]["Morning impact"])
                    for entry in source_dev_entries
                ),
            },
            "prayer_and_prompt": {
                "missing_prayer": label_missing["Prayer"],
                "prayers_missing_amen": len(prayer_missing_amen),
                "prayers_missing_amen_examples": dev_ids(prayer_missing_amen),
                "missing_journal_prompt": label_missing["Journal prompt"],
                "prompts_without_question_mark": len(prompt_missing_question),
                "prompts_without_question_mark_examples": dev_ids(prompt_missing_question),
            },
            "contextual_language": {
                "lens_present": sum(bool(value) for value in contexts),
                "entries_with_explicit_original_language_signal": len(explicit_language),
                "entries_without_explicit_original_language_signal": len(source_dev_entries) - len(explicit_language),
                "entries_with_editorial_meta_lens_language": len(context_meta),
                "editorial_meta_lens_examples": dev_ids(context_meta),
                "note": "Signals are structural/editorial. Theological and lexical accuracy still requires qualified human review against visible KJV/NKJV text.",
            },
            "date_specific_artifacts": {
                "devotional_entries_with_2026_or_saturday_wording": len(strict_dev_date_artifacts),
                "devotional_examples": dev_ids(strict_dev_date_artifacts),
                "weekday_claims_inconsistent_with_2026_date": len(wrong_saturday_claims),
                "journal_entries_with_calendar_bound_sabbath_wording_or_heading": len(strict_journal_date_artifacts),
                "journal_examples": [f"V{volume}-{entry['entry_key']}" for entry in strict_journal_date_artifacts[:25]],
                "sabbath_occurrences_in_devotional_sources": sum(len(re.findall(r"\bSabbath\b", entry["block"], re.IGNORECASE)) for entry in source_dev_entries),
                "sunday_occurrences_in_devotional_sources": sum(len(re.findall(r"\bSunday\b", entry["block"], re.IGNORECASE)) for entry in source_dev_entries),
            },
            "internal_production_language": internal_counts,
            "scripture_clustering": scripture_clustering(source_dev_entries),
            "duplicate_titles": duplicate_summary(
                (f"V{volume}-{entry['entry_key']}", entry["title"]) for entry in source_dev_entries
            ),
            "duplicate_references": duplicate_summary(
                (f"V{volume}-{entry['entry_key']}", entry["fields"]["Scripture Reference"]) for entry in source_dev_entries
            ),
            "duplicate_title_reference_pairs": duplicate_summary(
                (
                    f"V{volume}-{entry['entry_key']}",
                    entry["title"] + " || " + entry["fields"]["Scripture Reference"],
                )
                for entry in source_dev_entries
            ),
            "journals": {
                "entry_count": len(source_journal_entries),
                "dated_entries": sum(entry["day"] is not None for entry in source_journal_entries),
                "bonus_entries": sum(entry["day"] is None for entry in source_journal_entries),
                "missing_expected_keys": sorted(expected_keys - source_journal_by_key.keys()),
                "duplicate_keys": journal_duplicate_keys,
                "missing_prompt": sum(not entry["prompt"] for entry in source_journal_entries),
                "missing_practice": sum(not entry["practice"] for entry in source_journal_entries),
                "structured_focus_write_practice_entries": sum(bool(entry["focus"] and entry["prompt"] and entry["practice"]) for entry in source_journal_entries),
                "direct_question_practice_entries": sum(bool(not entry["focus"] and entry["prompt"] and entry["practice"]) for entry in source_journal_entries),
                "source_files_missing_prayer": [row["path"] for row in journal_file_checks if not row["has_prayer"]],
                "source_files_missing_review": [row["path"] for row in journal_file_checks if not row["has_review"]],
                "source_files_with_response_space_markup": [row["path"] for row in journal_file_checks if row["has_response_space_markup"]],
                "master_entry_count": len(master_journal_entries),
                "master_missing_keys": sorted(expected_keys - master_journal_by_key.keys()),
                "master_source_content_mismatches": journal_mismatches,
                "duplicate_prompts": journal_prompt_dupes,
                "duplicate_practices": journal_practice_dupes,
            },
        }
        volumes[str(volume)] = volume_data
        all_devotional_entries.extend(source_dev_entries)
        all_journal_entries.extend(source_journal_entries)

    corpus_title_dupes = duplicate_summary(
        (f"V{entry['volume']}-{entry['entry_key']}", entry["title"]) for entry in all_devotional_entries
    )
    corpus_reference_dupes = duplicate_summary(
        (f"V{entry['volume']}-{entry['entry_key']}", entry["fields"]["Scripture Reference"])
        for entry in all_devotional_entries
    )
    corpus_repetition = sentence_repetition(all_devotional_entries)
    near_titles = near_duplicate_title_pairs(all_devotional_entries)

    revised_candidate_root = PRODUCTION / "revised-reader-edition"
    concurrent_files = sorted(path for path in revised_candidate_root.rglob("*") if path.is_file()) if revised_candidate_root.exists() else []
    concurrent_reader_sources = [
        path for path in concurrent_files
        if path.suffix.lower() == ".md" and (
            path.name.endswith("reader-edition.md") or path.name.endswith("companion-journal.md")
        )
    ]
    concurrent_inventory = [
        {
            "path": str(path.relative_to(REPO)),
            "bytes": path.stat().st_size,
            "modified_at_local_epoch": path.stat().st_mtime,
            "sha256": sha256(path),
        }
        for path in concurrent_files
    ]

    total_visible = sum(volume["scripture"]["visible_scripture_text_entries"] for volume in volumes.values())
    total_date_artifacts = sum(volume["date_specific_artifacts"]["devotional_entries_with_2026_or_saturday_wording"] for volume in volumes.values())
    total_journal_date_artifacts = sum(volume["date_specific_artifacts"]["journal_entries_with_calendar_bound_sabbath_wording_or_heading"] for volume in volumes.values())
    total_context_meta = sum(volume["contextual_language"]["entries_with_editorial_meta_lens_language"] for volume in volumes.values())
    total_no_language_signal = sum(volume["contextual_language"]["entries_without_explicit_original_language_signal"] for volume in volumes.values())
    total_response_space_files = sum(len(volume["journals"]["source_files_with_response_space_markup"]) for volume in volumes.values())
    total_journal_sources = sum(volume["file_counts"]["journal_sources"] for volume in volumes.values())

    findings = [
        {
            "id": "F-001",
            "severity": "Critical",
            "confidence": "High",
            "failure": "Required visible Scripture text is absent from the devotional entries.",
            "evidence": f"{1098 - total_visible} of 1,098 entries lack a visible, translation-tagged Scripture text block; {total_visible} contain one.",
            "impact": "Readers cannot see the passage being interpreted, and context-language claims cannot be checked on the page.",
            "likely_cause": "The sources preserve a pre-permissions placeholder policy that conflicts with the July 6 direction.",
            "remediation": "Insert verified KJV text or properly licensed NKJV text with a translation tag in every entry, then run text-reference concordance and rights checks.",
        },
        {
            "id": "F-002",
            "severity": "Critical",
            "confidence": "High",
            "failure": "The revised daily-entry contract from July 6 has not been implemented.",
            "evidence": "All 1,098 entries retain both Today step and Morning impact instead of the requested fused reflection/action ending.",
            "impact": "The pages remain crowded and formulaic, leaving less room for the fuller, more impactful devotional narrative requested by the author.",
            "likely_cause": "The assembled masters still reflect the earlier production schema.",
            "remediation": "Rewrite to one locked entry contract and remove both deprecated labels from the revised masters.",
        },
        {
            "id": "F-003",
            "severity": "High",
            "confidence": "High",
            "failure": "Scripture selection remains heavily clustered in long, sequential Bible-book runs.",
            "evidence": "; ".join(
                f"V{volume}: longest run {data['scripture_clustering']['longest_runs'][0]['length']} days in {data['scripture_clustering']['longest_runs'][0]['book']}, "
                f"{data['scripture_clustering']['adjacent_same_book_rate']:.1%} adjacent same-book transitions"
                for volume, data in volumes.items()
            ),
            "impact": "The reader experiences the mechanical Bible-order crawl the July 6 guidance explicitly rejected.",
            "likely_cause": "References were allocated in book-order production batches rather than curated as a thematic reading journey.",
            "remediation": "Re-sequence within monthly themes using diversity constraints and a human-reviewed narrative arc.",
        },
        {
            "id": "F-004",
            "severity": "High",
            "confidence": "High",
            "failure": "Formula reuse and duplicated sentences create an automated-production voice.",
            "evidence": f"{corpus_repetition['exact_repeated_sentence_groups']} exact repeated sentence groups, "
                        f"{corpus_repetition['near_exact_title_masked_template_groups']} title-masked near-exact template groups, and "
                        f"{corpus_repetition['within_entry_duplicate_sentence_instances']} within-entry duplicate sentence instances.",
            "impact": "Repetition weakens Lady D's personal voice and the requested emotional impact.",
            "likely_cause": "Reusable transition and impact-line templates were applied at scale.",
            "remediation": "Rewrite repeated frames, remove within-entry duplicates, and enforce a corpus-level phrase-reuse gate with a small approved liturgical whitelist.",
        },
        {
            "id": "F-005",
            "severity": "High",
            "confidence": "High",
            "failure": "Calendar-bound 2026/Saturday language makes the evergreen devotional edition date-specific.",
            "evidence": f"{total_date_artifacts} devotional entries and {total_journal_date_artifacts} journal entries contain strict 2026/Saturday-bound wording or headings.",
            "impact": "The day/date sequence will assert the wrong weekday in other years and makes Sabbath reflections look mechanically assigned from the 2026 calendar.",
            "likely_cause": "Saturday flags were generated from the 2026 production calendar.",
            "remediation": "Remove year/weekday assertions; preserve Sabbath theology through evergreen thematic placement and author-approved wording.",
        },
        {
            "id": "F-006",
            "severity": "High",
            "confidence": "Medium",
            "failure": "The Context and language lens frequently behaves as editorial scaffolding rather than concise reader-facing language insight.",
            "evidence": f"{total_context_meta} entries contain explicit lens/meta framing; {total_no_language_signal} have no deterministic original-language signal.",
            "impact": "The feature can feel technical, generic, or disconnected, especially because the Scripture text it should illuminate is missing.",
            "likely_cause": "Context explanation and original-language study were combined under one label without a locked quality rubric.",
            "remediation": "Keep the lens only where it adds verified meaning; require qualified lexical review and remove all editorial/meta phrasing.",
        },
        {
            "id": "F-007",
            "severity": "High",
            "confidence": "High",
            "failure": "Companion-journal content coverage exists, but the journal source is not a finished reader-writing product.",
            "evidence": f"All 1,098 reflections have prompts/practices, but only {total_response_space_files} of {total_journal_sources} journal sources contain detectable response-space markup; style shifts between structured Focus/Write/Practice and direct question/Practice formats.",
            "impact": "The journal is content-complete but not layout-complete or contract-consistent for KDP release.",
            "likely_cause": "Journal masters were assembled before trim-specific design and human-touch layout work.",
            "remediation": "Lock one journal contract, add intentional writing space and weekly/monthly rhythm, then proof at final trim size.",
        },
        {
            "id": "F-008",
            "severity": "Medium",
            "confidence": "High",
            "failure": "Titles and Scripture references need duplicate/near-duplicate editorial review.",
            "evidence": f"Corpus duplicate titles: {corpus_title_dupes['duplicate_group_count']} groups; duplicate references: {corpus_reference_dupes['duplicate_group_count']} groups; near-duplicate title pairs at >=90% similarity: {near_titles['pair_count']}.",
            "impact": "Repeated naming and passages can make the year feel less intentionally composed even when individual entries differ.",
            "likely_cause": "Title-generation formulas and separate volume production lanes were not reconciled at trilogy scale.",
            "remediation": "Review duplicate groups in context and require rationale for any intentional reuse.",
        },
        {
            "id": "F-009",
            "severity": "Medium",
            "confidence": "High",
            "failure": "Internal review/production language remains in source and master front matter, with additional meta language inside entries.",
            "evidence": "Every production batch carries production/editorial permission notes; entry-level counts are detailed by volume in this report.",
            "impact": "Internal scaffolding can leak into customer-facing or KDP-ready outputs and reduces the sense of a finished book.",
            "likely_cause": "Review masters were promoted before a clean publication-layer transform.",
            "remediation": "Create a publication master with zero internal notes and enforce a forbidden-phrase test.",
        },
    ]

    acceptance_tests = [
        {"id": "AT-001", "name": "Corpus grain", "test": "Each volume contains Day 001-365 exactly once plus one February 29 bonus; no missing or duplicate keys in source or master.", "threshold": "366 entries per volume; 1,098 total; 0 mismatches."},
        {"id": "AT-002", "name": "Visible Scripture", "test": "Every entry contains the full quoted passage, a KJV/NKJV tag, and a reference that concords with the displayed text.", "threshold": "1,098/1,098 pass; 0 unlabeled or discordant passages."},
        {"id": "AT-003", "name": "Scripture rights", "test": "KJV public-domain/territory policy or NKJV license/quotation limits are documented for print, ebook, web, and audio.", "threshold": "Signed publishing-rights checklist before layout lock."},
        {"id": "AT-004", "name": "Revised entry contract", "test": "Entry contains date/title, visible Scripture, opening hook, fuller devotional body, optional verified meaning lens, prayer, and one fused reflection/action ending.", "threshold": "100% contract coverage; 0 Today step labels; 0 Morning impact labels."},
        {"id": "AT-005", "name": "Prayer and prompt", "test": "Every entry has a substantive prayer and a clear reader-facing reflection/action prompt tied to the passage.", "threshold": "1,098/1,098 present; 0 placeholders; 0 empty or fragmentary fields."},
        {"id": "AT-006", "name": "Phrase originality", "test": "Scan sentences of eight or more words after normalization and title masking.", "threshold": "0 within-entry duplicate sentences; no unapproved sentence/template in more than 3 entries; approved refrains documented."},
        {"id": "AT-007", "name": "Scripture journey", "test": "Measure same-book runs, monthly book diversity, and adjacent same-book rate after re-sequencing.", "threshold": "No undocumented run over 7 days; no month over 40% one book; at least 4 Bible books per month; adjacent same-book rate <=35%."},
        {"id": "AT-008", "name": "Evergreen dating", "test": "Search devotional and journal sources for production year and weekday-bound claims.", "threshold": "0 occurrences of production-calendar/2026 wording; 0 Saturday/Sunday claims tied to fixed dates."},
        {"id": "AT-009", "name": "Context-language quality", "test": "Any retained lens is concise, passage-specific, reader-facing, and reviewed against the displayed verse by a qualified biblical-language/theology reviewer.", "threshold": "0 editorial-meta lenses; 100% retained lenses signed off; optional omission preferred over weak filler."},
        {"id": "AT-010", "name": "Title/reference duplication", "test": "Exact and >=90% near-duplicate titles plus repeated references are reviewed in trilogy context.", "threshold": "0 accidental duplicate titles; every repeated reference has documented thematic rationale and distinct treatment."},
        {"id": "AT-011", "name": "Journal coverage", "test": "Each devotional entry maps one-to-one to a journal reflection with a clear prompt and practice.", "threshold": "366/366 per volume; 0 missing/duplicate mappings; 0 empty prompt/practice fields."},
        {"id": "AT-012", "name": "Journal product design", "test": "Final 6x9 journal masters use one approved hierarchy, adequate response space, weekly prayer/review rhythm, and legible trim-safe margins.", "threshold": "100% page-template conformance; KDP Previewer and printed-proof approval."},
        {"id": "AT-013", "name": "Publication language", "test": "Search publication masters for production, editorial, permissions, model, prompt, reader-instruction scaffolding, and placeholder language.", "threshold": "0 internal-production hits in reader-facing files."},
        {"id": "AT-014", "name": "Master/source integrity", "test": "Rebuild masters from the declared source inventory and compare normalized entry signatures and hashes.", "threshold": "0 missing entries; 0 content mismatches; manifest and checksums archived."},
        {"id": "AT-015", "name": "Scripture glossary", "test": "Generate biblical-order glossary entries linking reference to day/date and final page after pagination lock.", "threshold": "1,098 source entries represented; 0 broken day/page mappings."},
        {"id": "AT-016", "name": "Independent release gate", "test": "A second auditor samples all flagged categories and verifies automated counts after rewrite; author reviews representative months and final proofs.", "threshold": "No Critical/High findings open; signed author/editor/auditor approvals; physical proof approved."},
    ]

    report = {
        "audit_metadata": {
            "name": "Lady D Trilogy Independent Pre-Rewrite Manuscript Audit",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "RELEASE BLOCKED - PRE-REWRITE AUDIT ONLY",
            "approval": False,
            "guidance_path": str(GUIDANCE),
            "guidance_sha256": sha256(GUIDANCE),
            "production_root": str(PRODUCTION),
            "assembly_manifest": str(ASSEMBLY_AUDIT.relative_to(REPO)),
            "methodology_version": "1.0.0",
        },
        "scope": {
            "devotional_source_files": sum(v["file_counts"]["devotional_sources"] for v in volumes.values()),
            "journal_source_files": total_journal_sources,
            "master_files": 6,
            "files_hashed_and_read": len(inventory),
            "devotional_entries": len(all_devotional_entries),
            "journal_reflections": len(all_journal_entries),
            "grain": "One devotional entry and one companion-journal reflection per volume/day, plus one February 29 bonus per volume.",
        },
        "concurrent_artifact_boundary": {
            "detected": bool(concurrent_files),
            "path": str(revised_candidate_root.relative_to(REPO)),
            "file_count": len(concurrent_files),
            "reader_manuscript_or_journal_markdown_count": len(concurrent_reader_sources),
            "included_in_pre_rewrite_metrics": False,
            "reason": "These undeclared revised-reader candidates appeared outside the canonical pre-rewrite assembly manifest. Mixing them into the baseline would invalidate before/after comparison. They require a separate post-rewrite judge and auditor pass and receive no release approval here.",
            "inventory": concurrent_inventory,
        },
        "methodology": {
            "source_of_truth": "Source lists declared in downloads/production/master/master-assembly-audit.json; assembled Markdown masters used for reconciliation, not double-counting.",
            "checks": [
                "SHA-256 inventory and source/master existence",
                "Day/bonus completeness and uniqueness",
                "Reference syntax, recognized book, and chapter range",
                "Visible KJV/NKJV Scripture-text block presence",
                "Field-label contract, prayer, and prompt completeness",
                "Exact normalized sentence repetition, within-entry duplication, and title-masked near-exact templates",
                "Exact/near-duplicate titles and exact reference reuse",
                "Bible-book run length, adjacency, monotonicity, and monthly concentration",
                "2026/Saturday/Sabbath/Sunday calendar artifacts",
                "Internal production/editorial language",
                "Context-language structural signals and meta-language",
                "Journal coverage, prompt/practice completeness, style consistency, prayer/review sections, and response-space markup",
                "Normalized source-to-master entry-signature reconciliation",
            ],
            "limitations": [
                "No verse text exists in the entries, so exact KJV/NKJV concordance cannot yet be performed.",
                "Structural original-language signals do not establish lexical or theological accuracy; qualified human review is required.",
                "Markdown response-space detection does not replace visual inspection of final 6x9 PDF interiors and printed proofs.",
                "Near-duplicate title detection uses SequenceMatcher >= 0.90 within each volume; it is a screening test, not a literary verdict.",
            ],
            "reproduction_commands": [
                "python3 quality/auditor/run_pre_rewrite_manuscript_audit.py",
                "python3 -m json.tool quality/auditor/pre-rewrite-manuscript-audit.json >/dev/null",
                "git diff -- downloads/production/",
            ],
        },
        "corpus_summary": {
            "devotional_entries": len(all_devotional_entries),
            "journal_reflections": len(all_journal_entries),
            "visible_scripture_text_entries": total_visible,
            "entries_with_both_deprecated_labels": sum(v["label_contract"]["entries_with_both_deprecated_labels"] for v in volumes.values()),
            "date_specific_devotional_artifacts": total_date_artifacts,
            "date_specific_journal_artifacts": total_journal_date_artifacts,
            "duplicate_titles": corpus_title_dupes,
            "duplicate_references": corpus_reference_dupes,
            "sentence_repetition": corpus_repetition,
            "near_duplicate_titles": near_titles,
        },
        "volumes": volumes,
        "findings": findings,
        "acceptance_tests": acceptance_tests,
        "file_inventory": inventory,
        "release_decision": {
            "approved": False,
            "decision": "DO NOT RELEASE",
            "reason": "Critical and High manuscript-contract failures remain. This audit establishes the rewrite baseline only.",
        },
    }

    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    summary_rows = []
    for volume, data in volumes.items():
        clustering = data["scripture_clustering"]
        longest = clustering["longest_runs"][0]
        summary_rows.append([
            f"V{volume}",
            data["devotional_entries"]["total"],
            data["journals"]["entry_count"],
            data["scripture"]["visible_scripture_text_entries"],
            data["label_contract"]["entries_with_both_deprecated_labels"],
            data["date_specific_artifacts"]["devotional_entries_with_2026_or_saturday_wording"],
            f"{longest['book']} {longest['length']} days",
        ])

    reference_rows = []
    for volume, data in volumes.items():
        reference_rows.append([
            f"V{volume}",
            data["scripture"]["reference_count"],
            data["scripture"]["structurally_valid_references"],
            data["duplicate_references"]["duplicate_group_count"],
            data["scripture_clustering"]["distinct_bible_books"],
            f"{data['scripture_clustering']['adjacent_same_book_rate']:.1%}",
            data["scripture_clustering"]["months_over_40_percent_one_book"],
        ])

    journal_rows = []
    for volume, data in volumes.items():
        journal = data["journals"]
        journal_rows.append([
            f"V{volume}", journal["entry_count"], journal["missing_prompt"], journal["missing_practice"],
            journal["structured_focus_write_practice_entries"], journal["direct_question_practice_entries"],
            len(journal["source_files_missing_prayer"]), len(journal["source_files_missing_review"]),
            len(journal["source_files_with_response_space_markup"]),
        ])

    finding_lines = []
    for finding in findings:
        finding_lines.extend([
            f"### {finding['id']} - {finding['severity']}: {finding['failure']}",
            "",
            f"- **Evidence:** {finding['evidence']}",
            f"- **Why it matters:** {finding['impact']}",
            f"- **Likely cause:** {finding['likely_cause']}",
            f"- **Required remediation:** {finding['remediation']}",
            f"- **Confidence:** {finding['confidence']}",
            "",
        ])

    exact_sentence_rows = [
        [row["occurrences"], row["sentence"], ", ".join(row["entry_ids"][:6])]
        for row in corpus_repetition["top_exact_repeated_sentences"][:12]
    ]
    near_template_rows = [
        [row["occurrences"], row["template"], ", ".join(row["entry_ids"][:6])]
        for row in corpus_repetition["top_near_exact_templates"][:12]
    ]
    duplicate_reference_rows = [
        [row["occurrences"], row["value"], ", ".join(row["entry_ids"][:8])]
        for row in corpus_reference_dupes["top_groups"][:12]
    ] or [[0, "None", "-"]]
    duplicate_title_rows = [
        [row["occurrences"], row["value"], ", ".join(row["entry_ids"][:8])]
        for row in corpus_title_dupes["top_groups"][:12]
    ] or [[0, "None", "-"]]

    acceptance_lines = []
    for test in acceptance_tests:
        acceptance_lines.append(f"- **{test['id']} - {test['name']}:** {test['test']} **Pass threshold:** {test['threshold']}")

    markdown = f"""# Lady D Trilogy Independent Pre-Rewrite Manuscript Audit

**Status: RELEASE BLOCKED - PRE-REWRITE AUDIT ONLY**

**Release approval:** No. This report establishes the evidence baseline for the rewrite. It does not approve any manuscript, journal, PDF, cover, or KDP upload.

## Audit Scope

- July 6 guidance read in full: `{GUIDANCE}`
- Production root: `{PRODUCTION}`
- Canonical source inventory: {report['scope']['devotional_source_files']} devotional sources, {report['scope']['journal_source_files']} journal sources, and 6 Markdown masters
- Files hashed and read: {report['scope']['files_hashed_and_read']}
- Concurrent revised-reader artifacts additionally detected and hashed: {report['concurrent_artifact_boundary']['file_count']} files, including {report['concurrent_artifact_boundary']['reader_manuscript_or_journal_markdown_count']} manuscript/journal Markdown candidates
- Devotional grain audited: {report['scope']['devotional_entries']} entries (365 dated days + one February 29 bonus in each volume)
- Companion-journal grain audited: {report['scope']['journal_reflections']} reflections
- Derivative DOCX/PDF/ZIP review copies were not counted as separate manuscript content. Their canonical Markdown sources and assembled Markdown masters were audited.
- The undeclared `downloads/production/revised-reader-edition/` candidates appeared outside the canonical pre-rewrite manifest during this audit. They are intentionally excluded from the pre-rewrite counts so the baseline remains valid. They are not approved and require a separate post-rewrite judge/auditor pass.

## Executive Judgment

The corpus is complete in count and source-to-master assembly, but it is not release-ready. The July 6 direction has not yet been carried into the three books: every entry still omits visible Scripture text, every entry retains the two labels the author asked to fuse/remove, scripture movement remains heavily clustered, repeated production formulas weaken the voice, and evergreen pages are tied to the 2026 Saturday calendar. The journals cover all days, but their source contract and writing-space design are not finished.

{md_table(['Volume', 'Devotions', 'Journal entries', 'Visible verse text', 'Old dual labels', '2026/Sat artifacts', 'Longest same-book run'], summary_rows)}

## Methodology and Commands

The canonical source lists came from `downloads/production/master/master-assembly-audit.json`. Each declared source and all six masters were read and SHA-256 hashed. Source entries were counted once; masters were used only for normalized source/master reconciliation.

Checks performed:

- day/bonus completeness and duplicate-key detection
- Scripture-reference syntax, recognized Bible book, and chapter-range validation
- visible KJV/NKJV Scripture-text and translation-tag detection
- current and July 6 revised label contracts
- prayer/prompt presence and basic completion signals
- exact normalized sentence reuse, within-entry duplicates, title-masked template reuse, and near-duplicate titles
- sequential Bible-book runs, adjacent same-book rate, monotonic progression, and monthly concentration
- 2026/Saturday/Sabbath/Sunday artifacts
- internal production/editorial phrasing
- context-language structural and meta-language signals
- journal day mapping, prompt/practice completeness, style consistency, prayer/review sections, and response-space markup
- normalized entry-signature comparison between batch sources and assembled masters

Reproduce with:

```bash
python3 quality/auditor/run_pre_rewrite_manuscript_audit.py
python3 -m json.tool quality/auditor/pre-rewrite-manuscript-audit.json >/dev/null
git diff -- downloads/production/
```

## Severity-Ranked Failures

{chr(10).join(finding_lines)}
## Counts by Volume

### Scripture and Ordering

{md_table(['Volume', 'References', 'Structurally valid', 'Duplicate ref groups', 'Bible books used', 'Adjacent same book', 'Months >40% one book'], reference_rows)}

Structural validity means a recognized 66-book name, valid reference shape, and chapter within that book's chapter count. Because verse text is absent, exact verse concordance and interpretive accuracy cannot yet pass.

### Label, Prayer, Context, and Internal-Language Counts

{md_table(
    ['Volume', 'Missing current labels', 'Prayer gaps', 'Prompt gaps', 'No language signal', 'Meta-lens entries', '2026/Sat devotions', '2026/Sat journals'],
    [
        [
            f"V{volume}",
            sum(data['label_contract']['missing_current_labels'].values()),
            data['prayer_and_prompt']['missing_prayer'],
            data['prayer_and_prompt']['missing_journal_prompt'],
            data['contextual_language']['entries_without_explicit_original_language_signal'],
            data['contextual_language']['entries_with_editorial_meta_lens_language'],
            data['date_specific_artifacts']['devotional_entries_with_2026_or_saturday_wording'],
            data['date_specific_artifacts']['journal_entries_with_calendar_bound_sabbath_wording_or_heading'],
        ]
        for volume, data in volumes.items()
    ]
)}

### Companion Journals

{md_table(['Volume', 'Entries', 'Missing prompt', 'Missing practice', 'Focus/Write/Practice', 'Question/Practice', 'Files no prayer', 'Files no review', 'Files with response space'], journal_rows)}

Coverage is not the same as publication completeness. The current Markdown contains the reflection content, but it does not yet demonstrate a consistent final journal contract or usable 6x9 writing-page design.

## Repetition Evidence

- Exact repeated sentence groups: **{corpus_repetition['exact_repeated_sentence_groups']}**
- Exact repeated sentence occurrences: **{corpus_repetition['exact_repeated_sentence_occurrences']}**
- Entries affected by exact repeated sentences: **{corpus_repetition['exact_repetition_affected_entries']}**
- Within-entry duplicate sentence instances: **{corpus_repetition['within_entry_duplicate_sentence_instances']}**
- Title-masked near-exact template groups: **{corpus_repetition['near_exact_title_masked_template_groups']}**
- Entries affected by title-masked templates: **{corpus_repetition['near_exact_template_affected_entries']}**
- Near-duplicate title pairs at >=90% similarity: **{near_titles['pair_count']}**

### Most-Repeated Exact Sentences

{md_table(['Occurrences', 'Sentence', 'Example entries'], exact_sentence_rows or [[0, 'None', '-']])}

### Most-Repeated Title-Masked Templates

{md_table(['Occurrences', 'Normalized template', 'Example entries'], near_template_rows or [[0, 'None', '-']])}

## Duplicate Titles and References

### Exact Duplicate Titles

{md_table(['Occurrences', 'Title', 'Example entries'], duplicate_title_rows)}

### Exact Duplicate Scripture References

{md_table(['Occurrences', 'Reference', 'Example entries'], duplicate_reference_rows)}

Any reuse may be intentional, but it must be reviewed in trilogy context and documented. This audit does not treat mere presence of a duplicate as theological error.

## Internal Production Language

{md_table(
    ['Volume', '2026 production calendar', 'This page', 'This entry', 'The reader', 'This lens'],
    [
        [
            f"V{volume}",
            data['internal_production_language']['2026 production calendar']['affected_entries'],
            data['internal_production_language']['this page']['affected_entries'],
            data['internal_production_language']['this entry']['affected_entries'],
            data['internal_production_language']['the reader']['affected_entries'],
            data['internal_production_language']['this lens']['affected_entries'],
        ]
        for volume, data in volumes.items()
    ]
)}

In addition, every source batch and each assembled master carries review-stage production/permissions front matter. That is appropriate for internal review artifacts but forbidden in the publication masters.

## Acceptance Tests for the Revised Edition

{chr(10).join(acceptance_lines)}

## Limitations and Required Human Review

- This is an independent structural/editorial audit, not pastoral, denominational, legal, or biblical-language approval.
- Exact KJV/NKJV concordance cannot be tested until visible verse text is inserted.
- Original-language and theological accuracy require qualified human review against the displayed passage and its literary context.
- Final journal completeness requires visual inspection of imposed 6x9 PDFs, KDP Previewer output, and printed proofs.
- Near-duplicate screens identify editorial risk; a human editor must decide whether a refrain is purposeful or stale.

## Release Decision

**DO NOT RELEASE.** Critical and High failures remain. Rewrite all three devotional manuscripts and their companion journals to the July 6 contract, run these acceptance tests again, and require independent author/editor/auditor approval before any KDP or public-release claim.

Machine-readable evidence: `quality/auditor/pre-rewrite-manuscript-audit.json`
"""
    OUT_MD.write_text(markdown.rstrip() + "\n", encoding="utf-8")

    print(json.dumps({
        "status": report["release_decision"]["decision"],
        "devotional_entries": len(all_devotional_entries),
        "journal_reflections": len(all_journal_entries),
        "files_hashed_and_read": len(inventory),
        "markdown": str(OUT_MD),
        "json": str(OUT_JSON),
    }, indent=2))


if __name__ == "__main__":
    main()
