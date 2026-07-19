# Lady D Trilogy Independent Current-Schema Post-Rewrite Audit

**Manuscript gate: PASS**  
**Production-interior artifact gate: PASS**  
**Public/KDP release gate: HOLD**  
**Independent editorial score: 100/100** (binding minimum: 88/100)

> All earlier and interrupted findings were discarded. This report was recomputed from the final hash-locked one-primary-Scripture corpus only. Empty compatibility fields for an optional second Scripture are not treated as missing content.

## Hash Lock

- Volume 1 JSON: `531b3f91dd0cb7c361f3277ae250eb11dcc7b9e15fda032e3ad905db8700d290`
- Volume 2 JSON: `180df45c3be4efb746bf6247f219f02c1acada933df4f9af942b90934a304340`
- Volume 3 JSON: `bd13507187fca9f42be31b0e7ee271637bf32f8cabdedd7812faadeae18f7675`
- Contract: `source/research/2026-07-06-transcript-directed-editorial-contract.md`
- Contract SHA-256: `b61fcc12f564326104fb415c19f171a8f544fc115ec5ff7c0953384b4d13baca`
- KJV archive SHA-256: `4ea6952590d070bfa22985aded48a49581e31b568a60aa09e25f73462e700e7d`
- OpenBible archive SHA-256: `1775644c918fd5751292e3e5bad17461326a1f60537f1838401487a104860b78`
- Interior ZIP SHA-256: `26cb1202ea70d72537e09ded73f270f9f44d3dbae0b6e1fea1be76f6e6a9a22f`
- Independent judge checklist SHA-256: `421e83573b5baf73e480e96cd80919bf9e84c60da7480627d5709d55ad3f828d`

## Executive Finding

The current edition contains **1,098 devotionals**, **1,098 matching journal units**, and **1,098 required primary KJV quotations**. It contains **0** nonempty second Scriptures, which is valid under the binding contract.
The audit also checked **150** Volume 2 Gospel reassignments, **6 DOCX files**, **6 PDFs**, and **2,364 PDF pages**.

Release remains on hold because:

- **Final author visual approval is not evidenced.**
- **KDP Previewer approval is not evidenced.**
- **Physical-proof approval is not evidenced.**

## Binding Gates

| Gate | Weight | Result |
|---|---:|---|
| G01 - Corpus counts, dates, leap day, and Markdown index | 8 | PASS |
| G02 - Exact primary KJV concordance and reader-facing reference naming | 14 | PASS |
| G03 - JSON-to-reader Markdown integrity | 8 | PASS |
| G04 - One-Scripture schema and current labels | 6 | PASS |
| G05 - Evergreen calendar, Sabbath placement, legacy-label, and unsupported-claim hygiene | 7 | PASS |
| G06 - Unique, natural titles within each volume | 8 | PASS |
| G07 - Body, closing, prayer, response, and grammar | 14 | PASS |
| G08 - No severe repeated devotional or substantive journal templates | 8 | PASS |
| G09 - Original-language placement and context contract | 5 | PASS |
| G10 - Journal fields, one-to-one mapping, prompt variants, monthly reviews, and nine lines | 8 | PASS |
| G11 - Non-mechanical primary Scripture journey | 6 | PASS |
| G12 - Provenance and documented Gospel-parallel fidelity | 8 | PASS |

## Corpus Integrity

| Check | Result |
|---|---:|
| Count/date/leap failures | 0 |
| Reference/translation failures | 0 |
| Exact primary KJV mismatches | 0 |
| References using `Psalms` instead of `Psalm` | 0 |
| Reader JSON/Markdown mismatches | 0 |
| Journal field/writing-space mismatches | 0 |
| Scripture Journey Index mismatches | 0 |
| Source-provenance failures | 0 |
| Rendered second-Scripture labels | 0 |
| Old theme-label hits | 0 |
| Stale month/year transition hits | 0 |
| Detached Sabbath or weekday failures | 0 |
| Unsupported removal/readiness claims | 0 |
| Diagnostic titles with non-adjacent repeated words | 41 |
| Sentence-level Scripture-invitation fragments | 0 |
| Malformed `teach me rest` constructions | 0 |
| Sentence-leading `Neither do`/`Neither does` reader-prose fragments | 0 |

