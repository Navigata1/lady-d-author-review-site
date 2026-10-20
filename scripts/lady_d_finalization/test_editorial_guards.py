"""Regression checks for the independent reviewers' concrete gate findings."""
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import audit_editorial_pdfs as pdf
import package_editorial as package
from audit_editorial import quotations_equal
from build_interiors import clean_document_dashes, shift_devotional_page_references


class EditorialGuards(unittest.TestCase):
    def setUp(self):
        expected=json.loads((pdf.ROOT/'source/finalization/book-inventory.json').read_text())
        self.good={'status':'PASS','results':[{**item,'sha256':'a'*64,'bytes':1} for item in expected]}

    def test_exact_six_inventory(self):
        self.assertEqual(len(pdf.validate_inventory(self.good)),6)

    def test_missing_duplicate_and_failed_builds_fail(self):
        for results in [[],self.good['results'][:1],self.good['results'][:5]+[self.good['results'][0]]]:
            with self.subTest(results=len(results)),self.assertRaises(AssertionError):
                pdf.validate_inventory({'status':'PASS','results':results})
        bad=copy.deepcopy(self.good);bad['status']='FAIL'
        with self.assertRaises(AssertionError):pdf.validate_inventory(bad)
        for key,value in [('pdf','wrong.pdf'),('pages',1)]:
            bad=copy.deepcopy(self.good);bad['results'][0][key]=value
            with self.assertRaises(AssertionError):pdf.validate_inventory(bad)

    def test_scripture_punctuation_and_boundaries_are_protected(self):
        for left,right in [('God is now here','God is nowhere'),('their sin\u2014;','their sin - ;'),('God','god')]:
            self.assertFalse(quotations_equal([left],[right]))
        markup='<p>author\u2014text</p><p class="txt long">their sin\u2014;</p>'
        self.assertEqual(clean_document_dashes(markup),'<p>author - text</p><p class="txt long">their sin\u2014;</p>')

    def test_added_front_matter_moves_printed_folios_and_reference_table(self):
        markup='<td class="pg">7</td><div class="folio"><b>1</b> &nbsp;·&nbsp; 7</div>'
        expected='<td class="pg">9</td><div class="folio"><b>1</b> &nbsp;·&nbsp; 9</div>'
        self.assertEqual(shift_devotional_page_references(markup,2),expected)

    def test_stale_pdf_numbers_fail_even_when_body_contains_new_number(self):
        self.assertTrue(pdf.pdf_folio_matches('Reading\n1 · 9\n','<b>1</b> &nbsp;·&nbsp; 9'))
        self.assertFalse(pdf.pdf_folio_matches('Reading includes 1 · 9\n1 · 7\n','<b>1</b> &nbsp;·&nbsp; 9'))
        self.assertTrue(pdf.pdf_reference_matches('GENESIS 15:2 · SEE DEVOTIONAL P. 9',9))
        self.assertFalse(pdf.pdf_reference_matches('GENESIS 15:2 · SEE DEVOTIONAL P. 7',9))

    def archive(self,path,payloads,override=None):
        entries=[{'path':name,'bytes':len(data),'sha256':package.digest(data)} for name,data in sorted(payloads.items())]
        manifest={'entries':entries,'entryCount':len(entries),'kind':'portable-web-review','editionDate':package.DATE}
        with zipfile.ZipFile(path,'w') as archive:
            archive.writestr('DELIVERY-NOTES.md','fixture')
            archive.writestr('MANIFEST.json',json.dumps(manifest))
            archive.writestr('SHA256SUMS.txt','\n'.join(f'{e["sha256"]}  {e["path"]}' for e in entries)+'\n')
            for name,data in payloads.items():archive.writestr(name,(override or {}).get(name,data))

    def test_archive_binds_current_transformed_bytes(self):
        payload={'index.html':b'current'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.zip'
            self.archive(path,payload)
            with patch.object(package,'collect',return_value=payload):
                self.assertEqual(package.verify_archive(path)['status'],'PASS')
            with patch.object(package,'collect',return_value={'index.html':b'new edition'}),self.assertRaises(ValueError):
                package.verify_archive(path)
            self.archive(path,payload,{'index.html':b'stale'})
            with patch.object(package,'collect',return_value=payload),self.assertRaises(ValueError):
                package.verify_archive(path)


if __name__=='__main__':unittest.main()
