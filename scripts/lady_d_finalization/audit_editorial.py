"""Verify author vocabulary, manuscript structure, and unchanged Scripture blocks."""
from __future__ import annotations
import hashlib
import html
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'source/finalization/editorial-2026-10-20/baseline'
REPORT = ROOT / 'quality/editorial-2026-10-20'
SCORER = Path('/Users/IDC2.5/.agents/skills/ai-humanizer/scripts/score.js')
SLUGS = ['surrendering-to-gods-love','walking-with-jesus','filled-with-the-holy-spirit']


def quotations_equal(before, after):
    return before == after


def prose(records):
    return '\n\n'.join('\n'.join([r['title'],*r['body'],r['closing'],r['prayer'],r['journal_reflect'],r['journal_act']]) for r in records)


def plain(value):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',value))).strip()


def quote_blocks(document):
    quotes=[]
    for section in re.findall(r'<section class="leaf [^"]*" id="dA\d+">(.*?)</section>',document,re.S):
        for block in re.findall(r'<(?:blockquote class="anchor"|div class="thread")>(.*?)</(?:blockquote|div)>',section,re.S):
            match=re.search(r'<p class="txt[^"]*">(.*?)</p>',block,re.S)
            if match:quotes.append(plain(match[1]))
    return quotes


def main():
    errors=[];volumes=[]
    for before, after in [('God is now here', 'God is nowhere'), ('their sin\u2014;', 'their sin - ;'), ('God', 'god')]:
        if quotations_equal([before], [after]):
            raise AssertionError('Scripture gate accepted altered quotation text')
    REPORT.mkdir(parents=True,exist_ok=True)
    for volume,slug in enumerate(SLUGS,1):
        filename=f'vol{volume}-polished-366-days.json'
        before=json.loads((BASELINE/filename).read_text())
        after=json.loads((ROOT/'source/finalization/polished'/filename).read_text())
        if {r['day'] for r in after} != set(range(366)) or len(after)!=366:errors.append(f'Volume {volume}: day keys/count changed')
        before_by_day={r['day']:r for r in before}
        for record in after:
            if set(record)!=set(before_by_day[record['day']]):errors.append(f'Volume {volume} day {record["day"]}: field set changed')
            if len(record['body'])!=4 or not all(record['body']):errors.append(f'Volume {volume} day {record["day"]}: four paragraphs required')
            for key in ['title','closing','prayer','journal_reflect','journal_act']:
                if not record.get(key):errors.append(f'Volume {volume} day {record["day"]}: empty {key}')
            if not record['prayer'].endswith('Amen.'):errors.append(f'Volume {volume} day {record["day"]}: prayer ending changed')
        raw=prose(after)
        count=len(re.findall(r'\bbeloved\b',raw,re.I))
        if count:errors.append(f'Volume {volume}: {count} rejected terms remain in author prose')
        hashes={}
        for label,records in [('before',before),('after',after)]:
            path=REPORT/f'volume-{volume}-{label}.txt';path.write_text(prose(records)+'\n')
            hashes[label]=hashlib.sha256(path.read_bytes()).hexdigest()
        scores={label:json.loads(subprocess.run(['node',str(SCORER),'--json',str(REPORT/f'volume-{volume}-{label}.txt')],capture_output=True,text=True,check=True).stdout) for label in ['before','after']}
        title_changes=[{'day':r['day'],'before':before_by_day[r['day']]['title'],'after':r['title']} for r in after if before_by_day[r['day']]['title']!=r['title']]
        document=(ROOT/f'public/downloads/lady-d-finalization/volume-{volume}-{slug}-polished-devotional.html').read_text()
        template=(ROOT/f'source/finalization/templates/vol{volume}-devotional-source.html').read_text()
        old_quotes=quote_blocks(template);new_quotes=quote_blocks(document)
        if len(new_quotes)!=732 or not quotations_equal(old_quotes,new_quotes):errors.append(f'Volume {volume}: protected Scripture blocks changed or disappeared')
        authored_markup=re.sub(r'<p class="txt[^"]*">.*?</p>','',document,flags=re.S)
        authored_remaining=len(re.findall(r'\bbeloved\b',plain(authored_markup),re.I))
        if authored_remaining:errors.append(f'Volume {volume}: {authored_remaining} rejected terms remain outside Scripture in HTML')
        journal=(ROOT/f'public/downloads/lady-d-finalization/volume-{volume}-{slug}-polished-companion-journal.html').read_text()
        journal_remaining=len(re.findall(r'\bbeloved\b',plain(journal),re.I))
        if journal_remaining:errors.append(f'Volume {volume} journal: {journal_remaining} rejected terms remain')
        for prefix in ['public/', '']:
            manifest=json.loads((ROOT/f'{prefix}downloads/lady-d-finalization/audiobook/lady-d-volume-{volume}-audiobook-manifest.json').read_text())
            if len(manifest['tracks'])!=366:errors.append(f'Volume {volume}: narration track count differs')
            current={record['day']:record for record in after}
            for track in manifest['tracks']:
                record=current[track['day']]
                pairs=[(track['title'],record['title']),(track['body'],record['body']),(track['prayer'],record['prayer']),(track['carry_line'],record['closing'])]
                if any(left!=right for left,right in pairs):errors.append(f'Volume {volume} day {track["day"]}: {prefix}narration source is stale')
        def starters(records):return Counter(' '.join(p.split()[:2]) for r in records for p in r['body'])
        volumes.append({'volume':volume,'entries':len(after),'changedDays':[r['day'] for r in after if r!=before_by_day[r['day']]],'baselineRejectedTerms':len(re.findall(r'\bbeloved\b',prose(before),re.I)),'remainingRejectedTerms':count,'titleChanges':title_changes,'protectedScriptureBlocks':len(new_quotes),'ScriptureOccurrencesRetained':sum(len(re.findall(r'\bbeloved\b',q,re.I)) for q in new_quotes),'hashes':hashes,'paragraphStartersBefore':starters(before).most_common(8),'paragraphStartersAfter':starters(after).most_common(8),'humanizer':{'authority':'advisory','before':scores['before']['score'],'after':scores['after']['score'],'delta':scores['after']['score']-scores['before']['score']}})
    report={'status':'FAIL' if errors else 'PASS','authorDirectionDate':'2026-10-20','scope':'Authored prose and current six book interiors; exact Scripture retained. Historical sources are preserved.','volumes':volumes,'errors':errors}
    (REPORT/'editorial-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'volumes':[{k:r[k] for k in ['volume','entries','baselineRejectedTerms','remainingRejectedTerms','protectedScriptureBlocks','ScriptureOccurrencesRetained','titleChanges','humanizer']} for r in volumes],'errors':errors},indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
