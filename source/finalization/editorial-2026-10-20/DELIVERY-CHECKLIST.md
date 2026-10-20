# October Author Edition

## Source Order

1. The complete August 3 author-written example is calibration evidence. Preserve it verbatim.
2. `author-voice-contract.json` records the October vocabulary direction. Exact Bible quotations are exempt.
3. The dated `baseline/` files preserve the pre-edit manuscripts. Edit only the current `polished/` corpus.
4. `enrichment-revisions.json` records language-note prose changes; original Scripture, language forms, and references remain source evidence.
5. `monthly-prayers.json` contains the distinct journal month-end prayers.

## Build And Verify

Run commands individually from the repository root, with the Codex bundled Node dependencies on `NODE_PATH` for Playwright. Browser scripts use the installed Google Chrome executable. No external model, image-generation, or audio-synthesis service is needed to reproduce these derivatives.

```bash
python3 scripts/lady_d_finalization/build_interiors.py
python3 scripts/lady_d_finalization/build_audiobook_handoff.py
python3 scripts/lady_d_finalization/build_31_day_visual_devotional.py
python3 scripts/lady_d_finalization/audit_editorial.py
node scripts/lady_d_finalization/verify_editorial_layout.cjs
node scripts/lady_d_finalization/render_editorial_pdfs.cjs
python3 scripts/lady_d_finalization/audit_editorial_pdfs.py
python3 scripts/lady_d_finalization/package_editorial.py
node scripts/lady_d_finalization/verify_editorial_package.cjs
```

The older expanded 31-day motion product is a separate demonstration. Its corpus follows the current trilogy. The approved concise illustrated journal retains its existing 31 scenes and short messages.

After publication, run `verify_editorial_release.cjs` against the canonical public site. It rejects redirects to an external login page, compares exact deployed bytes, hashes all six PDF downloads and the web ZIP, checks internal routes remain unavailable, and exercises mobile/desktop reading navigation. No payment is submitted.

## Interpretation Of Checks

- Editorial workers read all 1,098 entries. The independent judge samples specific revisions; its report identifies the limits.
- The humanizer score is advisory. A flat score does not negate a concrete writing improvement, and a low score is not evidence of author approval.
- The all-page HTML fit check and daily PDF text checks complement, rather than replace, rendered-page inspection.
- The master ZIP contains all six PDFs locally. The smaller web review ZIP contains self-contained readers and art; its PDF, payment, and separate motion links require internet.
- Author voice/theological signoff, the friend's final foreword, exact retail cover wraps, production metadata, KDP Previewer, and physical proofs remain publishing gates. Do not label this author edition a retail-certified release.
