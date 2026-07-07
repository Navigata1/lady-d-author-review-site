#!/usr/bin/env python3
from pathlib import Path
import re, shutil, subprocess, os, json

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
PUBLIC.mkdir(exist_ok=True)
PAYMENT_LINK = 'https://buy.stripe.com/5kQ14pgB3bdAafQezM0VO04'
LIVE_BASE = 'https://lady-d-author-review-site.vercel.app'
DATE = '2026-07-06'

books = [
    {
        'vol':'Volume 1', 'title':'Surrendering to God’s Love', 'subtitle':'A 365-Day Devotional Journey into the Father’s Heart',
        'html':'book-1-surrendering-to-gods-love-review.html', 'cover':'production-assets/author-review-covers/volume-1-author-review-cover.png',
        'pdf':'downloads/production/kdp/interior-drafts/volume-1/volume-1-full-6x9-interior-draft.pdf',
        'journal':'downloads/production/kdp/companion-journal-drafts/volume-1/volume-1-companion-journal-6x9-draft.pdf'
    },
    {
        'vol':'Volume 2', 'title':'Walking with Jesus', 'subtitle':'A 365-Day Devotional Journey of Daily Discipleship',
        'html':'book-2-walking-with-jesus-review.html', 'cover':'production-assets/author-review-covers/volume-2-author-review-cover.png',
        'pdf':'downloads/production/kdp/interior-drafts/volume-2/volume-2-full-6x9-interior-draft.pdf',
        'journal':'downloads/production/kdp/companion-journal-drafts/volume-2/volume-2-companion-journal-6x9-draft.pdf'
    },
    {
        'vol':'Volume 3', 'title':'Filled with the Holy Spirit', 'subtitle':'A 365-Day Devotional Journey in Spirit-Led Living',
        'html':'book-3-filled-with-the-holy-spirit-review.html', 'cover':'production-assets/author-review-covers/volume-3-author-review-cover.png',
        'pdf':'downloads/production/kdp/interior-drafts/volume-3/volume-3-full-6x9-interior-draft.pdf',
        'journal':'downloads/production/kdp/companion-journal-drafts/volume-3/volume-3-companion-journal-6x9-draft.pdf'
    }
]

STYLE = r'''
:root{--ink:#241913;--muted:#746252;--paper:#fffaf2;--cream:#f3e6d2;--card:#fffdf8;--line:rgba(86,54,26,.18);--gold:#b9852e;--deep:#4e2c14;--wine:#6b2e25;--green:#276148;--blue:#2f527c;--shadow:0 24px 80px rgba(62,37,16,.13)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,#fff8e8,#f4e3ca 48%,#ead0ad);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.58}.wrap{max-width:1180px;margin:auto;padding:38px 20px 78px}.nav{position:sticky;top:0;z-index:10;background:rgba(32,20,12,.94);backdrop-filter:blur(18px);display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px 18px}.nav a,.nav span{color:white;text-decoration:none;font-size:13px;font-weight:850;padding:8px 11px;border-radius:999px;background:rgba(255,255,255,.09)}.nav .brand{background:transparent;color:#f4d492}.hero{border-radius:34px;background:linear-gradient(135deg,#1f130b,#5b351a 68%,#8c6428);color:white;padding:46px;box-shadow:var(--shadow);position:relative;overflow:hidden}.hero:after{content:"";position:absolute;right:-95px;top:-95px;width:280px;height:280px;border-radius:50%;background:rgba(255,255,255,.11)}.kicker{text-transform:uppercase;letter-spacing:.18em;color:#c18a34;font-size:12px;font-weight:950}.hero .kicker{color:#f6d383}h1,h2,h3{font-family:Georgia,"Times New Roman",serif;line-height:1.05;margin:0 0 14px}h1{font-size:clamp(42px,7vw,86px);letter-spacing:-.045em}h2{font-size:clamp(30px,4vw,50px);letter-spacing:-.025em}h3{font-size:24px}.lead{font-size:clamp(18px,2vw,23px);max-width:900px}.hero .lead{color:#f8ead8}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:18px;margin-top:22px}.card{grid-column:span 6;background:rgba(255,253,248,.95);border:1px solid var(--line);border-radius:24px;padding:24px;box-shadow:var(--shadow)}.third{grid-column:span 4}.full{grid-column:1/-1}.mini{grid-column:span 3}.badge{display:inline-flex;border-radius:999px;background:#efe1c8;color:#5a3b17;padding:7px 10px;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.ok{background:#e7f5ed;color:var(--green)}.warn{background:#fff0d3;color:#855812}.blue{background:#e7f0fb;color:var(--blue)}.wine{background:#fae7e2;color:var(--wine)}.btn{display:inline-flex;align-items:center;gap:8px;text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:11px 15px;margin:5px 6px 5px 0;color:#35261c;background:white;font-weight:900}.btn.gold{background:linear-gradient(135deg,#b9852e,#e4bf72);color:#1f130b;border:0}.btn.dark{background:#241913;color:white;border:0}.muted{color:var(--muted)}.stat strong{display:block;font-family:Georgia,serif;font-size:46px;line-height:1;color:var(--deep)}.book{display:grid;grid-template-columns:155px 1fr;gap:20px;align-items:center}.book img{width:100%;border-radius:14px;box-shadow:0 16px 42px rgba(62,37,16,.18);border:1px solid rgba(255,255,255,.7)}.table{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#fff}.table th,.table td{text-align:left;vertical-align:top;padding:13px 14px;border-bottom:1px solid var(--line)}.table th{background:#f7ebd8;color:#492811;text-transform:uppercase;font-size:.8rem;letter-spacing:.08em}.table tr:last-child td{border-bottom:0}.callout{border-radius:18px;border:1px solid var(--line);background:#fff8e8;padding:16px 18px}.stage{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.stage div{border:1px solid var(--line);border-radius:16px;padding:14px;background:white}.stage strong{display:block;color:var(--deep)}footer{margin-top:26px;color:var(--muted);font-size:.9rem}.print-hide{}@media(max-width:820px){.card,.third,.mini{grid-column:1/-1}.hero{padding:30px 24px}.wrap{padding:24px 12px 58px}.book{grid-template-columns:1fr}.book img{max-width:230px}.table{font-size:.92rem}}@media print{.nav,.print-hide{display:none}.wrap{padding:0}.hero,.card{box-shadow:none}.card{break-inside:avoid}body{background:white}.hero{color:#241913;background:white;border:1px solid #ddd}.hero .lead,.hero .kicker{color:#241913}.btn{display:none}}
'''

