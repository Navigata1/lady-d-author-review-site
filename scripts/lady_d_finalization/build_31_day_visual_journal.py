#!/usr/bin/env python3
"""Build Lady D's concise 31-page visual journal and its scene-production console."""

from __future__ import annotations

import html
import json
import re
import shutil
import zipfile
from pathlib import Path


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
    judge_path = ROOT / "quality/31-day-visual-journal-v2/editorial-judge.json"
    judge_passed = False
    if judge_path.exists():
        judge_passed = json.loads(judge_path.read_text(encoding="utf-8")).get("status") == "PASS"
    with zipfile.ZipFile(KJV_ZIP) as archive:
        for day in plan["days"]:
            full_verse = load_verse(archive, day["reference"])
            verify_excerpt(day["scriptureExcerpt"], full_verse, day["reference"])
            art_relative = f"assets/lady-d-31-visual-journal-v2/scenes/day-{day['day']:02d}.jpg"
            art_path = ROOT / art_relative
            day["scriptureFull"] = full_verse
            day["translation"] = "KJV"
            day["art"] = art_relative
            if art_path.exists() and judge_passed:
                day["artStatus"] = "internally-qualified-author-review"
            elif art_path.exists():
                day["artStatus"] = "generated-awaiting-gauntlet"
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
    return f'''<section class="journal-page {esc(text_class(day['textZone']))} {esc(tone)} family-{esc(family)}" style="--art:url('{esc(art)}');--accent:{esc(day['palette'][1])};--ink:{esc(day['palette'][4])}" data-day="{day['day']}" data-art-status="{esc(day['artStatus'])}">
  <div class="art" role="img" aria-label="{esc(day['title'])} visual scene"></div>
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
    pages = "\n".join(render_page(day) for day in corpus["days"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(corpus['title'])} | Lady D</title>
<style>
@font-face{{font-family:Fraunces;src:url('assets/fonts/fraunces-regular.ttf') format('truetype');font-weight:400;font-display:swap}}@font-face{{font-family:Fraunces;src:url('assets/fonts/fraunces-semibold.ttf') format('truetype');font-weight:600;font-display:swap}}@font-face{{font-family:Fraunces;src:url('assets/fonts/fraunces-bold.ttf') format('truetype');font-weight:700;font-display:swap}}@font-face{{font-family:Pinyon;src:url('assets/fonts/pinyon-script.ttf') format('truetype');font-display:swap}}@font-face{{font-family:Inter;src:url('assets/fonts/inter-regular.ttf') format('truetype');font-weight:400;font-display:swap}}@font-face{{font-family:Inter;src:url('assets/fonts/inter-semibold.ttf') format('truetype');font-weight:600;font-display:swap}}@font-face{{font-family:Inter;src:url('assets/fonts/inter-extrabold.ttf') format('truetype');font-weight:800;font-display:swap}}
:root{{--green:#173d34;--gold:#c99a45;--paper:#f8f1e5}}*{{box-sizing:border-box}}html{{background:#17251f}}body{{margin:0;color:#17233d;background:#e8e3dc;font-family:Inter,Arial,sans-serif}}.toolbar{{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:10px;padding:11px 16px;color:#fff;background:#102d27;border-bottom:1px solid rgba(255,255,255,.15)}}.toolbar strong{{margin-right:auto;font-family:Fraunces,Georgia,serif}}.toolbar a{{color:#fff;text-decoration:none;font-size:12px;font-weight:750}}.hero{{display:grid;place-items:center;min-height:440px;padding:64px 24px;color:#fff;text-align:center;background:linear-gradient(135deg,rgba(17,58,47,.96),rgba(81,48,75,.82)),url('assets/lady-d-31-visual-journal-v2/scenes/day-22.jpg') center/cover}}.hero-inner{{max-width:790px}}.hero .eyebrow{{margin:0;color:#efcf87;font-size:11px;font-weight:900;text-transform:uppercase}}.hero h1{{margin:10px 0 14px;font:600 clamp(42px,8vw,76px)/.96 Fraunces,Georgia,serif}}.hero p{{margin:0 auto;max-width:680px;font:18px/1.6 Georgia,serif}}.hero small{{display:block;margin-top:16px;color:#dce8e2}}.book{{padding:28px 0 70px}}.journal-page{{position:relative;width:6in;height:9in;margin:20px auto;overflow:hidden;background:#1c2e29;box-shadow:0 22px 60px rgba(15,31,25,.25);break-after:page;page-break-after:always}}.art{{position:absolute;inset:0;background-image:var(--art);background-position:center;background-size:cover}}.scrim{{position:absolute;inset:0;pointer-events:none}}.copy{{position:absolute;z-index:3;width:3.35in;max-width:58%;padding:.24in .27in .28in}}.upper-left .copy{{top:.45in;left:.42in}}.upper-right .copy{{top:.45in;right:.42in}}.upper-center .copy{{top:.38in;left:50%;width:4.7in;max-width:78%;transform:translateX(-50%);text-align:center}}.left .copy{{top:1.32in;left:.38in}}.right .copy{{top:1.28in;right:.38in}}.lower-left .copy{{bottom:.55in;left:.4in}}.dark-copy .scrim{{background:linear-gradient(90deg,rgba(250,246,236,.96) 0,rgba(250,246,236,.78) 49%,rgba(250,246,236,0) 76%)}}.dark-copy.upper-right .scrim,.dark-copy.right .scrim{{background:linear-gradient(270deg,rgba(250,246,236,.96) 0,rgba(250,246,236,.78) 49%,rgba(250,246,236,0) 76%)}}.dark-copy.upper-center .scrim{{background:linear-gradient(180deg,rgba(250,246,236,.95) 0,rgba(250,246,236,.72) 38%,rgba(250,246,236,0) 68%)}}.dark-copy.lower-left .scrim{{background:linear-gradient(0deg,rgba(21,35,49,.92),rgba(21,35,49,.7) 43%,transparent 70%)}}.light-copy .copy,.dark-copy.lower-left .copy{{color:#fff;text-shadow:0 2px 14px rgba(0,0,0,.5)}}.light-copy .scrim{{background:linear-gradient(90deg,rgba(12,26,39,.88),rgba(12,26,39,.56) 48%,transparent 78%)}}.light-copy.upper-right .scrim{{background:linear-gradient(270deg,rgba(12,26,39,.88),rgba(12,26,39,.56) 48%,transparent 78%)}}.light-copy.upper-center .scrim{{background:linear-gradient(180deg,rgba(12,26,39,.85),rgba(12,26,39,.52) 42%,transparent 72%)}}.day-label{{margin:0;color:var(--accent);font-size:8pt;font-weight:900;letter-spacing:.18em;text-transform:uppercase}}.copy h2{{margin:.04in 0 .1in;font:600 28pt/.92 Fraunces,Georgia,serif;letter-spacing:0}}.copy h2::first-line{{font-style:italic}}.encouragement{{margin:0 0 .14in;font:10.2pt/1.42 Georgia,serif}}blockquote{{margin:0;padding:.12in .14in;background:color-mix(in srgb,var(--accent) 82%,#513761);color:#fff;clip-path:polygon(2% 0,99% 3%,97% 96%,0 100%);font:italic 10pt/1.35 Georgia,serif}}blockquote p{{margin:0}}blockquote cite{{display:block;margin-top:.06in;font:7pt/1.2 Inter,Arial,sans-serif;font-style:normal;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}blockquote cite b{{color:#f4d580}}.prayer{{margin:.13in 0 0;font:8.2pt/1.38 Georgia,serif}}.prayer span{{display:block;margin-bottom:.025in;color:var(--accent);font:800 6.5pt/1 Inter,Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase}}.affirmation{{display:inline-block;margin:.12in 0 0;padding:.06in .1in;color:#fff;background:#173d34;font:italic 9pt/1.25 Georgia,serif;clip-path:polygon(0 8%,97% 0,100% 88%,3% 100%)}}footer{{position:absolute;z-index:3;left:.28in;right:.28in;bottom:.17in;display:flex;justify-content:space-between;gap:12px;color:rgba(255,255,255,.86);font-size:6pt;font-weight:800;text-shadow:0 1px 5px #000;text-transform:uppercase}}.proof-flag{{position:absolute;z-index:6;top:.18in;right:.18in;padding:5px 8px;color:#fff;background:#8a2f3a;font-size:7pt;font-weight:900;text-transform:uppercase}}@media(max-width:680px){{.toolbar{{font-size:11px}}.toolbar a:nth-of-type(2){{display:none}}.hero{{min-height:360px}}.journal-page{{width:min(calc(100vw - 20px),6in);height:auto;aspect-ratio:2/3}}.journal-page .copy{{max-width:76%;transform:scale(.82);transform-origin:top left}}.upper-right .copy,.right .copy{{transform-origin:top right}}.journal-page.upper-center .copy{{max-width:82%;transform:translateX(-50%) scale(.82);transform-origin:top center}}}}@media print{{@page{{size:6in 9in;margin:0}}body{{background:#fff;print-color-adjust:exact;-webkit-print-color-adjust:exact}}.toolbar,.hero{{display:none}}.book{{padding:0}}.journal-page{{width:6in;height:9in;margin:0;box-shadow:none}}.proof-flag{{display:none}}}}
</style></head><body>
<nav class="toolbar"><strong>Thirty-One Mornings of Light</strong><a href="/">Publishing home</a><a href="lady-d-31-day-motion.html">Motion demonstration</a><a href="{CONSOLE_NAME}">Scene console</a></nav>
<header class="hero"><div class="hero-inner"><p class="eyebrow">The concise visual journal</p><h1>Thirty-One Mornings of Light</h1><p>One image. One message. One Scripture. One prayer. Thirty-one distinct moments of hope designed to be felt quickly and carried all day.</p><small>This replaces the long-form proof as the intended print experience. The earlier motion edition remains available as a separate demonstration.</small></div></header>
<main class="book">{pages}</main></body></html>'''


