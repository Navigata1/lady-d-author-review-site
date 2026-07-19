# Lady D Trilogy Independent Pre-Rewrite Manuscript Audit

**Status: RELEASE BLOCKED - PRE-REWRITE AUDIT ONLY**

**Release approval:** No. This report establishes the evidence baseline for the rewrite. It does not approve any manuscript, journal, PDF, cover, or KDP upload.

## Audit Scope

- July 6 guidance read in full: `/Users/IDC2.5/Downloads/Untitled meeting Jul 6, 2026.md`
- Production root: `/Users/IDC2.5/Documents/LADY D/lady-d-author-review-site/downloads/production`
- Canonical source inventory: 166 devotional sources, 165 journal sources, and 6 Markdown masters
- Files hashed and read: 337
- Concurrent revised-reader artifacts additionally detected and hashed: 14 files, including 6 manuscript/journal Markdown candidates
- Devotional grain audited: 1098 entries (365 dated days + one February 29 bonus in each volume)
- Companion-journal grain audited: 1098 reflections
- Derivative DOCX/PDF/ZIP review copies were not counted as separate manuscript content. Their canonical Markdown sources and assembled Markdown masters were audited.
- The undeclared `downloads/production/revised-reader-edition/` candidates appeared outside the canonical pre-rewrite manifest during this audit. They are intentionally excluded from the pre-rewrite counts so the baseline remains valid. They are not approved and require a separate post-rewrite judge/auditor pass.

## Executive Judgment

The corpus is complete in count and source-to-master assembly, but it is not release-ready. The July 6 direction has not yet been carried into the three books: every entry still omits visible Scripture text, every entry retains the two labels the author asked to fuse/remove, scripture movement remains heavily clustered, repeated production formulas weaken the voice, and evergreen pages are tied to the 2026 Saturday calendar. The journals cover all days, but their source contract and writing-space design are not finished.

| Volume | Devotions | Journal entries | Visible verse text | Old dual labels | 2026/Sat artifacts | Longest same-book run |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | 366 | 366 | 0 | 366 | 44 | Genesis 178 days |
| V2 | 366 | 366 | 0 | 366 | 52 | Matthew 191 days |
| V3 | 366 | 366 | 0 | 366 | 52 | Judges 96 days |

## Methodology and Commands

The canonical source lists came from `downloads/production/master/master-assembly-audit.json`. Each declared source and all six masters were read and SHA-256 hashed. Source entries were counted once; masters were used only for normalized source/master reconciliation.

Checks performed:

- day/bonus completeness and duplicate-key detection
- Scripture-reference syntax, recognized Bible book, and chapter-range validation
- visible KJV/NKJV Scripture-text and translation-tag detection
- current and July 6 revised label contracts
- prayer/prompt presence and basic completion signals
- exact normalized sentence reuse, within-entry duplicates, title-masked template reuse, and near-duplicate titles
- sequential Bible-book runs, adjacent same-book rate, monotonic progression, and monthly concentration
- 2026/Saturday/Sabbath/Sunday artifacts
- internal production/editorial phrasing
- context-language structural and meta-language signals
- journal day mapping, prompt/practice completeness, style consistency, prayer/review sections, and response-space markup
- normalized entry-signature comparison between batch sources and assembled masters

Reproduce with:

```bash
python3 quality/auditor/run_pre_rewrite_manuscript_audit.py
python3 -m json.tool quality/auditor/pre-rewrite-manuscript-audit.json >/dev/null
git diff -- downloads/production/
```

## Severity-Ranked Failures

### F-001 - Critical: Required visible Scripture text is absent from the devotional entries.

- **Evidence:** 1098 of 1,098 entries lack a visible, translation-tagged Scripture text block; 0 contain one.
- **Why it matters:** Readers cannot see the passage being interpreted, and context-language claims cannot be checked on the page.
- **Likely cause:** The sources preserve a pre-permissions placeholder policy that conflicts with the July 6 direction.
- **Required remediation:** Insert verified KJV text or properly licensed NKJV text with a translation tag in every entry, then run text-reference concordance and rights checks.
- **Confidence:** High

### F-002 - Critical: The revised daily-entry contract from July 6 has not been implemented.

