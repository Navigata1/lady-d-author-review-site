"""Package the October author edition with a working portable directory tree."""
from __future__ import annotations
import hashlib
import json
import posixpath
import re
import shutil
import sys
import zipfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'public'
DOWNLOADS=PUBLIC/'downloads/lady-d-finalization'
QUALITY=ROOT/'quality/editorial-2026-10-20'
DATE='2026-10-20'
ORIGIN='https://lady-d-author-review-site.vercel.app/'
PAGES=['susan-damon-hub.html','lady-d-finalization-review.html','lady-d-cover-decision-deck.html','lady-d-31-day-visual-journal.html','lady-d-31-day-visual-journal-scene-console.html','susan-damon-publishing-proposal.html']


def digest(data):return hashlib.sha256(data).hexdigest()


class References(HTMLParser):
    def __init__(self):
        super().__init__();self.values=[]
    def handle_starttag(self, tag, attrs):
        self.values += [value for key,value in attrs if key in ['href','src'] and value]


def check_dependencies(payloads):
    for name,data in payloads.items():
        if not name.endswith(('.html','.css')):continue
        source=data.decode();references=References()
        if name.endswith('.html'):references.feed(source)
        values=references.values+[m[1] for m in re.finditer(r'''url\(['"]?([^)'"\s]+)''',source)]
        for value in values:
            parsed=urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path:continue
            target=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(parsed.path)))
            if target not in payloads:raise ValueError(f'Package dependency missing: {name} -> {value}')


def collect(master):
    paths=[PUBLIC/name for name in PAGES]
    paths+=sorted(DOWNLOADS.glob('volume-*-polished-*.html'))
    paths+=sorted((DOWNLOADS/'audiobook').glob('*'))
    paths+=[PUBLIC/'assets/idc-palm-logo.png',PUBLIC/'assets/lady-d-hub-polish.css',DOWNLOADS/'lady-d-cover-qualification.json']
    for directory in ['assets/fonts','assets/lady-d-reader','assets/lady-d-interiors','assets/lady-d-31-visual-journal-v2/scenes','covers/lady-d-finalization']:
        paths += [p for p in (PUBLIC/directory).rglob('*') if p.is_file()]
    if master:
        paths += [p for p in DOWNLOADS.glob('*.pdf') if p.name.startswith('Lady-D-Volume-') or p.name=='Lady-D-Thirty-One-Mornings-of-Light-Visual-Journal-6x9.pdf']
        paths += [PUBLIC/'susan-damon-publishing-proposal.pdf']
    payloads={}
    for source in sorted(set(paths)):
        name=str(source.relative_to(PUBLIC));data=source.read_bytes()
        if source.suffix=='.html':
            text=data.decode()
            text=text.replace('href="/"','href="'+ORIGIN+'"')
            text=text.replace('href="lady-d-31-day-motion.html"','href="'+ORIGIN+'lady-d-31-day-motion.html"')
            # Packages do not recursively contain the ZIPs linked from the live hub.
            text=re.sub(r'href="((?:downloads/lady-d-finalization/)?[^"<>]+\.zip)"',lambda m:'href="'+ORIGIN+('downloads/lady-d-finalization/' if '/' not in m[1] else '')+m[1]+'"',text)
            text=re.sub(r"url\((['\"]?)/(covers/[^)'\"]+)\1\)",lambda m:'url('+m[1]+posixpath.relpath(m[2],posixpath.dirname(name) or '.')+m[1]+')',text)
            if not master:
                text=re.sub(r'href="([^"<>]+\.pdf)"',lambda m:'href="'+ORIGIN+('downloads/lady-d-finalization/' if source.parent==DOWNLOADS else '')+m[1]+'"' if not m[1].startswith('http') else m[0],text)
            data=text.encode()
        payloads[name]=data
    if master:
        for path in sorted((ROOT/'source/finalization/polished').glob('*.json')):
            payloads['production/source/'+path.name]=path.read_bytes()
        for path in [QUALITY/name for name in ['editorial-audit.json','layout-audit.json','pdf-build.json','pdf-audit.json','independent-review.md','technical-review.md',*[f'volume-{v}-editorial.md' for v in range(1,4)]]]:
            payloads['production/evidence/'+path.name]=path.read_bytes()
        payloads['production/author-voice-contract.json']=(ROOT/'source/finalization/author-voice-contract.json').read_bytes()
        payloads['production/book-inventory.json']=(ROOT/'source/finalization/book-inventory.json').read_bytes()
        for name in ['EDITORIAL-BRIEF.md','DELIVERY-CHECKLIST.md','enrichment-revisions.json','monthly-prayers.json']:
            payloads['production/source/'+name]=(ROOT/'source/finalization/editorial-2026-10-20'/name).read_bytes()
    check_dependencies(payloads)
    return payloads


