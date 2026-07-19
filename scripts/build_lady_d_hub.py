#!/usr/bin/env python3
from pathlib import Path
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
PUBLIC.mkdir(exist_ok=True)

DATE = "2026-07-08"
PACKAGE_TOTAL = 2000
PRIOR_PAID = 200
CHECK_PAID = 400
PAID_TOTAL = PRIOR_PAID + CHECK_PAID
BALANCE_DUE = PACKAGE_TOTAL - PAID_TOTAL
PAYMENT_LINK = "stripe-payment-link-pending-1400.html"
OLD_PAYMENT_LINK_STATUS = "retired_checkout_do_not_send"
STRIPE_PERMISSION_STATUS = "live restricted key cannot create prices/payment links"
PROVIDER_EMAIL = "jon-isaac@islanddevcrew.com"
CLIENT_EMAIL = "1ladysd23@gmail.com"
LOGO = "assets/idc-palm-logo.png"
ENHANCED_STATE_REPORT = "lady-d-enhanced-state-of-the-union-2026-07-19.html"
ENHANCED_PLAN_REPORT = "lady-d-enhanced-plan-of-attack-2026-07-19.html"

books = [
    {
        "vol": "Volume 1",
        "title": "Surrendering to God's Love",
        "subtitle": "A 365-day devotional journey into the Father's heart.",
        "html": "book-1-surrendering-to-gods-love-review.html",
        "cover": "production-assets/author-review-covers/volume-1-author-review-cover.png",
        "pdf": "downloads/production/kdp/interior-drafts/volume-1/volume-1-full-6x9-interior-draft.pdf",
        "journal": "downloads/production/kdp/companion-journal-drafts/volume-1/volume-1-companion-journal-6x9-draft.pdf",
    },
    {
        "vol": "Volume 2",
        "title": "Walking with Jesus",
        "subtitle": "A 365-day devotional journey of daily discipleship.",
        "html": "book-2-walking-with-jesus-review.html",
        "cover": "production-assets/author-review-covers/volume-2-author-review-cover.png",
        "pdf": "downloads/production/kdp/interior-drafts/volume-2/volume-2-full-6x9-interior-draft.pdf",
        "journal": "downloads/production/kdp/companion-journal-drafts/volume-2/volume-2-companion-journal-6x9-draft.pdf",
    },
    {
        "vol": "Volume 3",
        "title": "Filled with the Holy Spirit",
        "subtitle": "A 365-day devotional journey in Spirit-led living.",
        "html": "book-3-filled-with-the-holy-spirit-review.html",
        "cover": "production-assets/author-review-covers/volume-3-author-review-cover.png",
        "pdf": "downloads/production/kdp/interior-drafts/volume-3/volume-3-full-6x9-interior-draft.pdf",
        "journal": "downloads/production/kdp/companion-journal-drafts/volume-3/volume-3-companion-journal-6x9-draft.pdf",
    },
]

STYLE = r"""
:root{
  --ink:#173334; --muted:#667776; --paper:#f6faf7; --card:#fff;
  --teal:#087b74; --deep:#123747; --aqua:#0c9eb6; --gold:#c48b19;
  --coral:#df654d; --line:#d9e4df; --cream:#fff9ec;
  --shadow:0 22px 70px rgba(10,45,48,.12);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:linear-gradient(180deg,#eef7f4,#fffaf1 46%,#f5efe2);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}
a{color:var(--teal);font-weight:850}
.nav{position:sticky;top:0;z-index:15;background:rgba(18,55,71,.96);backdrop-filter:blur(16px);display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px 18px}
.nav a,.nav span{color:white;text-decoration:none;font-size:13px;font-weight:850;padding:8px 11px;border-radius:999px;background:rgba(255,255,255,.09)}
.nav .brand{background:transparent;color:#f7d58f}
.wrap{max-width:1120px;margin:auto;padding:34px 18px 78px}
.hero{display:grid;grid-template-columns:1fr 190px;gap:26px;align-items:center;background:linear-gradient(135deg,var(--deep),var(--teal) 64%,var(--gold));color:white;border-radius:8px;padding:42px;box-shadow:var(--shadow);overflow:hidden}
.hero-logo{width:160px;max-width:100%;border-radius:28px;filter:drop-shadow(0 18px 35px rgba(0,0,0,.22))}
.kicker{text-transform:uppercase;letter-spacing:.16em;color:var(--gold);font-size:12px;font-weight:950}
.hero .kicker{color:#f9dda2}
h1,h2,h3{line-height:1.06;margin:0 0 14px}
h1{font-size:clamp(34px,5.8vw,70px);letter-spacing:-.035em}
h2{font-size:clamp(27px,3.2vw,42px);letter-spacing:-.02em}
h3{font-size:21px}
p{margin:0 0 12px}
.lead{font-size:clamp(18px,2vw,22px);max-width:900px}
.hero .lead{color:#f1fffb}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:18px;margin-top:22px}
.card{grid-column:span 6;background:rgba(255,255,255,.98);border:1px solid var(--line);border-radius:8px;padding:24px;box-shadow:var(--shadow)}
.third{grid-column:span 4}.mini{grid-column:span 3}.full{grid-column:1/-1}
.gold-top{border-top:7px solid var(--gold)}.teal-top{border-top:7px solid var(--teal)}.coral-top{border-top:7px solid var(--coral)}
.badge,.chip{display:inline-flex;align-items:center;border-radius:999px;background:#eaf5f2;color:#07524f;border:1px solid #cae0db;padding:7px 10px;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.06em;margin:3px}
.btn{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:13px 18px;margin:6px 8px 6px 0;color:#122c2d;background:white;font-weight:950;min-width:150px}
.btn.gold{background:linear-gradient(135deg,var(--gold),#efc96c);color:#102b2d;border:0}.btn.teal{background:var(--teal);color:white;border:0}.btn.dark{background:var(--deep);color:white;border:0}.btn.coral{background:var(--coral);color:white;border:0}
.muted{color:var(--muted)}.stat strong{display:block;font-size:43px;line-height:1;color:var(--deep);font-weight:650}
.book{display:grid;grid-template-columns:126px 1fr;gap:18px;align-items:center}
.book img{width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:6px;box-shadow:0 16px 38px rgba(10,45,48,.18)}
.cover-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.cover-card{border:1px solid var(--line);border-radius:8px;background:#fff;padding:12px;break-inside:avoid}
.cover-card img{width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:6px;box-shadow:0 12px 28px rgba(10,45,48,.14)}
.table{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:#fff}
.table th,.table td{text-align:left;vertical-align:top;padding:12px 13px;border-bottom:1px solid var(--line)}
.table th{background:var(--deep);color:white;text-transform:uppercase;font-size:.78rem;letter-spacing:.08em}
.table tr:last-child td{border-bottom:0}
.callout{border-left:6px solid var(--teal);background:#f2faf7;border-radius:8px;padding:16px 18px}
.warning{border-left-color:var(--coral);background:#fff5ef}
.money{background:linear-gradient(135deg,var(--deep),var(--teal));color:white;border-radius:8px;padding:26px}
.money .big{font-size:58px;line-height:1;font-weight:450}
.paybox{background:#fff7ea;border:1px solid #ecd6b3;border-radius:8px;padding:22px}
.page{max-width:1120px;margin:22px auto;background:white;border:1px solid var(--line);box-shadow:0 18px 55px rgba(10,45,48,.08);padding:38px 46px;border-radius:8px;break-after:page}
.page:last-child{break-after:auto}
.page-header{display:grid;grid-template-columns:1fr 250px;gap:20px;border-bottom:5px solid var(--teal);padding-bottom:18px;margin-bottom:20px}
.brand-lockup{display:grid;grid-template-columns:78px 1fr;gap:16px;align-items:center}
.logo-img{width:72px;height:72px;object-fit:cover;border-radius:15px;box-shadow:0 10px 28px rgba(18,55,71,.22)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.footer{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:14px;margin-top:28px;font-size:12px;color:#697675}
.sig{height:70px;border-bottom:1px solid #9ca7a5;margin-top:20px}
.print-only{display:none}
@media(max-width:820px){
  .card,.third,.mini{grid-column:1/-1}.hero{grid-template-columns:1fr;padding:28px 22px}.wrap{padding:22px 12px 58px}.book{grid-template-columns:1fr}.book img{max-width:190px}.two,.page-header,.cover-grid{grid-template-columns:1fr}.page{padding:25px 18px;overflow:hidden}.table{display:block;max-width:100%;overflow-x:auto;font-size:.92rem;-webkit-overflow-scrolling:touch}.table tbody{display:table;width:100%}.btn{width:100%;margin-right:0}.money .big{font-size:44px}.brand-lockup{grid-template-columns:58px 1fr}.logo-img{width:54px;height:54px}
}
@media print{
  @page{size:Letter;margin:.36in}
  body{background:white;font-size:11.5px}.nav,.wrap,.screen-only{display:none}.print-only{display:block}
  .page{box-shadow:none;border:0;border-radius:0;max-width:none;min-height:9.95in;page-break-after:always;margin:0;padding:0;break-after:page}
  .page:last-child{page-break-after:auto;break-after:auto}.page h1{font-size:28px!important}.page h2{font-size:21px}.page h3{font-size:15px}.page p{margin:.28rem 0}.page-header{grid-template-columns:1fr 230px;padding-bottom:10px;margin-bottom:12px}.logo-img{width:55px;height:55px}.brand-lockup{grid-template-columns:62px 1fr}.chip{padding:4px 8px;margin:2px}.money{padding:15px}.money .big{font-size:40px}.paybox{padding:13px}.table th,.table td{padding:7px 8px}.btn{display:none}a{color:#07524f}.footer{position:absolute;left:0;right:0;bottom:0}.page{position:relative}.table th,.money{print-color-adjust:exact;-webkit-print-color-adjust:exact}.cover-grid{grid-template-columns:repeat(3,1fr);gap:10px}.cover-card{padding:8px}
}
"""