- **Evidence:** All 1,098 entries retain both Today step and Morning impact instead of the requested fused reflection/action ending.
- **Why it matters:** The pages remain crowded and formulaic, leaving less room for the fuller, more impactful devotional narrative requested by the author.
- **Likely cause:** The assembled masters still reflect the earlier production schema.
- **Required remediation:** Rewrite to one locked entry contract and remove both deprecated labels from the revised masters.
- **Confidence:** High

### F-003 - High: Scripture selection remains heavily clustered in long, sequential Bible-book runs.

- **Evidence:** V1: longest run 178 days in Genesis, 97.0% adjacent same-book transitions; V2: longest run 191 days in Matthew, 97.2% adjacent same-book transitions; V3: longest run 96 days in Judges, 95.3% adjacent same-book transitions
- **Why it matters:** The reader experiences the mechanical Bible-order crawl the July 6 guidance explicitly rejected.
- **Likely cause:** References were allocated in book-order production batches rather than curated as a thematic reading journey.
- **Required remediation:** Re-sequence within monthly themes using diversity constraints and a human-reviewed narrative arc.
- **Confidence:** High

### F-004 - High: Formula reuse and duplicated sentences create an automated-production voice.

- **Evidence:** 44 exact repeated sentence groups, 9 title-masked near-exact template groups, and 28 within-entry duplicate sentence instances.
- **Why it matters:** Repetition weakens Lady D's personal voice and the requested emotional impact.
- **Likely cause:** Reusable transition and impact-line templates were applied at scale.
- **Required remediation:** Rewrite repeated frames, remove within-entry duplicates, and enforce a corpus-level phrase-reuse gate with a small approved liturgical whitelist.
- **Confidence:** High

### F-005 - High: Calendar-bound 2026/Saturday language makes the evergreen devotional edition date-specific.

- **Evidence:** 148 devotional entries and 140 journal entries contain strict 2026/Saturday-bound wording or headings.
- **Why it matters:** The day/date sequence will assert the wrong weekday in other years and makes Sabbath reflections look mechanically assigned from the 2026 calendar.
- **Likely cause:** Saturday flags were generated from the 2026 production calendar.
- **Required remediation:** Remove year/weekday assertions; preserve Sabbath theology through evergreen thematic placement and author-approved wording.
- **Confidence:** High

### F-006 - High: The Context and language lens frequently behaves as editorial scaffolding rather than concise reader-facing language insight.

- **Evidence:** 569 entries contain explicit lens/meta framing; 612 have no deterministic original-language signal.
- **Why it matters:** The feature can feel technical, generic, or disconnected, especially because the Scripture text it should illuminate is missing.
- **Likely cause:** Context explanation and original-language study were combined under one label without a locked quality rubric.
- **Required remediation:** Keep the lens only where it adds verified meaning; require qualified lexical review and remove all editorial/meta phrasing.
- **Confidence:** Medium

### F-007 - High: Companion-journal content coverage exists, but the journal source is not a finished reader-writing product.

- **Evidence:** All 1,098 reflections have prompts/practices, but only 0 of 165 journal sources contain detectable response-space markup; style shifts between structured Focus/Write/Practice and direct question/Practice formats.
- **Why it matters:** The journal is content-complete but not layout-complete or contract-consistent for KDP release.
- **Likely cause:** Journal masters were assembled before trim-specific design and human-touch layout work.
- **Required remediation:** Lock one journal contract, add intentional writing space and weekly/monthly rhythm, then proof at final trim size.
- **Confidence:** High

### F-008 - Medium: Titles and Scripture references need duplicate/near-duplicate editorial review.

- **Evidence:** Corpus duplicate titles: 1 groups; duplicate references: 82 groups; near-duplicate title pairs at >=90% similarity: 79.
- **Why it matters:** Repeated naming and passages can make the year feel less intentionally composed even when individual entries differ.
- **Likely cause:** Title-generation formulas and separate volume production lanes were not reconciled at trilogy scale.
- **Required remediation:** Review duplicate groups in context and require rationale for any intentional reuse.
- **Confidence:** High

### F-009 - Medium: Internal review/production language remains in source and master front matter, with additional meta language inside entries.

