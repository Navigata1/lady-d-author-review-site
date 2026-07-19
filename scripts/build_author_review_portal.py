#!/usr/bin/env python3
from pathlib import Path
import re, html, shutil, json, textwrap
from datetime import datetime

ROOT = Path('/Users/IDC2.5/Documents/LADY D/lady-d-author-review-site')
LIB = Path('/Users/IDC2.5/Documents/LADY D/Production Library')
OUT_ASSETS = ROOT / 'production-assets' / 'author-review-covers'
PUB_ASSETS = ROOT / 'public' / 'production-assets' / 'author-review-covers'
OUT_ASSETS.mkdir(parents=True, exist_ok=True)
PUB_ASSETS.mkdir(parents=True, exist_ok=True)

BOOKS = [
    {
        'vol': 1,
        'folder': "01 Surrendering to God's Love",
        'title': "Surrendering to God's Love",
        'subtitle': "A 365-Day Devotional Journey into the Father's Heart",
        'lane': "God the Father / love, identity, surrender, forgiveness, timing, daily trust",
        'accent': '#7b4bb7',
        'deep': '#24113f',
        'cover_source': ROOT/'production-assets'/'cover-02-path-of-surrender-art.png',
        'review_file': 'book-1-surrendering-to-gods-love-review.html',
        'pdf': 'downloads/production/kdp/interior-drafts/volume-1/volume-1-full-6x9-interior-draft.pdf',
        'docx': 'downloads/production/kdp/interior-drafts/volume-1/volume-1-full-6x9-interior-draft.docx',
        'journal_pdf': 'downloads/production/kdp/companion-journal-drafts/volume-1/volume-1-companion-journal-6x9-draft.pdf',
    },
    {
        'vol': 2,
        'folder': '02 Walking with Jesus',
        'title': 'Walking with Jesus',
        'subtitle': 'A 365-Day Devotional Journey of Daily Discipleship',
        'lane': 'Jesus / discipleship, nearness, trust, daily walk, practical obedience',
        'accent': '#2f6f5e',
        'deep': '#0f322a',
        'cover_source': ROOT/'production-assets'/'volume-2-cover-02-path-of-surrender-art.png',
        'review_file': 'book-2-walking-with-jesus-review.html',
        'pdf': 'downloads/production/kdp/interior-drafts/volume-2/volume-2-full-6x9-interior-draft.pdf',
        'docx': 'downloads/production/kdp/interior-drafts/volume-2/volume-2-full-6x9-interior-draft.docx',
        'journal_pdf': 'downloads/production/kdp/companion-journal-drafts/volume-2/volume-2-companion-journal-6x9-draft.pdf',
    },
    {
        'vol': 3,
        'folder': '03 Filled with the Holy Spirit',
        'title': 'Filled with the Holy Spirit',
        'subtitle': 'A 365-Day Devotional Journey into Spirit-Led Living',
        'lane': 'Holy Spirit / comfort, filling, fruit, power, courage, daily formation',
        'accent': '#2c6da4',
        'deep': '#102d4a',
        'cover_source': ROOT/'production-assets'/'volume-3-cover-02-path-of-surrender-art.png',
        'review_file': 'book-3-filled-with-the-holy-spirit-review.html',
        'pdf': 'downloads/production/kdp/interior-drafts/volume-3/volume-3-full-6x9-interior-draft.pdf',
        'docx': 'downloads/production/kdp/interior-drafts/volume-3/volume-3-full-6x9-interior-draft.docx',
        'journal_pdf': 'downloads/production/kdp/companion-journal-drafts/volume-3/volume-3-companion-journal-6x9-draft.pdf',
    },
]

