#!/usr/bin/env python3
"""Build Lady D's concise 31-page visual journal and its scene-production console."""

from __future__ import annotations

import html
import json
import re
import shutil
import zipfile
from pathlib import Path

import journal_presentation as presentation


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source/finalization/31-day-visual-journal-v2"
PLAN_PATH = SOURCE / "visual-journal-plan.json"
CORPUS_PATH = SOURCE / "visual-journal.json"
KJV_ZIP = ROOT / "source/scripture/eng-kjv2006_usfm.zip"
ASSET_DIR = ROOT / "assets/lady-d-31-visual-journal-v2"
PUBLIC = ROOT / "public"
DOWNLOADS = ROOT / "downloads/lady-d-finalization"

PAGE_NAME = "lady-d-31-day-visual-journal.html"
CONSOLE_NAME = "lady-d-31-day-visual-journal-scene-console.html"
DOWNLOAD_JSON = "Lady-D-31-Day-Visual-Journal-Source.json"

BOOK_FILES = {
    "Genesis": "02-GENeng-kjv2006.usfm",
    "Exodus": "03-EXOeng-kjv2006.usfm",
    "Deuteronomy": "06-DEUeng-kjv2006.usfm",
    "Psalm": "20-PSAeng-kjv2006.usfm",
    "Isaiah": "24-ISAeng-kjv2006.usfm",
    "Zechariah": "39-ZECeng-kjv2006.usfm",
    "Matthew": "70-MATeng-kjv2006.usfm",
    "Mark": "71-MRKeng-kjv2006.usfm",
    "Luke": "72-LUKeng-kjv2006.usfm",
    "John": "73-JHNeng-kjv2006.usfm",
    "Acts": "74-ACTeng-kjv2006.usfm",
    "Romans": "75-ROMeng-kjv2006.usfm",
    "Galatians": "78-GALeng-kjv2006.usfm",
    "Ephesians": "79-EPHeng-kjv2006.usfm",
    "Philippians": "80-PHPeng-kjv2006.usfm",
    "2 Timothy": "85-2TIeng-kjv2006.usfm",
    "1 Peter": "90-1PEeng-kjv2006.usfm",
}

