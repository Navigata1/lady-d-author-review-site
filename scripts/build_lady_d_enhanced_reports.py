#!/usr/bin/env python3
from __future__ import annotations

import base64
import glob
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

DATE = "2026-07-19"
STATE_FILE = f"lady-d-enhanced-state-of-the-union-{DATE}.html"
PLAN_FILE = f"lady-d-enhanced-plan-of-attack-{DATE}.html"

PACKAGE_TOTAL = 2000
PRIOR_PAID = 200
CHECK_PAID = 400
PAID_TOTAL = PRIOR_PAID + CHECK_PAID
BALANCE_DUE = PACKAGE_TOTAL - PAID_TOTAL

LOGO = ROOT / "assets" / "idc-palm-logo.png"
PROOF_JSON = ROOT / "downloads" / "production" / "kdp" / "proof-decision-application" / "proof-decision-application.json"
VOLUME1_MASTER = ROOT / "downloads" / "production" / "master" / "volume-1-master-interior-manuscript.md"
LINE_EDIT_ROOT = ROOT / "downloads" / "production" / "kdp" / "author-voice-line-edit"

BOOKS = [
    {
        "vol": "Volume 1",
        "title": "Surrendering to God's Love",
        "focus": "The Father's love, identity, surrender, forgiveness, timing, trust.",
        "words": 128276,
        "sabbath": 302,
        "status": "266 impact edits completed; 100 old impact templates remain before full line-edit lock.",
    },
    {
        "vol": "Volume 2",
        "title": "Walking with Jesus",
        "focus": "Jesus, discipleship, nearness, obedience as response, daily walk.",
        "words": 95114,
        "sabbath": 300,
        "status": "Architecture assembled; needs scripture-visible sample rebuild and voice-depth pass.",
    },
    {
        "vol": "Volume 3",
        "title": "Filled with the Holy Spirit",
        "focus": "Holy Spirit, comfort, filling, fruit, courage, Spirit-led formation.",
        "words": 91521,
        "sabbath": 194,
        "status": "Architecture assembled; needs repetition audit and living-language pass.",
    },
]

JOURNALS = [
    {"title": "Surrendering to God's Love Companion Journal", "words": 19854, "pages": 470, "sabbath": 177},
    {"title": "Walking with Jesus Companion Journal", "words": 17134, "pages": 477, "sabbath": 206},
    {"title": "Filled with the Holy Spirit Companion Journal", "words": 17665, "pages": 483, "sabbath": 143},
]


def money(value: int) -> str:
    return f"${value:,.0f}"


def data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def proof_stats() -> dict:
    default = {
        "products": 6,
        "words": 369564,
        "sunday_mentions": 0,
        "sabbath_mentions": 1322,
        "placeholder_markers": 0,
        "decision_items": 0,
        "review_required_contexts": 0,
    }
    if not PROOF_JSON.exists():
        return default
    data = json.loads(PROOF_JSON.read_text(encoding="utf-8"))
    proof = data.get("current_proof_audit_totals", {})
    queue = data.get("current_queue_totals", {})
    return {
        "products": proof.get("products", default["products"]),
        "words": proof.get("words", default["words"]),
        "sunday_mentions": proof.get("sunday_mentions", default["sunday_mentions"]),
        "sabbath_mentions": proof.get("sabbath_mentions", default["sabbath_mentions"]),
        "placeholder_markers": queue.get("placeholder_markers", default["placeholder_markers"]),
        "decision_items": queue.get("decision_items", default["decision_items"]),
        "review_required_contexts": proof.get("review_required_contexts", default["review_required_contexts"]),
    }


def line_edit_stats() -> dict:
    total = 0
    files = sorted(LINE_EDIT_ROOT.glob("*/volume-1-*-line-edit.json"))
    for path in files:
        try:
            total += len(json.loads(path.read_text(encoding="utf-8")).get("entries", []))
        except Exception:
            continue
    stale = 0
    if VOLUME1_MASTER.exists():
        stale = VOLUME1_MASTER.read_text(encoding="utf-8", errors="ignore").count("Let the Father's love carry")
    return {
        "batch_files": len(files),
        "edited_entries": total,
        "stale_volume1_impact_templates": stale,
    }


def latest_benchmark() -> dict:
    paths = sorted(glob.glob("/tmp/lady-d-template-benchmark-*/benchmark.json"))
    if not paths:
        return {
            "dir": "not captured in this session",
            "checks": 0,
            "all_200": False,
            "console_errors": 0,
            "missing_images": 0,
            "overflow_total": 0,
        }
    latest = Path(paths[-1])
    data = json.loads(latest.read_text(encoding="utf-8"))
    results = data.get("results", [])
    return {
        "dir": data.get("dir", str(latest.parent)),
        "checks": len(results),
        "all_200": all(r.get("status") == 200 for r in results),
        "console_errors": sum(len(r.get("errors", [])) for r in results),
        "missing_images": sum(r.get("missingImageCount", 0) for r in results),
        "overflow_total": sum(r.get("xOverflow", 0) for r in results),
        "titles": sorted({r.get("title", "") for r in results if r.get("title")}),
    }


STATS = proof_stats()
LINE = line_edit_stats()
BENCH = latest_benchmark()
LOGO_URI = data_uri(LOGO)