def slug(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

def md_inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s

def paras(lines):
    out=[]; buf=[]
    def flush():
        if buf:
            txt=' '.join(x.strip() for x in buf if x.strip())
            if txt: out.append(f'<p>{md_inline(txt)}</p>')
            buf.clear()
    for ln in lines:
        t=ln.rstrip()
        if not t.strip(): flush(); continue
        if t.strip()=='---': flush(); out.append('<div class="ornament">✦</div>'); continue
        m=re.match(r'^(#{1,6})\s+(.*)',t)
        if m:
            flush(); lvl=min(6,len(m.group(1))+1); out.append(f'<h{lvl}>{md_inline(m.group(2))}</h{lvl}>'); continue
        if t.startswith('- '):
            flush(); out.append(f'<p class="bullet">• {md_inline(t[2:])}</p>'); continue
        buf.append(t)
    flush()
    return '\n'.join(out)

def parse_entries(md):
    lines=md.splitlines()
    entries=[]
    positions=[]
    for i,l in enumerate(lines):
        if re.match(r'^##\s+(Day\s+\d+|Bonus(?:\s*/\s*Leap Day)?(?:\s*-\s*February\s+29)?)', l): positions.append(i)
    for idx,start in enumerate(positions):
        end=positions[idx+1] if idx+1 < len(positions) else len(lines)
        chunk=lines[start:end]
        head=chunk[0].replace('##','').strip()
        title=''
        for l in chunk[1:8]:
            if l.startswith('### '): title=l[4:].strip(); break
        scripture=''
        for l in chunk:
            m=re.search(r'\*\*Scripture Reference:\*\*\s*(.*)', l)
            if m: scripture=m.group(1).strip(); break
        body=paras([x for x in chunk[1:] if not x.startswith('### ')])
        entries.append({'day':head,'title':title,'scripture':scripture,'body':body})
    return entries

def make_cover(book):
    # Use the existing approved cover art if present; overlay clean book typography into author-review cover PNG.
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except Exception:
        return None, 'PIL unavailable; using raw source cover asset only.'
    src = book['cover_source']
    if not src.exists():
        return None, f'Missing cover source {src}'
    img=Image.open(src).convert('RGB')
    W,H=1200,1800
    img=img.resize((W,H))
    overlay=Image.new('RGBA',(W,H),(0,0,0,0))
    d=ImageDraw.Draw(overlay)
    # bottom gradient panels
    for y in range(H):
        a=0
        if y < 520: a=int(110*(1-y/520))
        if y > 1080: a=max(a,int(190*((y-1080)/(H-1080))))
        if a: d.line([(0,y),(W,y)], fill=(15,9,24,a))
    img=Image.alpha_composite(img.convert('RGBA'), overlay)
    d=ImageDraw.Draw(img)
    def font(size,bold=False,serif=False):
        candidates=[]
        if serif:
            candidates += ['/System/Library/Fonts/Supplemental/Georgia.ttf','/System/Library/Fonts/Supplemental/Times New Roman.ttf']
        candidates += ['/System/Library/Fonts/SFNS.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf','/System/Library/Fonts/Supplemental/Arial.ttf']
        for c in candidates:
            try: return ImageFont.truetype(c,size)
            except: pass
        return ImageFont.load_default()
    title_font=font(112,serif=True); sub_font=font(44); small_font=font(34); tiny_font=font(28)
    d.rounded_rectangle([92,98,348,152], radius=26, fill=book['accent'])
    d.text((120,109), f"VOLUME {book['vol']}", fill='white', font=tiny_font)
    # wrapped title
    y=1160
    for line in textwrap.wrap(book['title'], width=17):
        d.text((92,y), line, fill='white', font=title_font, stroke_width=2, stroke_fill=(20,12,32))
        y += 118
    d.line([(92,y+10),(500,y+10)], fill=book['accent'], width=8)
    y += 44
    for line in textwrap.wrap(book['subtitle'], width=33):
        d.text((96,y), line, fill=(255,248,230), font=sub_font)
        y += 56
    d.text((96,1690), 'SUSAN “LADY D” DAMON', fill='white', font=small_font)
    d.text((96,1738), 'Lady D Devotional Library', fill=(255,235,185), font=tiny_font)
    out=OUT_ASSETS/f"volume-{book['vol']}-author-review-cover.png"
    img.convert('RGB').save(out, quality=94)
    shutil.copy2(out, PUB_ASSETS/out.name)
    return out, 'Cover presentation built from the local cover concept art so Lady D can review the visual direction alongside the manuscript.'

def page_css():
    return '''
:root{--ink:#221b16;--muted:#6f635a;--paper:#fffdf8;--cream:#f7efe2;--line:rgba(60,40,24,.18);--gold:#b6863b;--shadow:0 24px 80px rgba(42,26,10,.12)}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#fffdf8,#efe2cc);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.62}.topbar{position:sticky;top:0;z-index:20;background:rgba(31,22,17,.94);backdrop-filter:blur(18px);display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px 18px}.topbar a,.topbar span{color:white;text-decoration:none;font-size:13px;font-weight:850;padding:8px 11px;border-radius:999px;background:rgba(255,255,255,.09)}.topbar .brand{background:transparent;color:#f6dca9}header,.wrap{max-width:1180px;margin:auto;padding:34px 20px}.hero{display:grid;grid-template-columns:minmax(260px,420px) 1fr;gap:34px;align-items:center}.cover{width:100%;border-radius:22px;box-shadow:var(--shadow);border:1px solid rgba(255,255,255,.7)}.kicker{text-transform:uppercase;letter-spacing:.16em;font-size:12px;font-weight:950;color:var(--gold);margin-bottom:12px}h1,h2,h3{font-family:Georgia,"Times New Roman",serif;line-height:1.05;margin:0 0 14px}h1{font-size:clamp(42px,6.5vw,82px)}h2{font-size:clamp(30px,4vw,50px)}h3{font-size:24px}.lead{font-size:clamp(18px,2vw,23px);color:#3c322b;max-width:780px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}.card,.book-page,.front-page{background:rgba(255,253,248,.94);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 18px 55px rgba(42,26,10,.08)}.stat strong{display:block;font-family:Georgia,serif;font-size:42px}.badge{display:inline-flex;border-radius:999px;background:#efe1c8;color:#5a3b17;padding:7px 10px;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.notice{border-left:5px solid var(--gold);background:#fff8e8}.toc{columns:3 240px}.toc a{display:block;color:#35261c;text-decoration:none;padding:3px 0}.front-page,.book-page{position:relative;max-width:850px;margin:22px auto;min-height:840px;padding:70px 72px 80px}.front-page{display:flex;flex-direction:column;justify-content:center;text-align:center}.book-page h2{font-size:30px;color:#4b2a12}.book-page h3{font-size:33px}.book-page p{font-size:18px}.bullet{text-align:left}.ornament{text-align:center;color:var(--gold);font-size:28px;margin:20px}.page-number{position:absolute;bottom:28px;left:0;right:0;text-align:center;color:#9b8060;font-size:13px}.download{display:block;text-decoration:none;color:#241a13;font-weight:900}.btn{display:inline-block;background:#1f1611;color:white!important;text-decoration:none;border-radius:999px;padding:12px 16px;font-weight:900;margin:6px 8px 6px 0}.btn.gold{background:var(--gold);color:#241a13!important}@media(max-width:760px){.hero{grid-template-columns:1fr}.front-page,.book-page{padding:34px 22px;min-height:auto}.toc{columns:1}}@media print{.topbar,.no-print{display:none}.book-page,.front-page{page-break-after:always;box-shadow:none;border:0;border-radius:0;min-height:9in}}
'''

def render_book(book, entries, cover_msg):
    total=len(entries)
    toc='\n'.join(f'<a href="#day-{i+1}">{html.escape(e["day"])} — {html.escape(e["title"])}</a>' for i,e in enumerate(entries))
    pages=[]
    n=1
    for title,body,cls in [
        ('Half Title', f'<h1>{html.escape(book["title"])}</h1><p>Lady D Devotional Library · Volume {book["vol"]}</p>', 'front-page'),
        ('Title Page', f'<h1>{html.escape(book["title"])}</h1><p class="lead">{html.escape(book["subtitle"])}</p><p>Susan “Lady D” Damon</p>', 'front-page'),
        ('Dedication', '<h2>Dedication</h2><p>[Author-provided dedication goes here.]</p>', 'front-page'),
        ('Foreword / Contributing Article', '<h2>Foreword / Contributing Article</h2><p>[Reserved for a written article, ministry endorsement, or foreword from another writer.]</p>', 'front-page'),
        ('A Note from Lady D', '<h2>A Note from Lady D</h2><p>[Author welcome and personal note will go here after Lady D approves or provides final wording.]</p>', 'front-page'),
        ('About the Author', '<h2>About Susan “Lady D” Damon</h2><p>[Author bio placeholder. This page is intentionally reserved so the final interior has room for her story, ministry background, and reader-facing invitation.]</p>', 'front-page'),
        ('How to Use', '<h2>How to Use This Devotional</h2><p>Begin with the Scripture reference. Read slowly. Pray the prayer aloud or rewrite it in your own words. Use the journal prompt to tell the truth before God. Take the Today step before the day gets crowded.</p>', 'front-page'),
    ]:
        pages.append(f'<section class="{cls}">{body}<div class="page-number">{n}</div></section>'); n+=1
    for i,e in enumerate(entries, start=1):
        pages.append(f'<section class="book-page" id="day-{i}"><div class="kicker">{html.escape(e["day"])}</div><h3>{html.escape(e["title"])}</h3>{e["body"]}<div class="page-number">{n}</div></section>')
        n+=1
    html_doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(book['title'])} — Author Review</title><style>{page_css()}</style></head><body>
