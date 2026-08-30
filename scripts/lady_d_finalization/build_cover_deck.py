#!/usr/bin/env python3
"""Build the standalone Lady D cover decision deck from qualified real art."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "quality/finalization/lady-d-cover-qualification.json"
OUTPUT = ROOT / "public/lady-d-cover-decision-deck.html"

VOLUME = {
    1: {
        "title": "Surrendering to God's Love",
        "lane": "God the Father",
        "accent": "#9b4260",
        "subtitle": "A 365-Day Devotional Journey into the Father's Heart",
    },
    2: {
        "title": "Walking with Jesus",
        "lane": "Jesus the Son",
        "accent": "#427f69",
        "subtitle": "A 365-Day Devotional Journey of Daily Discipleship",
    },
    3: {
        "title": "Filled with the Holy Spirit",
        "lane": "The Holy Spirit",
        "accent": "#377ca8",
        "subtitle": "A 365-Day Devotional Journey of Power, Comfort, and Fire",
    },
}


def main() -> None:
    data = json.loads(DATA.read_text())
    cards = []
    table_rows = []
    for item in data["candidates"]:
        volume = VOLUME[item["volume"]]
        shortlist = " shortlisted" if item["id"] in data["shortlist"] else ""
        cards.append(f"""
        <article class="candidate{shortlist}" data-volume="{item['volume']}" data-id="{item['id']}">
          <div class="cover" style="--accent:{volume['accent']};background-image:url('{item['file']}')">
            <span class="volume">Volume {item['volume']}</span>
            <div class="type-lockup">
              <h3>{html.escape(volume['title'])}</h3>
              <p>{html.escape(volume['subtitle'])}</p>
              <b>Susan "Lady D" Damon</b>
            </div>
          </div>
          <div class="card-copy">
            <div class="rank"><span>#{item['volume_rank']} in Volume {item['volume']}</span><strong>{item['score']}</strong></div>
            <h2>{html.escape(item['direction'])}</h2>
            <p>{html.escape(item['rationale'])}</p>
            <dl>
              <div><dt>Brightness</dt><dd>{item['average_luminance']} / 255</dd></div>
              <div><dt>Dark mass</dt><dd>{item['dark_mass_percent']}%</dd></div>
              <div><dt>Brief fidelity</dt><dd>{item['brief_fidelity']} / 25</dd></div>
              <div><dt>Thumbnail</dt><dd>{item['thumbnail_clarity']} / 25</dd></div>
            </dl>
            <button type="button" class="select" data-select="{item['id']}">Shortlist this direction</button>
          </div>
        </article>""")
        table_rows.append(f"""
          <tr data-volume="{item['volume']}">
            <td>V{item['volume']}-{item['volume_rank']}</td>
            <td>{html.escape(item['direction'])}</td>
            <td>{item['genre_fit']}/30</td>
            <td>{item['thumbnail_clarity']}/25</td>
            <td>{item['brief_fidelity']}/25</td>
            <td>{item['distinction']}/20</td>
            <td><strong>{item['score']}</strong></td>
          </tr>""")

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lady D Cover Decision Deck</title>
  <style>
    :root{{--paper:#fbfaf7;--ink:#171c20;--muted:#667078;--line:#d8ddd9;--gold:#b88b3e;--wine:#7a3046;--green:#427f69;--blue:#377ca8}}
    *{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;letter-spacing:0}}
    header{{min-height:72vh;padding:28px clamp(22px,5vw,72px) 64px;display:grid;align-content:space-between;background:#172123;color:#fff;position:relative;overflow:hidden}}
    header:after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(12,19,20,.95),rgba(12,19,20,.58) 55%,rgba(12,19,20,.1)),url('/covers/lady-d-finalization/v1-a-her-golden-valley.png') center 54%/cover;opacity:.92}}
    header>*{{position:relative;z-index:1}} nav{{display:flex;justify-content:space-between;align-items:center;font-size:12px;text-transform:uppercase;font-weight:800}} nav a{{color:#fff;text-decoration:none}} .hero{{max-width:760px;padding-top:12vh}}
    .eyebrow{{font-size:12px;text-transform:uppercase;font-weight:800;color:#e6c77c}} h1{{font-family:Georgia,"Times New Roman",serif;font-size:clamp(48px,8vw,104px);line-height:.94;font-weight:500;margin:14px 0 24px;letter-spacing:0}} .hero>p{{font-family:Georgia,serif;font-size:clamp(18px,2vw,25px);line-height:1.45;margin:0;max-width:680px;color:#edf1eb}}
    .proof{{display:flex;gap:10px;flex-wrap:wrap;margin-top:28px}} .proof span{{border:1px solid rgba(255,255,255,.35);padding:9px 12px;border-radius:3px;font-size:12px;font-weight:700;background:rgba(13,22,23,.35)}}
    main{{padding:0 clamp(20px,5vw,72px) 80px}} .brief{{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(260px,.6fr);gap:48px;padding:64px 0;border-bottom:1px solid var(--line)}} .brief h2,.section-head h2{{font-family:Georgia,serif;font-size:clamp(34px,5vw,62px);font-weight:500;margin:0 0 18px;letter-spacing:0}} .brief p{{font-family:Georgia,serif;font-size:20px;line-height:1.55;color:#374147;margin:0}} blockquote{{margin:0;padding:24px;border-left:4px solid var(--gold);background:#f2eee3;font-family:Georgia,serif;font-size:20px;line-height:1.5}}
    .filters{{display:flex;gap:8px;flex-wrap:wrap;padding:28px 0;position:sticky;top:0;background:rgba(251,250,247,.94);backdrop-filter:blur(12px);z-index:5;border-bottom:1px solid var(--line)}} .filters button{{border:1px solid var(--line);background:#fff;padding:10px 14px;border-radius:4px;font-weight:800;color:var(--ink);cursor:pointer}} .filters button.active{{background:var(--ink);color:#fff;border-color:var(--ink)}}
    .section-head{{display:flex;justify-content:space-between;gap:24px;align-items:end;padding:52px 0 24px}} .section-head p{{max-width:520px;color:var(--muted);line-height:1.55}}
    .gallery{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}} .candidate{{border-top:4px solid var(--accent,#b88b3e);background:#fff;box-shadow:0 10px 30px rgba(17,28,30,.08)}} .candidate[hidden]{{display:none}} .candidate.shortlisted{{outline:2px solid #c49a4b;outline-offset:3px}}
    .cover{{aspect-ratio:2/3;background-size:cover;background-position:center;position:relative;color:#fff;overflow:hidden}} .cover:after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(8,12,13,.12) 0%,transparent 36%,transparent 55%,rgba(8,12,13,.78) 100%)}} .volume{{position:absolute;z-index:2;top:18px;left:18px;padding:6px 9px;background:var(--accent);font-size:10px;font-weight:900;text-transform:uppercase;border-radius:3px}}
    .type-lockup{{position:absolute;z-index:2;left:22px;right:22px;bottom:24px;text-shadow:0 2px 14px rgba(0,0,0,.75)}} .type-lockup h3{{font-family:Georgia,serif;font-size:clamp(27px,3.2vw,48px);line-height:.96;font-weight:500;margin:0 0 10px;letter-spacing:0}} .type-lockup p{{font-family:Georgia,serif;font-size:12px;line-height:1.35;margin:0 0 16px;max-width:280px}} .type-lockup b{{font-size:10px;text-transform:uppercase}}
    .card-copy{{padding:22px}} .rank{{display:flex;justify-content:space-between;align-items:center;text-transform:uppercase;font-size:11px;font-weight:900;color:var(--muted)}} .rank strong{{font-family:Georgia,serif;font-size:32px;color:var(--accent)}} .card-copy h2{{font-family:Georgia,serif;font-size:30px;font-weight:500;margin:10px 0;letter-spacing:0}} .card-copy>p{{min-height:76px;color:#4d565c;line-height:1.5}}
    dl{{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);border:1px solid var(--line);margin:20px 0}} dl div{{background:#fff;padding:10px}} dt{{font-size:10px;text-transform:uppercase;color:var(--muted);font-weight:800}} dd{{margin:4px 0 0;font-weight:800}} .select{{width:100%;padding:12px;border:0;border-radius:3px;background:var(--ink);color:#fff;font-weight:800;cursor:pointer}} .select.chosen{{background:var(--accent)}}
    .ranking{{margin-top:72px;overflow:auto}} table{{width:100%;border-collapse:collapse;min-width:740px}} th,td{{text-align:left;padding:14px 12px;border-bottom:1px solid var(--line)}} th{{font-size:11px;text-transform:uppercase;color:var(--muted)}}
    .decision{{margin-top:72px;padding:36px;background:#172123;color:#fff;display:grid;grid-template-columns:1fr auto;gap:32px;align-items:center}} .decision h2{{font-family:Georgia,serif;font-size:40px;font-weight:500;margin:0 0 10px;letter-spacing:0}} .decision p{{color:#cfd9d5;line-height:1.5;margin:0}} .decision button{{padding:14px 18px;border:0;border-radius:3px;background:#e6c77c;color:#172123;font-weight:900;cursor:pointer}}
    footer{{padding:32px clamp(20px,5vw,72px);display:flex;justify-content:space-between;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}}
    @media(max-width:900px){{.gallery{{grid-template-columns:repeat(2,minmax(0,1fr))}}.brief{{grid-template-columns:1fr}}}}
    @media(max-width:620px){{header{{min-height:82vh}}.gallery{{grid-template-columns:1fr}}.section-head{{display:block}}.card-copy>p{{min-height:0}}.decision{{grid-template-columns:1fr}}footer{{display:block}}}}
    @media print{{header{{min-height:5.5in;break-after:page}}.filters,.select,.decision button{{display:none}}main{{padding:0 16px}}.gallery{{grid-template-columns:repeat(3,1fr);gap:12px}}.candidate{{break-inside:avoid;box-shadow:none;border:1px solid #bbb}}.card-copy{{padding:12px}}.card-copy>p{{min-height:0;font-size:11px}}dl{{font-size:10px}}}}
  </style>
</head>
<body>
  <header>
    <nav><span>IDC Publishing / Author Review</span><a href="/">Lady D Hub</a></nav>
    <div class="hero">
      <span class="eyebrow">Real Art / Qualified / Ready for Author Selection</span>
      <h1>Luminous Cover Family</h1>
      <p>Ten cover candidates built from Lady D's own descriptions, corrected against her brightness feedback, and presented as one coherent Father, Son, and Spirit journey.</p>
      <div class="proof"><span>10 qualified renders</span><span>161.8-205.6 luminance</span><span>0.4-13.5% dark mass</span><span>No baked text</span></div>
    </div>
  </header>
  <main>
    <section class="brief">
      <div><span class="eyebrow">The Author's Direction</span><h2>Bright enough to carry the message.</h2><p>The first cover round had meaning, but its dark framing weakened the shelf presence. This round keeps what Lady D named: the golden valley, woman in white, eagle and flowers; the footsteps she praised for Jesus; and a dove, flame, wind, water, and opening sky for the Spirit.</p></div>
      <blockquote>"If they were all sitting on the shelf, they just look dark... They're not bright."<br><br><strong>- Lady D</strong></blockquote>
    </section>
    <div class="filters" role="group" aria-label="Filter cover candidates">
      <button class="active" data-filter="all">All ten</button>
      <button data-filter="1">Volume I / Father</button>
      <button data-filter="2">Volume II / Son</button>
      <button data-filter="3">Volume III / Spirit</button>
    </div>
    <section>
      <div class="section-head"><div><span class="eyebrow">Selection Gallery</span><h2>Real choices, one matched family.</h2></div><p>Volume II includes a fourth author-directed Footprints variation. The top-ranked image in each volume is pre-shortlisted, not pre-selected.</p></div>
      <div class="gallery">{''.join(cards)}</div>
    </section>
    <section class="ranking">
      <div class="section-head"><div><span class="eyebrow">Qualification + Editorial Review</span><h2>Ranking ledger.</h2></div><p>All images first passed dimensions, luminance, and dark-mass gates. Editorial scoring then follows the Joyce deck rubric.</p></div>
      <table><thead><tr><th>Rank</th><th>Direction</th><th>Genre</th><th>Thumbnail</th><th>Brief</th><th>Distinction</th><th>Total</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table>
    </section>
    <section class="decision"><div><h2>Author shortlist</h2><p id="selection-copy">Preloaded: Her Golden Valley / Footsteps at Dawn / After the Rain.</p></div><button id="copy-selection" type="button">Copy selection</button></section>
  </main>
  <footer><span>Susan "Lady D" Damon / Cover Decision Deck</span><span>IDC Publishing / August 30, 2026</span></footer>
  <script>
    const defaults = ['v1-a-her-golden-valley','v2-d-carried-on-the-way','v3-c-after-rain'];
    const selection = new Set(defaults);
    const names = Object.fromEntries([...document.querySelectorAll('.candidate')].map(card => [card.dataset.id, card.querySelector('.card-copy h2').textContent]));
    function renderSelection() {{
      document.querySelectorAll('[data-select]').forEach(button => {{
        const chosen = selection.has(button.dataset.select);
        button.classList.toggle('chosen', chosen);
        button.textContent = chosen ? 'Shortlisted' : 'Shortlist this direction';
      }});
      document.getElementById('selection-copy').textContent = [...selection].map(id => names[id]).join(' / ') || 'No directions shortlisted yet.';
    }}
    document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {{
      document.querySelectorAll('[data-filter]').forEach(item => item.classList.remove('active'));
      button.classList.add('active');
      const filter = button.dataset.filter;
      document.querySelectorAll('.candidate').forEach(card => card.hidden = filter !== 'all' && card.dataset.volume !== filter);
    }}));
    document.querySelectorAll('[data-select]').forEach(button => button.addEventListener('click', () => {{
      selection.has(button.dataset.select) ? selection.delete(button.dataset.select) : selection.add(button.dataset.select);
      renderSelection();
    }}));
    document.getElementById('copy-selection').addEventListener('click', async () => {{
      const text = 'Lady D cover shortlist: ' + ([...selection].map(id => names[id]).join(' / ') || 'none');
      await navigator.clipboard.writeText(text);
      document.getElementById('copy-selection').textContent = 'Copied';
      setTimeout(() => document.getElementById('copy-selection').textContent = 'Copy selection', 1400);
    }});
    renderSelection();
  </script>
</body>
</html>"""
    OUTPUT.write_text(document)
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    main()