- **Evidence:** Every production batch carries production/editorial permission notes; entry-level counts are detailed by volume in this report.
- **Why it matters:** Internal scaffolding can leak into customer-facing or KDP-ready outputs and reduces the sense of a finished book.
- **Likely cause:** Review masters were promoted before a clean publication-layer transform.
- **Required remediation:** Create a publication master with zero internal notes and enforce a forbidden-phrase test.
- **Confidence:** High

## Counts by Volume

### Scripture and Ordering

| Volume | References | Structurally valid | Duplicate ref groups | Bible books used | Adjacent same book | Months >40% one book |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | 366 | 366 | 0 | 6 | 97.0% | 12 |
| V2 | 366 | 366 | 0 | 3 | 97.2% | 12 |
| V3 | 366 | 366 | 0 | 7 | 95.3% | 10 |

Structural validity means a recognized 66-book name, valid reference shape, and chapter within that book's chapter count. Because verse text is absent, exact verse concordance and interpretive accuracy cannot yet pass.

### Label, Prayer, Context, and Internal-Language Counts

| Volume | Missing current labels | Prayer gaps | Prompt gaps | No language signal | Meta-lens entries | 2026/Sat devotions | 2026/Sat journals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 0 | 0 | 0 | 124 | 247 | 44 | 36 |
| V2 | 0 | 0 | 0 | 122 | 19 | 52 | 52 |
| V3 | 0 | 0 | 0 | 366 | 303 | 52 | 52 |

### Companion Journals

| Volume | Entries | Missing prompt | Missing practice | Focus/Write/Practice | Question/Practice | Files no prayer | Files no review | Files with response space |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 366 | 0 | 0 | 182 | 184 | 0 | 0 | 0 |
| V2 | 366 | 0 | 0 | 0 | 366 | 0 | 0 | 0 |
| V3 | 366 | 0 | 0 | 0 | 366 | 0 | 0 | 0 |

Coverage is not the same as publication completeness. The current Markdown contains the reflection content, but it does not yet demonstrate a consistent final journal contract or usable 6x9 writing-page design.

## Repetition Evidence

- Exact repeated sentence groups: **44**
- Exact repeated sentence occurrences: **1551**
- Entries affected by exact repeated sentences: **987**
- Within-entry duplicate sentence instances: **28**
- Title-masked near-exact template groups: **9**
- Entries affected by title-masked templates: **838**
- Near-duplicate title pairs at >=90% similarity: **79**

### Most-Repeated Exact Sentences

| Occurrences | Sentence | Example entries |
| --- | --- | --- |
| 128 | Do not rush past the verse; let it steady you before you move. | V1-day-110, V1-day-115, V1-day-120, V1-day-182, V1-day-187, V1-day-192 |
| 128 | Let the Spirit press this from information into formation. | V1-day-106, V1-day-111, V1-day-116, V1-day-183, V1-day-188, V1-day-198 |
| 127 | Let prayer turn insight into obedience before noon. | V1-day-093, V1-day-098, V1-day-103, V1-day-108, V1-day-113, V1-day-118 |
| 125 | Take one surrendered step before worry gets the first word. | V1-day-092, V1-day-097, V1-day-102, V1-day-107, V1-day-112, V1-day-117 |
| 125 | This day falls on Saturday, the seventh-day Sabbath in the 2026 production calendar. | V1-day-220, V1-day-227, V1-day-234, V1-day-241, V1-day-248, V1-day-255 |
| 121 | Start from what God has revealed, not from what the day is demanding. | V1-day-099, V1-day-104, V1-day-109, V1-day-114, V1-day-186, V1-day-191 |
| 73 | Receive the truth deeply enough that it changes your next decision. | V1-day-122, V1-day-127, V1-day-132, V1-day-137, V1-day-142, V1-day-147 |
| 73 | Walk out of this page with courage, tenderness, and clarity. | V1-day-121, V1-day-126, V1-day-131, V1-day-136, V1-day-141, V1-day-146 |
| 71 | The day does not get to name you before God does. | V1-day-125, V1-day-130, V1-day-135, V1-day-140, V1-day-145, V1-day-150 |
| 70 | Carry this like bread for the road, not decoration for the shelf. | V1-day-123, V1-day-128, V1-day-133, V1-day-138, V1-day-143, V1-day-148 |
| 69 | Let this word give your morning a spine and your heart a place to rest. | V1-day-124, V1-day-129, V1-day-134, V1-day-139, V1-day-144, V1-day-149 |
| 49 | Akoloutheo means to follow as a disciple, not merely admire from a distance. | V2-bonus, V2-day-005, V2-day-010, V2-day-015, V2-day-020, V2-day-025 |