def build(master):
    name=(f'Lady-D-Trilogy-Author-Edition-Master-{DATE}.zip' if master else f'Lady-D-Trilogy-Web-Review-Package-{DATE}.zip')
    destination=ROOT/'output'/name
    payloads=collect(master)
    entries=[{'path':name,'bytes':len(data),'sha256':digest(data)} for name,data in sorted(payloads.items())]
    notes=('Lady D - October 20, 2026 author edition\n\n'
      'Start with susan-damon-hub.html. The books remain under downloads/lady-d-finalization/, matching the website directory structure. Artwork, fonts, and online-book controls are bundled.\n\n'
      +('This master includes the six revised 6x9 book PDFs and the concise 31-day illustrated PDF, plus their readers, covers, narration manifests, and editorial evidence.\n' if master else 'This smaller web review package includes the online books, gallery, covers, and narration manifests. PDF and ZIP links open the current website and require internet.\n')
      +'\nPayment links and the separate motion demonstration require internet. No audio has been generated. Author review and final printed proof remain the next publishing steps.\n\n'
      +'Author commentary follows the October vocabulary direction. Exact Bible quotations retain their wording. Historical audit material in production/ documents earlier wording.\n')
    manifest={'schema':'lady-d.editorial-package/v1','editionDate':DATE,'kind':'complete-master' if master else 'portable-web-review','entryCount':len(entries),'entries':entries}
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        archive.writestr('DELIVERY-NOTES.md',notes)
        archive.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        archive.writestr('SHA256SUMS.txt','\n'.join(f'{entry["sha256"]}  {entry["path"]}' for entry in entries)+'\n')
        for name,data in payloads.items():archive.writestr(name,data)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip():raise ValueError('ZIP CRC failure')
        for entry in entries:
            if digest(archive.read(entry['path']))!=entry['sha256']:raise ValueError(f'ZIP hash mismatch {entry["path"]}')
    if not master:
        if destination.stat().st_size>100*1024*1024:raise ValueError('Web review exceeds 100MiB; reduce duplicate assets before shipping')
        for directory in [DOWNLOADS,ROOT/'downloads/lady-d-finalization']:
            shutil.copy2(destination,directory/destination.name)
    return {'path':str(destination),'bytes':destination.stat().st_size,'sha256':digest(destination.read_bytes()),'entries':len(entries)}


def verify_archive(destination):
    payloads=collect(False)
    entries=[{'path':name,'bytes':len(data),'sha256':digest(data)} for name,data in sorted(payloads.items())]
    with zipfile.ZipFile(destination) as archive:
        names=archive.namelist()
        expected=set(payloads)|{'DELIVERY-NOTES.md','MANIFEST.json','SHA256SUMS.txt'}
        if len(names)!=len(expected) or set(names)!=expected:raise ValueError('ZIP has missing, duplicate, or unexpected members')
        if archive.testzip():raise ValueError('ZIP CRC failure')
        manifest=json.loads(archive.read('MANIFEST.json'))
        if manifest.get('entries')!=entries or manifest.get('entryCount')!=len(entries) or manifest.get('kind')!='portable-web-review' or manifest.get('editionDate')!=DATE:raise ValueError('ZIP manifest is stale or invalid')
        sums='\n'.join(f'{entry["sha256"]}  {entry["path"]}' for entry in entries)+'\n'
        if archive.read('SHA256SUMS.txt').decode()!=sums:raise ValueError('ZIP checksum list differs from current payload')
        for name,data in payloads.items():
            if archive.read(name)!=data:raise ValueError(f'Stale ZIP member: {name}')
    return {'status':'PASS','path':str(destination),'sha256':digest(destination.read_bytes()),'entries':len(entries),'payloadIdentity':'exact-current-transformed-public-tree'}


def main():
    (ROOT/'output').mkdir(exist_ok=True)
    for name in ['editorial-audit.json','layout-audit.json','pdf-build.json','pdf-audit.json']:
        if json.loads((QUALITY/name).read_text()).get('status')!='PASS':raise ValueError(f'Packaging requires a completed passing {name}')
    built=json.loads((QUALITY/'pdf-build.json').read_text())['results']
    audited=json.loads((QUALITY/'pdf-audit.json').read_text())['results']
    if {r['pdf']:r['sha256'] for r in built}!={r['pdf']:r['sha256'] for r in audited}:raise ValueError('PDF audit is stale for this build')
    report={'master':build(True),'web':build(False),'status':'PASS'}
    (QUALITY/'package-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['--verify-web-archive']:
        print(json.dumps(verify_archive(ROOT/'output'/f'Lady-D-Trilogy-Web-Review-Package-{DATE}.zip'),indent=2))
    else:main()
