#!/usr/bin/env python3
"""Build KDP interior finalization artifacts for the Lady D trilogy."""

from __future__ import annotations

import html
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "downloads" / "production" / "kdp" / "interior-finalization"
PUBLIC_OUT = ROOT / "public" / "downloads" / "production" / "kdp" / "interior-finalization"
PUBLIC_PAGE = ROOT / "public" / "release-status.html"
SOURCE_PAGE = ROOT / "release-status.html"
LIBRARY_ROOT = Path("/Users/IDC2.5/Documents/LADY D/Production Library")
SHARED_LIBRARY = LIBRARY_ROOT / "_Shared" / "KDP Readiness" / "Interior Finalization"


@dataclass(frozen=True)
class Book:
    volume: int
    title: str
    subtitle: str
    lane: str
    manuscript_pages: int
    journal_pages: int
    manuscript_words: int
    journal_words: int
    sabbath_mentions: int
    folder: str
    cover_width_white: str
    cover_width_cream: str


BOOKS = [
    Book(
        1,
        "Surrendering to God's Love",
        "A 365-Day Devotional Journey into the Father's Heart",
        "God the Father / love, identity, surrender, forgiveness, timing, daily trust",
        409,
        94,
        131305,
        20799,
        274,
        "01 Surrendering to God's Love",
        "13.171 x 9.250 in",
        "13.273 x 9.250 in",
    ),
    Book(
        2,
        "Walking with Jesus",
        "A 365-Day Devotional Journey with the Son",
        "Jesus / discipleship, nearness, obedience, healing, following, abiding",
        350,
        81,
        98804,
        18940,
        294,
        "02 Walking with Jesus",
        "13.038 x 9.250 in",
        "13.125 x 9.250 in",
    ),
    Book(
        3,
        "Filled with the Holy Spirit",
        "A 365-Day Devotional Journey of Power, Comfort, and Fire",
        "Holy Spirit / filling, comfort, conviction, gifts, fruit, rain, oil, breath",
        339,
        90,
        95247,
        19003,
        188,
        "03 Filled with the Holy Spirit",
        "13.013 x 9.250 in",
        "13.098 x 9.250 in",
    ),
]


def current_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in content.rstrip().splitlines())
    path.write_text(cleaned + "\n")


def front_back_template(book: Book) -> str:
    return f"""# {book.title} - KDP Front and Back Matter Template

Generated: 2026-07-01

Status: Draft publishing template. This is not legal advice and is not the final KDP upload file.

## Book Metadata

- Title: {book.title}
- Subtitle: {book.subtitle}
- Author line: Susan "Lady D" Damon
- Series: Lady D Devotional Library
- Volume: {book.volume}
- Spiritual lane: {book.lane}
- Current manuscript review pages: {book.manuscript_pages}
- Current companion journal review pages: {book.journal_pages}

## Recommended Front Matter Order

1. Half-title page: `{book.title}`
2. Series page: `Lady D Devotional Library`
3. Title page: `{book.title}` / `{book.subtitle}` / `Susan "Lady D" Damon`
4. Copyright page with final copyright owner, ISBN, imprint, permissions, and edition data.
5. Dedication page: `[Author-provided dedication goes here.]`
6. Author welcome: a short note from Susan "Lady D" Damon in her own voice.
7. How to use this devotional.
8. Scripture and permissions note.
9. Sabbath and grace framing note.
10. Reader orientation.
11. January 1 devotional entry.

## Draft Copyright Page Text

Copyright (c) 2026 Susan Damon. All rights reserved.

Published by IDC Publishing.

ISBN: [TBD]

No part of this publication may be reproduced, stored, or transmitted in any form without written permission from the publisher, except for brief quotations in reviews or devotional discussion.

Scripture references are included in the current review manuscript without full Bible text. If final Bible quotation text is added, insert the exact required copyright and permission notice for the selected Bible translation before KDP upload.

This devotional is written from a Seventh-day Adventist Christian frame. Sabbath language refers to the seventh-day/Saturday Sabbath. Obedience is presented as a response to God's grace, not a means of earning God's love.

## Draft Author Welcome

Dear reader,

This devotional year is an invitation to meet God in the real morning, before the day has had time to name you. Bring your questions, your unfinished places, your family burdens, your hopes, and your need for grace. Let the Lord speak first. Let Scripture steady your steps. Let prayer become practical enough to walk out before noon.

My prayer is that each entry helps you receive God's love more deeply and respond with a life more surrendered, more honest, and more available to Him.

With love,

Susan "Lady D" Damon

## Draft How to Use This Devotional

1. Begin with the Scripture reference.
2. Read the devotional slowly, listening for one phrase that meets your real life.
3. Pray the prayer aloud or rewrite it in your own words.
4. Use the journal prompt to tell the truth before God.
5. Take the Today step before the day gets crowded.
6. Let the morning impact line become a small act of obedience.

## Draft Sabbath and Grace Framing Note

Throughout this devotional, Sabbath refers to the seventh-day/Saturday Sabbath. The goal is not religious performance. Sabbath is treated as a gift of rest, worship, trust, and holy rhythm. Obedience is framed as the fruit of receiving God's grace, not a way to earn His love.

## Recommended Back Matter Order

1. Closing year-end reflection.
2. Invitation to use the companion journal.
3. Prayer of surrender for the next season.
4. About Susan "Lady D" Damon.
5. About IDC Publishing.
6. Other volumes in the Lady D Devotional Library.
7. Acknowledgments.

## Draft Closing Reflection

You have walked through a year of Scripture, prayer, surrender, and practical obedience. Do not rush past what God has formed. Return to the entries that still speak. Carry the prayers into the next season. Let the Lord continue what He has begun.

## Required Before Final Upload

- Replace all placeholders.
- Lock final Bible translation and permissions statement.
- Confirm copyright owner and ISBN.
- Confirm author dedication, acknowledgments, and author bio.
- Run final copyedit and theological review.
- Re-export final interior PDF from the designed 6 x 9 template.
- Run KDP Previewer and proof-order review.
"""


