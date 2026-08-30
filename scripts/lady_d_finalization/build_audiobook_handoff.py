#!/usr/bin/env python3
"""Build provider-neutral audiobook manifests from the polished trilogy."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public/downloads/lady-d-finalization/audiobook"
SOURCE_OUT = ROOT / "output/audiobook"

VOLUMES = {
    1: {
        "title": "Surrendering to God's Love",
        "lane": "God the Father",
        "html": "volume-1-surrendering-to-gods-love-polished-devotional.html",
    },
    2: {
        "title": "Walking with Jesus",
        "lane": "Jesus the Son",
        "html": "volume-2-walking-with-jesus-polished-devotional.html",
    },
    3: {
        "title": "Filled with the Holy Spirit",
        "lane": "The Holy Spirit",
        "html": "volume-3-filled-with-the-holy-spirit-polished-devotional.html",
    },
}


def class_set(attrs: list[tuple[str, str | None]]) -> set[str]:
    value = dict(attrs).get("class") or ""
    return set(value.split())


class DevotionalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str]]] = []
        self.section: str | None = None
        self.records: dict[str, dict[str, object]] = {}
        self.body_index: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = class_set(attrs)
        if tag == "section":
            identifier = dict(attrs).get("id")
            self.section = identifier if identifier and re.fullmatch(r"d[AB]\d+", identifier) else None
            if self.section:
                self.records.setdefault(self.section, {"meta": "", "scripture": "", "reference": "", "body": [], "carry": "", "prayer": ""})
        self.stack.append((tag, classes))
        if self.section and self.section.startswith("dB") and tag == "p" and self._ancestor_has("body"):
            record = self.records[self.section]
            body = record["body"]
            assert isinstance(body, list)
            body.append("")
            self.body_index = len(body) - 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "section":
            self.section = None
        if tag == "p":
            self.body_index = None
        if self.stack:
            self.stack.pop()

    def _ancestor_has(self, class_name: str) -> bool:
        return any(class_name in classes for _, classes in self.stack)

    def _current_has(self, class_name: str) -> bool:
        return bool(self.stack and class_name in self.stack[-1][1])

    def handle_data(self, data: str) -> None:
        if not self.section or not data.strip():
            return
        record = self.records[self.section]
        text = re.sub(r"\s+", " ", data)
        if self.section.startswith("dA"):
            if self._current_has("meta") or self._ancestor_has("meta"):
                record["meta"] = str(record["meta"]) + text
            elif self._current_has("txt") and self._ancestor_has("anchor"):
                record["scripture"] = str(record["scripture"]) + text
            elif self._current_has("ref") and self._ancestor_has("anchor"):
                record["reference"] = str(record["reference"]) + text
        else:
            if self.body_index is not None and self._ancestor_has("body"):
                body = record["body"]
                assert isinstance(body, list)
                body[self.body_index] += text
            elif self._current_has("carry"):
                record["carry"] = str(record["carry"]) + text
            elif self._current_has("prayer") or self._ancestor_has("prayer"):
                record["prayer"] = str(record["prayer"]) + text


def slug(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return clean[:56].rstrip("-")


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCE_OUT.mkdir(parents=True, exist_ok=True)
    summaries = []

    for volume, config in VOLUMES.items():
        polished = json.loads((ROOT / f"source/finalization/polished/vol{volume}-polished-366-days.json").read_text())
        enrichment = json.loads((ROOT / f"source/finalization/enrichment/vol{volume}-enrichment-366-days.json").read_text())
        by_day = {record["day"]: record for record in polished}
        enrichment_by_day = {record["day"]: record for record in enrichment}

        parser = DevotionalParser()
        html_path = ROOT / "public/downloads/lady-d-finalization" / config["html"]
        parser.feed(html_path.read_text())

        tracks = []
        total_words = 0
        total_seconds = 0
        for day in list(range(1, 60)) + [0] + list(range(60, 366)):
            source = by_day[day]
            page_id = 60 if day == 0 else day if day < 60 else day + 1
            page_a = parser.records[f"dA{page_id}"]
            page_b = parser.records[f"dB{page_id}"]
            body = [clean(value) for value in source["body"]]
            carry = clean(source["closing"])
            prayer = clean(source["prayer"])
            scripture = clean(page_a["scripture"])
            reference = clean(page_a["reference"])
            meta = clean(page_a["meta"])
            meta_parts = [part.strip() for part in meta.split("·")]
            calendar = meta_parts[1] if len(meta_parts) > 1 else ("February 29" if day == 0 else f"Day {day}")
            month = calendar.split()[0]
            narration = [source["title"], reference, scripture, *body, carry, prayer]
            words = sum(len(re.findall(r"\b[\w']+\b", part)) for part in narration)
            seconds = round(words / 145 * 60 + 16)
            order = len(tracks) + 1
            day_token = "leap-day" if day == 0 else f"day-{day:03d}"
            filename = f"{order:03d}-{day_token}-{slug(source['title'])}.wav"
            enrichment_record = enrichment_by_day.get(day, {})
            tracks.append({
                "order": order,
                "day": day,
                "calendar_date": calendar,
                "month": month,
                "title": source["title"],
                "scripture_reference": reference,
                "scripture_text": scripture,
                "translation": "KJV",
                "body": body,
                "carry_line": carry,
                "prayer": prayer,
                "pronunciation_editor_note": {
                    "language": enrichment_record.get("lens_lang"),
                    "transliteration": enrichment_record.get("lens_translit"),
                    "source_script": enrichment_record.get("lens_script"),
                    "status": "editorial aid; confirm before voiced inclusion",
                },
                "estimated_words": words,
                "estimated_seconds_at_145_wpm": seconds,
                "source_filename": filename,
                "stitch_group": month.lower(),
            })
            total_words += words
            total_seconds += seconds

        manifest = {
            "schema": "lady-d.audiobook-manifest/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "volume": volume,
            "title": config["title"],
            "author": "Susan 'Lady D' Damon",
            "lane": config["lane"],
            "track_count": len(tracks),
            "estimated_words": total_words,
            "estimated_finished_hours": round(total_seconds / 3600, 2),
            "preferred_release_structure": "opening credits, 12 monthly chapter files, February 29 bonus, closing credits",
            "source_chunk_structure": "one lossless WAV per devotional day before monthly stitching",
            "release_boundary": "No audio synthesized. AI/TTS output is preview-only unless the author consents and the chosen distributor explicitly authorizes it.",
            "tracks": tracks,
        }
        payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        filename = f"lady-d-volume-{volume}-audiobook-manifest.json"
        (OUT / filename).write_text(payload)
        (SOURCE_OUT / filename).write_text(payload)
        summaries.append({
            "volume": volume,
            "title": config["title"],
            "tracks": len(tracks),
            "words": total_words,
            "hours": round(total_seconds / 3600, 2),
        })

    blueprint = f"""# Lady D Audiobook Production Blueprint

