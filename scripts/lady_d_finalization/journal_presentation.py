"""Customer-facing reader and gallery, sharing the same print-page content."""

from html import escape

TITLE = "Thirty-One Mornings of Light"
HOME = "https://lady-d-author-review-site.vercel.app/"
READER = "lady-d-31-day-visual-journal.html"
GALLERY = "lady-d-31-day-visual-journal-scene-console.html"
PDF = "downloads/lady-d-finalization/Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf"


def icon(name):
    return f'<img class="icon" src="assets/lady-d-reader/{name}.svg" alt="" width="20" height="20">'


def head(title):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="description" content="Thirty-one illustrated moments of Scripture, prayer, and encouragement by Susan Lady D Damon.">
<title>{escape(title)} | Lady D</title>
<link rel="stylesheet" href="assets/lady-d-reader/reader.css">
<script defer src="assets/lady-d-reader/reader.js"></script></head>'''


def topbar(gallery=False):
    return f'''<a class="skip-link" href="#main">Skip to reading</a>
<nav class="topbar" aria-label="Journal navigation">
<a class="author-brand" href="{HOME}">{icon('house')}<span>Lady D <small>Devotional Library</small></span></a>
<div class="top-actions"><a class="nav-link" href="{READER if gallery else GALLERY}" aria-label="{'Read the journal' if gallery else 'All 31 days'}" title="{'Read the journal' if gallery else 'All 31 days'}">{icon('book-open' if gallery else 'grid-2x2')}<span>{'Read the journal' if gallery else 'All 31 days'}</span></a>
<a class="nav-link" href="{PDF}" download aria-label="Download PDF" title="Download PDF">{icon('download')}<span>Download PDF</span></a></div></nav>'''


def render_journal(corpus, pages):
    options = ''.join(f'<option value="{d["day"]}">{d["day"]:02d} · {escape(d["title"])}</option>' for d in corpus['days'])
    return f'''{head(TITLE)}<body class="journal-reader">{topbar()}
<header class="reader-heading"><p class="eyebrow">Scripture · prayer · a little light for today</p>
<h1>{TITLE}</h1><p class="byline">By Susan &ldquo;Lady D&rdquo; Damon</p></header>
<main id="main" tabindex="-1">
<div class="reader-controls" hidden>
<div class="day-select"><label for="day-select">Your day</label><select id="day-select">{options}</select></div>
<div class="view-switch" role="group" aria-label="Reading view">
<button type="button" data-view="page" aria-pressed="true" aria-label="Illustrated page" title="Illustrated page">{icon('image')}<span>Illustrated</span></button>
<button type="button" data-view="text" aria-pressed="false" aria-label="Larger reading text" title="Larger reading text">{icon('book-open')}<span>Read text</span></button></div></div>
<div class="book">{pages}</div>
<article class="reading-panel" aria-label="Today's reading" hidden></article>
<nav class="page-turner" aria-label="Turn the page" hidden>
<button type="button" id="previous-day" class="icon-button" aria-label="Previous day" title="Previous day">{icon('chevron-left')}</button>
<p id="page-status" role="status" aria-live="polite" aria-atomic="true">Day 01 of 31 · Held</p>
<button type="button" id="next-day" class="icon-button" aria-label="Next day" title="Next day">{icon('chevron-right')}</button></nav>
</main><footer class="reader-footer">A little hope to carry with you. <a href="{GALLERY}">Explore the whole journey</a><small>Author review edition</small></footer>
</body></html>'''


def render_console(corpus):
    groups = []
    for movement in corpus['movements']:
        cards = []
        for day in corpus['days']:
            if day['movement'] != movement['id']:
                continue
            cards.append(f'''<article class="gallery-day"><a href="{READER}#day-{day['day']:02d}">
<div class="gallery-art"><img src="{escape(day['art'])}" alt="{escape(day['scene'].split('. ')[0])}" width="1800" height="2700" loading="lazy" decoding="async"><span class="gallery-number">{day['day']:02d}</span></div>
<div class="gallery-copy"><h3>{escape(day['title'])}</h3><p>{escape(day['affirmation'])}</p><span>{escape(day['reference'])} · KJV</span></div></a></article>''')
        groups.append(f'''<section class="gallery-movement" data-movement="{movement['id']}" id="movement-{movement['id']}"><header><p class="eyebrow">Days {escape(movement['days'])}</p><h2>{escape(movement['title'])}</h2><p>{escape(movement['promise'])}</p></header><div class="gallery-grid">{''.join(cards)}</div></section>''')
    return f'''{head('The 31-Day Gallery')}<body class="gallery-body">{topbar(True)}
<header class="gallery-heading"><p class="eyebrow">Thirty-One Mornings of Light</p><h1>A day for the heart<br>you bring today.</h1><p>Quiet rooms. Open skies. A faithful presence through it all.</p></header>
<nav class="movement-nav" aria-label="Movements of the journal">{''.join(f'<a href="#movement-{m["id"]}">{escape(m["title"])}</a>' for m in corpus['movements'])}</nav>
<main id="main" class="gallery-main" tabindex="-1">{''.join(groups)}</main>
<footer class="reader-footer">Susan &ldquo;Lady D&rdquo; Damon · Author review edition <a href="{READER}">Return to the journal</a></footer></body></html>'''