REPORT_STYLE = r"""
:root{color-scheme:dark;--bg:#070f1c;--paper:#0d1b2f;--paper-2:#10243b;--ink:#eef6ff;--muted:#a9bdd3;--line:rgba(169,189,211,.18);--accent:#58d7b3;--blue:#77b7ff;--amber:#ffd166;--red:#ff8f8f;--good:#8ef2c0;--violet:#c4a7ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,rgba(88,215,179,.16),transparent 30rem),radial-gradient(circle at top right,rgba(119,183,255,.14),transparent 32rem),var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.55}
main{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:42px 0 64px}h1,h2,h3{margin:0;line-height:1.12}h1{max-width:950px;margin-top:10px;font-size:clamp(2.15rem,5.4vw,4.25rem);letter-spacing:-.04em}h2{margin-bottom:16px;font-size:clamp(1.45rem,3vw,2.05rem)}h3{margin-bottom:8px;font-size:1.05rem;color:#fff}p{margin:0}a{color:var(--blue)}code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;color:#dff7ef}.eyebrow{color:var(--accent);font-size:.78rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}
.hero{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:26px;align-items:end;padding:24px 0 34px;border-bottom:1px solid var(--line)}.hero .summary{max-width:780px;margin-top:18px;color:var(--muted);font-size:1.08rem}
.panel,.verdict-card,.task,.lane,.finding,.phase-card,.metric{border:1px solid var(--line);border-radius:16px;background:linear-gradient(180deg,var(--paper-2),var(--paper));box-shadow:0 18px 46px rgba(0,0,0,.25)}.verdict-card{padding:22px}.task,.lane,.metric{padding:18px}.verdict-card strong{display:block;color:var(--accent);font-size:1.65rem;line-height:1.1}.verdict-card span{display:block;margin-top:10px;color:var(--muted);font-size:.95rem}section{padding-top:38px}.grid{display:grid;gap:16px}.grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.grid.four{grid-template-columns:repeat(4,minmax(0,1fr))}.panel{padding:20px}.panel p,li,.muted{color:var(--muted)}.metric strong{display:block;margin-bottom:6px;color:#fff;font-size:1.75rem;line-height:1}.chip{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;padding:4px 10px;margin:2px 4px 2px 0;background:rgba(255,255,255,.05);color:var(--muted);font-size:.78rem;font-weight:800}.chip.red{color:var(--red);border-color:rgba(255,143,143,.4)}.chip.amber{color:var(--amber);border-color:rgba(255,209,102,.4)}.chip.green{color:var(--good);border-color:rgba(142,242,192,.4)}.chip.blue{color:var(--blue);border-color:rgba(119,183,255,.4)}.chip.violet{color:var(--violet);border-color:rgba(196,167,255,.4)}
ul{margin:10px 0 0;padding-left:20px}li+li{margin-top:7px}table{width:100%;border-collapse:collapse;margin-top:8px;font-size:.92rem}th,td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}th{background:rgba(255,255,255,.05);color:#fff;font-size:.8rem;letter-spacing:.06em;text-transform:uppercase}td{color:var(--muted)}td b,td strong{color:#fff}.table-wrap{overflow-x:auto;border-radius:12px}.finding{padding:16px 18px;margin-top:10px}.finding .sev{font-weight:900;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin-right:8px}.sev.high{color:var(--red)}.sev.medium{color:var(--amber)}.sev.low{color:var(--blue)}.finding h3{display:inline;font-size:.98rem}.finding p{margin-top:6px;font-size:.92rem}.phase-card{display:grid;grid-template-columns:92px 1fr;gap:18px;padding:22px;margin-top:14px}.phase-num{display:grid;place-items:center;width:72px;height:72px;border-radius:18px;background:rgba(88,215,179,.12);color:var(--accent);font-weight:950;font-size:1.5rem}.phase-card.p0 .phase-num{background:rgba(255,143,143,.12);color:var(--red)}.phase-card.p1 .phase-num{background:rgba(255,209,102,.12);color:var(--amber)}.phase-card.p3 .phase-num{background:rgba(119,183,255,.12);color:var(--blue)}.phase-card.p4 .phase-num{background:rgba(196,167,255,.12);color:var(--violet)}.phase-meta{margin-top:4px;font-size:.85rem;color:var(--accent);font-weight:800}.footer-note{margin-top:40px;border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:.92rem}.kicker{color:var(--muted);margin-bottom:14px;max-width:860px}.report-nav{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}.report-nav a{color:#fff;text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:7px 10px;background:rgba(255,255,255,.05);font-size:.8rem;font-weight:800}
@media(max-width:900px){main{width:min(100% - 24px,760px);padding-top:24px}.hero,.grid.two,.grid.three,.grid.four{grid-template-columns:1fr}.phase-card{grid-template-columns:1fr}}
@media print{body{background:#07101d;color:#eef6ff;print-color-adjust:exact;-webkit-print-color-adjust:exact}main{width:auto;padding:.08in}.report-nav{display:none}h1{font-size:42px!important}h2{font-size:24px!important;margin-bottom:10px}.hero{grid-template-columns:1fr;gap:14px;padding:0 0 18px}.hero .summary{font-size:.96rem;margin-top:10px}.verdict-card{padding:16px}.verdict-card strong{font-size:1.32rem}.verdict-card span{font-size:.86rem}.chip{font-size:.68rem;padding:3px 8px}.verdict-card,.panel,.finding,.metric,.phase-card{break-inside:avoid}.phase-card{padding:14px;margin-top:8px;gap:12px;grid-template-columns:64px 1fr}.phase-num{width:52px;height:52px;border-radius:14px}section{break-inside:auto;padding-top:24px}.grid{gap:10px}a{color:#bfe2ff}}
"""


def money(value: int) -> str:
    return f"${value:,.0f}"


def write_both(name: str, html: str) -> None:
    (ROOT / name).write_text(html, encoding="utf-8")
    (PUBLIC / name).write_text(html, encoding="utf-8")