def page(title, body, active=''):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{STYLE}</style></head><body><nav class="nav"><span class="brand">Lady D Publishing Hub</span><a href="susan-damon-hub.html">Hub</a><a href="susan-damon-expanded-invoice.html">Invoice</a><a href="lady-d-project-dashboard.html">Dashboard</a><a href="index.html">Author Review</a><a href="lady-d-author-site.html">Lady D Site</a></nav>{body}</body></html>'''

book_cards = '\n'.join(f'''<article class="card book"><img src="{b['cover']}" alt="{b['title']} cover"><div><div class="kicker">{b['vol']} · devotional + journal</div><h3>{b['title']}</h3><p class="muted">{b['subtitle']}</p><p><span class="badge ok">366 entries</span> <span class="badge blue">HTML now</span> <span class="badge warn">PDF proof lane</span></p><a class="btn gold" href="{b['html']}">Open HTML book</a><a class="btn" href="{b['pdf']}">PDF proof</a><a class="btn" href="{b['journal']}">Journal PDF</a></div></article>''' for b in books)

invoice_body = f'''
<main class="wrap">
<header class="hero"><div class="kicker">Island Development Crew · Expanded Publishing Package Invoice</div><h1>Susan “Lady D” Damon Publishing Package</h1><p class="lead">Updated invoice and payment agreement for the expanded devotional library: three devotional books, three companion journals, the 31-day visual devotional lane, and the Juan R. Damon testimony book.</p><p><span class="badge">Prepared {DATE}</span> <span class="badge ok">Payment link verified: $2,300</span></p></header>
<section class="grid"><article class="card third stat"><strong>$2,500</strong><span>Total expanded package value</span></article><article class="card third stat"><strong>$200</strong><span>Prior payment credit received</span></article><article class="card third stat"><strong>$2,300</strong><span>Remaining balance due</span></article></section>
<section class="grid"><article class="card full"><h2>Payment</h2><p class="lead">The remaining balance is due through the secure Stripe checkout below.</p><p class="print-hide"><a class="btn gold" href="{PAYMENT_LINK}">Pay $2,300 remaining balance</a><a class="btn" href="susan-damon-expanded-invoice.pdf">Download PDF invoice</a><a class="btn" href="susan-damon-hub.html">Back to hub</a></p><p><strong>Payment link:</strong> <a href="{PAYMENT_LINK}">{PAYMENT_LINK}</a></p></article></section>
<section class="grid"><article class="card full"><h2>Expanded Scope of Work</h2><table class="table"><tr><th>Lane</th><th>Included work</th></tr><tr><td><strong>Devotional Book Collection</strong></td><td>Three 365-day devotional books: <em>Surrendering to God’s Love</em>, <em>Walking with Jesus</em>, and <em>Filled with the Holy Spirit</em>; author-review HTML editions; production formatting path; proofing and publishing preparation.</td></tr><tr><td><strong>Companion Journals</strong></td><td>Three paired companion journals aligned with the devotional collection, prepared for reflective use and print/digital formatting.</td></tr><tr><td><strong>31-Day Visual Devotional</strong></td><td>Visual devotional/product lane derived from the original 31-day devotional source and related publishing system, included as part of the expanded arrangement.</td></tr><tr><td><strong>Juan R. Damon Testimony Book</strong></td><td>Testimony/memorial book lane remains included in the payment arrangement at this cost, with structure, development, formatting, and publishing-prep support to be handled in the same controlled review/proof workflow.</td></tr><tr><td><strong>Publishing + Distribution Prep</strong></td><td>KDP paperback preparation, Kindle/digital prep, PDF/digital distribution packaging, cover/interior formatting, metadata support, proofing workflow, and author review portal/dashboard.</td></tr><tr><td><strong>Rights + Voice Preservation</strong></td><td>Preservation of Susan Damon’s devotional voice; scripture/reference/provenance review; author-facing review gates; final approval workflow before public publishing.</td></tr></table></article></section>
<section class="grid"><article class="card"><h2>Terms</h2><ul><li>Prior $200 payment is credited against the expanded $2,500 package.</li><li>Remaining $2,300 balance covers the expanded scope listed above.</li><li>Final publication remains subject to author approval, proof review, KDP/format validation, ISBN/barcode decisions where applicable, and any rights/scripture permissions required.</li><li>Additional marketing campaigns, live event coordination, paid advertising, full audiobook narration/production, and future products beyond this listed package remain outside scope unless approved separately in writing.</li></ul></article><article class="card"><h2>Status</h2><ul><li>Author review portal exists and displays the three devotional books in HTML format.</li><li>PDF proof links are staged where current draft PDFs exist and can be upgraded as final proof PDFs are generated.</li><li>Live project dashboard and Lady D website shell are now attached through the hub.</li><li>Testimony book is explicitly included in this expanded invoice.</li></ul></article></section>
<footer>Island Development Crew LLC / Island Dev Crew Consulting · Prepared for Susan “Lady D” Damon · {DATE}</footer>
</main>
'''

hub_body = f'''
<main class="wrap"><header class="hero"><div class="kicker">Lady D · IDC Publishing Command Hub</div><h1>Susan Damon Publishing Hub</h1><p class="lead">One clean place for Mrs. Susan Damon to access the invoice, payment link, author-review portal, live project dashboard, devotional books, companion journals, and future Lady D product website.</p><p><a class="btn gold" href="susan-damon-expanded-invoice.html">View invoice</a><a class="btn" href="susan-damon-expanded-invoice.pdf">Download invoice PDF</a><a class="btn dark" href="{PAYMENT_LINK}">Pay $2,300 balance</a></p></header>
<section class="grid"><article class="card"><h2>📄 Expanded Invoice</h2><p>The updated agreement/invoice reflects the full $2,500 expanded package, $200 paid credit, and $2,300 remaining balance.</p><a class="btn gold" href="susan-damon-expanded-invoice.html">View invoice</a><a class="btn" href="susan-damon-expanded-invoice.pdf">PDF invoice</a><a class="btn" href="{PAYMENT_LINK}">Stripe checkout</a></article><article class="card"><h2>📊 Live Project Dashboard</h2><p>Current status, product lanes, completion gates, review priorities, and next actions for the publishing package.</p><a class="btn gold" href="lady-d-project-dashboard.html">Open dashboard</a><a class="btn" href="release-status.html">Release status</a><a class="btn" href="production.html">Production archive</a></article></section>
<section class="grid"><article class="card full"><h2>📚 Devotional Library</h2><p class="lead">The author-review portal now functions as the book access layer. HTML review editions are available now; PDF proof links are staged for final proof upgrades.</p><div class="grid">{book_cards}</div></article></section>
<section class="grid"><article class="card"><h2>🕊️ Testimony Book Lane</h2><p>The Juan R. Damon testimony book is included in the payment arrangement at this cost. It should be treated as its own controlled product lane: source intake, structure, author/family review, proofing, and publishing prep.</p><a class="btn" href="lady-d-project-dashboard.html#testimony">View testimony lane</a></article><article class="card"><h2>🌿 Lady D Website</h2><p>A warm public-facing website shell is attached for Lady D’s ministry/products. This can later host purchase links, Gumroad/KDP links, testimonials, devotional samples, and product collection pages.</p><a class="btn gold" href="lady-d-author-site.html">Open Lady D site</a></article></section>
<section class="grid"><article class="card full callout"><h2>What this hub solves</h2><p>Instead of scattering links across texts, PDFs, Stripe, and Vercel pages, this hub becomes the client-facing command center: invoice + payment, review books, proof dashboard, and future product website under one roof.</p></article></section></main>
'''

dashboard_body = f'''
<main class="wrap"><header class="hero"><div class="kicker">Live Publishing Dashboard · Lady D</div><h1>Project Dashboard</h1><p class="lead">Current operating view for completing the expanded publishing package without losing scope, author voice, or proof discipline.</p><p><span class="badge ok">Portal live</span> <span class="badge warn">Final KDP proof pending</span> <span class="badge blue">Payment lane ready</span></p></header>
<section class="grid"><article class="card mini stat"><strong>3</strong><span>Devotional books</span></article><article class="card mini stat"><strong>3</strong><span>Companion journals</span></article><article class="card mini stat"><strong>1</strong><span>31-day visual devotional lane</span></article><article class="card mini stat"><strong>1</strong><span>Testimony book lane</span></article></section>
<section class="grid"><article class="card full"><h2>Completion Gates</h2><div class="stage"><div><strong>1 · Source Lock</strong><span class="muted">Declare canonical sources for each product.</span></div><div><strong>2 · Proof Pass</strong><span class="muted">Editorial, theological, and author-voice review.</span></div><div><strong>3 · KDP Files</strong><span class="muted">Interior PDFs + full cover wraps.</span></div><div><strong>4 · Author Approval</strong><span class="muted">Susan Damon reviews and approves.</span></div><div><strong>5 · Physical Proofs</strong><span class="muted">Order and inspect print proofs.</span></div><div><strong>6 · Publish</strong><span class="muted">Release after proof evidence.</span></div></div></article></section>
<section class="grid"><article class="card"><h2>Ready / Available Now</h2><ul><li>Three HTML devotional review editions.</li><li>Companion journal draft links.</li><li>Cover-review visual direction for the three devotional volumes.</li><li>Expanded invoice page and downloadable PDF.</li><li>Stripe checkout showing $2,300 remaining balance.</li></ul></article><article class="card"><h2>Needs Finalization</h2><ul><li>Canonical source registry and final source freeze.</li><li>Final copyedit/theological proof and author approval.</li><li>KDP Previewer checks and physical proof order.</li><li>Final full-wrap cover PDFs after page count/trim/ISBN decisions.</li><li>Juan R. Damon testimony book source intake and product plan.</li></ul></article></section>
<section id="testimony" class="grid"><article class="card full"><h2>Juan R. Damon Testimony Book Lane</h2><table class="table"><tr><th>Step</th><th>Status / action</th></tr><tr><td>Scope</td><td>Included in the expanded payment arrangement at the current $2,500 package cost.</td></tr><tr><td>Source Intake</td><td>Collect testimony source material, family details, photos, recordings, written notes, and any sensitive content boundaries.</td></tr><tr><td>Structure</td><td>Build a reverent testimony/memorial book outline with chapters, photo/story placement, scripture framing, and review checkpoints.</td></tr><tr><td>Production</td><td>Move through the same proof discipline: source lock, draft, family/author review, interior formatting, cover, KDP/digital prep.</td></tr></table></article></section>
<section class="grid"><article class="card full"><h2>Priority Next Actions</h2><ol><li>Use the hub link as the central Mrs. Damon access point.</li><li>Confirm payment through the $2,300 Stripe link.</li><li>Lock final scope and product registry.</li><li>Generate final proof PDFs for the three books and three journals.</li><li>Start testimony book source intake after the core portal/invoice is approved.</li></ol></article></section></main>
'''

author_site_body = f'''
<main class="wrap"><header class="hero"><div class="kicker">Lady D Devotional Library · Public Website Shell</div><h1>Devotionals for a Life Walking With Jesus</h1><p class="lead">A warm, author-facing product website for Susan “Lady D” Damon’s devotional ministry — ready to grow into a public storefront for books, journals, visual devotionals, testimony work, speaking, and ministry resources.</p><p><a class="btn gold" href="index.html">Preview books</a><a class="btn" href="susan-damon-hub.html">Publishing hub</a></p></header>
<section class="grid"><article class="card full"><h2>Featured Devotional Collection</h2><div class="grid">{book_cards}</div></article></section>
<section class="grid"><article class="card"><h2>About Lady D</h2><p>Susan “Lady D” Damon writes with warmth, faith, direct encouragement, and a heart for helping readers walk with Jesus in daily life. This page is staged as the future public home for her devotional library and ministry products.</p></article><article class="card"><h2>Coming Product Lanes</h2><ul><li>Devotional book collection</li><li>Companion journals</li><li>31-day visual devotional</li><li>Juan R. Damon testimony book</li><li>Reader resources, samples, and future product checkout links</li></ul></article></section>
<section class="grid"><article class="card full callout"><h2>Website Direction</h2><p>This is intentionally a shell, not a fake finished storefront. Once final product PDFs/KDP/Gumroad links are approved, this can become the public Lady D product site attached directly to the author review package.</p></article></section></main>
'''

files = {
    'susan-damon-expanded-invoice.html': page('Susan Damon Expanded Publishing Invoice', invoice_body),
    'susan-damon-hub.html': page('Susan Damon Publishing Hub', hub_body),
    'lady-d-project-dashboard.html': page('Lady D Project Dashboard', dashboard_body),
    'lady-d-author-site.html': page('Lady D Devotional Library Website', author_site_body),
}

for name, html in files.items():
    (ROOT / name).write_text(html, encoding='utf-8')
    (PUBLIC / name).write_text(html, encoding='utf-8')

# Patch existing index to expose hub/business lane without replacing the existing review portal.
for idx in [ROOT / 'index.html', PUBLIC / 'index.html']:
    html = idx.read_text(encoding='utf-8')
    if 'susan-damon-hub.html' not in html.split('</nav>')[0]:
        html = html.replace('<a href="release-status.html">Release dashboard</a><a href="production.html">Production archive</a>', '<a href="susan-damon-hub.html">Publishing hub</a><a href="susan-damon-expanded-invoice.html">Invoice</a><a href="lady-d-project-dashboard.html">Live dashboard</a><a href="lady-d-author-site.html">Lady D site</a><a href="release-status.html">Release dashboard</a><a href="production.html">Production archive</a>')
    marker = '<section class="card"><h2>What has been done</h2>'
    if 'business-hub-lane' not in html and marker in html:
        insert = f'''<section id="business-hub-lane" class="card notice"><h2>Publishing Hub, Invoice, and Payment Lane</h2><p>The expanded package now has a central access hub with the updated $2,500 scope, $200 paid credit, $2,300 remaining balance, live Stripe checkout, project dashboard, and future Lady D product website.</p><p><a class="btn gold" href="susan-damon-hub.html">Open Susan Damon Hub</a><a class="btn" href="susan-damon-expanded-invoice.html">View updated invoice</a><a class="btn" href="susan-damon-expanded-invoice.pdf">Invoice PDF</a><a class="btn" href="lady-d-project-dashboard.html">Live dashboard</a><a class="btn" href="lady-d-author-site.html">Lady D website</a></p></section>'''
        html = html.replace(marker, insert + marker)
    idx.write_text(html, encoding='utf-8')

# Generate invoice PDF and copy to public.
chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
invoice_url = 'file://' + str(ROOT / 'susan-damon-expanded-invoice.html')
pdf = ROOT / 'susan-damon-expanded-invoice.pdf'
if Path(chrome).exists():
    subprocess.run([chrome, '--headless', '--disable-gpu', f'--print-to-pdf={pdf}', invoice_url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy2(pdf, PUBLIC / pdf.name)

# Build delivery zip with supported file types only.
zip_path = ROOT / 'Lady-D-Hub-Invoice-Dashboard-Package-2026-07-06.zip'
if zip_path.exists():
    zip_path.unlink()
subprocess.run(['zip','-j','-q',str(zip_path),
    str(ROOT/'susan-damon-expanded-invoice.pdf'),
    str(ROOT/'lady-d-state-of-the-union-2026-07-06.pdf'),
    str(ROOT/'lady-d-plan-of-attack-2026-07-06.pdf')], check=True)

manifest = {
    'generated': DATE,
    'payment_link': PAYMENT_LINK,
    'pages': list(files.keys()),
    'invoice_pdf': 'susan-damon-expanded-invoice.pdf',
    'zip': zip_path.name,
    'scope': ['3 devotional books','3 companion journals','31-day visual devotional','Juan R. Damon testimony book','publishing prep','project dashboard','Lady D website shell']
}
(ROOT/'lady-d-hub-build-manifest-2026-07-06.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(PUBLIC/'lady-d-hub-build-manifest-2026-07-06.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