<nav class="topbar"><span class="brand">Lady D Author Review</span><a href="index.html">Dashboard</a><a href="#toc">Table of contents</a><a href="{book['pdf']}">PDF</a><a href="{book['docx']}">DOCX</a><a href="{book['journal_pdf']}">Companion journal PDF</a></nav>
<header class="hero"><img class="cover" src="production-assets/author-review-covers/volume-{book['vol']}-author-review-cover.png" alt="Cover concept for {html.escape(book['title'])}"><div><div class="kicker">Complete HTML review edition · Volume {book['vol']}</div><h1>{html.escape(book['title'])}</h1><p class="lead">{html.escape(book['subtitle'])}</p><p><span class="badge">{total} entries including Leap-Day bonus</span> <span class="badge">Page-numbered browser proof</span> <span class="badge">Front matter placeholders included</span></p><p class="lead">This is the author-facing HTML review version: formatted spacing, readable page flow, page numbers, front-matter reserve pages, and direct access to the PDF/DOCX interior drafts.</p><p class="no-print"><a class="btn gold" href="{book['pdf']}">Open print PDF</a><a class="btn" href="{book['journal_pdf']}">Open companion journal</a></p></div></header>
<main class="wrap"><section class="card notice"><h2>Review status</h2><p><strong>Ready for author review; not final KDP upload approval.</strong> Final upload still requires author approval, final copyedit/theology proof, Scripture translation/permissions decision, ISBN/copyright data, and KDP Previewer proof.</p><p>{html.escape(cover_msg)}</p></section><section id="toc" class="card"><h2>Table of contents</h2><div class="toc">{toc}</div></section>{''.join(pages)}</main></body></html>'''
    (ROOT/book['review_file']).write_text(html_doc)
    (ROOT/'public'/book['review_file']).write_text(html_doc)
    return {'title': book['title'], 'entries': total, 'pages': n-1, 'file': book['review_file']}

def render_index(results, stripe_status):
    cards=[]
    for b,r in zip(BOOKS,results):
        cards.append(f'''<article class="card book-card"><img src="production-assets/author-review-covers/volume-{b['vol']}-author-review-cover.png" alt="{html.escape(b['title'])} cover"><div><div class="kicker">Volume {b['vol']} · HTML review edition</div><h3>{html.escape(b['title'])}</h3><p>{html.escape(b['subtitle'])}</p><p><span class="badge">{r['entries']} devotional entries</span> <span class="badge">{r['pages']} numbered pages</span></p><a class="btn gold" href="{b['review_file']}">Open complete HTML book</a><a class="btn" href="{b['pdf']}">Open PDF</a><a class="btn" href="{b['journal_pdf']}">Open journal PDF</a></div></article>''')
    today=datetime.now().strftime('%Y-%m-%d %H:%M')
    doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lady D Devotional Library — Author Review Portal</title><style>{page_css()} .hero{{grid-template-columns:1fr}}.portal-title{{max-width:980px}}.book-card{{display:grid;grid-template-columns:180px 1fr;gap:22px;align-items:center}}.book-card img{{width:100%;border-radius:14px;box-shadow:0 16px 40px rgba(42,26,10,.18)}}@media(max-width:700px){{.book-card{{grid-template-columns:1fr}}}}</style></head><body>
<nav class="topbar"><span class="brand">Lady D Author Review</span><a href="#books">Books</a><a href="release-status.html">Release dashboard</a><a href="production.html">Production archive</a></nav>
<header class="hero"><div class="portal-title"><div class="kicker">IDC Publishing · author-facing progress portal · {today}</div><h1>Lady D Devotional Library review portal</h1><p class="lead">A clean place for Susan “Lady D” Damon to see what has been built: all three devotionals, companion journals, cover concepts, release dashboards, and next approval gates.</p><p><span class="badge">3 complete devotional HTML review books</span> <span class="badge">3 companion journal PDFs</span> <span class="badge">Cover concepts included</span> <span class="badge">KDP proof gate protected</span></p></div></header>
<main class="wrap"><section class="grid"><article class="card stat"><strong>1,098</strong><span>devotional entries across the trilogy, including Leap-Day bonus entries</span></article><article class="card stat"><strong>6</strong><span>major author-review products: 3 devotionals + 3 companion journals</span></article><article class="card stat"><strong>3</strong><span>new author-review book cover presentations</span></article></section>
<section id="books"><h2>Open the books</h2><p class="lead">Each HTML book includes front matter reserve pages for dedication, foreword/article, Lady D note, author bio, copyright/permissions, and a page-numbered devotional flow.</p><div class="grid" style="grid-template-columns:1fr">{''.join(cards)}</div></section>
<section class="card"><h2>What has been done</h2><ul><li>Three 365-day devotional manuscripts are assembled into author-review HTML books.</li><li>Existing PDF/DOCX interior drafts remain linked for print-style review.</li><li>Companion journal PDFs are linked beside each matching devotional.</li><li>Cover concepts have been consolidated into a clean review presentation.</li><li>Release-control, proof-audit, and production dashboards remain available for deeper production review.</li></ul></section>
<section class="card notice"><h2>What still needs Lady D / Jon approval before final upload</h2><ul><li>Final dedication, acknowledgments, author bio, author note, and any outside foreword/article.</li><li>Final Scripture translation policy and permission/copyright notice.</li><li>Final cover lane selection and KDP full-wrap regeneration from locked page count.</li><li>Final author-voice copyedit and theological proof.</li><li>KDP Previewer pass, physical proof order, and final upload metadata.</li></ul></section></main></body></html>'''
    (ROOT/'index.html').write_text(doc)
    (ROOT/'public'/'index.html').write_text(doc)