def shell(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{STYLE}</style></head><body><nav class="nav"><span class="brand">Lady D Publishing Hub</span><a href="susan-damon-hub.html">Hub</a><a href="susan-damon-publishing-proposal.html">Proposal/Invoice</a><a href="lady-d-project-dashboard.html">Dashboard</a><a href="{ENHANCED_STATE_REPORT}">Enhanced State</a><a href="{ENHANCED_PLAN_REPORT}">Enhanced Plan</a><a href="index.html">Author Review</a><a href="lady-d-author-site.html">Lady D Site</a></nav>{body}</body></html>"""


def report_shell(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{REPORT_STYLE}</style></head><body><main><nav class="report-nav"><a href="susan-damon-hub.html">Hub</a><a href="susan-damon-publishing-proposal.html">Proposal/Invoice</a><a href="lady-d-project-dashboard.html">Dashboard</a><a href="{ENHANCED_PLAN_REPORT}">Enhanced Plan</a><a href="{ENHANCED_STATE_REPORT}">Enhanced State</a><a href="lady-d-plan-of-attack-2026-07-08.html">July 8 Plan</a><a href="lady-d-state-of-the-union-2026-07-08.html">July 8 State</a></nav>{body}</main></body></html>"""


def book_cards(buttons: bool = True) -> str:
    pieces = []
    for b in books:
        links = ""
        if buttons:
            links = f'<a class="btn gold" href="{b["html"]}">Open HTML book</a><a class="btn" href="{b["pdf"]}">Book PDF</a><a class="btn" href="{b["journal"]}">Journal PDF</a>'
        pieces.append(
            f"""<article class="card book"><img src="{b['cover']}" alt="{b['title']} cover"><div><div class="kicker">{b['vol']} - devotional + journal</div><h3>{b['title']}</h3><p class="muted">{b['subtitle']}</p><p><span class="badge">HTML review</span><span class="badge">PDF proof lane</span><span class="badge">Companion journal</span></p>{links}</div></article>"""
        )
    return "".join(pieces)


cover_cards = "".join(
    f"""<article class="cover-card"><img src="{b['cover']}" alt="{b['title']} cover"><h3>{b['vol']}</h3><p><strong>{b['title']}</strong></p><p class="muted">{b['subtitle']}</p></article>"""
    for b in books
)

proposal_pages = f"""
<section class="page">
  <div class="page-header">
    <div class="brand-lockup">
      <img class="logo-img" src="{LOGO}" alt="Island Development Crew palm logo">
      <div>
        <div class="kicker">Island Dev Crew Consulting - Publishing Systems</div>
        <h1 style="font-size:34px">Susan "Lady D" Damon Publishing Package</h1>
        <p>Corrected agreement, proposal, and execute-ready invoice for the current devotional publishing package.</p>
      </div>
    </div>
    <div style="text-align:right;font-size:13px">
      <strong>Prepared:</strong> July 8, 2026<br>
      <strong>Client:</strong> Susan "Lady D" Damon<br>{CLIENT_EMAIL}<br>
      <strong>Provider:</strong> Jonathan Isaac<br>Island Development Crew LLC<br>{PROVIDER_EMAIL}
    </div>
  </div>
  <div class="callout"><strong>Current correction.</strong> This package now reflects the updated payment facts: current package total {money(PACKAGE_TOTAL)}, {money(PAID_TOTAL)} already paid ({money(PRIOR_PAID)} prior payment + {money(CHECK_PAID)} check), and {money(BALANCE_DUE)} remaining balance. Juan Damon testimony work has been separated from this invoice and should be scoped separately if/when approved.</div>
  <div class="chips"><span class="chip">3 devotional books</span><span class="chip">3 companion journals</span><span class="chip">31-day visual devotional</span><span class="chip">KDP + digital prep</span><span class="chip">Author review hub</span><span class="chip">Juan testimony separate</span></div>
  <div class="two">
    <div class="money"><div>CURRENT PACKAGE TOTAL</div><div class="big">{money(PACKAGE_TOTAL)}</div><p>{money(PAID_TOTAL)} paid to date - {money(BALANCE_DUE)} remaining balance.</p></div>
    <div class="paybox"><p><strong>Payment status:</strong> A new Stripe payment link must be created for the corrected {money(BALANCE_DUE)} remaining balance.</p><p><strong>Payment-link status page:</strong><br><a href="{PAYMENT_LINK}">{PAYMENT_LINK}</a></p><p class="muted">The retired checkout should not be used for this corrected invoice.</p></div>
  </div>
  <div class="footer"><span>Island Dev Crew Consulting - {PROVIDER_EMAIL}</span><span>Lady D Publishing Proposal - Page 1 of 8</span></div>
</section>
<section class="page">
  <h2>1 - Executive Summary</h2>
  <p>This proposal covers the current Lady D devotional publishing package as a professional, proof-gated publishing system. It keeps the strength of the original agreement while reflecting the expanded devotional-library work that now exists: a three-volume devotional series, companion journals, a visual devotional lane, review portal, dashboard, and KDP/digital publishing preparation.</p>
  <table class="table"><tr><th>Track</th><th>Scope</th><th>Current status</th></tr>
  <tr><td><strong>Devotional Trilogy</strong></td><td>Three 365-day devotional books with author-review HTML editions and proof-PDF lanes.</td><td>Assembled for author/publisher review; not final KDP upload files yet.</td></tr>
  <tr><td><strong>Companion Journals</strong></td><td>Three paired journals aligned with the devotional books.</td><td>Draft/proof lanes staged; final print locks pending.</td></tr>
  <tr><td><strong>Visual Devotional</strong></td><td>31-day visual devotional lane from the earlier devotional concept.</td><td>Included in current package as a product lane.</td></tr>
  <tr><td><strong>Publishing System</strong></td><td>Hub, invoice, dashboard, author-review site, Lady D site shell, and payment-link status.</td><td>Built into the review package and ready for corrected payment link.</td></tr>
  <tr><td><strong>Juan Damon testimony</strong></td><td>Testimony/autobiography/memorial concept.</td><td><strong>Separated from this invoice.</strong> Future scope only unless separately approved.</td></tr>
  </table>
  <h2>2 - Recommended Execution</h2>
  <div class="two"><div class="callout"><strong>Finalize first.</strong><br>Freeze scope and source files before producing more assets. The project has enough material to move into proof discipline.</div><div class="callout"><strong>Publish with proof.</strong><br>Move from review HTML/PDF drafts into KDP-ready interiors, final cover wraps, Previewer checks, and physical proof review.</div></div>
  <div class="footer"><span>Corrected package supersedes the prior balance language.</span><span>Page 2 of 8</span></div>
</section>
<section class="page">
  <h2>3 - Execute-Ready Invoice</h2>
  <table class="table"><tr><th>Line</th><th>Description</th><th>Amount</th></tr>
  <tr><td>1</td><td>Three-book devotional library development, structuring, formatting, and author-review delivery.</td><td>$800</td></tr>
  <tr><td>2</td><td>Three companion journals aligned to the devotional collection.</td><td>$400</td></tr>
  <tr><td>3</td><td>31-day visual devotional product lane adapted from the earlier devotional concept.</td><td>$250</td></tr>
  <tr><td>4</td><td>Author review hub, progress dashboard, corrected proposal/invoice, Lady D website shell, and client navigation.</td><td>$250</td></tr>
  <tr><td>5</td><td>KDP/digital publishing prep, cover/interior coordination, proof workflow, rights/scripture/provenance support.</td><td>$300</td></tr>
  <tr><td colspan="2"><strong>Current package total</strong></td><td><strong>{money(PACKAGE_TOTAL)}</strong></td></tr>
  <tr><td colspan="2">Paid credit already received ({money(PRIOR_PAID)} prior payment + {money(CHECK_PAID)} check)</td><td>- {money(PAID_TOTAL)}</td></tr>
  <tr><td colspan="2"><strong>Remaining balance due</strong></td><td><strong>{money(BALANCE_DUE)}</strong></td></tr>
  </table>
  <div class="paybox" style="margin-top:18px"><h3>Payment Link Status</h3><p>The corrected Stripe checkout should be created for <strong>{money(BALANCE_DUE)}</strong>. Until that new link exists, this proposal points to a status page instead of the old checkout.</p><p><a href="{PAYMENT_LINK}"><strong>Open {money(BALANCE_DUE)} payment-link status</strong></a></p></div>
  <div class="footer"><span>Do not send the retired checkout for this corrected invoice.</span><span>Page 3 of 8</span></div>
</section>
<section class="page">
  <h2>4 - Product Exhibit</h2>
  <p>The invoice now carries visual proof of what is being produced, not just a list of words. These covers represent the active author-review devotional lanes.</p>
  <div class="cover-grid">{cover_cards}</div>
  <div class="callout" style="margin-top:16px"><strong>Why this matters.</strong> The customer can see the tangible publishing package: devotional volumes, companion-journal pairings, and a live review system that makes approval easier.</div>
  <div class="footer"><span>Cover art remains subject to author approval and KDP wrap locks.</span><span>Page 4 of 8</span></div>
</section>
<section class="page">
  <h2>5 - Deliverables & Success Criteria</h2>
  <table class="table"><tr><th>Deliverable</th><th>Success criteria</th></tr>
  <tr><td>Three devotional books</td><td>Each book has a reviewable HTML edition, final proof PDF lane, cover direction, front matter plan, and KDP-ready path.</td></tr>
  <tr><td>Three companion journals</td><td>Each journal pairs with its devotional volume and can stand as a reflective product.</td></tr>
  <tr><td>31-day visual devotional</td><td>Visual devotional lane remains included as a product expansion from the original 31-day work.</td></tr>
  <tr><td>Author hub + dashboard</td><td>One review site contains proposal/invoice, PDF, payment-link status, books, journals, dashboard, State of the Union, and Plan of Attack.</td></tr>
  <tr><td>Juan Damon testimony</td><td>Not part of this current {money(PACKAGE_TOTAL)} package. A separate testimony package can be scoped later with intake boundaries, approvals, and its own payment terms.</td></tr>
  </table>
  <h2>6 - Current Client Review Links</h2>
  <p><a href="susan-damon-hub.html">Publishing hub</a> - <a href="index.html">Author review portal</a> - <a href="lady-d-project-dashboard.html">Live dashboard</a> - <a href="lady-d-author-site.html">Lady D website shell</a></p>
  <div class="footer"><span>Review links are part of the client-facing package.</span><span>Page 5 of 8</span></div>
</section>
<section class="page">
  <h2>7 - Publishing Timeline & Production Gates</h2>
  <table class="table"><tr><th>Gate</th><th>Purpose</th><th>Evidence</th></tr>
  <tr><td>Source freeze</td><td>Name canonical sources for all six core products and the visual devotional lane.</td><td>Book registry / source manifest.</td></tr>
  <tr><td>Author decisions</td><td>Approve titles, cover direction, Bible policy, author bio, dedication, acknowledgments, and launch sequence.</td><td>Decision sheet and author approval.</td></tr>
  <tr><td>Editorial + theology proof</td><td>Protect Lady D's voice, Sabbath accuracy, scripture policy, and devotional usefulness.</td><td>Proof report and decision log.</td></tr>
  <tr><td>KDP interior export</td><td>Move from review HTML/PDF drafts to upload candidates.</td><td>Final print PDFs with checksums.</td></tr>
  <tr><td>Cover wrap lock</td><td>Finalize full cover PDFs after page count, trim, bleed, paper, ISBN/barcode decisions.</td><td>KDP cover calculator outputs.</td></tr>
  <tr><td>Physical proof</td><td>Validate readability, margins, cover alignment, paper feel, and author satisfaction.</td><td>Proof photos / approval notes.</td></tr>
  </table>
  <div class="footer"><span>Final publication remains proof-gated.</span><span>Page 6 of 8</span></div>
</section>
<section class="page">
  <h2>8 - Terms, Responsibilities, and Safeguards</h2>
  <div class="two"><div><h3>Provider Responsibilities</h3><ul><li>Preserve Susan Damon's devotional voice.</li><li>Maintain the author review hub and progress dashboard.</li><li>Prepare publishing-ready files after proof gates are passed.</li><li>Keep private source material out of public-facing pages unless approved.</li></ul></div><div><h3>Client Responsibilities</h3><ul><li>Review draft pages and consolidate feedback.</li><li>Confirm author bio, dedication, acknowledgments, cover choice, and Bible policy.</li><li>Confirm final publishing format and distribution direction.</li><li>Approve any separate testimony scope before testimony work is priced or included.</li></ul></div></div>
  <h3>Out of scope unless separately approved</h3><p>Paid marketing campaigns, live seminar coordination, full audiobook narration/production, foreign-language translation, book tour management, products beyond the listed current package, and Juan Damon testimony/autobiography work.</p>
  <div class="footer"><span>Confidentiality and rights language follows the original agreement.</span><span>Page 7 of 8</span></div>
</section>
<section class="page">
  <h2>Acceptance & Payment Instructions</h2>
  <p>By approving this corrected proposal/invoice, the parties acknowledge the current {money(PACKAGE_TOTAL)} package total, {money(PAID_TOTAL)} paid to date, and {money(BALANCE_DUE)} remaining balance.</p>
  <div class="two"><div><h3>Provider</h3><p>Jonathan Isaac<br>Island Development Crew LLC / Island Dev Crew Consulting<br>{PROVIDER_EMAIL}</p><div class="sig"></div><p class="muted">Signature / Date</p></div><div><h3>Client</h3><p>Susan "Lady D" Damon<br>{CLIENT_EMAIL}</p><div class="sig"></div><p class="muted">Signature / Date</p></div></div>
  <div class="paybox"><h3>Payment Instructions</h3><ol><li>Review this proposal/invoice and the live author review hub.</li><li>Create or insert the corrected Stripe checkout for {money(BALANCE_DUE)} before sending the payment button externally.</li><li>Use the dashboard for project status and approval gates.</li><li>Final upload/publishing occurs only after author approval and proof validation.</li></ol></div>
  <div class="footer"><span>Signature-ready PDF; e-sign platform optional if audit trail is required.</span><span>Page 8 of 8</span></div>
</section>
"""

proposal_body = f"""
<main class="print-only">{proposal_pages}</main>
<main class="wrap screen-only"><header class="hero"><div><div class="kicker">Island Development Crew - Proposal & Execute-Ready Invoice</div><h1>Susan "Lady D" Damon Publishing Package</h1><p class="lead">A corrected, PDF-ready client package with IDC branding, product-cover exhibits, author-review links, and the updated {money(PACKAGE_TOTAL)} / {money(PAID_TOTAL)} paid / {money(BALANCE_DUE)} remaining payment structure.</p><p><a class="btn gold" href="susan-damon-publishing-proposal.pdf">Download PDF</a><a class="btn teal" href="{PAYMENT_LINK}">Prepare {money(BALANCE_DUE)} Stripe link</a><a class="btn" href="susan-damon-hub.html">Back to hub</a></p></div><img class="hero-logo" src="{LOGO}" alt="Island Development Crew palm logo"></header></main>
<main class="screen-only">{proposal_pages}</main>
"""

hub_body = f"""
<main class="wrap"><header class="hero"><div><div class="kicker">Lady D - IDC Publishing Command Hub</div><h1>Susan Damon Publishing Hub</h1><p class="lead">One clean place for Mrs. Susan Damon to access the corrected invoice/proposal, author-review portal, live project dashboard, State of the Union, Plan of Attack, devotional books, companion journals, and future Lady D product website.</p></div><img class="hero-logo" src="{LOGO}" alt="Island Development Crew palm logo"></header>
<section class="grid"><article class="card third stat"><strong>{money(PACKAGE_TOTAL)}</strong><span>Current package</span></article><article class="card third stat"><strong>{money(PAID_TOTAL)}</strong><span>Paid to date</span></article><article class="card third stat"><strong>{money(BALANCE_DUE)}</strong><span>Remaining balance</span></article></section>
<section class="grid"><article class="card gold-top"><h2>Proposal & Execute-Ready Invoice</h2><p>The corrected proposal/invoice: updated scope, {money(PACKAGE_TOTAL)} package total, {money(PAID_TOTAL)} paid credit, {money(BALANCE_DUE)} remaining balance, product-cover exhibits, separated testimony lane, terms, signatures, and payment-link status.</p><a class="btn gold" href="susan-damon-publishing-proposal.html">View proposal</a><a class="btn" href="susan-damon-publishing-proposal.pdf">Download PDF</a><a class="btn teal" href="{PAYMENT_LINK}">Prepare {money(BALANCE_DUE)} link</a><p class="muted">Also: <a href="susan-damon-expanded-invoice.html">invoice mirror</a> - <a href="susan-damon-expanded-invoice.pdf">invoice PDF mirror</a></p></article><article class="card teal-top"><h2>Enhanced State & Plan</h2><p>The new enhanced artifacts absorb the latest July 6 guidance: better devotional depth, scripture visibility, KJV/NKJV policy, less mechanical scripture order, cover upgrades, 31-day visual devotional prompt lane, and a reusable client package template.</p><a class="btn dark" href="{ENHANCED_STATE_REPORT}">Enhanced State</a><a class="btn" href="{ENHANCED_PLAN_REPORT}">Enhanced Plan</a><p class="muted">Prior correction pages remain available: <a href="lady-d-state-of-the-union-2026-07-08.html">July 8 State</a> - <a href="lady-d-plan-of-attack-2026-07-08.html">July 8 Plan</a></p></article></section>
<section class="grid"><article class="card full"><h2>Devotional Library</h2><p class="lead">HTML review editions are available now. PDF proof lanes are staged and will be upgraded as final proof PDFs are generated.</p><div class="grid">{book_cards()}</div></article></section>
<section class="grid"><article class="card coral-top"><h2>Separated Testimony Lane</h2><p>Juan Damon testimony/autobiography work is no longer included in the current {money(PACKAGE_TOTAL)} invoice. It remains valuable, but it needs separate intake, family/content boundaries, approval checkpoints, and pricing.</p><a class="btn" href="lady-d-project-dashboard.html#testimony">View separated lane</a></article><article class="card"><h2>Lady D Website</h2><p>A public-facing product website shell is attached for future books, journals, KDP/Gumroad links, devotional samples, and ministry products.</p><a class="btn gold" href="lady-d-author-site.html">Open Lady D site</a></article></section></main>
"""

dashboard_body = f"""
<main class="wrap"><header class="hero"><div><div class="kicker">Live Publishing Dashboard - Lady D</div><h1>Project Dashboard</h1><p class="lead">Current operating view for completing the corrected publishing package without losing scope, author voice, or proof discipline.</p><p><span class="badge">Portal live</span><span class="badge">Invoice corrected</span><span class="badge">Payment link pending</span><span class="badge">Testimony separated</span></p></div><img class="hero-logo" src="{LOGO}" alt="Island Development Crew palm logo"></header>
<section class="grid"><article class="card mini stat"><strong>3</strong><span>Devotional books</span></article><article class="card mini stat"><strong>3</strong><span>Companion journals</span></article><article class="card mini stat"><strong>1</strong><span>31-day visual devotional</span></article><article class="card mini stat"><strong>{money(BALANCE_DUE)}</strong><span>Balance due</span></article></section>
<section class="grid"><article class="card full"><h2>Completion Gates</h2><table class="table"><tr><th>Gate</th><th>Status</th><th>Next action</th></tr><tr><td>Proposal / invoice</td><td>Corrected</td><td>Mrs. Damon can view HTML and download PDF; create the new {money(BALANCE_DUE)} Stripe checkout before sending externally.</td></tr><tr><td>Author review portal</td><td>Live</td><td>Review three devotional HTML books and companion journal PDF lanes.</td></tr><tr><td>Source freeze</td><td>Pending</td><td>Create final book registry and canonical source list.</td></tr><tr><td>KDP proof files</td><td>Pending</td><td>Generate final interiors, wraps, and Previewer evidence.</td></tr><tr><td>Physical proof</td><td>Pending</td><td>Order/inspect proofs before public publishing.</td></tr></table></article></section>
<section id="testimony" class="grid"><article class="card full coral-top"><h2>Juan Damon Testimony Lane - Separate Scope</h2><table class="table"><tr><th>Step</th><th>Status / action</th></tr><tr><td>Scope</td><td>Separated from the current {money(PACKAGE_TOTAL)} publishing package and not part of the {money(BALANCE_DUE)} remaining balance.</td></tr><tr><td>Source Intake</td><td>Future work should collect testimony source material, family details, photos, recordings, written notes, and sensitive content boundaries.</td></tr><tr><td>Structure</td><td>Build a reverent testimony/memorial book outline only after approval and separate payment terms.</td></tr><tr><td>Production</td><td>Move through source lock, draft, family review, interior formatting, cover, proofing, and KDP/digital prep as its own project.</td></tr></table></article></section></main>
"""

author_site_body = f"""
<main class="wrap"><header class="hero"><div><div class="kicker">Lady D Devotional Library - Public Website Shell</div><h1>Devotionals for a Life Walking With Jesus</h1><p class="lead">A warm public website shell for Susan "Lady D" Damon's devotional ministry, staged to become the storefront for books, journals, visual devotionals, speaking, and reader resources.</p><a class="btn gold" href="index.html">Preview books</a><a class="btn" href="susan-damon-hub.html">Publishing hub</a></div><img class="hero-logo" src="{LOGO}" alt="Island Development Crew palm logo"></header><section class="grid"><article class="card full"><h2>Featured Devotional Collection</h2><div class="grid">{book_cards()}</div></article></section><section class="grid"><article class="card"><h2>About Lady D</h2><p>Susan "Lady D" Damon writes with warmth, faith, direct encouragement, and a heart for helping readers walk with Jesus in daily life.</p></article><article class="card"><h2>Coming Product Lanes</h2><ul><li>Devotional book collection</li><li>Companion journals</li><li>31-day visual devotional</li><li>Reader resources and purchase links</li><li>Separate future testimony/autobiography lane if approved</li></ul></article></section></main>
"""

payment_status_body = f"""
<main class="wrap"><header class="hero"><div><div class="kicker">Payment Link Status - Corrected Invoice</div><h1>{money(BALANCE_DUE)} Stripe Link Needed</h1><p class="lead">The customer-facing package has been corrected to the {money(PACKAGE_TOTAL)} total, {money(PAID_TOTAL)} paid, and {money(BALANCE_DUE)} remaining balance. The retired checkout should not be sent.</p><a class="btn gold" href="susan-damon-publishing-proposal.html">Back to proposal</a></div><img class="hero-logo" src="{LOGO}" alt="Island Development Crew palm logo"></header><section class="grid"><article class="card full warning"><h2>Action Required Before Sending Payment Button</h2><p>Create a new live Stripe payment link for <strong>{money(BALANCE_DUE)} USD</strong> and replace this status page link in the package.</p><table class="table"><tr><th>Field</th><th>Correct value</th></tr><tr><td>Product/name</td><td>Susan Damon - Corrected Publishing Package Remaining Balance</td></tr><tr><td>Amount</td><td>{money(BALANCE_DUE)}.00 USD</td></tr><tr><td>Description</td><td>Remaining balance for current Lady D publishing package: 3 devotional books, 3 companion journals, 31-day visual devotional, author review hub, dashboard, KDP/digital preparation. Juan Damon testimony separated from current package.</td></tr><tr><td>Metadata</td><td>client=Susan Damon; package_total={PACKAGE_TOTAL}; paid_credit={PAID_TOTAL}; remaining_balance={BALANCE_DUE}; testimony_scope=separate</td></tr></table><p class="muted">Status: {OLD_PAYMENT_LINK_STATUS}.</p></article></section></main>
"""

state_body = f"""
<header class="hero">
  <div><p class="eyebrow">Lady D Project - State of the Union - July 8, 2026</p><h1>The package is real; the finish now has to be disciplined.</h1><p class="summary">This report is built from the local Lady D review site, the original agreement extraction, May 5 and June 14 transcript summaries, the July 6 Fireflies transcript, the July 6 release-control handoff, KDP proof/readiness packs, and live reference sites for the desired client-package standard. The headline: the project has crossed from idea generation into product finalization, but the invoice, payment link, testimony scope, latest author feedback, and proof gates had to be corrected before it could be sent confidently.</p><div style="margin-top:16px"><span class="chip green">6 core KDP-facing products assembled</span><span class="chip amber">{money(BALANCE_DUE)} corrected balance</span><span class="chip red">retired checkout blocked</span><span class="chip blue">Juan testimony separated</span><span class="chip violet">template system now reusable</span></div></div>
  <aside class="verdict-card"><strong>Verdict: strong production candidate, not final-publication ready.</strong><span>The Lady D library has substance, assets, and a live review ecosystem. It still needs author decisions, payment-link replacement, source freeze, Bible policy, KDP Previewer, and physical proof before public release.</span></aside>
</header>
<section><h2>Executive Scoreboard</h2><div class="grid four"><article class="metric"><strong>3</strong><span class="muted">Full devotional volumes in review lanes.</span></article><article class="metric"><strong>3</strong><span class="muted">Companion journals paired to the trilogy.</span></article><article class="metric"><strong>{money(PACKAGE_TOTAL)}</strong><span class="muted">Corrected current package value.</span></article><article class="metric"><strong>{money(PAID_TOTAL)}</strong><span class="muted">Paid to date after the {money(CHECK_PAID)} check.</span></article></div></section>
<section><h2>What the Audit Actually Found</h2><p class="kicker">Confirmed items below are grounded in local files and transcript summaries; unverified external actions are kept separate.</p>
  <article class="finding"><span class="sev high">High</span><h3>Invoice truth was stale.</h3><p>The generated proposal still used the prior expanded-package pricing and old checkout path. The corrected source now uses {money(PACKAGE_TOTAL)} total, {money(PAID_TOTAL)} paid, and {money(BALANCE_DUE)} due.</p></article>
  <article class="finding"><span class="sev high">High</span><h3>Juan Damon testimony was incorrectly bundled.</h3><p>The current customer-facing invoice had testimony language inside the package. The June 14 transcript treated testimony/autobiography as a separate future/complementary work. The corrected documents now mark that lane separate.</p></article>
  <article class="finding"><span class="sev medium">Medium</span><h3>The project is assembled, not upload-final.</h3><p>The proof packs show six core products, zero placeholders in checked sources, zero Sunday mentions, and a substantial word base. They also explicitly block final upload until author decisions, Bible policy, KDP Previewer, cover locks, and physical proof.</p></article>
  <article class="finding"><span class="sev medium">Medium</span><h3>July 6 author feedback changes the proof lane.</h3><p>The latest Fireflies transcript says the drafts need actual scripture text on each devotional page, less sterile devotional language, context-language simplification or removal, fused practical steps/journal prompts, fuller journal pages, brighter/higher-resolution covers, and research into Amazon author/editor-copy economics.</p></article>
  <article class="finding"><span class="sev medium">Medium</span><h3>The design system was split across several successful examples.</h3><p>The strongest reusable pattern is a blend: Oakwood's IDC proposal clarity, Joyce's elegant author navigation, and Lady D's warm review portal. The corrected package extracts that into one local CSS/template system with the IDC palm logo.</p></article>
  <div class="grid two" style="margin-top:18px"><article class="panel"><h3>What is genuinely excellent</h3><ul><li>Three-volume devotional architecture with companion journals.</li><li>Live author-review portal with product links and dashboards.</li><li>KDP proof/readiness packs that state boundaries honestly.</li><li>Strong visual cover assets that make the invoice feel tangible.</li></ul></article><article class="panel"><h3>Structural debt to burn down</h3><ul><li>Create the real {money(BALANCE_DUE)} Stripe link.</li><li>Freeze source manifests and remove stale public paths from active navigation.</li><li>Complete final author decisions before more generation.</li><li>Run KDP Previewer and physical proof before public launch language.</li></ul></article></div>
</section>
<section><h2>Reference Pattern Decision</h2><p class="kicker">The final client-package template should borrow different strengths from each source rather than copying one page wholesale.</p><div class="table-wrap"><table><thead><tr><th>Reference</th><th>Best strength to preserve</th><th>How Lady D now uses it</th></tr></thead><tbody><tr><td><strong>Lady D author review</strong></td><td>Warm author/product review environment.</td><td>Keep the book-first portal and devotionally gentle voice.</td></tr><tr><td><strong>Oakwood AI Lab IDC</strong></td><td>Clean IDC proposal structure, logo, price cards, client package clarity.</td><td>Use the IDC palette, logo lockup, pricing box, and hub model.</td></tr><tr><td><strong>Joyce publishing site</strong></td><td>Elegant author navigation and literary polish.</td><td>Use smoother mobile navigation and a richer public author shell.</td></tr><tr><td><strong>Martin Electric estimate</strong></td><td>Photo/product appendix makes scope concrete.</td><td>Use book-cover exhibits in the invoice instead of a words-only quote.</td></tr></tbody></table></div></section>
<section><h2>Baseline to Target</h2><div class="table-wrap"><table><thead><tr><th>Dimension</th><th>Baseline</th><th>Target gate</th><th>Status</th></tr></thead><tbody><tr><td><strong>Invoice/payment</strong></td><td>Stale balance and retired checkout language.</td><td>Correct {money(BALANCE_DUE)} link created and inserted.</td><td>Document fixed; Stripe link pending.</td></tr><tr><td><strong>Scope</strong></td><td>Testimony bundled into current package.</td><td>Current package excludes testimony; separate scope available later.</td><td>Fixed in generated pages.</td></tr><tr><td><strong>Content depth</strong></td><td>Lady D described some drafts as sterile because scripture text, voice, and prompt clarity were not fully finished.</td><td>Scripture present, voice-filter pass complete, context language resolved, prompts simplified, journals human-finished.</td><td>Needs next production pass.</td></tr><tr><td><strong>Publishing readiness</strong></td><td>Production candidate artifacts exist.</td><td>KDP Previewer + physical proof + author approvals complete.</td><td>Still pending.</td></tr><tr><td><strong>Template reuse</strong></td><td>Several good one-off layouts.</td><td>One client package pattern reusable for invoices/proposals/dashboards.</td><td>Started with shared generator + CSS.</td></tr></tbody></table></div></section>
<p class="footer-note">Evidence: original agreement extraction, May 5 and June 14 transcript summaries, July 6 Fireflies transcript 01KWXC5F7J9EPX9BDPXEBWVKK5, July 6 release-control brief, KDP proof/readiness packs, local generated HTML, and live visual references: <a href="https://lady-d-author-review-site.vercel.app/">Lady D</a>, <a href="https://oakwood-ai-hub.vercel.app/ai-lab-idc/">Oakwood IDC</a>, and <a href="https://joyce-publishing-fade-deck-site.vercel.app/">Joyce publishing site</a>.</p>
"""

plan_body = f"""
<header class="hero">
  <div><p class="eyebrow">Lady D Project - Plan of Attack - July 8, 2026</p><h1>Finish the package in gates, not another expansion spiral.</h1><p class="summary">The plan is to lock truth first, then polish the template system, then move six products through proof gates. The plan covers at least four deliverables: corrected proposal/invoice, client hub/dashboard, State of the Union and Plan of Attack reports, KDP proof/finalization package, public Lady D author site, and separated testimony scope.</p><div style="margin-top:16px"><span class="chip red">P0 payment truth</span><span class="chip amber">P1 template lock</span><span class="chip green">P2 KDP proof lane</span><span class="chip blue">P3 client dashboard</span><span class="chip violet">P4 future testimony scope</span></div></div>
  <aside class="verdict-card"><strong>Operating principle: no more public-facing ambiguity.</strong><span>Every customer page should answer three questions clearly: what is included, what is owed, and what must happen before publication.</span></aside>
</header>
<section><h2>Phase Plan</h2><p class="kicker">Sequenced by risk reduction: money/scope first, template second, publication third.</p>
  <article class="phase-card p0"><div class="phase-num">0</div><div><h3>Correct payment and scope - stop the confusion</h3><p class="phase-meta">Immediate - owner: Jon/IDC</p><ul><li>Use {money(PACKAGE_TOTAL)} package total, {money(PAID_TOTAL)} paid, and {money(BALANCE_DUE)} balance everywhere in the active package.</li><li>Create a live Stripe link for {money(BALANCE_DUE)} and replace <code>{PAYMENT_LINK}</code>.</li><li>Keep Juan Damon testimony separate from this invoice unless a new scope is approved.</li></ul></div></article>
  <article class="phase-card p1"><div class="phase-num">1</div><div><h3>Lock the client-package template - make this reusable</h3><p class="phase-meta">Next build pass - owner: Codex/IDC</p><ul><li>Keep the IDC palm logo, teal/deep/gold/coral palette, pricing cards, signature blocks, and PDF-ready page sections.</li><li>Use visual exhibits by job type: book covers for publishing, photos for trades/facilities, screenshots for software.</li><li>Keep mobile navigation like Joyce and proposal clarity like Oakwood.</li></ul></div></article>
  <article class="phase-card"><div class="phase-num">2</div><div><h3>Move six products through proof discipline</h3><p class="phase-meta">Production finalization - owner: Jon + Lady D</p><ul><li>Freeze source manifests for the three devotionals and three journals.</li><li>Collect author decisions: titles, covers, Bible policy, bio, dedication, acknowledgments, launch order.</li><li>Generate final interiors and wraps only after page count and trim choices are locked.</li><li>Run KDP Previewer and order physical proofs before public release language.</li></ul></div></article>
  <article class="phase-card p3"><div class="phase-num">3</div><div><h3>Apply the July 6 author-feedback pass</h3><p class="phase-meta">Content refinement - owner: IDC + Lady D</p><ul><li>Add actual scripture text to each devotional page after Bible-policy approval.</li><li>Remove or simplify context-language material if it takes space from devotional depth.</li><li>Fuse today's step / morning impact material into clearer journal prompts.</li><li>Brighten and regenerate higher-resolution covers; finish journal page layouts with a human pass.</li><li>Research Amazon author/editor-copy cost and workflow before the first upload.</li></ul></div></article>
  <article class="phase-card p3"><div class="phase-num">4</div><div><h3>Turn the hub into the client control room</h3><p class="phase-meta">Client visibility - owner: IDC</p><ul><li>Keep the corrected invoice, dashboard, State of the Union, Plan of Attack, author review books, and author site shell linked from one hub.</li><li>Keep status language honest: review-ready, proof-ready, upload-ready, published.</li><li>Use the dashboard for weekly status and approval requests.</li></ul></div></article>
  <article class="phase-card p4"><div class="phase-num">5</div><div><h3>Scope Juan Damon testimony separately</h3><p class="phase-meta">Future lane - owner: Lady D + family approval</p><ul><li>Collect source recordings, photos, family notes, sensitivity boundaries, and desired audience.</li><li>Write a separate estimate with its own payment, timeline, review, and rights language.</li><li>Do not blend it back into the current {money(PACKAGE_TOTAL)} invoice.</li></ul></div></article>
</section>
<section><h2>Deliverable Map</h2><div class="grid three"><article class="task"><span class="chip red">Deliverable 1</span><h3>Corrected proposal/invoice</h3><p>HTML + PDF, IDC logo, product-cover exhibit, {money(BALANCE_DUE)} balance, testimony separated.</p></article><article class="task"><span class="chip amber">Deliverable 2</span><h3>Client hub + dashboard</h3><p>One clean route into invoice, books, reports, project gates, and payment status.</p></article><article class="task"><span class="chip green">Deliverable 3</span><h3>State + Plan reports</h3><p>Flagship HTML reports that tell the truth, name the risks, and guide execution.</p></article><article class="task"><span class="chip blue">Deliverable 4</span><h3>KDP finalization pack</h3><p>Source freeze, author decisions, Bible policy, final interiors/wraps, Previewer, physical proof.</p></article><article class="task"><span class="chip violet">Deliverable 5</span><h3>Lady D public site</h3><p>Warm author/product shell modeled after Joyce with Lady D's own devotional identity.</p></article><article class="task"><span class="chip">Deliverable 6</span><h3>Separate testimony package</h3><p>Future estimate for Juan Damon testimony/autobiography with boundaries and approvals.</p></article></div></section>
<section><h2>Immediate Task Board</h2><div class="table-wrap"><table><thead><tr><th>Task</th><th>Owner</th><th>Done when</th></tr></thead><tbody><tr><td><strong>Create corrected Stripe link</strong></td><td>Jon/Stripe account</td><td>Live checkout shows {money(BALANCE_DUE)} and the retired checkout is not used.</td></tr><tr><td><strong>Author decision sheet</strong></td><td>Lady D + Jon</td><td>Titles, cover direction, Bible policy, bio, dedication, acknowledgments, and launch order are approved.</td></tr><tr><td><strong>July 6 feedback pass</strong></td><td>IDC</td><td>Scripture, context-language, prompt, cover brightness, and journal-layout changes are applied to a review sample.</td></tr><tr><td><strong>Amazon copy economics</strong></td><td>IDC</td><td>Author/editor-copy costs, proof-copy workflow, and retail pricing options are documented for Lady D.</td></tr><tr><td><strong>Final proof build</strong></td><td>IDC</td><td>Final PDFs/wraps have checksums and pass visual proof review.</td></tr><tr><td><strong>KDP Previewer</strong></td><td>IDC</td><td>Previewer screenshots/logs show no blocking margin/bleed/interior issues.</td></tr><tr><td><strong>Physical proof</strong></td><td>Lady D + IDC</td><td>Printed proof is reviewed, photographed, and approved before public release.</td></tr></tbody></table></div></section>
<section><h2>Client Template Rules Going Forward</h2><div class="grid two"><article class="panel"><h3>Every proposal should include</h3><ul><li>IDC brand/logo lockup and clear price box.</li><li>What is included, excluded, paid, and owed.</li><li>Visual exhibit section matched to the job type.</li><li>Customer-friendly hub + downloadable PDF.</li><li>Signature/approval area and payment-link status.</li></ul></article><article class="panel"><h3>Every dashboard should include</h3><ul><li>Current status and next owner.</li><li>Completion gates, not vague progress claims.</li><li>Links to live artifacts and PDFs.</li><li>Separate future lanes clearly marked as separate.</li><li>Mobile-friendly navigation and no hidden stale payment terms.</li></ul></article></div></section>
<p class="footer-note">Evidence: local Lady D generator, original agreement extraction, May 5 and June 14 transcript summaries, July 6 Fireflies transcript 01KWXC5F7J9EPX9BDPXEBWVKK5, July 6 release-control brief, KDP proof/readiness packs, and visual references from the Lady D, Oakwood IDC, Joyce, and Martin-style package patterns.</p>
"""

pages = {
    "susan-damon-publishing-proposal.html": shell("Susan Damon Publishing Proposal & Execute-Ready Invoice", proposal_body),
    "susan-damon-expanded-invoice.html": shell("Susan Damon Corrected Publishing Invoice", proposal_body),
    "susan-damon-hub.html": shell("Susan Damon Publishing Hub", hub_body),
    "lady-d-project-dashboard.html": shell("Lady D Project Dashboard", dashboard_body),
    "lady-d-author-site.html": shell("Lady D Devotional Library Website", author_site_body),
    PAYMENT_LINK: shell("Lady D Stripe Payment Link Status", payment_status_body),
    "stripe-payment-update-status.html": shell("Lady D Stripe Payment Update Status", payment_status_body),
    "lady-d-state-of-the-union-2026-07-08.html": report_shell("Lady D State of the Union - July 8, 2026", state_body),
    "lady-d-plan-of-attack-2026-07-08.html": report_shell("Lady D Plan of Attack - July 8, 2026", plan_body),
}

for name, html in pages.items():
    write_both(name, html)

for idx in [ROOT / "index.html", PUBLIC / "index.html"]:
    if not idx.exists():
        continue
    html = idx.read_text(encoding="utf-8")
    html = re.sub(
        r'<nav class="topbar">.*?</nav>',
        f'<nav class="topbar"><span class="brand">Lady D Author Review</span><a href="#books">Books</a><a href="susan-damon-hub.html">Publishing hub</a><a href="susan-damon-publishing-proposal.html">Proposal/Invoice</a><a href="lady-d-project-dashboard.html">Live dashboard</a><a href="{ENHANCED_STATE_REPORT}">Enhanced State</a><a href="{ENHANCED_PLAN_REPORT}">Enhanced Plan</a><a href="lady-d-author-site.html">Lady D site</a><a href="release-status.html">Release dashboard</a></nav>',
        html,
        count=1,
        flags=re.S,
    )
    card = f"""<section id="business-hub-lane" class="card notice"><h2>Proposal & Execute-Ready Invoice</h2><p>The corrected package now has a robust proposal/invoice page like the Oakwood hub: viewable HTML proposal, downloadable PDF invoice/proposal, {money(PACKAGE_TOTAL)} package total, {money(PAID_TOTAL)} paid, {money(BALANCE_DUE)} balance due, live dashboard, enhanced State of the Union, enhanced Plan of Attack, and future Lady D product website.</p><p><a class="btn gold" href="susan-damon-publishing-proposal.html">View proposal</a><a class="btn" href="susan-damon-publishing-proposal.pdf">Download PDF</a><a class="btn" href="{PAYMENT_LINK}">Prepare {money(BALANCE_DUE)} Stripe link</a><a class="btn" href="lady-d-project-dashboard.html">Live dashboard</a><a class="btn" href="{ENHANCED_STATE_REPORT}">Enhanced State</a><a class="btn" href="{ENHANCED_PLAN_REPORT}">Enhanced Plan</a></p></section>"""
    old = re.search(r'<section id="business-hub-lane".*?</section>', html, flags=re.S)
    if old:
        html = html[: old.start()] + card + html[old.end() :]
    else:
        html = html.replace('<section class="card"><h2>What has been done</h2>', card + '<section class="card"><h2>What has been done</h2>')
    idx.write_text(html, encoding="utf-8")


def export_pdf(html_name: str, pdf_name: str) -> bool:
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not Path(chrome).exists():
        return False
    src = ROOT / html_name
    pdf = ROOT / pdf_name
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf}",
            "file://" + str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(pdf, PUBLIC / pdf.name)
    return True