### Most-Repeated Title-Masked Templates

| Occurrences | Normalized template | Example entries |
| --- | --- | --- |
| 366 | let the spirit carry into one faithful step today | V3-bonus, V3-day-001, V3-day-002, V3-day-003, V3-day-004, V3-day-005 |
| 366 | walk with jesus through in one faithful step today | V2-bonus, V2-day-001, V2-day-002, V2-day-003, V2-day-004, V2-day-005 |
| 96 | let the father's love carry into one faithful step today | V1-day-266, V1-day-267, V1-day-268, V1-day-269, V1-day-270, V1-day-272 |
| 4 | by starting from what god has revealed not from what the day is demanding | V1-day-186, V1-day-246, V1-day-256, V1-day-338 |
| 3 | father teach me to | V1-day-181, V1-day-247, V1-day-259 |
| 3 | in family work grief ministry and private prayer | V2-day-118, V2-day-244, V3-day-114 |
| 2 | holy spirit in me | V3-day-180, V3-day-313 |
| 2 | in you | V1-day-105, V1-day-110 |
| 2 | today | V1-day-057, V1-day-058 |

## Duplicate Titles and References

### Exact Duplicate Titles

| Occurrences | Title | Example entries |
| --- | --- | --- |
| 3 | Grace for the Extra Day | V1-bonus, V2-bonus, V3-bonus |

### Exact Duplicate Scripture References

| Occurrences | Reference | Example entries |
| --- | --- | --- |
| 2 | Genesis 1:1 | V1-day-141, V3-day-069 |
| 2 | Genesis 1:10 | V1-day-079, V3-day-077 |
| 2 | Genesis 1:11 | V1-day-148, V3-day-019 |
| 2 | Genesis 1:12 | V1-day-149, V3-day-020 |
| 2 | Genesis 1:13 | V1-day-150, V3-day-078 |
| 2 | Genesis 1:14 | V1-day-151, V3-day-079 |
| 2 | Genesis 1:15 | V1-day-152, V3-day-080 |
| 2 | Genesis 1:16 | V1-day-153, V3-day-081 |
| 2 | Genesis 1:17 | V1-day-154, V3-day-082 |
| 2 | Genesis 1:18 | V1-day-155, V3-day-083 |
| 2 | Genesis 1:19 | V1-day-156, V3-day-084 |
| 2 | Genesis 1:2 | V1-day-142, V3-day-021 |

Any reuse may be intentional, but it must be reviewed in trilogy context and documented. This audit does not treat mere presence of a duplicate as theological error.

## Internal Production Language

| Volume | 2026 production calendar | This page | This entry | The reader | This lens |
| --- | --- | --- | --- | --- | --- |
| V1 | 26 | 25 | 0 | 28 | 1 |
| V2 | 52 | 25 | 1 | 7 | 2 |
| V3 | 52 | 23 | 1 | 11 | 10 |

In addition, every source batch and each assembled master carries review-stage production/permissions front matter. That is appropriate for internal review artifacts but forbidden in the publication masters.

## Acceptance Tests for the Revised Edition

