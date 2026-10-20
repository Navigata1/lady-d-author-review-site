#!/usr/bin/env python3
"""Build polished Lady D devotional and companion-journal HTML interiors."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "source/finalization/templates"
POLISHED_DIR = ROOT / "source/finalization/polished"
ENRICHMENT_DIR = ROOT / "source/finalization/enrichment"
OUTPUT_DIR = ROOT / "public/downloads/lady-d-finalization"
MIRROR_DIR = ROOT / "downloads/lady-d-finalization"
FRONT_MATTER_PATH = ROOT / "source/finalization/front-matter/lady-d-shared-front-matter.json"
REVISION_PATH = ROOT / "source/finalization/editorial-2026-10-20/enrichment-revisions.json"
MONTH_ART = {
    1: [1, 3, 5, 6, 7, 8, 20, 25, 26, 27, 28, 30],
    2: [2, 9, 10, 11, 12, 13, 14, 15, 16, 18, 29, 31],
    3: [4, 17, 19, 21, 22, 23, 24, 26, 27, 28, 30, 31],
}
DEVOTIONAL_PAGE_SHIFT = 2
BLANK_FRONT_MATTER_LEAF = (
    '<section class="leaf "><div class="rh"><span></span><i></i><span></span></div>'
    '<div class="flow"></div><div class="folio"></div></section>'
)

VOLUMES = {
    1: {
        "slug": "surrendering-to-gods-love",
        "label": "Volume One",
        "lane": "the Father's care",
    },
    2: {
        "slug": "walking-with-jesus",
        "label": "Volume Two",
        "lane": "the way of Jesus",
    },
    3: {
        "slug": "filled-with-the-holy-spirit",
        "label": "Volume Three",
        "lane": "the Spirit's nearness",
    },
}

MONTHS = [
    ("January", list(range(1, 32)), 31),
    ("February", list(range(32, 60)) + [0], 60),
    ("March", list(range(60, 91)), 91),
    ("April", list(range(91, 121)), 121),
    ("May", list(range(121, 152)), 152),
    ("June", list(range(152, 182)), 182),
    ("July", list(range(182, 213)), 213),
    ("August", list(range(213, 244)), 244),
    ("September", list(range(244, 274)), 274),
    ("October", list(range(274, 305)), 305),
    ("November", list(range(305, 335)), 335),
    ("December", list(range(335, 366)), 366),
]

DEEP_DIVE_CSS = r"""
.deep .flow{justify-content:flex-start}
.deep-head{text-align:center;margin-bottom:12px}
.deep-head .k{font-family:var(--sans);font-size:6.2pt;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:var(--gold)}
.deep-head h2{font-family:var(--disp);font-weight:600;font-size:15pt;line-height:1.16;color:var(--ink);margin-top:5px}
.deep-head p{font-style:italic;font-size:8.5pt;line-height:1.45;color:var(--ink-soft);max-width:4.2in;margin:7px auto 0}
.weave-row{border-top:1px solid var(--rule);padding:9px 2px 8px}
.weave-row:first-of-type{border-top:0}
.weave-row .meta{font-family:var(--sans);font-size:5.8pt;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--acc-ink)}
.weave-row h3{font-family:var(--disp);font-weight:600;font-size:9.6pt;line-height:1.25;color:var(--ink);margin-top:3px}
.weave-row p{font-size:7.9pt;line-height:1.4;color:var(--ink-soft);margin-top:3px}
.review-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;margin-top:8px;padding-top:8px;border-top:1px solid var(--rule)}
.review-q{font-size:7.7pt;line-height:1.36;color:var(--ink)}
.review-q b{font-family:var(--sans);font-size:5.6pt;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);display:block;margin-bottom:2px}
.review-lines{margin-top:4px}
.review-lines span{display:block;height:0.22in;border-bottom:1px solid var(--rule)}
.deep-prayer{margin-top:9px;padding:8px 11px;border-left:3px solid var(--acc2);background:rgba(176,134,59,.06);font-style:italic;font-size:8pt;line-height:1.42;color:var(--ink-soft)}
"""

FRONT_MATTER_CSS = r"""
.fm-copy{justify-content:flex-start;padding-top:.12in}
.fm-copy h1{font-size:23pt;margin:8px 0 8px}
.fm-copy .orn{margin:9px auto 12px}
.fmtext.acknowledgments{max-width:4.5in;font-size:8.45pt;line-height:1.43;color:var(--ink)}
.fmtext.acknowledgments p{margin-bottom:.54em}
.fmtext.acknowledgments .salutation{font-family:var(--disp);font-weight:600;color:var(--acc-ink);margin-bottom:.75em}
.fmtext.acknowledgments .closing{margin-top:.85em;margin-bottom:.22em;font-style:italic}
.fmtext.acknowledgments .signature{font-family:var(--disp);font-weight:600;color:var(--acc-ink)}
.foreword-reserve{max-width:4.15in;padding:20px 22px;border:1px solid var(--rule);border-top:3px solid var(--gold);background:#fffdf7;text-align:left}
.foreword-reserve p{font-size:10pt;line-height:1.58;color:var(--ink-soft);margin:0 0 .85em}
.foreword-reserve .status{font-family:var(--sans);font-size:6.4pt;line-height:1.55;letter-spacing:.12em;text-transform:uppercase;color:var(--acc-ink);padding-top:10px;border-top:1px solid var(--rule)}
"""


def clean_text(value: str) -> str:
    value = value.replace("\u2014", " - ").replace("\u2013", " - ").replace("\u2011", "-")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def esc(value: str) -> str:
    return html.escape(clean_text(value), quote=False)


def voice_day_for_source_index(index: int) -> int:
    if index == 60:
        return 0
    return index if index < 60 else index - 1


def title_class(title: str) -> str:
    return "long" if len(title) > 46 else ""


def body_tier(record: dict) -> str:
    character_count = sum(len(paragraph) for paragraph in record["body"]) + len(record["closing"]) + len(record["prayer"])
    if character_count > 2450:
        return "tighter"
    if character_count > 2100:
        return "tight"
    return ""


def section_pattern(identifier: str) -> re.Pattern[str]:
    return re.compile(
        rf"<section class=\"leaf [^\"]*\" id=\"{re.escape(identifier)}\">.*?</section>",
        re.DOTALL,
    )


def revised_enrichment(volume: int) -> list[dict]:
    records = json.loads((ENRICHMENT_DIR / f"vol{volume}-enrichment-366-days.json").read_text())
    revisions = json.loads(REVISION_PATH.read_text())[str(volume)]
    for record in records:
        record.update(revisions.get(str(record["day"]), {}))
    return records


def presentation(document: str, volume: int, records: list[dict], journal: bool) -> str:
    # Shared screen styling stays outside print geometry; dates retain stable page IDs.
    document = re.sub(r'<link\b[^>]*(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>', '', document)
    document = document.replace('</head>', '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<link rel="stylesheet" href="../../assets/lady-d-interiors/interiors.css">'
        '<script defer src="../../assets/lady-d-interiors/interiors.js"></script></head>', 1)
    document = document.replace('<body>', f'<body data-volume="{volume}">', 1)
    by_day = {record["day"]: record for record in records}
    options = []
    prefix = 'j' if journal else 'dA'
    for month, days, _ in MONTHS:
        group = []
        for date, day in enumerate(days, 1):
            index = 60 if day == 0 else day if day < 60 else day + 1
            group.append(f'<option value="{prefix}{index}">{month} {date} - {html.escape(by_day[day]["title"], quote=True)}</option>')
        options.append(f'<optgroup label="{month}">{"".join(group)}</optgroup>')
    pdf_name = {1:'Surrendering-to-Gods-Love', 2:'Walking-with-Jesus', 3:'Filled-with-the-Holy-Spirit'}[volume]
    pdf_name = f'Lady-D-Volume-{volume}-{pdf_name}-' + ('Companion-Journal-Deep-Dive-6x9.pdf' if journal else 'Polished-6x9.pdf')
    titles = {1:"Surrendering to God's Love", 2:'Walking with Jesus', 3:'Filled with the Holy Spirit'}
    toolbar = ('<a class="interior-skip" href="#'+prefix+'1">Skip to the first reading</a>'
        '<nav class="interior-toolbar" aria-label="Book navigation">'
        f'<span class="book-name">{esc(titles[volume])}</span>'
        '<a href="../../susan-damon-hub.html" aria-label="Publishing home" title="Publishing home"><img src="../../assets/lady-d-reader/house.svg" alt=""><span>Library</span></a>'
        f'<label class="select-label" for="reading-day">Choose a reading</label><select id="reading-day">{"".join(options)}</select>'
        f'<a href="{pdf_name}" aria-label="Download PDF" title="Download PDF"><img src="../../assets/lady-d-reader/download.svg" alt=""><span>PDF</span></a></nav>')
    document = document.replace(f'<body data-volume="{volume}">', f'<body data-volume="{volume}">{toolbar}', 1)
    if journal:
        month_index = 0
        def month_image(match: re.Match[str]) -> str:
            nonlocal month_index
            art_day = MONTH_ART[volume][month_index]
            month_index += 1
            # Keep faces in view when portrait scenes become landscape openings.
            crop = {6:'25%',17:'25%',26:'25%',31:'25%'}.get(art_day, '50%')
            return match.group(0) + f'<img class="monthly-art" style="object-position:50% {crop}" src="../../assets/lady-d-31-visual-journal-v2/scenes/day-{art_day:02d}.jpg" alt="" loading="lazy" width="1800" height="2700">'
        document = re.sub(r'<div class="flow mdiv">', month_image, document)
        if month_index != 12:
            raise ValueError(f'volume {volume} journal has {month_index} month dividers, expected 12')
    else:
        for _, days, _ in MONTHS:
            day = days[0]
            index = day if day < 60 else day + 1
            document = re.sub(rf'(<section class="leaf )([^"]*)(" id="dB{index}")', r'\1\2 month-start\3', document)
    return document


def load_front_matter() -> dict:
    payload = json.loads(FRONT_MATTER_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != "idc.lady_d_shared_front_matter/v1":
        raise ValueError("unexpected Lady D front-matter schema")
    if payload["acknowledgments"].get("status") != "author_supplied":
        raise ValueError("acknowledgments must be author supplied before composition")
    return payload


def shared_front_matter_pages(payload: dict) -> str:
    foreword = payload["foreword"]
    acknowledgments = payload["acknowledgments"]
    acknowledgment_paragraphs = "".join(
        f"<p>{esc(paragraph)}</p>" for paragraph in acknowledgments["paragraphs"]
    )
    return (
        '<section class="leaf "><div class="rh"><span></span><i></i><span></span></div>'
        '<div class="flow fm"><div class="k">Front Matter Contribution</div>'
        f'<h1>{esc(foreword["title"])}</h1><div class="orn"></div>'
        '<div class="foreword-reserve">'
        f'<p>{esc(foreword["message"])}</p>'
        f'<div class="status"><b>{esc(foreword["reviewLabel"])}</b><br>{esc(foreword["pending"])}</div>'
        '</div></div><div class="folio"></div></section>'
        '<section class="leaf "><div class="rh"><span></span><i></i><span></span></div>'
        '<div class="flow fm fm-copy">'
        f'<div class="k">From the Author</div><h1>{esc(acknowledgments["title"])}</h1><div class="orn"></div>'
        '<div class="fmtext acknowledgments">'
        f'<p class="salutation">{esc(acknowledgments["salutation"])}</p>'
        f'{acknowledgment_paragraphs}'
        f'<p class="closing">{esc(acknowledgments["closing"])}</p>'
        f'<p class="signature">{esc(acknowledgments["signature"])}</p>'
        '</div></div><div class="folio"></div></section>'
        f'{BLANK_FRONT_MATTER_LEAF}'
    )


def shift_devotional_page_references(document: str, shift: int) -> str:
    document = re.sub(
        r'(<td class="pg">)(\d+)(</td>)',
        lambda match: f'{match.group(1)}{int(match.group(2)) + shift}{match.group(3)}',
        document,
    )
    return re.sub(
        r'(<div class="folio"><b>.*?</b>\s*&nbsp;\s*·\s*&nbsp;\s*)(\d+)(</div>)',
        lambda match: f'{match.group(1)}{int(match.group(2)) + shift}{match.group(3)}',
        document,
    )


def shift_journal_reference(reference_html: str, shift: int) -> str:
    return re.sub(
        r'(see devotional p\.\s*)(\d+)',
        lambda match: f'{match.group(1)}{int(match.group(2)) + shift}',
        reference_html,
        flags=re.IGNORECASE,
    )


def extract_outer(section: str) -> tuple[str, str]:
    running_head = re.search(r"(<div class=\"rh\">.*?</div>)", section, re.DOTALL)
    folio = re.search(r"(<div class=\"folio\">.*?</div>)</section>$", section, re.DOTALL)
    if not running_head or not folio:
        raise ValueError("section is missing its running head or folio")
    return running_head.group(1), folio.group(1)


def build_devotional(volume: int, records: list[dict]) -> Path:
    source_path = TEMPLATE_DIR / f"vol{volume}-devotional-source.html"
    document = source_path.read_text(encoding="utf-8")
    by_day = {record["day"]: record for record in records}
    enrichment_by_day = {record["day"]: record for record in revised_enrichment(volume)}

    if document.count(BLANK_FRONT_MATTER_LEAF) != 1:
        raise ValueError(f"volume {volume} devotional must contain exactly one front-matter reserve leaf")
    document = document.replace("</style>", FRONT_MATTER_CSS + "\n</style>", 1)
    document = document.replace(BLANK_FRONT_MATTER_LEAF, shared_front_matter_pages(load_front_matter()), 1)
    document = shift_devotional_page_references(document, DEVOTIONAL_PAGE_SHIFT)

    for index in range(1, 367):
        day = voice_day_for_source_index(index)
        record = by_day[day]

        a_pattern = section_pattern(f"dA{index}")
        a_match = a_pattern.search(document)
        if not a_match:
            raise ValueError(f"missing devotional anchor section dA{index}")
        a_section = a_match.group(0)
        new_heading = f'<h1 class="{title_class(record["title"])}">{esc(record["title"])}</h1>'
        a_section = re.sub(r"<h1 class=\"[^\"]*\">.*?</h1>", new_heading, a_section, count=1, flags=re.DOTALL)
        language = enrichment_by_day[day]
        lens = (f'<div class="lens"><span class="lk">Root<br>Word</span><p><span class="g">{esc(language["lens_translit"])}</span>'
            f' · {esc(language["lens_script"])} ({esc(language["lens_lang"])}) - {esc(language["lens_gloss"])}</p></div>')
        a_section = re.sub(r'<div class="lens">.*?</div>', lambda _: lens, a_section, count=1, flags=re.DOTALL)
        note = f'<p class="note"><b>{esc(language["note_title"])}</b> {esc(language["note_body"])}</p>'
        a_section = re.sub(r'<p class="note">.*?</p>', lambda _: note, a_section, count=1, flags=re.DOTALL)
        document = document[: a_match.start()] + a_section + document[a_match.end() :]

        b_pattern = section_pattern(f"dB{index}")
        b_match = b_pattern.search(document)
        if not b_match:
            raise ValueError(f"missing devotional reading section dB{index}")
        running_head, folio = extract_outer(b_match.group(0))
        paragraphs = []
        for paragraph_index, paragraph in enumerate(record["body"]):
            class_name = "cap" if paragraph_index == 0 else ""
            paragraphs.append(f'<p class="{class_name}">{esc(paragraph)}</p>')
        tier = body_tier(record)
        rebuilt = (
            f'<section class="leaf {tier}" id="dB{index}">'
            f'{running_head}<div class="flow center"><div class="body">'
            f'{"".join(paragraphs)}</div>'
            f'<p class="carry">{esc(record["closing"])}</p>'
            f'<p class="prayer"><b>Prayer</b>{esc(record["prayer"])}</p>'
            f'<p class="contd">Carry it with you -&gt;</p></div>{folio}</section>'
        )
        document = document[: b_match.start()] + rebuilt + document[b_match.end() :]

    document = presentation(clean_document_dashes(document), volume, records, journal=False)
    output_path = OUTPUT_DIR / f"volume-{volume}-{VOLUMES[volume]['slug']}-polished-devotional.html"
    output_path.write_text(document, encoding="utf-8")
    MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    (MIRROR_DIR / output_path.name).write_text(document, encoding="utf-8")
    return output_path


def first_prayer_line(prayer: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", clean_text(prayer), maxsplit=1)[0]
    sentence = sentence.rstrip(".!?")
    if len(sentence) > 175:
        sentence = sentence[:172].rsplit(" ", 1)[0] + "..."
    return sentence


def journal_reference_map(document: str) -> tuple[dict[int, str], dict[int, str]]:
    references: dict[int, str] = {}
    observation_questions: dict[int, str] = {}
    for index in range(1, 367):
        match = section_pattern(f"j{index}").search(document)
        if not match:
            raise ValueError(f"missing journal section j{index}")
        section = match.group(0)
        ref_match = re.search(r"<p class=\"jref\">(.*?)</p>", section, re.DOTALL)
        questions = re.findall(
            r"<div class=\"jq\"><span class=\"jn\">\d+</span><p>(.*?)</p></div>",
            section,
            re.DOTALL,
        )
        if not ref_match or len(questions) < 2:
            raise ValueError(f"journal section j{index} is incomplete")
        day = voice_day_for_source_index(index)
        references[day] = clean_text(re.sub(r"<[^>]+>", "", ref_match.group(1)))
        observation_questions[day] = clean_text(re.sub(r"<[^>]+>", "", questions[0]))
    return references, observation_questions


def response_lines(count: int) -> str:
    return '<div class="review-lines">' + "".join("<span></span>" for _ in range(count)) + "</div>"


def deep_dive_page(
    volume: int,
    month: str,
    days: list[int],
    by_day: dict[int, dict],
    enrichment: dict[int, dict],
    references: dict[int, str],
) -> str:
    chosen_days = [days[0], days[len(days) // 2], days[-1]]
    rows: list[str] = []
    for day in chosen_days:
        record = by_day[day]
        thread = enrichment[day]
        day_label = "Leap Day" if day == 0 else f"Day {day}"
        anchor_ref = references[day].split(" - see devotional", 1)[0].split(" · see devotional", 1)[0]
        rows.append(
            '<div class="weave-row">'
            f'<div class="meta">{day_label} · {esc(anchor_ref)} + {esc(thread["thread_ref"])}</div>'
            f'<h3>{esc(record["title"])}</h3>'
            f'<p><b>{esc(thread["note_title"])}</b> {esc(thread["note_body"])}</p>'
            "</div>"
        )

    review_questions = [
        ("The truth I am carrying", f"Which Scripture or title from {month} keeps returning to you, and why?"),
        ("The thread I can now see", "Where did two passages begin answering each other in your life?"),
        ("The step that became real", "Which small act of obedience moved from intention into practice?"),
        ("The prayer for next month", f"What do you want {VOLUMES[volume]['lane']} to reshape as you continue?"),
    ]
    questions_html = "".join(
        f'<div class="review-q"><b>{esc(label)}</b>{esc(question)}{response_lines(2)}</div>'
        for label, question in review_questions
    )
    return (
        '<section class="leaf deep">'
        f'<div class="rh"><span>Monthly Deep Dive</span><i></i><span>{esc(month)}</span></div>'
        '<div class="flow">'
        '<div class="deep-head"><div class="k">Correlative Weave · Look Back, Listen Forward</div>'
        f'<h2>{esc(month)} in Conversation</h2>'
        f'<p>Pause before turning the page. Let three moments from {esc(month)} speak together, then name what God has made clearer in you.</p></div>'
        f'{"".join(rows)}<div class="review-grid">{questions_html}</div>'
        f'<div class="deep-prayer">{esc(json.loads((REVISION_PATH.parent / "monthly-prayers.json").read_text())[str(volume)][[item[0] for item in MONTHS].index(month)])}</div>'
        f'</div><div class="folio">Monthly Deep Dive · {esc(month)}</div></section>'
    )


def build_journal(volume: int, records: list[dict], enrichment_records: list[dict]) -> Path:
    source_path = TEMPLATE_DIR / f"vol{volume}-journal-source.html"
    document = source_path.read_text(encoding="utf-8")
    by_day = {record["day"]: record for record in records}
    enrichment = {record["day"]: record for record in enrichment_records}
    references, observation_questions = journal_reference_map(document)

    document = document.replace("</style>", DEEP_DIVE_CSS + "\n</style>", 1)

    for index in range(1, 367):
        day = voice_day_for_source_index(index)
        record = by_day[day]
        pattern = section_pattern(f"j{index}")
        match = pattern.search(document)
        if not match:
            raise ValueError(f"missing journal section j{index}")
        section = match.group(0)
        running_head, folio = extract_outer(section)
        reference = re.search(r"<p class=\"jref\">(.*?)</p>", section, re.DOTALL)
        if not reference:
            raise ValueError(f"journal section j{index} is missing its reference")
        reference_html = clean_document_dashes(reference.group(1))
        reference_html = shift_journal_reference(reference_html, DEVOTIONAL_PAGE_SHIFT)
        observation = observation_questions[day]
        prayer_line = first_prayer_line(record["prayer"])
        rebuilt = (
            f'<section class="leaf " id="j{index}">{running_head}<div class="flow">'
            f'<div class="jhead"><h2 class="{title_class(record["title"])}">{esc(record["title"])}</h2><span>{"Leap Day" if day == 0 else f"Day {day}"}</span></div>'
            f'<p class="jref">{reference_html}</p>'
            f'<div class="jq"><span class="jn">1</span><p>{esc(observation)}</p></div>'
            '<div class="jlines"><div class="jline"></div><div class="jline"></div><div class="jline"></div><div class="jline"></div></div>'
            f'<div class="jq"><span class="jn">2</span><p>{esc(record["journal_reflect"])}</p></div>'
            '<div class="jlines"><div class="jline"></div><div class="jline"></div><div class="jline"></div><div class="jline"></div></div>'
            f'<div class="jstrip"><b>One small step today</b>{esc(record["journal_act"])}</div>'
            f'<div class="jstrip"><b>Written-prayer starter</b><span class="ps">“{esc(prayer_line)} -”</span> finish the line in your own words.'
            '<div class="jlines" style="margin-top:5px"><div class="jline"></div><div class="jline"></div><div class="jline"></div></div></div>'
            f'</div>{folio}</section>'
        )
        document = document[: match.start()] + rebuilt + document[match.end() :]

    for month, days, end_index in MONTHS:
        page = deep_dive_page(volume, month, days, by_day, enrichment, references)
        pattern = section_pattern(f"j{end_index}")
        match = pattern.search(document)
        if not match:
            raise ValueError(f"could not append {month} deep dive after j{end_index}")
        document = document[: match.end()] + page + document[match.end() :]

    document = presentation(clean_document_dashes(document), volume, records, journal=True)
    output_path = OUTPUT_DIR / f"volume-{volume}-{VOLUMES[volume]['slug']}-polished-companion-journal.html"
    output_path.write_text(document, encoding="utf-8")
    MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    (MIRROR_DIR / output_path.name).write_text(document, encoding="utf-8")
    return output_path


def clean_document_dashes(document: str) -> str:
    # Scripture is an immutable source quotation, including its punctuation.
    parts = re.split(r'(<p class="txt[^\"]*">.*?</p>)', document, flags=re.DOTALL)
    for index in range(0, len(parts), 2):
        parts[index] = (parts[index].replace("\u2014", " - ")
            .replace("\u2013", " - ").replace("\u2011", "-")
            .replace("&mdash;", "-").replace("&ndash;", "-"))
    return ''.join(parts)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'assets/lady-d-interiors', ROOT / 'public/assets/lady-d-interiors', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'assets/fonts', ROOT / 'public/assets/fonts', dirs_exist_ok=True)
    outputs: list[str] = []
    for volume in range(1, 4):
        records = json.loads(
            (POLISHED_DIR / f"vol{volume}-polished-366-days.json").read_text(encoding="utf-8")
        )
        contract = json.loads((ROOT / 'source/finalization/author-voice-contract.json').read_text())
        for record in records:
            prose = '\n'.join([record['title'], *record['body'], record['closing'], record['prayer'], record['journal_reflect'], record['journal_act']])
            for word in contract['disallowedAuthorWords']:
                if re.search(rf'\b{re.escape(word)}\b', prose, re.I):
                    raise ValueError(f'Author vocabulary rule failed: volume {volume}, day {record["day"]}')
        enrichment = revised_enrichment(volume)
        outputs.append(str(build_devotional(volume, records).relative_to(ROOT)))
        outputs.append(str(build_journal(volume, records, enrichment).relative_to(ROOT)))
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
