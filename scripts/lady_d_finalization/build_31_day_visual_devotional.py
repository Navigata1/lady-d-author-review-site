#!/usr/bin/env python3
"""Build the shared corpus, print proof, motion reader, and scene console for Lady D's 31-day devotional."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source/finalization/31-day"
TEMPLATES = ROOT / "source/finalization/templates"
POLISHED = ROOT / "source/finalization/polished"
KIMI_PACK = ROOT / "source/finalization/kimi/prompt-pack-31day.html"
PUBLIC = ROOT / "public"
DOWNLOADS = ROOT / "downloads/lady-d-finalization"
PUBLIC_DOWNLOADS = PUBLIC / "downloads/lady-d-finalization"
ASSET_ROOT = "assets/lady-d-31-day"

VOLUME_NAMES = {
    0: "Trilogy Culmination",
    1: "Surrendering to God's Love",
    2: "Walking with Jesus",
    3: "Filled with the Holy Spirit",
}

MOVEMENT_ART = {
    1: f"{ASSET_ROOT}/movements/movement-1.jpg",
    2: f"{ASSET_ROOT}/movements/movement-2.jpg",
    3: f"{ASSET_ROOT}/movements/movement-3.jpg",
    4: f"{ASSET_ROOT}/movements/movement-4.jpg",
}

SCENE_FAMILIES = (
    "intimate-devotional-portrait",
    "wonder-landscape",
    "power-of-God",
    "nature-symbol",
    "biblical-symbol",
    "storm-to-peace",
    "light-and-darkness",
)


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def extract(pattern: str, value: str, *, required: bool = True) -> str:
    match = re.search(pattern, value, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        if required:
            raise ValueError(f"missing pattern: {pattern}")
        return ""
    return strip_tags(match.group(1))


def extract_raw(pattern: str, value: str, *, required: bool = True) -> str:
    match = re.search(pattern, value, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        if required:
            raise ValueError(f"missing raw pattern: {pattern}")
        return ""
    return match.group(1)


def source_voice_day(source_day: int) -> int:
    if source_day == 60:
        return 0
    return source_day if source_day < 60 else source_day - 1


def movement_for_day(day: int) -> int:
    if day <= 8:
        return 1
    if day <= 16:
        return 2
    if day <= 24:
        return 3
    return 4


def parse_source_catalog(volume: int) -> dict[int, dict]:
    document = (TEMPLATES / f"vol{volume}-devotional-source.html").read_text(encoding="utf-8")
    polished = json.loads((POLISHED / f"vol{volume}-polished-366-days.json").read_text(encoding="utf-8"))
    voice = {record["day"]: record for record in polished}
    catalog: dict[int, dict] = {}
    for source_day in range(1, 367):
        section_match = re.search(
            rf'<section class="leaf [^"]*" id="dA{source_day}">(.*?)</section>',
            document,
            flags=re.DOTALL,
        )
        if not section_match:
            raise ValueError(f"volume {volume} is missing source day {source_day}")
        section = section_match.group(1)
        record = voice[source_voice_day(source_day)]
        meta = extract(r'<div class="meta">(.*?)</div>', section)
        anchor = extract_raw(r'<blockquote class="anchor">(.*?)</blockquote>', section)
        verse = extract(r'<p class="txt [^"]*">(.*?)</p>', anchor)
        reference_line = extract(r'<p class="ref">(.*?)</p>', anchor)
        reference = reference_line.split(" · ", 1)[0]
        translation = "KJV" if "King James Version" in reference_line else "NKJV"
        lens = extract(r'<div class="lens">(.*?)</div>', section)
        thread = extract_raw(r'<div class="thread">(.*?)</div>', section)
        thread_ref = extract(r'<p class="ref">(.*?)</p>', thread).split(" · ", 1)[0]
        thread_text = extract(r'<p class="txt">(.*?)</p>', thread)
        catalog[source_day] = {
            "sourceDay": source_day,
            "sourceMeta": meta,
            "title": record["title"],
            "scripture": {"reference": reference, "translation": translation, "text": verse},
            "lens": lens,
            "thread": {"reference": thread_ref, "text": thread_text},
            "body": record["body"],
            "closing": record["closing"],
            "prayer": record["prayer"],
            "journalReflect": record["journal_reflect"],
            "journalAct": record["journal_act"],
        }
    return catalog


def parse_kimi_visual_specs() -> dict[int, dict]:
    document = KIMI_PACK.read_text(encoding="utf-8")
    cards = re.findall(r'<article class="day-card[^>]*id="day-(\d+)"[^>]*>(.*?)</article>', document, flags=re.DOTALL)
    if len(cards) != 31:
        raise ValueError(f"expected 31 recovered visual specs, found {len(cards)}")
    specs: dict[int, dict] = {}
    for raw_day, card in cards:
        day = int(raw_day)
        palette_block = extract_raw(r'<div class="pal-bar"[^>]*>(.*?)</div>', card)
        palette = re.findall(r'background:\s*(#[0-9a-fA-F]{6})', palette_block)
        motion_block = extract_raw(r'<ul class="motion">(.*?)</ul>', card)
        motion = [strip_tags(item) for item in re.findall(r'<li>(.*?)</li>', motion_block, flags=re.DOTALL)]
        specs[day] = {
            "recoveredTitle": extract(r'class="day-title"[^>]*>(.*?)</h3>', card),
            "environment": extract(r'<span class="flabel">Environment</span>\s*<p>(.*?)</p>', card),
            "palette": palette,
            "typeMood": extract(r'<span class="flabel">Type mood</span>\s*<p[^>]*>(.*?)</p>', card),
            "motion": motion,
            "basePrompt": extract(r'class="prompt-text"[^>]*>(.*?)</p>', card),
        }
    return specs


def day_31() -> dict:
    return {
        "sourceDay": 0,
        "sourceMeta": "Day 31 · Kingdom Light · Trilogy Culmination",
        "title": "The Love That Brings Us Into Fullness",
        "scripture": {
            "reference": "Ephesians 3:19",
            "translation": "KJV",
            "text": "And to know the love of Christ, which passeth knowledge, that ye might be filled with all the fulness of God.",
        },
        "lens": "pleroma · Greek · fullness — not a thin spiritual moment, but a life increasingly occupied and shaped by all that God gives of Himself.",
        "thread": {
            "reference": "2 Corinthians 13:14",
            "text": "The grace of the Lord Jesus Christ, and the love of God, and the communion of the Holy Ghost, be with you all. Amen.",
        },
        "body": [
            "There are seasons when you can name what is missing faster than you can name what God has already poured in. You see the empty chair, the unfinished answer, the tired place, the prayer that still has not opened into daylight. Paul does not finish this prayer by asking God to make His children better at hiding their emptiness. He asks that they would know the love of Christ and be filled with all the fulness of God.",
            "Notice how the whole family of God is gathered inside this prayer. Paul bows before the Father. He asks for strength through the Spirit in the inner person. He prays for Christ to dwell in the heart by faith. Then he reaches for a love so wide, so long, so deep, and so high that knowledge alone cannot hold it. The Father receives you, the Son comes near, and the Spirit makes room in you for what grace has already given.",
            "Maybe these thirty mornings have touched the place where fear, grief, shame, weariness, disappointment, or old self-protection still tries to tell you that you are empty and alone. Beloved, fullness is not pretending those places never existed. It is discovering that none of them is large enough to keep God out. His love can meet the wound without becoming wounded by it. His presence can enter the room you thought would always stay closed.",
            "So carry this journey forward as one who is received, accompanied, and filled. Let the Father's love steady you. Let the footsteps of Jesus lead you. Let the Holy Spirit breathe courage into the next faithful step. No ache is too deep for His love, no road too long for His presence, and no surrendered life too ordinary for His glory. Walk into the morning knowing that the God who brought you this far is still making His home in you.",
        ],
        "closing": "I am received by the Father, accompanied by Jesus, and filled by the Holy Spirit for the next faithful step.",
        "prayer": "Heavenly Father, thank You for receiving me into Your family. Lord Jesus, root me more deeply in the love that passes knowledge. Holy Spirit, strengthen my inner life and fill every surrendered place with the presence of God. Carry what I have learned into the way I speak, serve, forgive, rest, and hope. Make my ordinary life a dwelling place for Your love. In Jesus' name, Amen.",
        "journalReflect": "Where have I mistaken an unfinished place for an empty place, and how have the Father, Son, and Holy Spirit already been meeting me there?",
        "journalAct": "Write three sentences beginning with: 'Father, I receive...'; 'Jesus, I will follow...'; and 'Holy Spirit, fill...'. Keep them where you will see them tomorrow morning.",
    }


def build_corpus() -> dict:
    plan = json.loads((SOURCE / "selection-plan.json").read_text(encoding="utf-8"))
    catalogs = {volume: parse_source_catalog(volume) for volume in (1, 2, 3)}
    visuals = parse_kimi_visual_specs()
    movement_by_id = {item["id"]: item for item in plan["movements"]}
    days = []
    for selected in plan["days"]:
        target_day = selected["targetDay"]
        volume = selected["volume"]
        record = day_31() if volume == 0 else dict(catalogs[volume][selected["sourceDay"]])
        movement = movement_for_day(target_day)
        visual = visuals[target_day]
        visual_prompt = (
            f'{visual["basePrompt"]} The emotional and theological center is "{record["title"]}": '
            f'{record["closing"]} Keep the human figure dignified, modestly clothed, anatomically natural, and secondary to the spiritual landscape. '
            "Reserve clean negative space for separately typeset Scripture and title. Do not render typography inside the image."
        )
        draft_art = f"{ASSET_ROOT}/drafts/day-{target_day:02d}-v1.png"
        if not (ROOT / draft_art).exists():
            draft_art = None
        days.append(
            {
                "day": target_day,
                "movement": movement,
                "movementTitle": movement_by_id[movement]["title"],
                "movementPromise": movement_by_id[movement]["promise"],
                "volume": volume,
                "volumeTitle": VOLUME_NAMES[volume],
                "sourceDay": selected["sourceDay"],
                "selectionReason": selected["reason"],
                **record,
                "visual": {
                    "sceneFamily": SCENE_FAMILIES[(target_day - 1) % len(SCENE_FAMILIES)],
                    "environment": visual["environment"],
                    "palette": visual["palette"],
                    "typeMood": visual["typeMood"],
                    "motion": visual["motion"],
                    "prompt": visual_prompt,
                    "art": f"{ASSET_ROOT}/scenes/day-{target_day:02d}.png",
                    "draftArt": draft_art,
                    "fallbackArt": MOVEMENT_ART[movement],
                    "status": "awaiting-generated-scene",
                },
            }
        )
    return {
        "schema": "idc.lady_d_31_day_visual_devotional/v1",
        "title": plan["title"],
        "subtitle": plan["subtitle"],
        "scripturePolicy": "KJV throughout this production corpus; generated art contains no baked Scripture text.",
        "artPolicy": "Final scene art is qualified separately. Movement key art is a directional fallback, not a claim that all 31 scene renders are complete.",
        "movements": plan["movements"],
        "days": days,
    }


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def json_for_script(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def print_html(corpus: dict) -> str:
    pages = []
    for day in corpus["days"]:
        visual = day["visual"]
        body = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in day["body"])
        pages.append(
            f'''<section class="leaf image-leaf movement-{day['movement']}" style="--scene:url('{esc(visual['fallbackArt'])}')"><div class="image-wash"></div><div class="visual-copy"><p class="dayline">Day {day['day']:02d} &middot; {esc(day['movementTitle'])}</p><h2>{esc(day['title'])}</h2><blockquote>&ldquo;{esc(day['scripture']['text'])}&rdquo;<cite>{esc(day['scripture']['reference'])} &middot; {esc(day['scripture']['translation'])}</cite></blockquote><p class="affirm">{esc(day['closing'])}</p></div><p class="source">From {esc(day['volumeTitle']) if day['volume'] else 'the trilogy culmination'}</p></section>'''
        )
        pages.append(
            f'''<section class="leaf reading-leaf"><header><span>Day {day['day']:02d}</span><span>{esc(day['movementTitle'])}</span></header><div class="reading"><p class="kicker">{esc(day['volumeTitle'])}</p><h2>{esc(day['title'])}</h2><div class="verse"><b>{esc(day['scripture']['reference'])} &middot; {esc(day['scripture']['translation'])}</b><p>{esc(day['scripture']['text'])}</p></div><div class="body">{body}</div><p class="carry">Carry it with you &middot; {esc(day['closing'])}</p></div><footer>{day['day']:02d} &middot; Thirty-One Mornings of Light</footer></section>'''
        )
        pages.append(
            f'''<section class="leaf journal-leaf" style="--scene:url('{esc(visual['fallbackArt'])}')"><header><span>Day {day['day']:02d}</span><span>Carry it with you</span></header><div class="journal"><div class="art-window" role="img" aria-label="Directional art for Day {day['day']:02d}"></div><p class="journal-kicker">Language &middot; Scripture &middot; Response</p><h2>{esc(day['closing'])}</h2><div class="lens"><b>Language lens</b><p>{esc(day['lens'])}</p></div><div class="thread"><b>Correlative Scripture &middot; {esc(day['thread']['reference'])}</b><p>&ldquo;{esc(day['thread']['text'])}&rdquo;</p></div><div class="prayer"><b>Prayer</b><p>{esc(day['prayer'])}</p></div><div class="practice"><div><b>Reflect</b><p>{esc(day['journalReflect'])}</p></div><div><b>Live it</b><p>{esc(day['journalAct'])}</p></div></div><div class="writing-lines" aria-label="Writing space"><i></i><i></i><i></i></div></div><footer>{day['day']:02d} &middot; Thirty-One Mornings of Light</footer></section>'''
        )
    movement_rows = "".join(
        f"<li><b>{esc(item['title'])}</b><span>Days {esc(item['days'])} &middot; {esc(item['promise'])}</span></li>"
        for item in corpus["movements"]
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(corpus['title'])} | Print Production Proof</title><style>
:root{{--ink:#25281f;--green:#163f34;--gold:#b88a39;--wine:#783341;--paper:#fffdf8;--rule:#d8d8cb}}*{{box-sizing:border-box}}body{{margin:0;background:#dfe4df;color:var(--ink);font-family:Georgia,"Times New Roman",serif}}.toolbar{{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;padding:10px 16px;background:#102d27;color:#fff;font-family:Inter,system-ui,sans-serif}}.toolbar a{{color:#fff;text-decoration:none;font-weight:750}}.toolbar span{{margin-right:auto}}.book{{padding:24px 0}}.leaf{{position:relative;width:6in;height:9in;margin:18px auto;overflow:hidden;background:var(--paper);box-shadow:0 18px 50px rgba(20,35,28,.18);break-after:page;page-break-after:always}}.cover{{display:flex;align-items:flex-end;color:#fff;background:#153f34 url('{ASSET_ROOT}/movements/movement-4.jpg') center/cover}}.cover::after,.image-leaf::after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(13,38,31,.03),rgba(13,38,31,.82))}}.cover-copy{{position:relative;z-index:2;padding:.72in}}.cover .kicker,.dayline,.reading .kicker,.journal-kicker{{font-family:Inter,system-ui,sans-serif;font-size:8pt;font-weight:850;letter-spacing:.16em;text-transform:uppercase}}.cover h1{{margin:.08in 0;font-size:36pt;line-height:1.02}}.cover p{{font-size:14pt;line-height:1.35}}.contents{{padding:.68in}}.contents h2{{font-size:28pt;color:var(--green)}}.contents>p{{font-size:12pt;line-height:1.55}}.contents ol{{margin:.35in 0 0;padding:0;list-style:none}}.contents li{{padding:.16in 0;border-top:1px solid var(--rule)}}.contents li b,.contents li span{{display:block}}.contents li span{{margin-top:4px;color:#62685f;font-size:10pt}}.image-leaf{{color:#fff;background:#183d33 center/cover}}.image-leaf::before{{content:"";position:absolute;inset:0;background-image:var(--scene);background-position:center;background-size:cover}}.image-wash{{position:absolute;inset:0;z-index:1;background:linear-gradient(180deg,rgba(14,34,28,.12),rgba(14,34,28,.86) 74%,rgba(14,34,28,.94))}}.visual-copy{{position:absolute;z-index:3;left:.55in;right:.55in;bottom:.66in}}.dayline{{color:#f2d88e}}.visual-copy h2{{max-width:4.8in;margin:.08in 0 .2in;font-size:29pt;line-height:1.03}}blockquote{{margin:0;padding-left:.18in;border-left:2px solid #edcf75;font-size:14pt;line-height:1.4}}blockquote cite{{display:block;margin-top:.08in;font-family:Inter,system-ui,sans-serif;font-size:7pt;font-style:normal;text-transform:uppercase}}.affirm{{margin:.25in 0 0;max-width:4.75in;font-size:12pt;font-style:italic;line-height:1.45}}.source{{position:absolute;z-index:3;right:.3in;top:.32in;margin:0;font-family:Inter,system-ui,sans-serif;font-size:7pt;text-transform:uppercase}}.reading-leaf header,.reading-leaf footer,.journal-leaf header,.journal-leaf footer{{position:absolute;left:.48in;right:.48in;display:flex;justify-content:space-between;color:#6c7167;font-family:Inter,system-ui,sans-serif;font-size:7pt;text-transform:uppercase}}.reading-leaf header,.journal-leaf header{{top:.28in;padding-bottom:.1in;border-bottom:1px solid var(--rule)}}.reading-leaf footer,.journal-leaf footer{{bottom:.24in;padding-top:.1in;border-top:1px solid var(--rule)}}.reading{{padding:.72in .55in .55in}}.reading .kicker{{margin:0;color:var(--gold)}}.reading h2{{margin:.06in 0 .14in;color:var(--green);font-size:22pt;line-height:1.05}}.verse{{padding:.13in .16in;border-left:3px solid var(--gold);background:#f5efe2;font-size:9.2pt;line-height:1.4}}.verse p{{margin:.06in 0 0;font-style:italic}}.body{{margin-top:.14in;font-size:8.7pt;line-height:1.46}}.body p{{margin:0 0 .09in}}.carry{{margin:.12in 0;padding:.11in .14in;background:var(--green);color:#fff;font-size:9pt;font-weight:bold;line-height:1.4}}.journal{{padding:.7in .55in .5in}}.art-window{{height:1.18in;margin-bottom:.16in;background-image:linear-gradient(90deg,rgba(15,58,47,.18),rgba(15,58,47,.02)),var(--scene);background-position:center 38%;background-size:cover;border-bottom:4px solid var(--gold)}}.journal-kicker{{margin:0;color:var(--gold)}}.journal h2{{margin:.05in 0 .11in;color:var(--green);font-size:15.5pt;line-height:1.15}}.lens,.thread{{padding:.09in .12in;margin-top:.08in;border-left:3px solid var(--gold);background:#f5efe2;font-size:7.5pt;line-height:1.35}}.thread{{border-left-color:var(--green);background:#eef3ef}}.lens b,.thread b,.prayer b,.practice b{{color:var(--wine);font-family:Inter,system-ui,sans-serif;font-size:6.8pt;text-transform:uppercase}}.lens p,.thread p,.prayer p,.practice p{{margin:.035in 0 0}}.prayer{{margin-top:.09in;font-size:7.7pt;line-height:1.35}}.practice{{display:grid;grid-template-columns:1fr 1fr;gap:.15in;margin-top:.1in;padding-top:.09in;border-top:1px solid var(--rule);font-size:7.4pt;line-height:1.3}}.writing-lines{{display:grid;gap:.11in;margin-top:.13in}}.writing-lines i{{display:block;height:.01in;border-bottom:1px solid #c9cbbf}}@media(max-width:650px){{.leaf{{width:min(calc(100vw - 20px),6in);height:auto;min-height:9in}}.toolbar{{font-size:12px}}}}@media print{{@page{{size:6in 9in;margin:0}}body{{background:#fff;print-color-adjust:exact;-webkit-print-color-adjust:exact}}.toolbar{{display:none}}.book{{padding:0}}.leaf{{height:9in;margin:0;box-shadow:none}}}}
</style></head><body><nav class="toolbar"><span>Print production proof &middot; movement key art is directional</span><a href="/">Home</a><a href="lady-d-31-day-scene-review.html">Scene review</a><a href="lady-d-31-day-motion.html">Motion edition</a></nav><main class="book"><section class="leaf cover"><div class="cover-copy"><p class="kicker">Susan &ldquo;Lady D&rdquo; Damon</p><h1>{esc(corpus['title'])}</h1><p>{esc(corpus['subtitle'])}</p></div></section><section class="leaf contents"><p class="reading kicker">How the journey moves</p><h2>One light, four movements.</h2><p>Ten mornings rise from each devotional volume. The final morning gathers the Father's welcome, the footsteps of Jesus, and the Spirit's filling presence into one lived response.</p><ol>{movement_rows}</ol><div class="verse" style="margin-top:.35in"><b>Production note</b><p>Scripture is set separately from the imagery. Final scene art must pass the scene gauntlet before this proof is called print-final.</p></div></section>{''.join(pages)}</main></body></html>'''


def motion_html(corpus: dict) -> str:
    data = json_for_script(corpus)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#102d27"><title>{esc(corpus['title'])} | Living Edition</title><style>
:root{{--ink:#fff;--gold:#efcf78;--glass:rgba(13,39,31,.58)}}*{{box-sizing:border-box}}html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:#102d27;color:#fff;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}button,a{{font:inherit}}.stage{{position:fixed;inset:0;overflow:hidden}}.backdrop{{position:absolute;inset:-3%;background-position:center;background-size:cover;transform:scale(1.06);transition:background-image .8s ease,filter .8s ease;filter:saturate(1.08) brightness(.82)}}.backdrop::after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,25,20,.82),rgba(8,25,20,.2) 60%,rgba(8,25,20,.5)),linear-gradient(0deg,rgba(8,25,20,.72),transparent 55%)}}#scene{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}.fallback{{position:absolute;inset:0;background:radial-gradient(circle at 70% 25%,rgba(239,207,120,.18),transparent 30%)}}.chrome{{position:relative;z-index:3;height:100%;display:grid;grid-template-rows:auto 1fr auto;padding:22px 26px 24px}}.top{{display:flex;align-items:center;gap:12px}}.brand{{margin-right:auto;color:#fff;text-decoration:none;font-weight:850;line-height:1.05}}.brand small{{display:block;margin-top:3px;color:#d5dfd8;font-size:10px;font-weight:650;text-transform:uppercase}}.icon{{display:grid;place-items:center;width:42px;height:42px;border:1px solid rgba(255,255,255,.55);border-radius:50%;background:rgba(12,38,30,.3);color:#fff;cursor:pointer}}.icon:hover,.icon:focus-visible{{background:rgba(255,255,255,.16);outline:2px solid var(--gold);outline-offset:2px}}.progress{{position:absolute;top:0;left:0;height:3px;background:var(--gold);transition:width .5s ease}}.copy{{align-self:end;max-width:760px;padding-bottom:4vh}}.eyebrow{{margin:0;color:var(--gold);font-size:11px;font-weight:850;letter-spacing:.14em;text-transform:uppercase}}h1{{max-width:760px;margin:12px 0 14px;font-family:Georgia,"Times New Roman",serif;font-size:clamp(42px,6.5vw,84px);line-height:1.01;letter-spacing:0}}blockquote{{max-width:720px;margin:0;padding-left:18px;border-left:2px solid var(--gold);font-family:Georgia,"Times New Roman",serif;font-size:clamp(17px,2vw,24px);line-height:1.38}}blockquote cite{{display:block;margin-top:9px;font-family:Inter,system-ui,sans-serif;font-size:10px;font-style:normal;text-transform:uppercase}}.affirm{{max-width:700px;margin:18px 0 0;color:#eef4ef;font-size:15px;font-weight:650}}.bottom{{display:flex;align-items:center;gap:12px}}.day-count{{min-width:95px;color:#e4ebe6;font-size:12px;font-weight:800;text-transform:uppercase}}.movement{{margin-right:auto;color:var(--gold);font-family:Georgia,serif;font-size:18px}}.command{{min-height:44px;padding:9px 14px;border:1px solid rgba(255,255,255,.58);border-radius:6px;background:rgba(12,38,30,.35);color:#fff;font-weight:800;cursor:pointer}}.command.primary{{border-color:var(--gold);background:var(--gold);color:#20251f}}.reader{{position:fixed;z-index:8;inset:0 0 0 auto;width:min(610px,100%);padding:72px 34px 40px;overflow:auto;background:rgba(255,254,249,.97);color:#283029;transform:translateX(102%);transition:transform .45s cubic-bezier(.2,.8,.2,1)}}.reader.open{{transform:none}}.reader .close{{position:absolute;top:18px;right:20px;color:#153f34;border-color:#799085;background:transparent}}.reader .eyebrow{{color:#8b682d}}.reader h2{{margin:12px 0;font-family:Georgia,serif;font-size:36px;line-height:1.05}}.reader .verse{{padding:16px;border-left:3px solid #b88a39;background:#f5efe2;font-family:Georgia,serif;font-style:italic;line-height:1.5}}.reader .body{{font-family:Georgia,serif;font-size:17px;line-height:1.7}}.reader .body p{{margin:18px 0}}.reader .carry,.reader .prayer,.reader .practice{{padding:16px 18px;margin-top:17px}}.reader .carry{{background:#153f34;color:#fff;font-weight:750}}.reader .prayer{{background:#f4ede1}}.reader .practice{{border:1px solid #d8ddd7}}.picker{{position:fixed;z-index:9;inset:auto 0 0;padding:25px;background:#fff;color:#283029;transform:translateY(105%);transition:transform .4s ease}}.picker.open{{transform:none}}.picker-head{{display:flex;align-items:center;margin-bottom:16px}}.picker-head h2{{margin:0 auto 0 0;font-family:Georgia,serif}}.days{{display:grid;grid-template-columns:repeat(16,1fr);gap:7px}}.days button{{aspect-ratio:1;border:1px solid #cbd3cc;border-radius:50%;background:#fff;color:#234138;font-weight:800;cursor:pointer}}.days button.active{{border-color:#153f34;background:#153f34;color:#fff}}@media(max-width:760px){{.chrome{{padding:16px 15px 17px}}.top .icon:first-of-type{{display:none}}.copy{{padding-bottom:2vh}}h1{{font-size:42px}}blockquote{{font-size:17px}}.affirm{{font-size:13px}}.movement{{display:none}}.bottom{{flex-wrap:wrap}}.day-count{{margin-right:auto}}.bottom .command{{flex:1 1 120px}}.reader{{padding:68px 20px 30px}}.days{{grid-template-columns:repeat(8,1fr)}}}}@media(prefers-reduced-motion:reduce){{*{{scroll-behavior:auto!important;transition:none!important}}#scene{{display:none}}.backdrop{{transform:none}}}}
</style></head><body><main class="stage"><div class="backdrop" id="backdrop"><div class="fallback"></div></div><canvas id="scene" aria-hidden="true"></canvas><div class="progress" id="progress"></div><div class="chrome"><header class="top"><a class="brand" href="/">Thirty-One Mornings of Light<small>Lady D &middot; living devotional edition</small></a><button class="icon" id="pickerButton" title="Choose a day" aria-label="Choose a day">&#9783;</button><button class="icon" id="motionButton" title="Pause motion" aria-label="Pause motion">&#10074;&#10074;</button></header><section class="copy" aria-live="polite"><p class="eyebrow" id="eyebrow"></p><h1 id="title"></h1><blockquote><span id="verse"></span><cite id="reference"></cite></blockquote><p class="affirm" id="affirm"></p></section><footer class="bottom"><span class="day-count" id="dayCount"></span><span class="movement" id="movement"></span><button class="command" id="prev" aria-label="Previous day">&#8592;</button><button class="command primary" id="read">Read devotional</button><button class="command" id="next" aria-label="Next day">&#8594;</button></footer></div></main><aside class="reader" id="reader" aria-hidden="true"><button class="icon close" id="closeReader" aria-label="Close reading">&#10005;</button><p class="eyebrow" id="readerEyebrow"></p><h2 id="readerTitle"></h2><div class="verse" id="readerVerse"></div><div class="body" id="readerBody"></div><div class="carry" id="readerCarry"></div><div class="prayer" id="readerPrayer"></div><div class="practice" id="readerPractice"></div></aside><section class="picker" id="picker" aria-hidden="true"><div class="picker-head"><h2>Choose a morning</h2><button class="icon" id="closePicker" aria-label="Close day picker">&#10005;</button></div><div class="days" id="days"></div></section><script id="devotional-data" type="application/json">{data}</script><script type="module">
import * as THREE from './assets/vendor/three.module.min.js';
const corpus=JSON.parse(document.getElementById('devotional-data').textContent);let index=0,paused=matchMedia('(prefers-reduced-motion: reduce)').matches;const $=id=>document.getElementById(id);const backdrop=$('backdrop'),reader=$('reader'),picker=$('picker');
const palettes={{1:[0xefcf78,0xf4b58b],2:[0xaac8d4,0xe0b77c],3:[0xdcc477,0x83bfa9],4:[0xefcf78,0xc5a2d8]}};let renderer,scene,camera,points,clock;
function initThree(){{try{{renderer=new THREE.WebGLRenderer({{canvas:$('scene'),alpha:true,antialias:true}});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(58,innerWidth/innerHeight,.1,100);camera.position.z=6;const geometry=new THREE.BufferGeometry();const count=620,pos=new Float32Array(count*3);for(let i=0;i<count;i++){{pos[i*3]=(Math.random()-.5)*14;pos[i*3+1]=(Math.random()-.5)*10;pos[i*3+2]=(Math.random()-.5)*8}}geometry.setAttribute('position',new THREE.BufferAttribute(pos,3));points=new THREE.Points(geometry,new THREE.PointsMaterial({{color:0xefcf78,size:.035,transparent:true,opacity:.72,depthWrite:false}}));scene.add(points);clock=new THREE.Clock();resize();addEventListener('resize',resize);requestAnimationFrame(loop)}}catch(error){{$('scene').style.display='none';console.warn('WebGL fallback active',error)}}}}
function resize(){{if(!renderer)return;renderer.setSize(innerWidth,innerHeight,false);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix()}}function loop(){{if(renderer){{const t=clock.getElapsedTime();if(!paused){{points.rotation.y=t*.018;points.rotation.x=Math.sin(t*.08)*.05;points.position.y=Math.sin(t*.17)*.12}}renderer.render(scene,camera)}}requestAnimationFrame(loop)}}
function artFor(day){{return day.visual.status==='final-qualified' ? day.visual.art : day.visual.fallbackArt}}function render(){{const d=corpus.days[index];$('eyebrow').textContent=`Day ${{String(d.day).padStart(2,'0')}} · ${{d.volumeTitle}}`;$('title').textContent=d.title;$('verse').textContent='“'+d.scripture.text+'”';$('reference').textContent=d.scripture.reference+' · '+d.scripture.translation;$('affirm').textContent=d.closing;$('dayCount').textContent=`${{d.day}} / 31`;$('movement').textContent=d.movementTitle;$('progress').style.width=`${{(d.day/31)*100}}%`;backdrop.style.backgroundImage=`url('${{artFor(d)}}')`;if(points)points.material.color.setHex(palettes[d.movement][0]);$('readerEyebrow').textContent=`Day ${{d.day}} · ${{d.volumeTitle}}`;$('readerTitle').textContent=d.title;$('readerVerse').innerHTML=`<b>${{d.scripture.reference}} · ${{d.scripture.translation}}</b><br>${{d.scripture.text}}`;$('readerBody').innerHTML=d.body.map(p=>`<p>${{p}}</p>`).join('');$('readerCarry').textContent=d.closing;$('readerPrayer').innerHTML=`<b>Prayer</b><p>${{d.prayer}}</p>`;$('readerPractice').innerHTML=`<b>Reflect</b><p>${{d.journalReflect}}</p><b>Live it</b><p>${{d.journalAct}}</p>`;document.querySelectorAll('.days button').forEach((b,i)=>b.classList.toggle('active',i===index));history.replaceState(null,'','#day-'+d.day)}}
function setDay(next){{index=(next+31)%31;render()}}corpus.days.forEach((d,i)=>{{const b=document.createElement('button');b.textContent=d.day;b.setAttribute('aria-label','Open day '+d.day);b.onclick=()=>{{setDay(i);picker.classList.remove('open')}};$('days').appendChild(b)}});$('prev').onclick=()=>setDay(index-1);$('next').onclick=()=>setDay(index+1);$('read').onclick=()=>{{reader.classList.add('open');reader.setAttribute('aria-hidden','false')}};$('closeReader').onclick=()=>{{reader.classList.remove('open');reader.setAttribute('aria-hidden','true')}};$('pickerButton').onclick=()=>{{picker.classList.add('open');picker.setAttribute('aria-hidden','false')}};$('closePicker').onclick=()=>{{picker.classList.remove('open');picker.setAttribute('aria-hidden','true')}};$('motionButton').onclick=e=>{{paused=!paused;e.currentTarget.innerHTML=paused?'&#9654;':'&#10074;&#10074;';e.currentTarget.title=paused?'Resume motion':'Pause motion'}};addEventListener('keydown',e=>{{if(e.key==='ArrowRight')setDay(index+1);if(e.key==='ArrowLeft')setDay(index-1);if(e.key==='Escape'){{reader.classList.remove('open');picker.classList.remove('open')}}}});const hash=location.hash.match(/day-(\\d+)/);if(hash)index=Math.max(0,Math.min(30,Number(hash[1])-1));initThree();render();
</script></body></html>'''


def scene_review_html(corpus: dict) -> str:
    data = json_for_script(corpus)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lady D | 31-Day Scene Gauntlet</title><style>
:root{{--ink:#222920;--muted:#687168;--paper:#fffefd;--wash:#f1f4ef;--forest:#153f34;--gold:#b88a39;--wine:#7b3444;--line:#d8ded8}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.5}}.shell{{width:min(1180px,calc(100% - 32px));margin:auto}}header{{padding:62px 0;background:var(--forest);color:#fff}}header p{{max-width:820px;color:#d6e0da}}h1,h2,h3{{font-family:Georgia,serif;line-height:1.08}}h1{{font-size:clamp(38px,6vw,68px);margin:8px 0 16px}}.eyebrow{{color:#e5c878;font-size:11px;font-weight:850;text-transform:uppercase}}nav{{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px}}a,.button{{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:8px 12px;border:1px solid currentColor;border-radius:6px;color:inherit;text-decoration:none;font-weight:800}}main{{padding:50px 0 80px}}.truth{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line)}}.truth div{{padding:20px;border-right:1px solid var(--line)}}.truth div:last-child{{border-right:0}}.truth b{{display:block;color:var(--forest);font-family:Georgia,serif;font-size:34px}}.truth span{{color:var(--muted);font-size:13px}}.filter{{display:flex;gap:8px;flex-wrap:wrap;margin:28px 0}}.filter button{{padding:8px 11px;border:1px solid var(--line);border-radius:5px;background:#fff;cursor:pointer}}.filter button.active{{background:var(--forest);color:#fff}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}.card{{display:grid;grid-template-columns:190px 1fr;border:1px solid var(--line);background:#fff}}.preview{{position:relative;min-height:300px;background-position:center;background-size:cover}}.preview::after{{content:"";position:absolute;inset:0;background:linear-gradient(transparent,rgba(12,35,28,.68))}}.day{{position:absolute;z-index:2;left:12px;bottom:10px;color:#fff;font-family:Georgia,serif;font-size:30px}}.copy{{padding:20px}}.copy h2{{margin:4px 0 8px;font-size:25px}}.copy p{{color:var(--muted);font-size:13px}}.meta{{color:var(--gold);font-size:10px;font-weight:850;text-transform:uppercase}}details{{margin-top:13px;border-top:1px solid var(--line);padding-top:11px}}summary{{cursor:pointer;font-weight:800}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;color:#3f4941;font:12px/1.55 ui-monospace,monospace}}.decisions{{display:flex;gap:6px;flex-wrap:wrap;margin-top:14px}}.decisions button{{padding:7px 9px;border:1px solid var(--line);border-radius:5px;background:#fff;font-weight:750;cursor:pointer}}.decisions button[data-value="prompt-approved"]{{color:#1d6b4b}}.decisions button[data-value="hold"]{{color:#91661c}}.decisions button[data-value="regenerate"]{{color:#8b3549}}.status{{margin-top:10px;color:var(--wine);font-size:12px;font-weight:850}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}@media(max-width:620px){{.truth{{grid-template-columns:1fr 1fr}}.truth div:nth-child(2){{border-right:0}}.truth div:nth-child(-n+2){{border-bottom:1px solid var(--line)}}.card{{grid-template-columns:1fr}}.preview{{min-height:360px}}}}
</style></head><body><header><div class="shell"><p class="eyebrow">Generator &harr; critic decision surface</p><h1>31-Day Scene Gauntlet</h1><p>The message source is locked. Each prompt can now be approved before generation, then each real scene must clear message fidelity, brightness, composition, anatomy, and motion-separation gates before it enters the print or living edition.</p><nav><a href="/">Publishing home</a><a href="lady-d-31-day-visual-devotional.html">Print proof</a><a href="lady-d-31-day-motion.html">Motion edition</a></nav></div></header><main class="shell"><section class="truth"><div><b>31</b><span>locked devotional records</span></div><div><b>10 + 10 + 10</b><span>selected from the trilogy</span></div><div><b>1</b><span>new trinitarian culmination</span></div><div><b>88</b><span>minimum scene score after generation</span></div></section><div class="filter" id="filter"><button class="active" data-movement="all">All days</button><button data-movement="1">Awakening</button><button data-movement="2">Depths</button><button data-movement="3">Wonders</button><button data-movement="4">Kingdom Light</button></div><section class="grid" id="grid"></section></main><script id="data" type="application/json">{data}</script><script>
const corpus=JSON.parse(document.getElementById('data').textContent),grid=document.getElementById('grid'),key='lady-d-31-day-scene-decisions-v1',saved=JSON.parse(localStorage.getItem(key)||'{{}}');function render(filter='all'){{grid.innerHTML='';corpus.days.filter(d=>filter==='all'||String(d.movement)===filter).forEach(d=>{{const article=document.createElement('article');article.className='card';article.innerHTML=`<div class="preview" style="background-image:url('${{d.visual.draftArt||d.visual.fallbackArt}}')"><span class="day">${{String(d.day).padStart(2,'0')}}</span></div><div class="copy"><span class="meta">${{d.movementTitle}} · ${{d.volumeTitle}}</span><h2>${{d.title}}</h2><p><b>${{d.scripture.reference}}</b> · ${{d.selectionReason}}</p><details><summary>Scene brief and image prompt</summary><p><b>Family:</b> ${{d.visual.sceneFamily}}<br><b>Environment:</b> ${{d.visual.environment}}</p><pre>${{d.visual.prompt}}</pre><p><b>Motion:</b> ${{d.visual.motion.join(' ')}}</p></details><div class="decisions"><button data-value="prompt-approved">Approve prompt</button><button data-value="hold">Hold</button><button data-value="regenerate">Revise prompt</button></div><div class="status">${{saved[d.day]||(d.visual.draftArt?'Draft candidate available · print qualification pending':'Awaiting prompt decision · final scene not generated')}}</div></div>`;article.querySelectorAll('.decisions button').forEach(b=>b.onclick=()=>{{saved[d.day]=b.dataset.value;localStorage.setItem(key,JSON.stringify(saved));article.querySelector('.status').textContent=b.dataset.value+' · final scene still requires qualification'}});grid.appendChild(article)}})}}document.querySelectorAll('#filter button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('#filter button').forEach(x=>x.classList.remove('active'));b.classList.add('active');render(b.dataset.movement)}});render();
</script></body></html>'''


def write_mirrors(name: str, content: str) -> None:
    for directory in (ROOT, PUBLIC):
        directory.mkdir(exist_ok=True)
        (directory / name).write_text(content, encoding="utf-8")


def main() -> None:
    corpus = build_corpus()
    SOURCE.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    PUBLIC_DOWNLOADS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(corpus, ensure_ascii=False, indent=2) + "\n"
    (SOURCE / "visual-devotional.json").write_text(payload, encoding="utf-8")
    for directory in (DOWNLOADS, PUBLIC_DOWNLOADS):
        (directory / "Lady-D-31-Day-Visual-Devotional-Source.json").write_text(payload, encoding="utf-8")
    print_doc = print_html(corpus)
    motion_doc = motion_html(corpus)
    review_doc = scene_review_html(corpus)
    write_mirrors("lady-d-31-day-visual-devotional.html", print_doc)
    write_mirrors("lady-d-31-day-motion.html", motion_doc)
    write_mirrors("lady-d-31-day-scene-review.html", review_doc)
    for directory in (DOWNLOADS, PUBLIC_DOWNLOADS):
        (directory / "Lady-D-31-Day-Visual-Devotional-Print-Proof.html").write_text(print_doc, encoding="utf-8")
    print("built 31-day shared corpus, print proof, motion reader, and scene review console")


if __name__ == "__main__":
    main()
