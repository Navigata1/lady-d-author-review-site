#!/usr/bin/env python3
"""Apply a deterministic, context-preserving polish to Lady D's voice corpus."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "source/finalization/voice"
OUTPUT_DIR = ROOT / "source/finalization/polished"
QUALITY_DIR = ROOT / "quality/finalization"

TEXT_FIELDS = ("body", "closing", "prayer", "journal_reflect", "journal_act")

MEANS_FRAMES = (
    "Here, surrender looks like",
    "In this moment, surrender means",
    "Love asks for something concrete:",
    "The release He invites looks like",
    "Here is the response His love makes possible:",
    "This is the trust His love invites:",
)

AS_YOU_FRAMES = (
    "As you rest more fully in His love,",
    "As His love becomes the place you stand,",
    "As you release this into His care,",
    "With this held in His loving care,",
    "As you let His love steady you,",
    "As you stop carrying this alone,",
)

BY_FRAMES = (
    "Let His love meet you in",
    "Let trust take shape in",
    "Place yourself in His care by",
    "Give His love room by",
)

RESIDUAL_FRAMES = (
    "rest in His love",
    "entrust yourself to His care",
    "yield to His loving care",
    "place yourself in His care",
    "let His love become your resting place",
    "bring the whole matter into His care",
)

OUR_PART_FRAMES = (
    "What remains for us is to yield",
    "We are invited to release",
    "Our faithful response is to entrust",
    "The next faithful step is to yield",
)

OUR_PART_TO_FRAMES = (
    "Our faithful response is to trust",
    "We are invited to rest in",
    "What remains is to place our confidence in",
    "Our next step is to lean on",
)

GOD_LOVE_FRAMES = (
    "rest in God's love",
    "entrust yourself to God's care",
    "yield to God's loving care",
    "place the matter in God's hands",
)


def choose(options: tuple[str, ...], key: str, occurrence: int) -> str:
    digest = hashlib.sha256(f"{key}:{occurrence}".encode("utf-8")).digest()
    return options[int.from_bytes(digest[:4], "big") % len(options)]


def preserve_case(source: str, replacement: str) -> str:
    if source and source[0].islower():
        return replacement[0].lower() + replacement[1:]
    return replacement


def pronoun_frame(pronoun: str, key: str, occurrence: int) -> str:
    lower = pronoun.lower()
    possessive = {"we": "our", "you": "your", "i": "my"}[lower]
    frames = (
        f"When {pronoun} rest this in His care,",
        f"When His love becomes {possessive} resting place,",
        f"When {pronoun} stop carrying this alone,",
        f"When {pronoun} let His love hold the outcome,",
    )
    return choose(frames, key, occurrence)


def substitute(
    text: str,
    pattern: str,
    replacements: tuple[str, ...],
    key: str,
    counter: Counter[str],
) -> str:
    def callback(match: re.Match[str]) -> str:
        occurrence = counter[key]
        counter[key] += 1
        replacement = choose(replacements, key, occurrence)
        return preserve_case(match.group(0), replacement)

    return re.sub(pattern, callback, text, flags=re.IGNORECASE)


def polish_text(text: str, key: str, counter: Counter[str]) -> str:
    text = substitute(
        text,
        r"Surrender to His love means",
        MEANS_FRAMES,
        f"{key}:means",
        counter,
    )
    text = substitute(
        text,
        r"As you surrender to His love,",
        AS_YOU_FRAMES,
        f"{key}:as-you",
        counter,
    )

    pronoun_pattern = re.compile(r"When (we|you|I) surrender to His love,", re.IGNORECASE)

    def pronoun_callback(match: re.Match[str]) -> str:
        frame_key = f"{key}:when-{match.group(1).lower()}"
        occurrence = counter[frame_key]
        counter[frame_key] += 1
        return pronoun_frame(match.group(1), frame_key, occurrence)

    text = pronoun_pattern.sub(pronoun_callback, text)
    text = substitute(
        text,
        r"Surrender to His love by",
        BY_FRAMES,
        f"{key}:by",
        counter,
    )
    text = substitute(
        text,
        r"Our part is to surrender to",
        OUR_PART_TO_FRAMES,
        f"{key}:our-part-to",
        counter,
    )
    text = substitute(
        text,
        r"Our part is to surrender",
        OUR_PART_FRAMES,
        f"{key}:our-part",
        counter,
    )
    text = substitute(
        text,
        r"surrendering to His love",
        ("resting in His loving care", "placing the matter in His care"),
        f"{key}:gerund",
        counter,
    )
    text = substitute(
        text,
        r"surrender to His love",
        RESIDUAL_FRAMES,
        f"{key}:residual-his",
        counter,
    )
    text = substitute(
        text,
        r"surrender to (?:the )?Father's love",
        ("rest in the Father's love", "entrust yourself to the Father's care"),
        f"{key}:father",
        counter,
    )
    text = substitute(
        text,
        r"surrender to God's love",
        GOD_LOVE_FRAMES,
        f"{key}:god",
        counter,
    )

    # Humanizer-guided cleanup. These phrases are changed only where the
    # wording is editorial, not where the term appears inside a Scripture quote.
    text = re.sub(r"He sends people specifically to find you", "He sends people to find you by name", text)
    text = re.sub(r"clearly, specifically, kindly", "clearly and kindly", text)
    text = re.sub(r"honestly and specifically", "honestly and plainly", text)
    text = re.sub(r"plainly and specifically", "plainly and by name", text)
    text = re.sub(r"\bspecifically\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\btransformation\b", "inward change", text, flags=re.IGNORECASE)
    text = re.sub(r"\bempowering for the mission\b", "strength for the mission", text, flags=re.IGNORECASE)
    text = re.sub(r"\bempowered\b", "strengthened", text, flags=re.IGNORECASE)
    text = re.sub(r"\bempowering\b", "strengthening", text, flags=re.IGNORECASE)
    text = re.sub(r"\bempower\b", "strengthen", text, flags=re.IGNORECASE)
    text = re.sub(r"\bultimately in charge\b", "always in charge", text, flags=re.IGNORECASE)
    text = re.sub(r"\bjourney illuminated now\b", "journey lit now", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhumble alignment\b", "humble agreement", text, flags=re.IGNORECASE)
    text = re.sub(
        r"When you align your heart with",
        "When you bring your heart into agreement with",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"the outer landscape finally changes",
        "the outer circumstances finally change",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bthe intricate work\b", "the detailed work", text, flags=re.IGNORECASE)
    text = re.sub(r"\benduring in private\b", "holding on in private", text, flags=re.IGNORECASE)
    text = re.sub(
        r"loaded the wagons accordingly",
        "loaded the wagons for the road ahead",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"a marriage was twisted into leverage", "a marriage was twisted into a means of control", text, flags=re.IGNORECASE)
    text = re.sub(r"love from leverage", "love from control", text, flags=re.IGNORECASE)
    text = re.sub(r"love or leverage", "love or pressure", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r" {2,}", " ", text)
    return text


def corpus_text(records: list[dict]) -> str:
    parts: list[str] = []
    for record in records:
        parts.append(record["title"])
        parts.extend(record["body"])
        parts.extend(
            [
                record["closing"],
                record["prayer"],
                record["journal_reflect"],
                record["journal_act"],
            ]
        )
    return "\n\n".join(parts) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {"volumes": {}, "total_changed_entries": 0}

    all_before: list[str] = []
    all_after: list[str] = []

    for volume in range(1, 4):
        source_path = SOURCE_DIR / f"vol{volume}-voice-366-days.json"
        records = json.loads(source_path.read_text(encoding="utf-8"))
        polished = copy.deepcopy(records)
        counter: Counter[str] = Counter()
        changed_entries = 0
        changed_fields = 0
        examples: list[dict[str, object]] = []

        for original, revised in zip(records, polished, strict=True):
            if volume == 1 and original["day"] == 2:
                continue

            entry_changed = False
            for field in TEXT_FIELDS:
                if field == "body":
                    revised_body: list[str] = []
                    for paragraph_index, paragraph in enumerate(original[field]):
                        key = f"v{volume}:d{original['day']}:{field}:{paragraph_index}"
                        new_paragraph = polish_text(paragraph, key, counter)
                        revised_body.append(new_paragraph)
                        if new_paragraph != paragraph:
                            changed_fields += 1
                            entry_changed = True
                            if len(examples) < 12:
                                examples.append(
                                    {
                                        "day": original["day"],
                                        "field": f"body[{paragraph_index}]",
                                        "before": paragraph,
                                        "after": new_paragraph,
                                    }
                                )
                    revised[field] = revised_body
                else:
                    key = f"v{volume}:d{original['day']}:{field}"
                    new_text = polish_text(original[field], key, counter)
                    revised[field] = new_text
                    if new_text != original[field]:
                        changed_fields += 1
                        entry_changed = True
                        if len(examples) < 12:
                            examples.append(
                                {
                                    "day": original["day"],
                                    "field": field,
                                    "before": original[field],
                                    "after": new_text,
                                }
                            )

            if entry_changed:
                changed_entries += 1

        output_path = OUTPUT_DIR / f"vol{volume}-polished-366-days.json"
        output_path.write_text(
            json.dumps(polished, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        before_text = corpus_text(records)
        after_text = corpus_text(polished)
        (QUALITY_DIR / f"vol{volume}-before.txt").write_text(before_text, encoding="utf-8")
        (QUALITY_DIR / f"vol{volume}-after.txt").write_text(after_text, encoding="utf-8")
        all_before.append(before_text)
        all_after.append(after_text)

        report["volumes"][str(volume)] = {
            "entries": len(records),
            "changed_entries": changed_entries,
            "changed_fields": changed_fields,
            "replacement_frames": dict(sorted(counter.items())),
            "examples": examples,
        }
        report["total_changed_entries"] += changed_entries

    (QUALITY_DIR / "all-volumes-before.txt").write_text("\n".join(all_before), encoding="utf-8")
    (QUALITY_DIR / "all-volumes-after.txt").write_text("\n".join(all_after), encoding="utf-8")
    (QUALITY_DIR / "voice-polish-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