def render_console(corpus: dict) -> str:
    cards = []
    for day in corpus["days"]:
        art_exists = (ROOT / day["art"]).exists()
        preview = f'<img src="{esc(day["art"])}" alt="Day {day["day"]} generated scene">' if art_exists else '<div class="empty">Awaiting generation</div>'
        status = "Internally qualified; author review" if day["artStatus"] == "internally-qualified-author-review" else ("Generated, gauntlet pending" if art_exists else "Awaiting generation")
        cards.append(
            f'''<article class="scene" id="day-{day['day']:02d}"><div class="preview">{preview}</div><div class="scene-copy"><p class="eyebrow">Day {day['day']:02d} &middot; {esc(MOVEMENT_NAMES[day['movement']])}</p><h2>{esc(day['title'])}</h2><p>{esc(day['encouragement'])}</p><dl><div><dt>Scene family</dt><dd>{esc(day['sceneFamily'])}</dd></div><div><dt>Status</dt><dd>{esc(status)}</dd></div><div><dt>Text zone</dt><dd>{esc(day['textZone'])}</dd></div></dl><details><summary>Generation prompt</summary><pre>{esc(day['prompt'])}</pre></details></div></article>'''
        )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lady D 31-Scene Production Console</title><style>
*{{box-sizing:border-box}}body{{margin:0;color:#202a24;background:#f5f1e9;font-family:Inter,system-ui,sans-serif}}header{{padding:70px 24px;color:#fff;background:#153f34}}header div,main{{width:min(1180px,calc(100% - 36px));margin:auto}}h1,h2{{font-family:Georgia,serif}}h1{{margin:8px 0;font-size:clamp(42px,7vw,76px)}}header p{{max-width:760px;line-height:1.6}}.eyebrow{{margin:0;color:#bd9148;font-size:11px;font-weight:900;letter-spacing:.12em;text-transform:uppercase}}header .eyebrow{{color:#efd18d}}main{{padding:36px 0 80px}}.scene{{display:grid;grid-template-columns:260px 1fr;margin-bottom:22px;border:1px solid #d9d0c2;background:#fff;box-shadow:0 8px 25px rgba(20,45,35,.07)}}.preview{{min-height:390px;background:#d9ded9}}.preview img{{display:block;width:100%;height:100%;object-fit:cover}}.empty{{display:grid;place-items:center;height:100%;padding:20px;color:#6c746e;text-align:center}}.scene-copy{{padding:28px}}.scene h2{{margin:5px 0 12px;font-size:30px}}.scene-copy>p:not(.eyebrow){{line-height:1.6}}dl{{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}}dl div{{padding:9px 12px;background:#f4eee4}}dt{{color:#796e60;font-size:10px;font-weight:900;text-transform:uppercase}}dd{{margin:3px 0 0;font-size:12px;font-weight:750}}details{{border-top:1px solid #ddd3c5;padding-top:15px}}summary{{cursor:pointer;font-weight:850}}pre{{overflow:auto;white-space:pre-wrap;font:12px/1.6 ui-monospace,monospace}}@media(max-width:680px){{.scene{{grid-template-columns:1fr}}.preview{{height:520px}}}}
</style></head><body><header><div><p class="eyebrow">Generation &middot; qualification &middot; decision</p><h1>31-Scene Production Console</h1><p>Every day receives its own text-free visual generation. A scene is not final until it clears message fidelity, composition, anatomy, typography-zone, brightness, diversity, and print-resolution gates.</p></div></header><main>{''.join(cards)}</main></body></html>'''


def write_mirrors(name: str, content: str) -> None:
    (ROOT / name).write_text(content, encoding="utf-8")
    (PUBLIC / name).write_text(content, encoding="utf-8")


def sync_assets() -> None:
    destination = PUBLIC / "assets/lady-d-31-visual-journal-v2"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    source_scenes = ASSET_DIR / "scenes"
    if source_scenes.exists():
        shutil.copytree(source_scenes, destination / "scenes")


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