## Current Boundary

The manuscripts are audio-ready, but this package does not claim that release
audio has been synthesized, narrated, mastered, or accepted by a distributor.
The three JSON manifests provide 366 day-level source chunks per volume with the
KJV passage, polished devotion, carry line, prayer, filename, duration estimate,
month stitching group, and original-language pronunciation editor note.

As of April 15, 2026, ACX states that submitted audiobooks must be narrated by a
human unless otherwise authorized, and that unauthorized TTS, AI, or automated
recordings are prohibited. It also requires one chapter or section per upload
file, with separate opening and closing credits. Re-check the live requirements
before production and again before upload:

- https://help.acx.com/s/article/what-are-the-acx-audio-submission-requirements
- https://help.acx.com/s/article/upload-audio-files

## Recommended Production Lanes

### Lane A - Human release master

Lady D or a selected narrator records the approved manuscript. This is the
default public-release lane. Record a 15-minute checkpoint first, then secure
Lady D's written approval of voice, cadence, pronunciation, and emotional tone.

### Lane B - Explicitly authorized voice replica

Only use a replica of Lady D's voice after separate, informed written consent
that names the provider, permitted titles, permitted distribution channels,
retention policy, and revocation process. Confirm that the chosen distributor
authorizes that method before production. Consent to publish the books is not
consent to clone the author's voice.

### Lane C - Synthetic preview or app edition

GPT Voice, Gemini Live, Grok Voice, Hermes, or OpenClaw may create internal
timing studies or app previews where provider terms and author consent permit.
Do not relabel preview audio as an ACX-ready release master.

## Narration Direction

- Warm, grounded, intimate, and assured; never announcer-like.
- Target about 140-148 spoken words per minute before pauses.
- Let the Scripture reference settle, then read the verse with clean diction.
- Teach the second paragraph with clarity, not theatrical emphasis.
- Name concrete burdens without rushing them.
- Let each triadic send-off build gently; do not make every sentence peak.
- Give the carry line a full beat before the prayer.
- Pray as invitation, not performance.

## Daily Chunk Order

1. Day number and title.
2. Scripture reference and KJV text.
3. Four-paragraph devotional reading.
4. Carry line.
5. Prayer.
6. Two seconds of clean room tone.

Root-word and correlative-thread material remains available to the editor but is
not in the default spoken sequence. It can become a separate expanded or app
edition after pronunciation review.

## Stitching Plan

- Record or synthesize one lossless day chunk at a time.
- Keep source intermediates at 48 kHz / 24-bit WAV until final mastering.
- Keep opening credits, each monthly section, February 29 bonus, and closing
  credits as distinct deliverables.
- Use filenames from the manifests so retries remain deterministic.
- Generate a silence/peak/length report before stitching.
- Stitch only approved day chunks; never patch a rejected sentence invisibly.
- Master against the current target distributor's live technical requirements,
  then run that distributor's analysis/QA tool.

## Approval Gates

1. Author approves a 15-minute voice and pacing checkpoint.
2. Scripture references and proper-name pronunciations are spot checked.
3. Every day matches its manifest and has no missing or duplicated text.
4. Monthly joins contain no clicks, truncated breath, or repeated room tone.
5. Loudness, peaks, noise floor, encoding, and chapter labels pass the current
   distributor tool.
6. Lady D approves the complete human-listening proof before upload.

## Estimated Scope

| Volume | Day chunks | Estimated finished hours |
|---|---:|---:|
"""
    for summary in summaries:
        blueprint += f"| {summary['volume']} - {summary['title']} | {summary['tracks']} | {summary['hours']} |\n"
    blueprint += "\nEstimates use 145 words per minute plus a modest fixed pause allowance. Actual human performance will vary.\n"

    (OUT / "Lady-D-Audiobook-Production-Blueprint.md").write_text(blueprint)
    (SOURCE_OUT / "Lady-D-Audiobook-Production-Blueprint.md").write_text(blueprint)
    print(json.dumps({"status": "passed", "volumes": summaries}, indent=2))


if __name__ == "__main__":
    main()