MOVEMENT_NAMES = {1: "Held", 2: "Led", 3: "Filled", 4: "Carried Forward"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def normalize(value: str) -> str:
    value = value.replace("LORD'S", "LORDs")
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def clean_usfm(value: str) -> str:
    value = re.sub(r"\\f .*?\\f\*", "", value, flags=re.DOTALL)
    value = re.sub(r"\\x .*?\\x\*", "", value, flags=re.DOTALL)
    value = re.sub(r"\\(?:\+?w) ([^|\\]+?)(?:\|[^\\]+)?\\(?:\+?w)\*", r"\1", value)
    value = re.sub(r"\\(?:add|nd|wj)\s*", "", value)
    value = re.sub(r"\\(?:add|nd|wj)\*", "", value)
    value = re.sub(r"\\[a-zA-Z0-9+]+\*?(?:\s+)?", " ", value)
    value = value.replace("¶", "")
    return re.sub(r"\s+", " ", value).strip()


def parse_reference(reference: str) -> tuple[str, int, int]:
    match = re.fullmatch(r"(.+?)\s+(\d+):(\d+)", reference)
    if not match:
        raise ValueError(f"unsupported Scripture reference: {reference}")
    return match.group(1), int(match.group(2)), int(match.group(3))


def load_verse(archive: zipfile.ZipFile, reference: str) -> str:
    book, chapter, verse = parse_reference(reference)
    if book not in BOOK_FILES:
        raise ValueError(f"book not mapped for KJV verification: {book}")
    document = archive.read(BOOK_FILES[book]).decode("utf-8")
    chapter_match = re.search(
        rf"^\\c\s+{chapter}\s*$([\s\S]*?)(?=^\\c\s+\d+\s*$|\Z)",
        document,
        flags=re.MULTILINE,
    )
    if not chapter_match:
        raise ValueError(f"chapter not found: {reference}")
    verse_match = re.search(
        rf"^\\v\s+{verse}\s+([\s\S]*?)(?=^\\v\s+\d+\s+|\Z)",
        chapter_match.group(1),
        flags=re.MULTILINE,
    )
    if not verse_match:
        raise ValueError(f"verse not found: {reference}")
    return clean_usfm(verse_match.group(1))


def verify_excerpt(excerpt: str, full_verse: str, reference: str) -> None:
    pieces = [normalize(piece) for piece in re.split(r"\.{3}|…", excerpt) if normalize(piece)]
    normalized_verse = normalize(full_verse)
    cursor = 0
    for piece in pieces:
        position = normalized_verse.find(piece, cursor)
        if position < 0:
            raise ValueError(f"KJV excerpt mismatch at {reference}: {excerpt!r} not in {full_verse!r}")
        cursor = position + len(piece)


def scene_prompt(day: dict) -> str:
    return "\n".join(
        [
            "Use case: " + ("historical-scene" if "historical" in day["sceneFamily"] else "ads-marketing"),
            "Asset type: 6 x 9 portrait visual devotional journal page background",
            f"Day theme: {day['title']}.",
            f"Emotional center: {day['encouragement']}",
            f"Scene/backdrop: {day['scene']}",
            "Style/medium: Premium Christian publishing art with cinematic painterly-photographic realism, tactile detail, mature emotional warmth, natural anatomy, and the visual confidence of a finished gift-book page. The supplied reference pages guide richness and immediacy only; do not copy them.",
            f"Composition/framing: Vertical 2:3 portrait. Keep the designated {day['textZone']} typography zone visually calm and unobstructed while the rest of the frame tells a complete story.",
            "Lighting/mood: Luminous, hopeful, emotionally honest, peaceful without becoming bland. Use strategic shadow to make the light feel pure and earned.",
            "Color palette: " + ", ".join(day["palette"]) + ".",
            "Constraints: Generate artwork only. Absolutely no text, letters, numbers, logos, labels, signs, watermarks, pseudo-writing, or readable marks anywhere. Keep people dignified, modestly clothed, age-appropriate, and anatomically natural. Print-safe focal clarity.",
            "Avoid: copied layouts, generic stock worship poses, plastic faces, malformed hands, extra fingers or limbs, bleak grading, giant glowing crosses, illegible decorative text, and clutter inside the typography zone.",
        ]
    )


def build_corpus() -> dict:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if len(plan["days"]) != 31:
        raise ValueError("the visual journal requires exactly 31 days")
    with zipfile.ZipFile(KJV_ZIP) as archive:
        for day in plan["days"]:
            full_verse = load_verse(archive, day["reference"])
            verify_excerpt(day["scriptureExcerpt"], full_verse, day["reference"])
            art_relative = f"assets/lady-d-31-visual-journal-v2/scenes/day-{day['day']:02d}.jpg"
            art_path = ROOT / art_relative
            day["scriptureFull"] = full_verse
            day["translation"] = "KJV"
            day["art"] = art_relative
            if art_path.exists():
                day["artStatus"] = "generated-author-review"
            else:
                day["artStatus"] = "awaiting-generation"
            day["prompt"] = scene_prompt(day)
    corpus = {
        key: plan[key]
        for key in ("schema", "title", "subtitle", "author", "productIntent", "referencePolicy", "artPolicy", "movements")
    }
    corpus["schema"] = "idc.lady_d_31_day_visual_journal/v2"
    corpus["days"] = plan["days"]
    CORPUS_PATH.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return corpus


def text_class(zone: str) -> str:
    return zone.replace(" ", "-")


def render_page(day: dict) -> str:
    family = day["sceneFamily"]
    tone = "light-copy" if family in {"light-and-darkness", "cosmic-symbolic", "storm-to-peace"} or day["day"] in {15, 17, 23} else "dark-copy"
    existing = (ROOT / day["art"]).exists()
    art = day["art"] if existing else "assets/lady-d-31-day/movements/movement-1.jpg"
    missing = "" if existing else '\n  <span class="proof-flag">Scene pending</span>'
    return f'''<section id="day-{day['day']:02d}" class="journal-page {esc(text_class(day['textZone']))} {esc(tone)} family-{esc(family)}" style="--art:url('{esc(art)}');--accent:{esc(day['palette'][1])};--ink:{esc(day['palette'][4])}" data-day="{day['day']}" data-art-status="{esc(day['artStatus'])}">
  <div class="art" role="img" aria-label="{esc(day['scene'].split('. ')[0])}" style="background-image:url('{esc(art)}')"></div>
  <div class="scrim"></div>{missing}
  <article class="copy">
    <p class="day-label">Day {day['day']:02d}</p>
    <h2>{esc(day['title'])}</h2>
    <p class="encouragement">{esc(day['encouragement'])}</p>
    <blockquote><p>{esc(day['scriptureExcerpt'])}</p><cite>{esc(day['reference'])} <b>KJV</b></cite></blockquote>
    <p class="prayer"><span>Prayer</span>{esc(day['prayer'])}</p>
    <p class="affirmation">{esc(day['affirmation'])}</p>
  </article>
  <footer><span>Thirty-One Mornings of Light</span><span>Susan &ldquo;Lady D&rdquo; Damon</span></footer>
</section>'''


def render_journal(corpus: dict) -> str:
    return presentation.render_journal(corpus, "\n".join(render_page(day) for day in corpus["days"]))


def render_console(corpus: dict) -> str:
    return presentation.render_console(corpus)


def write_mirrors(name: str, content: str) -> None:
    (ROOT / name).write_text(content, encoding="utf-8")
    (PUBLIC / name).write_text(content, encoding="utf-8")


def sync_assets() -> None:
    destination = PUBLIC / "assets/lady-d-31-visual-journal-v2"
    destination.mkdir(parents=True, exist_ok=True)
    source_scenes = ASSET_DIR / "scenes"
    if source_scenes.exists():
        shutil.copytree(source_scenes, destination / "scenes", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets/lady-d-reader", PUBLIC / "assets/lady-d-reader", dirs_exist_ok=True)


def main() -> None:
    corpus = build_corpus()
    sync_assets()
    write_mirrors(PAGE_NAME, render_journal(corpus))
    write_mirrors(CONSOLE_NAME, render_console(corpus))
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CORPUS_PATH, DOWNLOADS / DOWNLOAD_JSON)
    public_downloads = PUBLIC / "downloads/lady-d-finalization"
    public_downloads.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CORPUS_PATH, public_downloads / DOWNLOAD_JSON)
    generated = sum(1 for day in corpus["days"] if (ROOT / day["art"]).exists())
    print(json.dumps({"status": "built", "days": 31, "generatedScenes": generated, "pendingScenes": 31 - generated}, indent=2))


if __name__ == "__main__":
    main()
