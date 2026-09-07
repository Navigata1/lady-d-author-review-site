# Independent Reader Review

Reviewed 2026-09-07, latest-code recheck at approximately 10:36 UTC.

**Verdict:** Fix the two reproduced reader navigation defects before treating this polish as complete. The revised PDF and mobile fallback checks below pass. The third finding is a pre-existing trilogy passage for targeted author review, not authorization to rewrite approved text. No numeric quality score is assigned.

Scope: read-only inspection of the five requested source files, the local journal and gallery at `http://127.0.0.1:8794`, existing polish screenshots, and existing trilogy HTML/PDF samples. Only this report was written. No build/export scripts that write artifacts were executed; Playwright probes and supplementary PDF renders used memory/stdout. No push, deployment, agent creation, or hub modifications.

## Findings

### 1. [P2] The skip link resets the selected day and overwrites reading progress

- Source: [reader.js:64](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/assets/lady-d-reader/reader.js:64>), with the skip target generated at [journal_presentation.py:27](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/scripts/lady_d_finalization/journal_presentation.py:27>).
- Reproduction against the latest local HTML: select Day 19, focus the day selector, press Shift+Tab four times to reach "Skip to reading", then Enter.
- Observed: before Enter, Day 19 is current and the skip link has focus. Afterwards, the fragment is `#main`, focus is correctly on `main`, but `.is-current[data-day]` is `1` and `localStorage['lady-d-mornings-last-day']` is `0`.
- Cause: every hash change calls `show(fromHash() ?? 0, false)`. The legitimate non-day fragment `#main` is interpreted as Day 1. `show()` also persists that unintended selection.
- Direction: distinguish day navigation from other document anchors. Preserve the current day and stored progress when following the skip link. Add the exact keyboard regression test to [verify_reader_polish.cjs](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/scripts/lady_d_finalization/verify_reader_polish.cjs:45>).
- Acceptance: the same keyboard sequence focuses `main` while Day 19, its text, and saved index `18` remain unchanged; genuine day hashes and browser Back/Forward still work.

### 2. [P2] Turning a page from the bottom of large-text mode skips the new reading's beginning

- Source: [reader.js:40](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/assets/lady-d-reader/reader.js:40>) and [reader.js:46](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/assets/lady-d-reader/reader.js:46>).
- Reproduction: use a 390 x 667 viewport, open Day 19, choose "Larger reading text", scroll to the bottom, and activate Next day.
- Observed after layout settles: Day 20 is correctly selected, but `scrollY=957`, the new heading's top is `-101.203125px`, and focus remains on `next-day`. The first viewport starts midway through the encouragement; the day heading and opening text are above it.
- Cause: `show()` replaces the reading content without bringing its beginning into view or providing a focus destination at that beginning. This affects the normal sequential-reading workflow, not just a malformed input.
- Direction: make an intentional viewport/focus transition to the new reading when turning pages in text mode, respecting reduced motion. Avoid forcing a jump merely for resize or print restoration.
- Acceptance: after Next/Previous from the bottom, the new heading and opening are visible; keyboard users can continue reading from the beginning. Cover a short phone height as well as the existing 1000px-height screenshots. The current test checks text presence/font size, not this transition.

### 3. [P2, Pre-Existing] Day 217's disclosure instruction lacks the safety distinction used elsewhere in Volume 1