def kit_markdown(commit: str) -> str:
    rows = "\n".join(
        f"| Volume {b.volume} | {b.title} | {b.manuscript_pages} | {b.journal_pages} | "
        f"{b.cover_width_white} | {b.cover_width_cream} |" for b in BOOKS
    )
    template_links = "\n".join(
        f"- Volume {b.volume}: `front-back-matter-template-volume-{b.volume}.md`" for b in BOOKS
    )
    return f"""# Lady D KDP Interior Finalization Kit

Generated: 2026-07-01

Repo commit at generation: `{commit}`

Status: Production-planning kit. This is not a final KDP upload package.

## Purpose

The three dated devotional manuscripts are complete at 365 dated entries plus the February 29 bonus for each volume. This kit turns the next publishing phase into a concrete checklist: front matter, back matter, permissions, trim readiness, final interior design, and KDP upload gates.

## Current Book Matrix

| Volume | Title | Manuscript review pages | Journal review pages | White-paper full-wrap working size | Cream-paper full-wrap working size |
| --- | --- | ---: | ---: | --- | --- |
{rows}

## Completed Production Evidence

- 1,098 day cards across the three volumes.
- Three master interior manuscripts in Markdown, DOCX, and PDF.
- Three master companion journals in Markdown, DOCX, and PDF.
- Master assembly audit result: pass.
- Sabbath guardrail preserved: Sunday mentions remain zero in master manuscripts and journals.
- Nine 6 x 9 front-cover art candidates.
- Path-route full-wrap draft pack for the three main manuscripts.
- KDP trim and cover readiness worksheet.
- Public Vercel review page for author-facing review.

## Interior Finalization Deliverables In This Kit

{template_links}

- `lady-d-kdp-interior-finalization-kit.md`
- `lady-d-kdp-interior-finalization-kit.docx`
- `lady-d-kdp-interior-finalization-kit.pdf`
- `lady-d-release-readiness-dashboard.html`
- `Lady-D-KDP-Interior-Finalization-Kit.zip`

## Standard Front Matter System

Use this order unless the author or publisher makes a deliberate change:

1. Half-title page.
2. Series page.
3. Title page.
4. Copyright page.
5. Dedication.
6. Author welcome.
7. How to use this devotional.
8. Scripture and permissions note.
9. Sabbath and grace framing note.
10. Reader orientation.
11. January 1 devotional entry.

## Standard Back Matter System

1. Closing year-end reflection.
2. Companion journal invitation.
3. Prayer of surrender for the next season.
4. About Susan "Lady D" Damon.
5. About IDC Publishing.
6. Other volumes in the Lady D Devotional Library.
7. Acknowledgments.

## Permissions Gate

The current manuscripts include Scripture references, not full Bible quotation text. Before KDP upload, choose one of these paths:

1. Keep references only and avoid adding Bible quotation text.
2. Add full Scripture text only after selecting a translation and inserting its required copyright and permission notice.
3. If using public-domain text, still disclose the translation/source clearly and consistently.

## Adventist Guardrail

Sabbath means seventh-day/Saturday Sabbath. Obedience must remain response to grace, not a way to earn God's love. Any final copyedit, typesetting, metadata, or marketing copy must preserve that theological frame.

## Judge And Auditor Loop

Run three to seven passes depending on risk:

1. Editorial judge: reader clarity, voice, flow, and author-heart fit.
2. Theological auditor: Sabbath frame, grace/obedience frame, Jesus-centered Spirit language.
3. Permissions auditor: Bible references/quotations, copyright notice, ISBN/imprint data.
4. Production auditor: 6 x 9 margins, page count, running heads, page numbers, image resolution.
5. Retail judge: cover thumbnail readability, Amazon metadata, description, categories, and series cohesion.
6. Proof auditor: KDP Previewer, printed proof, spine alignment, trim, bleed, and barcode area.
7. Final release judge: all blockers closed and no placeholder text remains.

## Remaining Gates Before True KDP Upload

- Final paper type and trim choices.
- Final front matter and back matter approval.
- Final author bio, dedication, acknowledgments, and ISBN.
- Final Bible permissions statement.
- Final copyedit of all three manuscripts and journals.
- Final 6 x 9 designed interiors with locked page counts.
- Regenerated full-wrap covers from final page counts.
- KDP Previewer pass for each upload file.
- Physical proof review before public release.

## Recommended Next Production Step

Build the final 6 x 9 interior template for Volume 1 first, using the front/back matter template in this kit. Once the template passes render QA, apply the same system to Volumes 2 and 3, then to the companion journals.
"""