## Results by Volume

| Vol. | Entries | Body words min/avg/max | Contexts | Monthly reviews | Index rows | Adjacent same-book | Longest run | Failing diversity months |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 366 | 118/193.8/269 | 320 | 12 | 366 | 27.2% | 4 | 0 |
| 2 | 366 | 99/128.9/169 | 365 | 12 | 366 | 7.4% | 2 | 0 |
| 3 | 366 | 99/129.8/170 | 366 | 12 | 366 | 3.9% | 2 | 0 |

## Exact Current Evidence

### KJV concordance failures (0)

None.

### Plural-Psalms reference failures (0)

None.

### Calendar artifacts (0)

None.

### Internal production language (0)

None.

### Original-language body leakage (0)

None.

### Context-contract failures (0)

None.

### Title naturalness flags (0)

None.

### Diagnostic repeated title-word candidates (41)

- `V1-D005`: Love That Sends You Sometimes Sends You Out Through Correction
- `V1-D006`: Beloved Identity Begins Under the God Who Was Already God in the Beginning
- `V1-D026`: The Action Has Moved Forward, But the Outcome Has Not Arrived
- `V1-D028`: Beloved Identity Should Make Us More Tender, Not More Exclusive
- `V1-D035`: The Father Does Not Rush Love, But He Does Call for a Choice
- `V1-D069`: The Heart That Calls You Is Also the Heart That Intervenes
- `V1-D076`: Jacob Is Not Informing God of Something God Forgot
- `V1-D146`: The Heart That Calls You Is Still the Father's Heart When Trust Is Tested
- `V1-D148`: Grace Sometimes Reaches the Heart Before the Heart Knows What to Do with It
- `V1-D183`: The Heart That Calls You Is Also the Heart That Comes Down
- `V1-D218`: Grace Forms Identity by Turning Frightening Places Into Places of Testimony
- `V1-D255`: Sarah Will Bear Isaac, and the Covenant Will Be Established Through Him
- `V1-D318`: The Promise Has a Location, But the Location Is Not Empty
- `V2-D015`: The Call to Follow Jesus Is Also the Call to Become Like Him
- `V2-D048`: Jesus Takes Words Seriously Because Words Carry Witness
- `V2-D089`: The Way of Peace Is Not Always the Way Around Suffering
- `V2-D093`: What Is Hidden Will Not Stay Hidden Forever
- `V2-D119`: Jesus Does Not Separate Holy Time from Holy Compassion
- `V2-D197`: Jesus Redirects the Heart Toward God and Toward the Commandments
- `V2-D204`: The Shepherd's Voice Can Sound Like Loss Before It Feels Like Life
- `V2-D223`: The Invitation of Jesus Is Not Only an Invitation to Come Close
- `V2-D246`: The Command Not to Fear Is Not Scolding
- `V2-D250`: The Call to Follow Is Also a Call to Bear Witness
- `V2-D251`: Grace Feeds the Servant, Then Sends the Servant As a Witness
- `V2-D256`: Jesus Calls a Child and Places That Child in the Middle of His Disciples
- `V2-D270`: Jesus Prepares His Disciples for Rejection Without Making Rejection Their Identity
- `V2-D281`: Jesus' Peace Does Not Pretend Sin Did Not Happen
- `V2-D295`: The Place Cleared for Prayer Becomes a Place Where Wounded People Can Come Near
- `V2-D341`: The Gifts Are Not Random, and They Are Not Given for Display
- `V3-D094`: The Life Surrendered Is the Life Truly Found
- `V3-D101`: Holy Things Are Made Holy by God
- `V3-D133`: Prayer Beyond Words Is the Moment When Prayer Must Become Obedient Movement
- `V3-D151`: Prayer Beyond Words Is Obedience That Has Moved Beyond Wishing
- `V3-D169`: Ehud Finishes One Part of the Assignment Before the Next Part Unfolds
- `V3-D201`: Witness Begins with What God Gives, Not What the Heart Invents
- `V3-D223`: Dry Places Do Not Always Look Dry from the Outside
- `V3-D241`: What God Appoints, God Also Uses to Bless the Place Where Life Is Forming
- `V3-D312`: Movement Comes, But It Comes with Cords
- `V3-D316`: Before the Heart Hears Boundary, It Hears Permission
- `V3-D343`: Conviction Without Condemnation Helps the Heart Receive Mercy Without Suspicion
- Full machine-readable list contains 41 rows.