STYLE = r"""
:root{
  color-scheme:dark;
  --bg:#06111f;
  --ink:#eef7f6;
  --muted:#aec1c5;
  --line:rgba(203,224,222,.18);
  --panel:#0e2134;
  --panel2:#112b3f;
  --teal:#20c7ad;
  --blue:#82b8ff;
  --gold:#efc35d;
  --coral:#ff8d75;
  --green:#96f0bc;
  --violet:#cdb7ff;
  --shadow:0 22px 70px rgba(0,0,0,.28);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:radial-gradient(circle at 10% 0%,rgba(32,199,173,.18),transparent 34rem),radial-gradient(circle at 90% 8%,rgba(130,184,255,.13),transparent 36rem),linear-gradient(180deg,#06111f,#071527 55%,#08101d);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.56}
a{color:var(--blue);font-weight:850}
.nav{position:sticky;top:0;z-index:30;display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:12px 18px;background:rgba(8,19,34,.94);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}
.nav a,.nav span{color:#fff;text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:7px 10px;background:rgba(255,255,255,.05);font-size:.78rem;font-weight:850}
.nav .brand{border:0;background:transparent;color:var(--gold)}
main{width:min(1180px,calc(100% - 32px));margin:auto;padding:36px 0 74px}
section{padding-top:38px}
h1,h2,h3{margin:0;line-height:1.08}
h1{font-size:clamp(2.35rem,5.8vw,5rem);letter-spacing:-.04em;max-width:930px}
h2{font-size:clamp(1.65rem,3.6vw,2.65rem);letter-spacing:-.02em;margin-bottom:14px}
h3{font-size:1.06rem;margin-bottom:8px}
p{margin:0}
ul,ol{margin:10px 0 0;padding-left:20px}
li+li{margin-top:7px}
code{color:#dbfff7}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:22px;align-items:stretch;padding-bottom:32px;border-bottom:1px solid var(--line)}
.hero-copy{padding:24px 0}
.eyebrow{color:var(--teal);font-size:.78rem;font-weight:900;letter-spacing:.15em;text-transform:uppercase}
.summary{margin-top:18px;color:var(--muted);font-size:1.08rem;max-width:860px}
.logo-card{border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,rgba(32,199,173,.12),rgba(239,195,93,.08)),var(--panel);box-shadow:var(--shadow);padding:22px;display:flex;flex-direction:column;justify-content:space-between}
.logo-card img{width:104px;height:104px;border-radius:22px;object-fit:cover;box-shadow:0 16px 38px rgba(0,0,0,.22)}
.logo-card strong{display:block;font-size:1.85rem;line-height:1.08;margin-top:18px}
.grid{display:grid;gap:16px}
.grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}
.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}
.grid.four{grid-template-columns:repeat(4,minmax(0,1fr))}
.panel,.metric,.lane,.prompt,.phase,.finding,.visual{border:1px solid var(--line);border-radius:16px;background:linear-gradient(180deg,var(--panel2),var(--panel));box-shadow:var(--shadow)}
.panel,.metric,.lane,.prompt,.phase,.finding{padding:18px}
.metric strong{display:block;font-size:2.05rem;line-height:1;color:#fff}
.metric span,.muted,.panel p,.lane p,.phase p,.finding p,.prompt p,td{color:var(--muted)}
.chip{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:4px 10px;margin:2px 4px 2px 0;background:rgba(255,255,255,.05);color:var(--muted);font-size:.75rem;font-weight:900;text-transform:uppercase;letter-spacing:.05em}
.chip.red{color:var(--coral);border-color:rgba(255,141,117,.38)}
.chip.gold{color:var(--gold);border-color:rgba(239,195,93,.38)}
.chip.green{color:var(--green);border-color:rgba(150,240,188,.38)}
.chip.blue{color:var(--blue);border-color:rgba(130,184,255,.38)}
.chip.violet{color:var(--violet);border-color:rgba(205,183,255,.38)}
table{width:100%;border-collapse:collapse;font-size:.92rem}
th,td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}
th{background:rgba(255,255,255,.055);color:#fff;text-transform:uppercase;letter-spacing:.06em;font-size:.76rem}
.table-wrap{overflow-x:auto;border-radius:13px}
.finding{margin-top:12px;border-left:5px solid var(--gold)}
.finding.high{border-left-color:var(--coral)}
.finding.good{border-left-color:var(--green)}
.finding.blue{border-left-color:var(--blue)}
.phase{display:grid;grid-template-columns:76px 1fr;gap:16px;margin-top:14px}
.num{width:62px;height:62px;border-radius:17px;display:grid;place-items:center;background:rgba(32,199,173,.12);color:var(--teal);font-size:1.45rem;font-weight:950}
.phase.p0 .num{color:var(--coral);background:rgba(255,141,117,.12)}
.phase.p1 .num{color:var(--gold);background:rgba(239,195,93,.12)}
.phase.p3 .num{color:var(--blue);background:rgba(130,184,255,.12)}
.phase.p4 .num{color:var(--violet);background:rgba(205,183,255,.12)}
.visual{padding:18px;overflow:hidden}
.visual svg{width:100%;height:auto;display:block}
.prompt pre{white-space:pre-wrap;color:#e9fff9;background:#071320;border:1px solid var(--line);border-radius:12px;padding:14px;overflow:auto;font-size:.88rem;line-height:1.48}
.book-spine{min-height:190px;border-radius:14px;border:1px solid var(--line);padding:18px;display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(145deg,rgba(239,195,93,.14),rgba(32,199,173,.1))}
.book-spine:nth-child(2){background:linear-gradient(145deg,rgba(130,184,255,.16),rgba(32,199,173,.08))}
.book-spine:nth-child(3){background:linear-gradient(145deg,rgba(205,183,255,.16),rgba(32,199,173,.08))}
.footer-note{margin-top:38px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:.92rem}
@media(max-width:900px){main{width:min(100% - 22px,760px);padding-top:24px}.hero,.grid.two,.grid.three,.grid.four{grid-template-columns:1fr}.phase{grid-template-columns:1fr}.logo-card{min-height:240px}}
@media print{body{background:#06111f;print-color-adjust:exact;-webkit-print-color-adjust:exact}.nav{display:none}main{width:auto;padding:.12in}.hero{grid-template-columns:1fr;gap:14px}h1{font-size:42px!important}h2{font-size:24px!important}.panel,.metric,.lane,.prompt,.phase,.finding,.visual{break-inside:avoid}.grid{gap:10px}section{padding-top:24px}.summary{font-size:.95rem}}
"""


