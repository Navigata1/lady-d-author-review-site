#!/usr/bin/env python3
"""Build polished Lady D devotional and companion-journal HTML interiors."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "source/finalization/templates"
POLISHED_DIR = ROOT / "source/finalization/polished"
ENRICHMENT_DIR = ROOT / "source/finalization/enrichment"
OUTPUT_DIR = ROOT / "public/downloads/lady-d-finalization"

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
            f'<p class="prayer"><b>A short prayer</b>{esc(record["prayer"])}</p>'
            f'<p class="contd">Carry it with you -&gt;</p></div>{folio}</section>'
        )
        document = document[: b_match.start()] + rebuilt + document[b_match.end() :]

    document = clean_document_dashes(document)
    output_path = OUTPUT_DIR / f"volume-{volume}-{VOLUMES[volume]['slug']}-polished-devotional.html"
    output_path.write_text(document, encoding="utf-8")
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
        '<div class="deep-prayer">Father, gather what You have taught me this month. Show me the thread I nearly missed, strengthen the step I have begun, and carry Your word with me into what comes next. In Jesus\' name, Amen.</div>'
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

    document = clean_document_dashes(document)
    output_path = OUTPUT_DIR / f"volume-{volume}-{VOLUMES[volume]['slug']}-polished-companion-journal.html"
    output_path.write_text(document, encoding="utf-8")
    return output_path


def clean_document_dashes(document: str) -> str:
    return (
        document.replace("\u2014", " - ")
        .replace("\u2013", " - ")
        .replace("\u2011", "-")
        .replace("&mdash;", "-")
        .replace("&ndash;", "-")
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    for volume in range(1, 4):
        records = json.loads(
            (POLISHED_DIR / f"vol{volume}-polished-366-days.json").read_text(encoding="utf-8")
        )
        enrichment = json.loads(
            (ENRICHMENT_DIR / f"vol{volume}-enrichment-366-days.json").read_text(encoding="utf-8")
        )
        outputs.append(str(build_devotional(volume, records).relative_to(ROOT)))
        outputs.append(str(build_journal(volume, records, enrichment).relative_to(ROOT)))
    print(json.dumps({"outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