### Missing-verb/title-substitution fragments (0)

None.

### Malformed context fragments (0)

None.

### Severe sentence fragments (0)

None.

### Sentence-level Scripture-invitation fragments (0)

None.

### Malformed teach-me-rest constructions (0)

None.

### Old theme-label hits (0)

None.

### Stale month/year transition hits (0)

None.

### Weekday-placement hits (0)

None.

### Detached Sabbath failures (0)

None.

### Unsupported removal claims (0)

None.

### Unsupported readiness claims (0)

None.

## Titles and Repetition

- Exact duplicate-title groups within volumes: **0**
- Exact duplicate-title groups across the trilogy: **1**
- Near-title pairs at >=90% within volumes: **4**
- Deterministic title-naturalness flags: **0**
- Judge-reviewed length-only title candidates: **65**
- Colon titles: **4**
- Volumes with a detected suffix or four-word-prefix title factory: **0**
- Exact repeated devotional sentence groups: **7**
- Entries affected by exact sentence repetition: **14**
- Maximum exact sentence reuse: **2** entries
- Masked devotional template groups used in more than three entries: **0**
- Within-entry duplicate sentences: **0**
- Substantive journal Reflect/Act groups used in more than three entries: **0**
- Repeated journal scaffold groups used in more than thirty entries: **24**
- Severe generated sentence-frame groups over thirty entries: **0**
- Maximum non-approved generated frame reuse: **20** entries

- Volume 1 title matrix: **0/366** titles (0.0%) map to **0** repeated suffix groups.
  - Four-word prefix families used >=10x affect **0/366** titles (0.0%) across **0** groups.
- Volume 2 title matrix: **0/366** titles (0.0%) map to **0** repeated suffix groups.
  - Four-word prefix families used >=10x affect **10/366** titles (2.7%) across **1** groups.
    - **10x** `The Road with Jesus`: The Road with Jesus Is Not Controlled by Self-protection; The Road with Jesus Is Refined by Restraint
- Volume 3 title matrix: **0/366** titles (0.0%) map to **0** repeated suffix groups.
  - Four-word prefix families used >=10x affect **0/366** titles (0.0%) across **0** groups.

Judge-listed remediation recheck:

- Reviewed title/reference rows: **16**; failures: **0**.
- Detached-prose rows: **4**; failures: **0**.
- Judge-listed grammar rows: **10**; failures: **0**.
- Checklist/source failures: **0**.
- Judge prose rows expressed with shorthand rather than fully qualified IDs: **7** (diagnostic only; current JSON rows are checked directly).
  - `V2-D075`: forbidden phrase absent=yes; passage-specific replacement present=yes.
  - `V3-D152`: forbidden phrase absent=yes; passage-specific replacement present=yes.
  - `V3-D233`: forbidden phrase absent=yes; passage-specific replacement present=yes.
  - `V3-D251`: forbidden phrase absent=yes; passage-specific replacement present=yes.
  - `V1-D051` (body): former defect absent=yes; repair present=yes.
  - `V1-D096` (body): former defect absent=yes; repair present=yes.
  - `V1-D109` (body): former defect absent=yes; repair present=yes.
  - `V1-D158` (body): former defect absent=yes; repair present=yes.
  - `V2-D321` (body): former defect absent=yes; repair present=yes.
  - `V3-D101` (body): former defect absent=yes; repair present=yes.
  - `V2-D055` (prayer): former defect absent=yes; repair present=yes.
  - `V2-D113` (prayer): former defect absent=yes; repair present=yes.
  - `V2-D335` (prayer): former defect absent=yes; repair present=yes.
  - `V3-D057` (prayer): former defect absent=yes; repair present=yes.