pdfs = {}
for html_name, pdf_name in [
    ("susan-damon-publishing-proposal.html", "susan-damon-publishing-proposal.pdf"),
    ("susan-damon-publishing-proposal.html", "susan-damon-expanded-invoice.pdf"),
    ("lady-d-state-of-the-union-2026-07-08.html", "lady-d-state-of-the-union-2026-07-08.pdf"),
    ("lady-d-plan-of-attack-2026-07-08.html", "lady-d-plan-of-attack-2026-07-08.pdf"),
]:
    pdfs[pdf_name] = export_pdf(html_name, pdf_name)

stripe_instructions = f"""# Lady D Corrected Stripe Payment Link Instructions

Generated: {DATE}

## Correct payment facts

- Customer: Susan "Lady D" Damon
- Email: {CLIENT_EMAIL}
- Current package total: {money(PACKAGE_TOTAL)}
- Paid to date: {money(PAID_TOTAL)} ({money(PRIOR_PAID)} prior payment + {money(CHECK_PAID)} check)
- Remaining balance: {money(BALANCE_DUE)}
- Juan Damon testimony/autobiography book: separate future scope, not part of this checkout

## Current Stripe status

The local package points to `{PAYMENT_LINK}` until a real live Stripe Payment Link exists.

Attempted live CLI creation was blocked because the configured live restricted key lacks permission to create Stripe Prices/Payment Links. Use the Stripe Dashboard with an owner/admin session, or provide a live key with the required Product, Price, and Payment Link creation permissions.

## Dashboard fields

- Product name: Susan Damon - Corrected Publishing Package Remaining Balance
- Amount: {money(BALANCE_DUE)}.00 USD
- Description: Remaining balance for current Lady D publishing package: 3 devotional books, 3 companion journals, 31-day visual devotional, author review hub, dashboard, KDP/digital preparation. Juan Damon testimony separated from current package.
- Metadata:
  - client=Susan Damon
  - project=Lady D publishing package
  - package_total={PACKAGE_TOTAL}
  - paid_credit={PAID_TOTAL}
  - remaining_balance={BALANCE_DUE}
  - testimony_scope=separate

## After the link is created

Update `PAYMENT_LINK` near the top of `scripts/build_lady_d_hub.py` from `{PAYMENT_LINK}` to the new live Stripe URL, then rerun:

```bash
python3 scripts/build_lady_d_hub.py
npm run build
```

Then verify:

```bash
rg -n "\\$2,300|\\$2,500|buy\\.stripe|Pay \\$2,300" susan-damon-publishing-proposal.html public/susan-damon-publishing-proposal.html
```

If the real live Stripe URL intentionally begins with `https://buy.stripe.com/`, the `buy\\.stripe` check should return the new corrected link only, not the retired checkout.
"""
(ROOT / "STRIPE_1400_PAYMENT_LINK_INSTRUCTIONS.md").write_text(stripe_instructions, encoding="utf-8")