def money_svg() -> str:
    paid_w = round(PAID_TOTAL / PACKAGE_TOTAL * 760)
    balance_w = 760 - paid_w
    return f"""
<svg viewBox="0 0 860 250" role="img" aria-label="Corrected payment map">
  <rect x="0" y="0" width="860" height="250" rx="24" fill="#071320"/>
  <text x="32" y="46" fill="#eef7f6" font-size="28" font-weight="800">Corrected Package Economics</text>
  <text x="32" y="78" fill="#aec1c5" font-size="16">Total {money(PACKAGE_TOTAL)} - paid {money(PAID_TOTAL)} - balance {money(BALANCE_DUE)} - testimony separate.</text>
  <rect x="48" y="116" width="{paid_w}" height="54" rx="14" fill="#96f0bc"/>
  <rect x="{48 + paid_w}" y="116" width="{balance_w}" height="54" rx="14" fill="#ff8d75"/>
  <text x="62" y="150" fill="#06111f" font-size="18" font-weight="900">Paid {money(PAID_TOTAL)}</text>
  <text x="{58 + paid_w}" y="150" fill="#06111f" font-size="18" font-weight="900">Balance {money(BALANCE_DUE)}</text>
  <line x1="48" y1="194" x2="808" y2="194" stroke="rgba(203,224,222,.35)" stroke-width="2"/>
  <text x="48" y="224" fill="#efc35d" font-size="15" font-weight="800">Action: create live Stripe link for {money(BALANCE_DUE)}; keep retired $400 checkout out of author-facing flow.</text>
</svg>"""


def production_svg() -> str:
    max_words = max([b["words"] for b in BOOKS] + [j["words"] for j in JOURNALS])
    rows = []
    products = [
        ("Vol 1 Devotional", 128276, "#20c7ad"),
        ("Vol 1 Journal", 19854, "#efc35d"),
        ("Vol 2 Devotional", 95114, "#82b8ff"),
        ("Vol 2 Journal", 17134, "#efc35d"),
        ("Vol 3 Devotional", 91521, "#cdb7ff"),
        ("Vol 3 Journal", 17665, "#efc35d"),
    ]
    for idx, (label, words, color) in enumerate(products):
        y = 74 + idx * 42
        width = max(18, round(words / max_words * 530))
        rows.append(
            f'<text x="30" y="{y + 19}" fill="#eef7f6" font-size="15" font-weight="750">{html.escape(label)}</text>'
            f'<rect x="190" y="{y}" width="{width}" height="24" rx="7" fill="{color}"/>'
            f'<text x="{204 + width}" y="{y + 18}" fill="#aec1c5" font-size="14">{words:,} words</text>'
        )
    return f"""
<svg viewBox="0 0 860 360" role="img" aria-label="Production evidence chart">
  <rect x="0" y="0" width="860" height="360" rx="24" fill="#071320"/>
  <text x="30" y="42" fill="#eef7f6" font-size="28" font-weight="800">Production Surface</text>
  {''.join(rows)}
  <text x="30" y="338" fill="#efc35d" font-size="15" font-weight="800">{STATS['products']} products checked - {STATS['words']:,} source words - {STATS['sunday_mentions']} Sunday mentions - {STATS['sabbath_mentions']:,} Sabbath mentions.</text>
</svg>"""


def system_svg() -> str:
    labels = [
        ("Sources", "audio, transcripts, author feedback"),
        ("Truth Lock", "scope, invoice, scripture policy"),
        ("Devotional Rewrite", "KJV/NKJV text, voice, stronger takeaways"),
        ("Design Lock", "6 x 9 layout, covers, journals"),
        ("Proof Gates", "KDP Previewer, physical proof"),
        ("Release", "Amazon, direct site, app, audiobook lanes"),
    ]
    nodes = []
    links = []
    for idx, (title, desc) in enumerate(labels):
        x = 34 + idx * 132
        nodes.append(
            f'<rect x="{x}" y="92" width="110" height="108" rx="18" fill="#112b3f" stroke="rgba(203,224,222,.28)"/>'
            f'<text x="{x + 14}" y="126" fill="#20c7ad" font-size="15" font-weight="900">{html.escape(title)}</text>'
            f'<foreignObject x="{x + 14}" y="140" width="82" height="46"><div xmlns="http://www.w3.org/1999/xhtml" style="font:12px Inter,system-ui;color:#aec1c5;line-height:1.25">{html.escape(desc)}</div></foreignObject>'
        )
        if idx < len(labels) - 1:
            links.append(f'<path d="M{x + 112} 146 C{x + 125} 146 {x + 127} 146 {x + 132} 146" stroke="#efc35d" stroke-width="3" fill="none" marker-end="url(#arrow)"/>')
    return f"""
<svg viewBox="0 0 860 292" role="img" aria-label="Lady D production system">
  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#efc35d"/></marker></defs>
  <rect x="0" y="0" width="860" height="292" rx="24" fill="#071320"/>
  <text x="30" y="42" fill="#eef7f6" font-size="28" font-weight="800">From Manuscript River to KDP-Ready Shelf</text>
  <text x="30" y="68" fill="#aec1c5" font-size="15">Three streams - Father, Son, Spirit - move through one proof-gated publishing system.</text>
  {''.join(links)}
  {''.join(nodes)}
  <path d="M58 236 C170 214 270 260 386 236 C510 208 610 260 780 224" stroke="#20c7ad" stroke-width="5" fill="none" opacity=".75"/>
  <text x="30" y="268" fill="#82b8ff" font-size="14" font-weight="850">Future branches: 31-day visual devotional app foundation, direct storefront, audiobook build after manuscript lock.</text>
</svg>"""