Auditor-led neither-clause remediation recheck:

- Reviewed Volume 2 rows: **8**; failures: **0**.
- Mark 11:33 exact KJV literal verified in `scripture_text`: **yes**.
- KJV `scripture_text` neither-clause literals excluded from the reader-prose rule: **3**.
  - `V2-D041` (Matthew 13:41): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D050` (Matthew 15:11): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D052` (Matthew 17:13): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D079` (Mark 6:3): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D187` (Mark 8:5): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D207` (Mark 8:35): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D212` (Matthew 15:21): former fragment absent=yes; passage-specific repair present=yes.
  - `V2-D325` (Mark 6:17): former fragment absent=yes; passage-specific repair present=yes.

Claimed production-phrase removals:

- `living center`: **0 occurrences** across **0 entries** (none).
- `Through that line`: **0 occurrences** across **0 entries** (none).
- `without fanfare`: **0 occurrences** across **0 entries** (none).
- `Practice the Scripture's invitation by`: **0 occurrences** across **0 entries** (none).

Controlled deepening scaffold (recalculated, not carried forward):

- Volume 1: **0 detected**; pre-scaffold range **n/a**.
- Volume 2: **101 detected**; pre-scaffold range **44-99 words**.
- Volume 3: **111 detected**; pre-scaffold range **55-99 words**.
- Trilogy total: **212**.
- Threshold violations: **0**.
- Diagnostic sub-100-word V2/V3 bodies without the scaffold: **0**.
- `V2-D187` final remediation: **PASS** (107 words, 4 paragraphs, controlled scaffold=none).

Most reused devotional sentences:

- **2x:** Genesis 1:13 closes the third day with evening and morning. (`V1-D201, V3-D325`)
- **2x:** Holy Spirit, give me power to witness truthfully. (`V3-D192, V3-D211`)
- **2x:** Holy Spirit, give me wind in the waiting. (`V3-D327, V3-D329`)
- **2x:** Holy Spirit, meet me in the hidden place. (`V3-D136, V3-D320`)
- **2x:** Practice the Scripture's invitation in family, work, grief, ministry, and private prayer. (`V2-D059, V3-D343`)
- **2x:** Receive the Scripture's invitation with an honest response. (`V1-D051, V3-D101`)
- **2x:** Then sit with this question: What pressure needs to be named before God today? (`V3-D293, V3-D299`)

## Reader-Facing Hygiene and Sabbath Placement

- Explicit Sabbath reader entries: **26** ({'1': 17, '2': 5, '3': 4}).
- Justification distribution: **{"Rest in the Father's Care theme": 17, 'primary Scripture explicitly names Sabbath/seventh day': 9}**.
- Detached Sabbath failures: **0**.
- Weekday hits: **0**.
- Old theme-label hits: **0**.
- Stale month/year transition hits: **0**.
- Unsupported removal/readiness claims: **0**.

## Primary Scripture Sequencing

Binding anti-crawl screen: adjacent same-book rate <=35%; no same-book run over seven dated readings; at least two books per month; no month over 85% one book. The JSON also retains stricter 40%/four-book diversity diagnostics without treating them as binding.