zip_path = ROOT / "Lady-D-Corrected-Package-2026-07-08.zip"
if zip_path.exists():
    zip_path.unlink()
zip_inputs = [
    ROOT / "susan-damon-publishing-proposal.html",
    ROOT / "susan-damon-publishing-proposal.pdf",
    ROOT / "lady-d-state-of-the-union-2026-07-08.html",
    ROOT / "lady-d-state-of-the-union-2026-07-08.pdf",
    ROOT / "lady-d-plan-of-attack-2026-07-08.html",
    ROOT / "lady-d-plan-of-attack-2026-07-08.pdf",
    ROOT / "STRIPE_1400_PAYMENT_LINK_INSTRUCTIONS.md",
]
subprocess.run(["zip", "-j", "-q", str(zip_path), *[str(p) for p in zip_inputs if p.exists()]], check=False)

manifest = {
    "generated": DATE,
    "package_total": PACKAGE_TOTAL,
    "prior_paid": PRIOR_PAID,
    "check_paid": CHECK_PAID,
    "paid_total": PAID_TOTAL,
    "remaining_balance": BALANCE_DUE,
    "payment_link_status": PAYMENT_LINK,
    "old_payment_link_status": OLD_PAYMENT_LINK_STATUS,
    "stripe_permission_status": STRIPE_PERMISSION_STATUS,
    "primary_proposal": "susan-damon-publishing-proposal.html",
    "primary_pdf": "susan-damon-publishing-proposal.pdf",
    "state_of_union": "lady-d-state-of-the-union-2026-07-08.html",
    "plan_of_attack": "lady-d-plan-of-attack-2026-07-08.html",
    "enhanced_state_of_union": ENHANCED_STATE_REPORT,
    "enhanced_plan_of_attack": ENHANCED_PLAN_REPORT,
    "pages": list(pages.keys()),
    "pdfs": pdfs,
    "scope_included": [
        "3 devotional books",
        "3 companion journals",
        "31-day visual devotional",
        "author review hub",
        "project dashboard",
        "Lady D website shell",
        "KDP/digital publishing prep",
    ],
    "scope_separate": ["Juan Damon testimony/autobiography book"],
    "source_meetings": [
        {"id": "01KQXAN1Y9WR2GD2EX7J687WYK", "date": "2026-05-05", "topic": "monthly devotional, journal, KDP, workbooks"},
        {"id": "01KV4JJ1M47PBZ75K78CQGP989", "date": "2026-06-14", "topic": "three-volume devotional bundle, companion journals, $2,000 package"},
        {"id": "01KWXC5F7J9EPX9BDPXEBWVKK5", "date": "2026-07-06", "topic": "author feedback, separate testimony lane, invoice/Stripe update"}
    ],
}
write_both("lady-d-hub-build-manifest-2026-07-08.json", json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