- **AT-001 - Corpus grain:** Each volume contains Day 001-365 exactly once plus one February 29 bonus; no missing or duplicate keys in source or master. **Pass threshold:** 366 entries per volume; 1,098 total; 0 mismatches.
- **AT-002 - Visible Scripture:** Every entry contains the full quoted passage, a KJV/NKJV tag, and a reference that concords with the displayed text. **Pass threshold:** 1,098/1,098 pass; 0 unlabeled or discordant passages.
- **AT-003 - Scripture rights:** KJV public-domain/territory policy or NKJV license/quotation limits are documented for print, ebook, web, and audio. **Pass threshold:** Signed publishing-rights checklist before layout lock.
- **AT-004 - Revised entry contract:** Entry contains date/title, visible Scripture, opening hook, fuller devotional body, optional verified meaning lens, prayer, and one fused reflection/action ending. **Pass threshold:** 100% contract coverage; 0 Today step labels; 0 Morning impact labels.
- **AT-005 - Prayer and prompt:** Every entry has a substantive prayer and a clear reader-facing reflection/action prompt tied to the passage. **Pass threshold:** 1,098/1,098 present; 0 placeholders; 0 empty or fragmentary fields.
- **AT-006 - Phrase originality:** Scan sentences of eight or more words after normalization and title masking. **Pass threshold:** 0 within-entry duplicate sentences; no unapproved sentence/template in more than 3 entries; approved refrains documented.
- **AT-007 - Scripture journey:** Measure same-book runs, monthly book diversity, and adjacent same-book rate after re-sequencing. **Pass threshold:** No undocumented run over 7 days; no month over 40% one book; at least 4 Bible books per month; adjacent same-book rate <=35%.
- **AT-008 - Evergreen dating:** Search devotional and journal sources for production year and weekday-bound claims. **Pass threshold:** 0 occurrences of production-calendar/2026 wording; 0 Saturday/Sunday claims tied to fixed dates.
- **AT-009 - Context-language quality:** Any retained lens is concise, passage-specific, reader-facing, and reviewed against the displayed verse by a qualified biblical-language/theology reviewer. **Pass threshold:** 0 editorial-meta lenses; 100% retained lenses signed off; optional omission preferred over weak filler.
- **AT-010 - Title/reference duplication:** Exact and >=90% near-duplicate titles plus repeated references are reviewed in trilogy context. **Pass threshold:** 0 accidental duplicate titles; every repeated reference has documented thematic rationale and distinct treatment.
- **AT-011 - Journal coverage:** Each devotional entry maps one-to-one to a journal reflection with a clear prompt and practice. **Pass threshold:** 366/366 per volume; 0 missing/duplicate mappings; 0 empty prompt/practice fields.
- **AT-012 - Journal product design:** Final 6x9 journal masters use one approved hierarchy, adequate response space, weekly prayer/review rhythm, and legible trim-safe margins. **Pass threshold:** 100% page-template conformance; KDP Previewer and printed-proof approval.
- **AT-013 - Publication language:** Search publication masters for production, editorial, permissions, model, prompt, reader-instruction scaffolding, and placeholder language. **Pass threshold:** 0 internal-production hits in reader-facing files.
- **AT-014 - Master/source integrity:** Rebuild masters from the declared source inventory and compare normalized entry signatures and hashes. **Pass threshold:** 0 missing entries; 0 content mismatches; manifest and checksums archived.
- **AT-015 - Scripture glossary:** Generate biblical-order glossary entries linking reference to day/date and final page after pagination lock. **Pass threshold:** 1,098 source entries represented; 0 broken day/page mappings.
- **AT-016 - Independent release gate:** A second auditor samples all flagged categories and verifies automated counts after rewrite; author reviews representative months and final proofs. **Pass threshold:** No Critical/High findings open; signed author/editor/auditor approvals; physical proof approved.

## Limitations and Required Human Review

- This is an independent structural/editorial audit, not pastoral, denominational, legal, or biblical-language approval.
- Exact KJV/NKJV concordance cannot be tested until visible verse text is inserted.
- Original-language and theological accuracy require qualified human review against the displayed passage and its literary context.
- Final journal completeness requires visual inspection of imposed 6x9 PDFs, KDP Previewer output, and printed proofs.
- Near-duplicate screens identify editorial risk; a human editor must decide whether a refrain is purposeful or stale.

## Release Decision

**DO NOT RELEASE.** Critical and High failures remain. Rewrite all three devotional manuscripts and their companion journals to the July 6 contract, run these acceptance tests again, and require independent author/editor/auditor approval before any KDP or public-release claim.

Machine-readable evidence: `quality/auditor/pre-rewrite-manuscript-audit.json`