def report_shell(title: str, current: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <nav class="nav">
    <span class="brand">Lady D Enhanced Mode</span>
    <a href="susan-damon-hub.html">Hub</a>
    <a href="susan-damon-publishing-proposal.html">Proposal</a>
    <a href="lady-d-project-dashboard.html">Dashboard</a>
    <a href="{STATE_FILE}">State</a>
    <a href="{PLAN_FILE}">Plan</a>
    <a href="index.html">Books</a>
    <a href="release-status.html">Release Status</a>
  </nav>
  <main data-report="{html.escape(current)}">{body}</main>
</body>
</html>"""


def state_page() -> str:
    book_cards = "".join(
        f"""
        <article class="book-spine">
          <div><span class="chip blue">{html.escape(book['vol'])}</span><h3>{html.escape(book['title'])}</h3><p>{html.escape(book['focus'])}</p></div>
          <p class="muted">{html.escape(book['status'])}</p>
        </article>
        """
        for book in BOOKS
    )
    findings = f"""
      <article class="finding high"><h3>Payment and scope truth is corrected, but Stripe still needs the live {money(BALANCE_DUE)} link.</h3><p>Current package is {money(PACKAGE_TOTAL)}. Paid to date is {money(PAID_TOTAL)}: {money(PRIOR_PAID)} prior plus the {money(CHECK_PAID)} check. Balance is {money(BALANCE_DUE)}. Juan Damon testimony/autobiography is outside this package.</p></article>
      <article class="finding"><h3>The books exist as a serious production surface, but the July 6 guidance changes the final format.</h3><p>Every devotional page now needs visible scripture text after Bible policy approval. The original-language lens only belongs where it clarifies instead of crowding. The daily ending needs stronger emotional carry, not a sterile production rhythm.</p></article>
      <article class="finding"><h3>The scripture journey needs to become curated, not merely sequential.</h3><p>The current Bible-order progression helped build the atlas, but the final reader journey should mix passages inside each month to create thematic echoes across the Father, Jesus, and Spirit volumes.</p></article>
      <article class="finding blue"><h3>The reusable client-package template is becoming visible.</h3><p>Playwright benchmarked Lady D, Oakwood, and Joyce on desktop/mobile: {BENCH['checks']} route/view checks, all 200 status: {BENCH['all_200']}, console errors: {BENCH['console_errors']}, missing images: {BENCH['missing_images']}, total horizontal overflow: {BENCH['overflow_total']}.</p></article>
      <article class="finding good"><h3>The proof discipline is already healthier than a typical AI book pipeline.</h3><p>Current proof audit reports {STATS['products']} products checked, {STATS['words']:,} source words, {STATS['placeholder_markers']} placeholders, {STATS['decision_items']} open proof-decision items, {STATS['review_required_contexts']} priority review contexts, and {STATS['sunday_mentions']} Sunday mentions.</p></article>
    """
    body = f"""
<header class="hero">
  <div class="hero-copy">
    <p class="eyebrow">Enhanced State of the Union - {DATE}</p>
    <h1>Lady D now has a publishing system. The next move is to make the books feel alive.</h1>
    <p class="summary">This report ingests the corrected package truth, June 14 devotional transcript notes, July 6 project guidance, KDP proof/readiness artifacts, the current Lady D repository state, and live browser checks against Lady D, Oakwood IDC, and Joyce. The result is a sharper state view for Susan "Lady D" Damon: scope corrected, payment clarified, testimony separated, and the editorial/design finish line reframed around scripture visibility, voice, cover quality, and KDP proof.</p>
    <p style="margin-top:16px"><span class="chip green">Tier B browser-rich enhanced report</span><span class="chip gold">print/mobile parity</span><span class="chip blue">2 evidence visuals</span><span class="chip violet">system visual</span><span class="chip red">video not rendered in this pass</span></p>
  </div>
  <aside class="logo-card">
    {f'<img src="{LOGO_URI}" alt="Island Development Crew palm logo">' if LOGO_URI else '<div></div>'}
    <div><strong>IDC Publishing Control Room</strong><p class="muted">Corrected invoice, author review, proof gates, and next production loops live in one connected hub.</p></div>
  </aside>
</header>

<section>
  <h2>Current Truth</h2>
  <div class="grid four">
    <article class="metric"><strong>1,098</strong><span>Devotional entries across Father, Son, and Holy Spirit volumes.</span></article>
    <article class="metric"><strong>{STATS['products']}</strong><span>KDP-facing products checked across devotionals and journals.</span></article>
    <article class="metric"><strong>{money(BALANCE_DUE)}</strong><span>Corrected remaining balance after {money(PAID_TOTAL)} paid.</span></article>
    <article class="metric"><strong>{STATS['sunday_mentions']}</strong><span>Sunday mentions in the current proof audit.</span></article>
  </div>
</section>

<section>
  <h2>Current-Model Understanding</h2>
  <div class="grid three">
    <article class="panel"><h3>Paid current scope</h3><ul><li>Three 365/366-day devotionals: Father, Son, Holy Spirit.</li><li>Three matching companion journals.</li><li>31-day visual devotional product lane.</li><li>Author review site, dashboard, proposal/invoice, KDP/digital preparation.</li></ul></article>
    <article class="panel"><h3>Separated scope</h3><ul><li>Juan Damon testimony/autobiography is not inside the current {money(PACKAGE_TOTAL)} invoice.</li><li>It should become its own intake, sensitivity, family-review, audiobook, and publishing package later.</li><li>No payment button or proposal should blend it back into the current balance.</li></ul></article>
    <article class="panel"><h3>Creative north star</h3><ul><li>Scripture text visible, with KJV as the default safe option unless NKJV permissions are approved.</li><li>Less mechanical Bible-order progression; more curated thematic scripture movement.</li><li>Lady D voice should feel warm, practical, reverent, and strong enough to land in the reader.</li></ul></article>
  </div>
</section>

<section>
  <h2>Evidence Visuals</h2>
  <div class="grid two">
    <article class="visual">{money_svg()}</article>
    <article class="visual">{production_svg()}</article>
  </div>
</section>

<section>
  <h2>What Is Strong</h2>
  <div class="grid three">{book_cards}</div>
</section>

<section>
  <h2>Book Quality Diagnosis</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Layer</th><th>Current Read</th><th>Current-Model Correction</th></tr></thead>
      <tbody>
        <tr><td><strong>Scripture</strong></td><td>References and context lenses exist, but the July 6 feedback says the text itself needs to be present on the page.</td><td>Build a Bible-policy pass: KJV default, NKJV optional if permission/copyright notice is approved, scripture box visible before devotional body.</td></tr>
        <tr><td><strong>Original language/context</strong></td><td>Useful but can feel like an academic artifact when space is tight.</td><td>Keep only one short "meaning lens" when it unlocks the passage; remove it when it steals warmth from the devotion.</td></tr>
        <tr><td><strong>Daily ending</strong></td><td>Morning impact and today-step patterns can feel template-driven.</td><td>Fuse the closing into one stronger reflection/action/journal block that feels spoken, memorable, and emotionally carried.</td></tr>
        <tr><td><strong>Scripture order</strong></td><td>The current atlas leans mechanical and sequential.</td><td>Create a scripture remix ledger: monthly themes stay intact, but passages move in curated arcs with echoes across the three volumes.</td></tr>
        <tr><td><strong>Journals</strong></td><td>Functional, but still too plain for the quality target.</td><td>Redesign journal pages with daily anchors, reflection lines, prayer response, scripture memory, and generous writing rhythm.</td></tr>
        <tr><td><strong>Covers</strong></td><td>Cohesive but dark; the project needs premium shelf presence.</td><td>Generate three art-first 6 x 9 routes per book with brighter light, deeper atmosphere, and typography-safe negative space.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>What Must Change</h2>
  {findings}
</section>

<section>
  <h2>Design Pattern Synthesis</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Reference</th><th>Strength To Keep</th><th>Lady D Implementation Rule</th></tr></thead>
      <tbody>
        <tr><td><strong>Lady D portal</strong></td><td>Book-first author review, product links, proof downloads.</td><td>Keep the devotional products one click away from every planning surface.</td></tr>
        <tr><td><strong>Oakwood IDC proposal</strong></td><td>Price clarity, compact cards, obvious buttons, execute-ready feel.</td><td>Every proposal must show total, paid, balance, scope, exclusions, and next payment action in the first viewport.</td></tr>
        <tr><td><strong>Joyce publishing deck</strong></td><td>Literary tone, mobile-friendly pills, author-site elegance.</td><td>Lady D's public shell should feel warm, literary, readable, and reverent rather than like an internal admin board.</td></tr>
        <tr><td><strong>Martin-style estimate pattern</strong></td><td>Visual exhibit makes the scope tangible.</td><td>Publishing invoices should show book covers, journals, samples, or screenshots, not only line-item text.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>System View</h2>
  <article class="visual">{system_svg()}</article>
</section>

<section>
  <h2>End-Of-Month Release Reality</h2>
  <div class="grid three">
    <article class="panel"><h3>July 19-21</h3><p>Lock invoice truth, template navigation, Bible policy decision path, and one Volume 1 sample page with visible scripture and fused reflection.</p></article>
    <article class="panel"><h3>July 22-26</h3><p>Scale the approved sample into Volume 1, produce the scripture glossary ledger, improve cover candidates, and regenerate PDF/HTML proof surfaces.</p></article>
    <article class="panel"><h3>July 27-31</h3><p>Run KDP Previewer on the chosen first-volume candidate, prepare author review package, order/plan proof, and decide whether to publish one volume first or hold for trilogy completion.</p></article>
  </div>
  <p class="muted" style="margin-top:12px">This timeline is aggressive. It is only honest if the first release target is one polished volume plus its companion journal, while the trilogy-wide architecture keeps moving behind it.</p>
</section>

<section>
  <h2>Evidence Boundary</h2>
  <div class="grid two">
    <article class="panel"><h3>Ingested and used</h3><ul><li>July 6 summary and action items from the attached project notes.</li><li>June 14 transcript files describing the {money(PACKAGE_TOTAL)} bundle and payment plan.</li><li>KDP proof/readiness JSON and release status pages.</li><li>Current local repository generators and public mirrors.</li><li>Playwright smoke benchmark for Lady D, Oakwood, and Joyce.</li></ul></article>
    <article class="panel"><h3>Held as source, not overclaimed</h3><ul><li>July 6 MP3 duration confirmed at 3,611.66 seconds, about 60.2 minutes.</li><li>Full fresh audio transcription was not performed in this pass.</li><li>NKJV scripture text should not be inserted until permissions/copyright notice is locked. KJV is safer as public-domain default where appropriate.</li><li>Final KDP upload is not approved until Previewer and physical proof pass.</li></ul></article>
  </div>
</section>

<p class="footer-note">Benchmark directory: {html.escape(BENCH['dir'])}. Generated by scripts/build_lady_d_enhanced_reports.py from local evidence and current project guidance.</p>
"""
    return report_shell("Lady D Enhanced State of the Union", "state", body)


def plan_page() -> str:
    prompt_main = """GOAL MODE PROMPT - Lady D Trilogy Finalization

Objective: turn the existing Lady D devotional trilogy and companion journals into release-ready, proof-gated books.

Rules:
- Start with the current repo and live site truth. Do not overwrite user changes.
- Preserve package truth: $2,000 total, $600 paid, $1,400 due, Juan Damon testimony separate.
- Use KJV as default scripture text unless NKJV permission/copyright notice is explicitly approved.
- Every devotional page must show the scripture text or a clearly approved scripture policy.
- Keep original-language/context notes only where they deepen the passage without crowding.
- Reorder scripture journeys inside monthly themes so the reader does not feel a mechanical Genesis-to-Revelation crawl.
- Write with Lady D's morning voice: warm, direct, reverent, practical, emotionally alive, not academic.
- Fuse Today step, Morning impact, and Journal prompt into one stronger reflection/action block when layout needs room.
- Build one Volume 1 sample first, visually inspect HTML/PDF, then scale.
- Maintain audit loops: voice judge, theology guardrail, repetition audit, scripture-policy audit, KDP proof audit.
- Update GitHub, Vercel, and author-facing dashboard artifacts after every approved production gate.

Done when:
- The hub, reports, invoice, dashboards, manuscripts, journals, downloads, and public mirrors agree.
- KDP Previewer and physical proof gates are explicitly passed before public release language is used."""

    prompt_visual = """GOAL MODE PROMPT - 31-Day Visual Devotional And App Foundation

Objective: create a 31-day visual devotional prompt pack and app-ready storyboard that feels immersive, colorful, worshipful, and modern.

Use:
- The existing Lady D voice sources and 31-day devotional reference.
- A high-dynamic-range visual direction: nature, water, light, mountains, gardens, city nights, wonders of creation, quiet interiors, worship atmosphere.
- Each day needs: scripture reference, short devotional line, visual scene prompt, motion/animation note, font/mood guidance, journal reflection, and accessibility alt text.
- Build as HTML first with cards, optional motion states, and prompt export. Treat full app build as future lane.

Done when:
- 31 prompts are organized, visually distinct, spiritually coherent, and ready for GPT Image 2.0 or app prototyping."""

    prompt_cover = """GPT IMAGE 2.0 COVER PROMPT SYSTEM

Canvas:
- 6 x 9 portrait front cover, highest quality, print-oriented, 300 DPI target.
- Generate art-first covers with safe margins and minimal or no embedded text. Final typography should be locked in design/layout pass.

Style:
- Elegant Christian devotional, premium Amazon KDP shelf presence, luminous but not gaudy, warm and hopeful, cohesive trilogy identity.
- Avoid dark muddy covers. Increase brightness, depth, contrast, and readable focal point.
- Create three routes per book: sanctuary light, path/journey, modern sacred minimal.
- Volume 1 should feel held by the Father's love: dawn, garden, open hands, warm gold, surrendered path.
- Volume 2 should feel like walking with Jesus: footsteps, road, sandals/robe edge suggested symbolically, Galilean light, open door.
- Volume 3 should feel Spirit-filled: wind, flame, living water, dove-light symbolism, upper-room glow, courage and comfort.

QA:
- Check thumbnail readability, full-size elegance, spiritual tone, title-safe negative space, and trilogy cohesion."""

    phases = [
        ("0", "Truth lock and money lane", "Patch all active generators and pages to $2,000 total, $600 paid, $1,400 balance; keep Juan Damon testimony separate; create/insert live Stripe link.", "No stale $2,300, $2,500, old checkout, or bundled testimony language in active generated surfaces."),
        ("1", "Template lock", "Convert the best Lady D/Oakwood/Joyce traits into one client package standard: proposal, invoice, visual exhibit, dashboard, progress page, mobile nav, PDF print parity.", "Desktop/mobile screenshots show no overflow, missing media, or random logo substitution."),
        ("2", "Scripture and layout sample", "Build a complete Volume 1 sample with visible scripture text, KJV/NKJV decision, context note policy, fused reflection prompt, and stronger devotional ending.", "One sample passes visual proof, voice review, theology guardrail, and page-fit checks."),
        ("3", "Scripture remix ledger", "Reorder passages inside monthly arcs so each book has variety, biblical coherence, and cross-volume echoes without losing the Father/Son/Spirit distinction.", "Each month has a scripture map, no stale sequential clusters, and a biblical-order glossary cross-reference."),
        ("4", "Volume and journal scale-out", "Apply the locked sample to all three devotionals and the three companion journals, with journal pages redesigned beyond plain half-lined pages.", "Six products regenerate with source manifests, checksums, review HTML, DOCX/PDF, and public download mirrors."),
        ("5", "Cover and visual suite", "Use GPT Image 2.0 highest quality to produce at least three cover options per devotional plus journal cover language and contact sheets.", "Nine improved cover candidates plus selected route and KDP wrap plan after page count lock."),
        ("6", "31-day visual devotional lane", "Build prompt-pack HTML and app-ready storyboard for immersive daily visuals, motion ideas, devotional text, journal reflection, and future app foundation.", "31 prompt cards export cleanly and can be passed to a separate app/image generation session."),
        ("7", "KDP and release gate", "Research author-copy economics, prepare KDP metadata, run Previewer, order physical proofs, then publish one volume first if Lady D approves.", "No public release language until Previewer screenshots/logs and physical proof approval exist."),
    ]
    phase_html = "".join(
        f"""
        <article class="phase p{idx if idx in {'0','1','3','4'} else ''}">
          <div class="num">{idx}</div>
          <div><h3>{html.escape(title)}</h3><p>{html.escape(action)}</p><p style="margin-top:8px"><span class="chip green">Done when</span> {html.escape(done)}</p></div>
        </article>
        """
        for idx, title, action, done in phases
    )
    body = f"""
<header class="hero">
  <div class="hero-copy">
    <p class="eyebrow">Enhanced Plan of Attack - {DATE}</p>
    <h1>Finish by locking one beautiful proof lane, then scaling with discipline.</h1>
    <p class="summary">This plan turns the new guidance into execution loops. It respects the corrected invoice, separates the testimony lane, raises the devotional quality bar, adds scripture visibility and glossary planning, upgrades covers, and prepares a separate 31-day visual devotional prompt/app foundation without derailing the core trilogy.</p>
    <p style="margin-top:16px"><span class="chip red">scope first</span><span class="chip gold">template lock</span><span class="chip green">scripture visible</span><span class="chip blue">voice-depth loops</span><span class="chip violet">KDP proof gate</span></p>
  </div>
  <aside class="logo-card">
    {f'<img src="{LOGO_URI}" alt="Island Development Crew palm logo">' if LOGO_URI else '<div></div>'}
    <div><strong>Goal Mode Runbook</strong><p class="muted">Use this page as the launch surface for separate Codex sessions: trilogy finalization, 31-day visual devotional, covers, and KDP release.</p></div>
  </aside>
</header>

<section>
  <h2>Goal Mode Workstreams</h2>
  <div class="grid three">
    <article class="panel"><h3>1. Trilogy Finalization</h3><p>Owns scripture visibility, KJV/NKJV policy, stronger devotional endings, scripture remix ledger, Volume 1 sample, and scale-out to all three books.</p></article>
    <article class="panel"><h3>2. Companion Journals</h3><p>Owns journal layout, daily response rhythm, writing-space usability, title/subtitle consistency, and print proof readability.</p></article>
    <article class="panel"><h3>3. Covers + Visuals</h3><p>Owns GPT Image 2.0 prompts, nine front-cover routes, journal visual family, contact sheets, thumbnail checks, and KDP wrap prep.</p></article>
    <article class="panel"><h3>4. 31-Day Visual Devotional</h3><p>Owns the prompt-pack HTML, visual storyboard, motion/app foundation, and future interactive devotional lane.</p></article>
    <article class="panel"><h3>5. Client Package Template</h3><p>Owns reusable proposal/invoice/dashboard/navigation layout, logo lock, visual exhibits, PDF print parity, and mobile behavior.</p></article>
    <article class="panel"><h3>6. Release + Commerce</h3><p>Owns Stripe correction, Amazon author-copy research, KDP metadata, Previewer checks, physical proof, GitHub push, and Vercel live verification.</p></article>
  </div>
</section>

<section>
  <h2>Execution Loops</h2>
  {phase_html}
</section>

<section>
  <h2>Devotional Entry Contract</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Slot</th><th>Purpose</th><th>Rule</th></tr></thead>
      <tbody>
        <tr><td><strong>Scripture Text</strong></td><td>Give the page life before commentary.</td><td>KJV default; NKJV only with permission/copyright notice approved.</td></tr>
        <tr><td><strong>Opening Hook</strong></td><td>Make the reader feel the day matters.</td><td>One vivid, pastoral sentence tied to the passage and Lady D's voice.</td></tr>
        <tr><td><strong>Devotional Body</strong></td><td>Build depth, not filler.</td><td>Four to five paragraphs where scripture, life, surrender, and encouragement converge.</td></tr>
        <tr><td><strong>Meaning Lens</strong></td><td>Use original-language/context only when helpful.</td><td>One short note, optional; no academic crowding.</td></tr>
        <tr><td><strong>Prayer</strong></td><td>Turn truth into communion.</td><td>Direct, reverent, emotionally honest, not recycled.</td></tr>
        <tr><td><strong>Reflection/Action</strong></td><td>Replace fragmented prompt pieces.</td><td>Fuse journal prompt, today step, and morning impact into one memorable reader response.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Cover Route Board</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Book</th><th>Route A</th><th>Route B</th><th>Route C</th></tr></thead>
      <tbody>
        <tr><td><strong>Surrendering to God's Love</strong></td><td>Dawn garden, open hands, warm golden presence.</td><td>Quiet path through wildflowers toward light.</td><td>Modern sacred minimal: linen, gold thread, soft halo, no clutter.</td></tr>
        <tr><td><strong>Walking with Jesus</strong></td><td>Sunlit road with footsteps and gentle horizon.</td><td>Open doorway into Galilean morning light.</td><td>Minimal path mark, warm teal/gold, devotional shelf elegance.</td></tr>
        <tr><td><strong>Filled with the Holy Spirit</strong></td><td>Upper-room glow with wind and living flame symbolism.</td><td>River/light/wind convergence through trees.</td><td>Dove-light abstract with deep blue, white, and gold movement.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Recommended GPT Settings</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Work Type</th><th>Recommended Setting</th><th>Why</th></tr></thead>
      <tbody>
        <tr><td><strong>Architecture, State/Plan, repo edits, KDP gates</strong></td><td>GPT 5.5 Extra High or highest-reasoning option available.</td><td>Use for decisions with scope, theology, invoice truth, layout rules, and release risk.</td></tr>
        <tr><td><strong>Daily devotional rewrite batches</strong></td><td>GPT 5.5 Medium to High; escalate difficult theology/voice batches to Extra High.</td><td>Medium/High is better for sustained editorial throughput; use judge loops to keep quality high.</td></tr>
        <tr><td><strong>Mechanical audits and link checks</strong></td><td>Fast setting or GPT 5.3 Spark class setting.</td><td>Good for rg audits, route lists, file manifests, status extraction, and smoke-test summaries. Do not use it for theology, finance truth, or final prose approval.</td></tr>
        <tr><td><strong>Cover and 31-day visual generation</strong></td><td>GPT Image 2.0, highest quality, portrait 6 x 9, print-oriented.</td><td>Use art-first generation, then do typography and KDP wrap composition in a layout pass.</td></tr>
      </tbody>
    </table>
  </div>
  <p class="muted" style="margin-top:12px">If model labels differ in the UI, choose the closest equivalent: highest reasoning for planning and proof, balanced/high for editorial batches, fast for audits, and highest-quality image generation for covers.</p>
</section>

<section>
  <h2>GitHub And Vercel Delivery Loop</h2>
  <div class="grid two">
    <article class="panel"><h3>Repo loop</h3><ol><li>Generate artifacts from scripts, not hand-edited output.</li><li>Run build and Playwright smoke tests.</li><li>Stage only intended source and generated deliverables.</li><li>Commit with an evidence-bearing message.</li><li>Push branch to <code>Navigata1/lady-d-author-review-site</code>.</li></ol></article>
    <article class="panel"><h3>Live loop</h3><ol><li>Deploy the exact <code>public/</code> state to Vercel production.</li><li>Verify hub, proposal, dashboard, enhanced reports, books, and payment status return 200.</li><li>Check desktop/mobile screenshots for overflow, clipping, missing media, and stale logo/payment text.</li><li>Update Lady D's live hub only after the smoke pass.</li></ol></article>
  </div>
</section>

<section>
  <h2>End-Of-Month Target</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Date Band</th><th>Target</th><th>Release Meaning</th></tr></thead>
      <tbody>
        <tr><td><strong>July 19-21</strong></td><td>Lock template, money truth, scripture policy decision path, and Volume 1 sample layout.</td><td>Ready to scale, not ready to publish.</td></tr>
        <tr><td><strong>July 22-26</strong></td><td>Volume 1 rewrite/proof pass, journal redesign sample, scripture glossary ledger, cover route generation.</td><td>First-volume candidate can enter proof review.</td></tr>
        <tr><td><strong>July 27-31</strong></td><td>KDP Previewer evidence, physical proof plan/order, author decision sheet, live hub update, public launch copy only if proof gates pass.</td><td>One-volume release candidate, with trilogy continuing behind it.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section>
  <h2>Plugin Guidance</h2>
  <div class="grid two">
    <article class="panel"><h3>Required now</h3><p>No additional plugin is required for the current local repo, GitHub, Vercel, Playwright, and GPT Image workflow.</p></article>
    <article class="panel"><h3>Useful later</h3><ul><li><strong>Google Drive</strong> if Lady D source recordings, transcripts, approvals, or PDFs move into Drive.</li><li><strong>Figma</strong> if covers, interiors, or reusable client templates need collaborative visual review.</li><li><strong>Gmail or Calendar</strong> only if you want approval emails or proof-review meetings managed from inside Codex.</li><li><strong>Box or SharePoint</strong> only for clients whose source libraries live there.</li></ul></article>
  </div>
</section>

<section>
  <h2>Prompt Blocks</h2>
  <div class="grid">
    <article class="prompt"><h3>Main trilogy correction session</h3><pre>{html.escape(prompt_main)}</pre></article>
    <article class="prompt"><h3>31-day visual devotional session</h3><pre>{html.escape(prompt_visual)}</pre></article>
    <article class="prompt"><h3>Cover generation session</h3><pre>{html.escape(prompt_cover)}</pre></article>
  </div>
</section>

<section>
  <h2>Acceptance Tests</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Gate</th><th>Command or Review</th><th>Pass Standard</th></tr></thead>
      <tbody>
        <tr><td>Financial truth</td><td><code>rg -n "\\$2,300|\\$2,500|2300|2500|buy\\.stripe|Pay \\$2,300" scripts *.html public</code></td><td>No active stale payment language except historical archived documents or explicit retired-link instructions.</td></tr>
        <tr><td>Build</td><td><code>npm run build</code></td><td>Static site builds without errors.</td></tr>
        <tr><td>Browser smoke</td><td>Playwright desktop and mobile for hub, proposal, dashboard, enhanced reports, books.</td><td>HTTP 200, no console errors, no missing images, no horizontal overflow.</td></tr>
        <tr><td>Devotional sample</td><td>Visual proof HTML/PDF for sample week.</td><td>Scripture visible, context lens readable or removed, reflection block stronger, no text collision.</td></tr>
        <tr><td>KDP release</td><td>KDP Previewer screenshots/logs plus physical proof photos.</td><td>No blocking margin, bleed, cover, interior, metadata, or permissions issue.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<p class="footer-note">This is the end-to-end runbook for separate goal-mode execution. It is intentionally more detailed than the client-facing proposal so the production loop can move without confusing Lady D.</p>
"""
    return report_shell("Lady D Enhanced Plan of Attack", "plan", body)


def write(name: str, content: str) -> None:
    clean = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    (ROOT / name).write_text(clean, encoding="utf-8")
    (PUBLIC / name).write_text(clean, encoding="utf-8")


def main() -> None:
    write(STATE_FILE, state_page())
    write(PLAN_FILE, plan_page())
    manifest = {
        "generated": DATE,
        "state": STATE_FILE,
        "plan": PLAN_FILE,
        "package_total": PACKAGE_TOTAL,
        "paid_total": PAID_TOTAL,
        "balance_due": BALANCE_DUE,
        "stats": STATS,
        "line_edit_stats": LINE,
        "benchmark": BENCH,
        "tier": "Tier B browser-rich enhanced report, no video rendered",
    }
    write(f"lady-d-enhanced-report-manifest-{DATE}.json", json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