- Source: [vol1-polished-366-days.json:3046](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/source/finalization/polished/vol1-polished-366-days.json:3046>) and [vol1-polished-366-days.json:3050](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/source/finalization/polished/vol1-polished-366-days.json:3050>), Day 217, "When Fear Made Us Hide the Truth".
- Rendered evidence: [Volume 1 HTML](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/downloads/lady-d-finalization/volume-1-surrendering-to-gods-love-polished-devotional.html>), section `#dB218`; [Volume 1 PDF](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/downloads/lady-d-finalization/Lady-D-Volume-1-Surrendering-to-Gods-Love-Polished-6x9.pdf>), physical PDF page 444, printed Day 217 / folio 442. The DOM ID is a sequential leaf identifier, not the printed day number.
- Confirmed wording: the prayer asks for courage to be honest "even when honesty feels unsafe". The surrounding application criticizes fear-based self-protection; the source journal action extends disclosure, "where needed, with the person involved". This reading does not distinguish uncomfortable honesty from disclosure to someone who presents an actual danger.
- Risk assessment: a reader in a coercive relationship could apply this generalized instruction against their own safety. This is a contextual ambiguity, not a claim that the author intends harm or that harm has occurred.
- Refutation checked: other sampled Volume 1 readings explicitly reject unsafe closeness, blind submission, and returning to danger (physical PDF pages 246, 270, and 484). Those are important safeguards to preserve, but they are not present in this standalone daily reading.
- Direction: refer only this passage and its companion action to the author/theological safety reviewer for a bounded decision. Do not automatically replace approved prose. This predates the journal polish and should not be misattributed to the reader changes.

## Verified And Preserved

- Fresh-session Chromium checks exercised all 31 illustrated days at widths 320, 390, 768, and 1440. Copy rectangles stayed inside the page and above the footer; no horizontal overflow or failed scene decoding was observed. Mobile heights included 667px.
- The gallery showed 31 loaded scene images with no horizontal overflow at those four widths. Gallery-to-Day-19 and onward-to-Day-20 navigation worked. Browser Back returned to the gallery, consistent with the deliberate `replaceState` policy; this is not reported as a defect. Reduced-motion scroll behavior was `auto`.
- Latest mobile no-JavaScript fallback: at 320px, document width remained 320px, all 31 leaves were present, and copy used relative flow. The latest two mode buttons have explicit `aria-label` values. No obsolete missing-label/fixed-width-fallback finding is retained.
- Actual in-memory printing from Day 31 in text mode produced all 31 pages at 432 x 648 points and restored the screen to Day 31 with 30 other leaves `aria-hidden`. This checks mode restoration/page visibility, not asset-loading completeness of that ad hoc export.
- Independently reopened the latest downloadable journal PDF: **49,135,490 bytes; 31 pages; every page 432 x 648 points; one embedded scene at least 1800 x 2700 per page**. Poppler `pdftotext -layout` matched all **186** required title/reference/encouragement/Scripture/prayer/affirmation fields to the current corpus, with zero mismatches. The revised exporter explicitly waits for all scene decodes and subsequent network idle.
- Inspected existing `reader-390.png`, `reader-text-390.png`, and print-page screenshots for Days 19 and 31 in this evidence directory; also inspected the live mobile gallery and a fresh Poppler render of latest PDF Day 8. The sampled compositions preserve the subject, clear hierarchy, and readable larger-text alternative. No sampled clipping was confirmed.
- Existing trilogy HTML was parsed across all three volumes for a bounded safety-keyword pass. PDF visual samples included Volume 1 physical page 270, Volume 2 page 9, and Volume 3 page 138; additional Volume 1 text samples included pages 3, 6, 9, 10, 246, 444, and 484. This is a sample review, not a complete theological/copy/print certification of all three 756-page volumes.
- Refuted before reporting: naive PDF extraction produced apparent missing phrases because shadow text is repeated in the content stream; Poppler layout extraction recovered all expected fields. PDF.js/canvas also drew rectangular shadow artifacts in a sample; independent Poppler rendering did not reproduce them. Neither is being presented as missing manuscript text or a confirmed print-layout defect.

## Evidence Boundary

The supplied test script was inspected but not executed because it writes screenshots and reports outside this task's single permitted output. Equivalent read-only probes covered the core assertions, with additional keyboard/short-viewport tests. Existing screenshot-report hashes predate the latest no-JavaScript/ARIA changes, so they are supporting visual evidence, not an exact-latest-build certificate.

No live production, packaged ZIP, full screen-reader session, Safari/Firefox, KDP Previewer, or physical print proof was tested. PDF packaging and the hub remain the other workers' responsibility. The trilogy's explicit author-review/foreword-placeholder boundaries remain in force.

Latest source SHA-256 values read during final verification:

```text
assets/lady-d-reader/reader.js
ba7f9bdaf114a41232aaff1aea664975a5a63ad3cdb10bf4e7ab168582a8cbcd
assets/lady-d-reader/reader.css
dca63575a81f1f76eccf4af9b7e719e28a88a7d085164b8ebf70c47f5a0c1d7e
scripts/lady_d_finalization/journal_presentation.py
7fca5484a562d2954b0119d92dc7231cd6aa6410d4b60d13d75148259f6a04db
scripts/lady_d_finalization/build_31_day_visual_journal.py
276426e5967aead1723cc43d775b05fae7bbbbaf35c971571e8b31897ca2554e
scripts/lady_d_finalization/verify_reader_polish.cjs
45ab1f85fc66c72257c9d269287b53b42e69f2d5bf95a1433cb78060550ffe95
```

## Findings Disposition: 2026-09-07 10:43 UTC

**Updated verdict:** Findings 1 and 2 are **CLOSED, independently reverified** against the updated local reader. Finding 3 remains **OPEN FOR AUTHOR REVIEW**. This addendum supersedes the initial verdict and reader-fix status above; the original evidence is retained as history. No new functional regression was confirmed in this bounded recheck. This is not deployment or publication approval.

- **Finding 1 closed:** [reader.js:73](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/assets/lady-d-reader/reader.js:73>) now ignores non-day fragments. Repeated the keyboard-only sequence from the focused Day 19 selector: Shift+Tab four times, then Enter on the skip link. Result: current day `19`, selector `19`, stored index `18`, and focus on `main`. Valid day hashes and Back/Forward across day fragments still select the expected days.
- **Finding 2 closed:** [reader.js:29](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/assets/lady-d-reader/reader.js:29>) focuses the new reading heading and scrolls it into view for explicit text-mode navigation. At 390 x 667, repeated both the newly added test sequence and the original bottom-of-document reproduction. Day 20's heading was focused, with top `89.796875px` and bottom `125.625px`, fully within the viewport. Entering text mode, Previous, selector changes, and ArrowRight from the focused heading also passed. The last-day Next boundary remained disabled.
- **Finding 3 unchanged:** Volume 1 Day 217, "When Fear Made Us Hide the Truth", remains a targeted author/theological safety-review item. The approved passage was not rewritten, and no disposition is inferred from the reader fixes. See Finding 3 above for the exact source, physical PDF page, and concern.

Read [verify_reader_polish.cjs:71](</Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/scripts/lady_d_finalization/verify_reader_polish.cjs:71>) through its new regression assertions: it checks Day 19/stored index 18/main focus and the focused, visible Day 20 heading at 390 x 667. Reproduced these assertions with separate read-only Playwright probes. The complete artifact-writing suite was not rerun by this reviewer.

Additional fix-adjacent checks passed:

- Genuine day fragment navigation, browser Back and Forward, and reduced-motion text navigation.
- A 390px-wide viewport-height resize retained Day 6, heading focus, and `scrollY=766` without an unsolicited navigation jump.
- Actual in-memory printing produced 31 pages and returned to text-mode Day 6 with 30 inactive leaves `aria-hidden` and unchanged `scrollY=766`. This was a navigation/print-restoration check, not a new packaging or artwork audit.
- Illustrated-mode first-day boundary, Next, reload persistence, and a desktop 1440 x 1000 text-mode page turn.
- Zero captured browser console errors or page exceptions during this recheck.
- Root files, `public/` mirrors, and local HTTP response bytes matched for reader JS, reader CSS, journal HTML, and gallery HTML.

Verified updated SHA-256 bindings:

```text
assets/lady-d-reader/reader.js
be2aa500ba5619ebea069433b837daab431eaf84ffa022fd9fa74c60e4532b5c
scripts/lady_d_finalization/verify_reader_polish.cjs
f9fb925069f919672d742f2399e45ece197ada15343abb6d8b38d4a6638c4dab
```

Only this disposition was appended. No implementation, approved text, package, or deployment changes were made. No broader scan or new quality score was introduced.