- Volume 1: 27.2% adjacent same-book; longest run 4 (Genesis); 0 months over 85%; 0 months under two books.
- Volume 2: 7.4% adjacent same-book; longest run 2 (Matthew); 0 months over 85%; 0 months under two books.
- Volume 3: 3.9% adjacent same-book; longest run 2 (Judges); 0 months over 85%; 0 months under two books.

## Volume 2 Gospel Parallel Audit

- Reassigned rows checked: **150** (expected 150)
- Direct OpenBible edges: **150**
- Non-edges: **0**
- Verse/window overlap failures: **0**
- Broad-exclusion failures: **0**
- Forced-mapping failures: **0**
- Confirmed source/primary attribution mismatches: **0**
- Lexical attribution candidates reviewed: **1**
- Reviewed immediate-context nonfailures: **1**
- Unreviewed semantic candidates: **0**
- Edge votes min/median/max: **1/8.0/130**
- Minimum verse-token / window-token / window-bigram overlap: **1/6/3**
- Target-book distribution: **{'Mark': 106, 'Luke': 43, 'John': 1}**

Reviewed immediate-context nonfailures:

- `V2-D002` (Matthew 16:20 -> Mark 8:30): Archived KJV Mark 8:27 identifies Jesus and His disciples, Mark 8:29 records Peter's confession that Jesus is the Christ, and Mark 8:30 immediately charges them to tell no one. The sentence accurately describes the immediate context and does not misattribute the source verse. Claim reviewed: Mark 8:30 comes after a powerful confession, yet Jesus gives His disciples instruction about what not to announce.


## Journal Contract

- Journal render/field/spacing mismatches: **0**
- Expected writing space: nine underscore lines per unit.
- Expected monthly rhythm: one review after each of twelve months.
- Repeated substantive prompt groups over three entries: **0**
- Prayer-record variants: **12/12**
- Follow-through variants: **12/12**
- Variant grammar/distribution failures: **0**

## Interior Artifact Audit

**Production-interior artifact gate: PASS**

- All DOCX, PDF, build-audit, index, and ZIP checks passed.

| Vol. | Reader PDF | Journal PDF | DOCX sync | Reader index rows | Reader index titles | Biblical order |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 395 pages | 393 pages | 0 mismatches | 366/366 | 366/366 | PASS |
| 2 | 395 pages | 393 pages | 0 mismatches | 366/366 | 366/366 | PASS |
| 3 | 395 pages | 393 pages | 0 mismatches | 366/366 | 366/366 | PASS |

## Production-Proof Boundary

**PARTIAL - LOCAL RENDERED-PAGE REVIEW PASSED**

The locked representative local rendered-page review supports only the local visual-evidence flag. It is not final author approval and does not replace KDP Previewer evidence or an approved physical proof.

- Local rendered-page evidence: PASS
- Final author visual approval: NOT EVIDENCED
- KDP Previewer: NOT EVIDENCED
- Physical proof: NOT EVIDENCED
- Visual-review evidence: `quality/visual-proof/post-rewrite-rendered-page-visual-review.md` (`c9cf1ea89480d430bceb09b81dae9dde2898ac930f88a9aa3f3c43a2992e6627`)

## Reproduction

```bash
python3 quality/auditor/run_post_rewrite_manuscript_audit.py
python3 -m json.tool quality/auditor/post-rewrite-manuscript-audit.json >/dev/null
shasum -a 256 downloads/production/revised-reader-edition/volume-1/volume-1-reader-edition.json downloads/production/revised-reader-edition/volume-2/volume-2-reader-edition.json downloads/production/revised-reader-edition/volume-3/volume-3-reader-edition.json
```

The script writes only this Markdown report and its JSON companion. It does not modify devotional or journal manuscripts.

## Required Disposition

**Public/KDP release: HOLD.** Manuscript and production-artifact verdicts remain separate above. A current representative local rendered-page review is recorded; public release remains prohibited until final author visual approval, KDP Previewer approval, and physical-proof approval are evidenced.