def dashboard_html(commit: str) -> str:
    cards = "".join(
        f"""
        <article class="card">
          <span>Volume {b.volume}</span>
          <h3>{html.escape(b.title)}</h3>
          <p>{html.escape(b.subtitle)}</p>
          <p><strong>Lane:</strong> {html.escape(b.lane)}</p>
          <dl>
            <div><dt>Manuscript</dt><dd>{b.manuscript_pages} pages / {b.manuscript_words:,} words</dd></div>
            <div><dt>Journal</dt><dd>{b.journal_pages} pages / {b.journal_words:,} words</dd></div>
            <div><dt>Status</dt><dd>Dated manuscript and journal review files are built. Final designed interior is still required.</dd></div>
            <div><dt>White-paper cover</dt><dd>{b.cover_width_white}</dd></div>
            <div><dt>Cream-paper cover</dt><dd>{b.cover_width_cream}</dd></div>
          </dl>
        </article>
        """
        for b in BOOKS
    )
    completed = [
        "1,098 devotional day cards generated and live.",
        "Three master manuscripts assembled in Markdown, DOCX, and PDF.",
        "Three companion journals assembled in Markdown, DOCX, and PDF.",
        "Nine 6 x 9 front-cover art candidates generated.",
        "Path-route full-wrap draft covers generated for the three main manuscripts.",
        "KDP trim and cover worksheet generated from official KDP guidance.",
        "Interior finalization front/back matter templates created for all three volumes.",
    ]
    remaining = [
        "Final paper type and ISBN/barcode data.",
        "Author-approved dedication, acknowledgments, and bio.",
        "Final Bible translation permissions statement.",
        "Final copyedit and theological proof pass.",
        "Final designed 6 x 9 interiors with locked page counts.",
        "Regenerated full-wrap covers from locked page counts.",
        "KDP Previewer and physical proof review.",
    ]
    completed_html = "".join(f"<li>{html.escape(item)}</li>" for item in completed)
    remaining_html = "".join(f"<li>{html.escape(item)}</li>" for item in remaining)
    guardrails = [
        "Sabbath remains seventh-day/Saturday Sabbath throughout the release lane.",
        "Obedience remains a response to God's grace, not a method of earning God's love.",
        "Final copyedit and metadata must preserve the Adventist theological frame.",
        "Scripture references may stay reference-only unless a final translation permission statement is added.",
    ]
    guardrails_html = "".join(f"<li>{html.escape(item)}</li>" for item in guardrails)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lady D Release Readiness Dashboard</title>
  <style>
    :root {{
      --ink: #111827;
      --paper: #fffdf8;
      --mist: #f5f2eb;
      --indigo: #182646;
      --teal: #1d716f;
      --gold: #c99335;
      --line: rgba(17, 24, 39, .14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, var(--paper), var(--mist));
      line-height: 1.5;
    }}
    header, main {{ max-width: 1180px; margin: 0 auto; padding: 34px 22px; }}
    h1, h2, h3 {{ font-family: Georgia, "Times New Roman", serif; line-height: 1.05; margin: 0 0 14px; letter-spacing: 0; }}
    h1 {{ font-size: clamp(42px, 7vw, 84px); max-width: 960px; }}
    h2 {{ font-size: clamp(28px, 4vw, 48px); }}
    p {{ margin: 0 0 14px; }}
    .lead {{ font-size: clamp(18px, 2vw, 23px); max-width: 820px; color: #2e3746; }}
    .kicker {{ color: var(--teal); font-weight: 900; letter-spacing: .14em; text-transform: uppercase; font-size: 12px; margin-bottom: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    .card, .panel {{
      border: 1px solid var(--line);
      background: white;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 18px 50px rgba(24, 38, 70, .10);
    }}
    .card span {{ color: var(--gold); font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: .12em; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .actions a {{
      display: inline-flex;
      align-items: center;
      min-height: 38px;
      padding: 8px 11px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--teal);
      background: white;
      font-size: 13px;
      font-weight: 900;
      text-decoration: none;
    }}
    dl {{ margin: 16px 0 0; display: grid; gap: 10px; }}
    dt {{ font-weight: 900; color: var(--indigo); }}
    dd {{ margin: 0; color: #374151; }}
    section {{ border-top: 1px solid var(--line); padding: 34px 0; }}
    ul {{ margin: 0; padding-left: 22px; }}
    li {{ margin: 8px 0; }}
    .status {{ display: inline-block; background: var(--indigo); color: white; padding: 7px 10px; border-radius: 999px; font-size: 12px; font-weight: 900; }}
    a {{ color: var(--teal); text-underline-offset: 3px; }}
  </style>
</head>
<body>
  <header>
    <div class="kicker">IDC Publishing release dashboard</div>
    <h1>Lady D Devotional Library release readiness</h1>
    <p class="lead">The three devotional manuscripts are complete at the dated-entry level and now have master assemblies, companion journals, cover candidates, KDP trim math, full-wrap drafts, and interior finalization templates. This dashboard separates what is complete from what still gates true KDP upload readiness.</p>
    <p><span class="status">Generated 2026-07-01</span> <span class="status">Base commit: {html.escape(commit)}</span></p>
    <div class="actions">
      <a href="production.html">Production Review</a>
      <a href="downloads/production/kdp/interior-finalization/Lady-D-KDP-Interior-Finalization-Kit.zip">Interior Kit ZIP</a>
      <a href="downloads/production/kdp/interior-finalization/lady-d-kdp-interior-finalization-kit.pdf">Interior Kit PDF</a>
    </div>
  </header>
  <main>
    <section>
      <h2>Book Status</h2>
      <div class="grid">{cards}</div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>Finalized So Far</h2>
        <ul>{completed_html}</ul>
      </div>
      <div class="panel">
        <h2>Remaining Gates Before KDP Upload</h2>
        <ul>{remaining_html}</ul>
      </div>
      <div class="panel">
        <h2>Guardrail Snapshot</h2>
        <ul>{guardrails_html}</ul>
      </div>
    </section>
    <section>
      <h2>Active Recommendation</h2>
      <p class="lead">Build the final Volume 1 6 x 9 interior template first, then apply the same design system to Volumes 2 and 3 and the companion journals. Do not mark any file as final upload-ready until KDP Previewer and physical proof review pass.</p>
      <p><a href="production.html">Return to production review page</a></p>
    </section>
  </main>
</body>
</html>
"""


def make_zip(paths: list[Path]) -> Path:
    zip_path = OUT / "Lady-D-KDP-Interior-Finalization-Kit.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            zf.write(path, path.name)
    shutil.copy2(zip_path, PUBLIC_OUT / zip_path.name)
    shutil.copy2(zip_path, SHARED_LIBRARY / zip_path.name)
    return zip_path


def main() -> None:
    commit = current_commit()
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUT.mkdir(parents=True, exist_ok=True)
    SHARED_LIBRARY.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []

    for book in BOOKS:
        path = OUT / f"front-back-matter-template-volume-{book.volume}.md"
        write(path, front_back_template(book))
        generated.append(path)
        shutil.copy2(path, PUBLIC_OUT / path.name)
        book_dir = LIBRARY_ROOT / book.folder / "06 Master Assembly"
        shutil.copy2(path, book_dir / path.name)

    kit = OUT / "lady-d-kdp-interior-finalization-kit.md"
    write(kit, kit_markdown(commit))
    generated.append(kit)
    shutil.copy2(kit, PUBLIC_OUT / kit.name)
    shutil.copy2(kit, SHARED_LIBRARY / kit.name)

    dashboard = OUT / "lady-d-release-readiness-dashboard.html"
    write(dashboard, dashboard_html(commit))
    generated.append(dashboard)
    shutil.copy2(dashboard, PUBLIC_OUT / dashboard.name)
    shutil.copy2(dashboard, SOURCE_PAGE)
    shutil.copy2(dashboard, PUBLIC_PAGE)
    shutil.copy2(dashboard, SHARED_LIBRARY / dashboard.name)

    zip_path = make_zip(generated)
    print({"kit": str(kit.relative_to(ROOT)), "dashboard": str(dashboard.relative_to(ROOT)), "zip": str(zip_path.relative_to(ROOT))})


if __name__ == "__main__":
    main()
