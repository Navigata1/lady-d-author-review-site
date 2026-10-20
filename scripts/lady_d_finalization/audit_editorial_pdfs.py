"""Check every daily PDF page against the current author-edition source."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from audit_editorial import quote_blocks, plain
from build_interiors import first_prayer_line, voice_day_for_source_index

ROOT = Path(__file__).resolve().parents[2]
QUALITY = ROOT / 'quality/editorial-2026-10-20'


def text_key(value):
    value = unicodedata.normalize('NFKD', value)
    return ''.join(c.casefold() for c in value if c.isalnum())


def pdf_folio_matches(page, folio):
    lines=[line.strip() for line in page.splitlines() if line.strip()]
    return bool(lines) and re.sub(r'\s+','',lines[-1]) == re.sub(r'\s+','',plain(folio))


def pdf_reference_matches(page, expected):
    number=re.search(r'see devotional p\.\s*(\d+)',page,re.I)
    return bool(number) and int(number[1]) == expected


def validate_inventory(build):
    expected = json.loads((ROOT / 'source/finalization/book-inventory.json').read_text())
    pairs = {(v, journal) for v in range(1,4) for journal in [False,True]}
    assert len(expected) == 6 and {(r['volume'],r['journal']) for r in expected} == pairs
    assert build['status'] == 'PASS' and len(build['results']) == 6, 'Exactly six passed PDF outputs are required'
    assert {(r['volume'],r['journal']) for r in build['results']} == pairs, 'Missing, duplicate, or unexpected PDF outputs'
    for item in expected:
        actual = next(r for r in build['results'] if (r['volume'],r['journal']) == (item['volume'],item['journal']))
        assert all(actual[key] == item[key] for key in ['html','pdf','pages']), 'Unexpected PDF output identity'
        assert re.fullmatch(r'[a-f0-9]{64}',actual['sha256']) and actual['bytes']>0
    return build['results']


def main():
    errors = []; results = []
    build = json.loads((QUALITY / 'pdf-build.json').read_text())
    validate_inventory(build)
    for item in build['results']:
        volume = item['volume']; journal = item['journal']
        pdf = ROOT / 'output/pdf' / item['pdf']
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != item['sha256']: errors.append(f'{item["pdf"]}: differs from recorded PDF build')
        document = (ROOT / 'public/downloads/lady-d-finalization' / item['html']).read_text()
        leaves = re.findall(r'<section class="leaf[^\"]*"(?: id="([^\"]+)")?>', document)
        # Logical order keeps a right-aligned day badge out of a multiline title.
        pages = subprocess.check_output(['pdftotext', '-raw', str(pdf), '-'], text=True).split('\f')
        if not pages[-1].strip(): pages.pop()
        if len(pages) != item['pages'] or len(leaves) != len(pages):
            errors.append(f'{item["pdf"]}: page/leaf count differs')
            continue
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        if not re.search(r'Page size:\s+432 x 648 pts', info): errors.append(f'{item["pdf"]}: not 6x9')
        records = json.loads((ROOT / f'source/finalization/polished/vol{volume}-polished-366-days.json').read_text())
        by_day = {r['day']: r for r in records}
        by_id = {identifier: text_key(text) for identifier, text in zip(leaves, pages) if identifier}
        sections = dict(re.findall(r'<section class="leaf[^\"]*" id="([^\"]+)">(.*?)</section>',document,re.S))
        if journal:
            devotional = (ROOT / 'public/downloads/lady-d-finalization' / item['html'].replace('companion-journal','devotional')).read_text()
            anchor_pages = {identifier: index+1 for index,identifier in enumerate(re.findall(r'<section class="leaf[^\"]*"(?: id="([^\"]+)")?>',devotional)) if identifier}
        checks = 0
        quotes = quote_blocks(document) if not journal else []
        for index in range(1, 367):
            record = by_day[voice_day_for_source_index(index)]
            if journal:
                fields = [record['title'], record['journal_reflect'], record['journal_act'], first_prayer_line(record['prayer'])]
                target = by_id[f'j{index}']
                reference = re.search(r'<p class="jref">(.*?)</p>',sections[f'j{index}'],re.S)
                number = re.search(r'see devotional p\.\s*(\d+)',plain(reference[1]),re.I)
                if not number or int(number[1]) != anchor_pages[f'dA{index}']: errors.append(f'Volume {volume} day {record["day"]}: journal reference is misaligned')
                if not pdf_reference_matches(pages[leaves.index(f'j{index}')],anchor_pages[f'dA{index}']): errors.append(f'Volume {volume} day {record["day"]}: printed PDF journal reference is stale')
            else:
                fields = [*record['body'], record['closing'], record['prayer']]
                target = by_id[f'dB{index}']
                for identifier in [f'dA{index}',f'dB{index}']:
                    folio=re.search(r'<div class="folio">(.*?)</div>',sections[identifier],re.S)
                    number=re.search(r'(\d+)$',plain(folio[1]))
                    if not number or int(number[1]) != leaves.index(identifier)+1: errors.append(f'Volume {volume} {identifier}: printed folio is misaligned')
                    if not pdf_folio_matches(pages[leaves.index(identifier)],folio[1]): errors.append(f'Volume {volume} {identifier}: printed PDF folio is stale')
                for value in [record['title'], *quotes[(index-1)*2:index*2]]:
                    checks += 1
                    if text_key(value) not in by_id[f'dA{index}']: errors.append(f'Volume {volume} day {record["day"]}: anchor/title PDF mismatch')
            for value in fields:
                checks += 1
                if text_key(value) not in target: errors.append(f'Volume {volume} day {record["day"]} {"journal" if journal else "devotional"}: missing current text: {value[:70]}')
        remaining = len(re.findall(r'\bbeloved\b', '\n'.join(pages), re.I))
        expected = 0 if journal else sum(len(re.findall(r'\bbeloved\b', q, re.I)) for q in quotes)
        if remaining != expected: errors.append(f'{item["pdf"]}: unexpected rejected-word count {remaining}, expected Scripture-only {expected}')
        if journal:
            prayers = json.loads((ROOT / 'source/finalization/editorial-2026-10-20/monthly-prayers.json').read_text())[str(volume)]
            whole = text_key('\n'.join(pages))
            for prayer in prayers:
                if text_key(prayer) not in whole: errors.append(f'Volume {volume}: month-end prayer missing')
        for prefix in ['public/downloads/lady-d-finalization', 'downloads/lady-d-finalization']:
            if (ROOT / prefix / item['pdf']).read_bytes() != pdf.read_bytes(): errors.append(f'{prefix}/{item["pdf"]}: PDF mirror differs')
        results.append({'pdf': item['pdf'], 'pages': len(pages), 'dailyTextChecks': checks, 'printedFolioChecks':0 if journal else 732,'printedJournalReferenceChecks':366 if journal else 0, 'ScriptureOnlyWordOccurrences': remaining, 'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()})
    report = {'status': 'FAIL' if errors else 'PASS', 'scope': 'All daily authored text and Scripture presence on their expected PDF pages; punctuation fidelity is checked separately against the HTML source.', 'results': results, 'errors': errors}
    (QUALITY / 'pdf-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if errors: raise SystemExit(1)


if __name__ == '__main__':
    (QUALITY / 'pdf-audit.json').write_text('{"status":"RUNNING"}\n')
    try: main()
    except Exception as error:
        (QUALITY / 'pdf-audit.json').write_text(json.dumps({'status':'FAIL','errors':[str(error)]},indent=2)+'\n')
        raise