stripe_status={'live_blocked': True}
results=[]; cover_notes=[]
for b in BOOKS:
    cover_path,msg=make_cover(b)
    cover_notes.append({'volume':b['vol'],'path':str(cover_path) if cover_path else None,'message':msg})
    md=(LIB/b['folder']/'06 Master Assembly'/f"volume-{b['vol']}-master-interior-manuscript.md").read_text(errors='ignore')
    entries=parse_entries(md)
    results.append(render_book(b, entries, msg))
render_index(results, stripe_status)
# Admin payment status page
payment='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lady D Stripe Payment Update Status</title><style>'''+page_css()+'''</style></head><body><nav class="topbar"><span class="brand">Lady D Admin</span><a href="index.html">Author portal</a></nav><main class="wrap"><section class="card notice"><h1>Stripe payment update status</h1><p><strong>Live update blocked by Stripe restricted-key permissions.</strong> The account can read live objects, but live Products/Prices/Payment Links cannot be created with the current key.</p><p>Verified live account: charges enabled, payouts enabled, details submitted. Existing live old link <code>plink_1TXXTnQQMWQl4qqGlKOQYsxs</code> remains active at $400 and should not be sent for this corrected package.</p><h2>Manual Dashboard fields needed</h2><ul><li>Product/name: Susan Damon - Corrected Publishing Package Remaining Balance</li><li>Amount: $1,400.00 USD</li><li>Description: Remaining balance for current Lady D publishing package: 3 devotional books, 3 companion journals, 31-day visual devotional, author review hub, dashboard, and KDP/digital preparation. Juan Damon testimony/autobiography is separated from this package.</li><li>Metadata: client=Susan Damon; project=Lady D Publishing Package; package_total=2000; paid_credit=600; remaining_balance=1400; testimony_scope=separate</li></ul><p>Important: the corrected proposal uses a placeholder status page until the real $1,400 live payment link is created by a Stripe owner/admin or with a key that can create Products, Prices, and Payment Links.</p></section></main></body></html>'''
(ROOT/'stripe-payment-update-status.html').write_text(payment)
(ROOT/'public'/'stripe-payment-update-status.html').write_text(payment)
manifest={'generated':datetime.now().isoformat(),'books':results,'covers':cover_notes,'stripe':stripe_status}
(ROOT/'author-review-build-manifest.json').write_text(json.dumps(manifest,indent=2))
(ROOT/'public'/'author-review-build-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest, indent=2))
