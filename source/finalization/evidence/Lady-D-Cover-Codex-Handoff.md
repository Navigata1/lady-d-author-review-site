# Lady D — Cover Generation, Qualification, Ranking & Decision Engine
### A Codex handoff brief (paste this whole file as the task)

> **Model note:** run this on Codex on the Mac, where you have a real image-generation
> tool. This is the engine that turns the *art direction* already produced into
> **actual, selectable, print-ready cover art** — matching the quality bar of the Joyce
> Ashford deck: `https://joyce-publishing-fade-deck-site.vercel.app/files/matched-cover-prompt-pack-v3`
> (10 covers, each with a confidence score, a rank, editorial rationale, shortlist +
> decision tooling). Lady D chooses from the deck; you build the deck.

> **Read `Lady-D-Cover-Vision-Brief.html` first.** It documents, from her own recorded
> words, exactly why the first cover round failed ("it's just a little dark... they're
> deserts... they're not bright") and measures it (70–139/255 average luminance against a
> 160+ floor). The brightness gate in §4 and the corrected prompts below come directly
> from that brief — do not regenerate against the old prompt-pack palettes without it.

---

## 0. Mission (one paragraph)

Generate real book-cover art for Susan "Lady D" Damon's three-volume devotional trilogy,
**qualify** each image against a print + genre rubric, **rank** them with confidence
scores and written rationale, and assemble a **decision deck** Lady D can browse and
shortlist from — then render the chosen direction as a matched three-volume set with
full print-ready wraparounds. Nothing is called "final" or "selected" until the deck is
built from real captured images and Lady D has actually shortlisted. This is an
evidence-gated engine, not a one-shot generation.

---

## 1. Source of truth (read these first)

All in `/Users/IDC2.5/Documents/LADY D/_synthesis-2026-07-19/`:

- **`Lady-D-Cover-Design-Studio.html`** — the art direction. Ten named directions, each
  with palette, suited volume, and a photoreal generation prompt. **This is your prompt
  source.** The CSS mockups on that page are *placeholders for layout only* — your job is
  to replace them with real generated art.
- **`Lady-D-Vol1-Devotional-6x9.pdf`** (and Vol2/Vol3) — the finished interiors, so the
  covers match the books' warmth and 6×9 trim.
- Lady D's own mockup (the "Radiant Surrender" wraparound) is the North Star for feel:
  warm golden-hour valley, a Black woman in white seated in quiet surrender, a soaring
  eagle, wildflowers, ornate gold script title, a small red heart, wine spine, and her
  poem on the back.

### The trilogy
| Vol | Title | Lane | Accent |
|---|---|---|---|
| I | *Surrendering to God's Love* | God the Father | warm gold / rose |
| II | *Walking with Jesus* | Jesus the Son | olive-grove gold |
| III | *Filled with the Holy Spirit* | The Holy Spirit | dawn blue / gold |

Subtitle pattern: "A 365-Day Devotional Journey…". Author line: **by Susan Damon**.

### Lady D's brief (the aesthetic to satisfy — and to score against)
- Warm, radiant, **golden-hour**, hopeful. African-American Christian devotional.
- Tender and reverent, never a travel poster, never cold or minimalist-flat (she
  rejected the understated first covers).
- Signature motifs available: sunrise, a woman in quiet surrender, an eagle, wildflowers,
  open hands, living water, a single **red heart**, ornate **gold** script lettering.
- The series heartbeat is **surrender to God's love**. Every cover should feel like it.

---

## 2. The ten directions (front-cover art prompts)

Generate art for all ten. Each prompt below is the base; append the **global style suffix**
(§3) to every one. Directions marked ★ are Lady D's stated favorites — weight them, but
generate all ten so the deck is a true field.

1. **★ Radiant Surrender** *(Vol I, her pick)* — A radiant golden-hour valley; a Black
   woman in a flowing white dress seated on a rock, seen from behind, gazing toward a
   glowing sunrise over rolling green hills and a distant river; a bald eagle soaring on
   the warm updraft to the right; wildflowers (gold, white, soft rose) in the foreground.
2. **The Narrow Path Home** *(Vol I)* — A luminous footpath winding through fields of
   lavender and roses toward a breaking golden sunrise; soft mist; the way home lit from
   the end.
3. **★ Wings Like Eagles** *(Vol III)* — A lone bald eagle soaring on warm updrafts above
   sunlit mountain ridges at dawn, blue-to-gold sky breaking open (Isaiah 40:31).
4. **Living Water** *(Vol III)* — A bright river of light winding through a green meadow at
   golden hour, a soft dove-shaped glow of light above; living and peaceful.
5. **★ The Footstep Road** *(Vol II — her explicitly praised element)* — A warm dirt road
   through **sunlit** olive groves and open fields in bright golden morning light; faint
   sandal footprints visible in the lit path, leading toward a bright dawn horizon; olive
   leaves lit green-gold, never shadowed. *(She said of the Jesus cover: "you can see the
   footsteps in the thing as well... it is nice." Keep footprints in every Vol II variation.)*
6. **Open Hands** *(any)* — Two open, upturned brown hands reaching up into warm morning
   light, god-rays pouring into the palms; **bright warm background, softly lit — not a dark
   ground**; sacred and tender.
7. **Fields of Grace** *(Vol I)* — A vast wildflower meadow (gold, white, soft rose)
   stretching to a low golden sun on the horizon; wide open sky; expansive and hopeful.
8. **The Father's Light** *(Vol I)* — Soft warm golden bokeh with a gentle silhouette of an
   embrace; shallow depth of field; comforting nearness.
9. **Sacred Gold** *(typographic, any)* — A **warm cream and soft-gold** textured ground
   (linen/parchment grain) with a bright central glow and ornate gold flourishes; wine used
   only as a thin border/accent, never as the field. Type-forward, no people. *(The original
   deep-wine version measured 70/255 — the darkest of the whole round.)*
10. **Breaking Dawn** *(Vol III)* — Brilliant sunbeams bursting through parting storm clouds
    over a calm green meadow; gold breaking through grey-blue; triumphant yet gentle.

---

## 3. Generation spec (apply to every render)

**Global style suffix (append to each prompt):**
> "…warm African-American Christian devotional cover art, cinematic golden-hour light,
> soft god-rays, gentle bokeh, hopeful and reverent mood, painterly-photoreal, rich warm
> palette (amber, gold, rose, sunlit green, cream). **Bright and radiant overall — light
> fills at least two-thirds of the frame; foreground flora and ground plane are directly
> sunlit, NOT silhouetted; no dark hillside or shadow mass framing the composition; no
> near-black regions.** Composition leaves the **upper third calm and uncluttered for a
> title**. No text, no lettering, no watermark, no frame."

**Palette correction (supersedes the old prompt packs).** The original packs led with
`deep indigo` / `earthy umber` (Vol I), `midnight blue` (Vol II), `deep teal` / `violet
shadow` (Vol III) with no cap on how much frame those hues could occupy — which is what
produced the dark round. Dark hues are now **accent only, at the extreme top edge**:
| Vol | Dominant (bright) | Allowed accent only |
|---|---|---|
| I | sunrise gold, warm cream, soft rose, sage green | thin soft indigo at top edge |
| II | dawn gold, warm parchment, sunlit olive green, clean white | midnight blue rimming top corners |
| III | flame gold, dove white, sunlit sky blue, fresh green | faint deep teal at extreme upper edge |

- **Tool:** your best available image model (e.g. `gpt-image-1`) at its **highest quality
  and largest size**. If native output is < 300 DPI at trim, upscale losslessly to the
  print target.
- **Aspect / size:** front-cover art at **6 × 9 portrait**. Print target with bleed =
  **6.25 × 9.25 in @ 300 DPI = 1875 × 2775 px**. Generate at the model's max, then
  upscale/crop to that, keeping a full-bleed safe area (nothing critical within 0.25 in of
  any edge).
- **Text layer is separate.** Generate the **art with a clean title zone** — do NOT bake
  the title into the model output (models mangle text). Set the title, subtitle, heart, and
  "by Susan Damon" as a **typographic overlay** afterward (ornate warm-gold serif +
  script flourish on the emphasis words, e.g. *God's Love* / *Jesus* / *Holy Spirit*, one
  small red heart). The Cover Design Studio shows the exact title treatment.
- **Variations:** **3 per direction** (30 total for Volume I round), varying only
  composition/light — same aesthetic. Capture the seed/params of each.
- **Filenames:** `covers/raw/{dir-slug}-v{1..3}.png`. Never overwrite; keep every render.

---

## 4. Qualification gate (reject-and-regenerate before ranking)

Score each raw image PASS/FAIL on **all** of the following. Any FAIL → regenerate that
variation (max 2 retries), log the reason. Only PASS images enter ranking.

- **BRIGHTNESS (hard gate — the #1 failure of the last round):** average frame luminance
  **≥ 160/255**, and **no contiguous shadow mass may exceed 25% of frame area**. Measure it,
  don't eyeball it:
  ```python
  from PIL import Image; import statistics
  im = Image.open(path).convert("RGB"); px = list(im.getdata())[::80]
  avg = [statistics.mean(c[i] for c in px) for i in range(3)]
  lum = 0.299*avg[0] + 0.587*avg[1] + 0.114*avg[2]     # must be >= 160
  dark = sum(1 for c in px if (0.299*c[0]+0.587*c[1]+0.114*c[2]) < 60) / len(px)  # must be <= 0.25
  ```
  For reference, the rejected round measured: Vol I sanctuary **139**, Vol I path **117**,
  Vol I minimal **70**, Vol II path **87**, Vol III path **88**. All would FAIL this gate.
- **Print-ready:** ≥ 300 DPI at 6.25 × 9.25; full-bleed, no white edges; no critical
  content in the 0.25 in bleed margin.
- **Anatomy/face sanity:** no distorted hands, faces, wings, or limbs; eagle and figures
  read correctly.
- **Thumbnail test:** legible and compelling scaled to **~300 px tall** (Amazon size) — the
  #1 retail requirement.
- **Title zone:** upper third calm enough for the title overlay to sit legibly (add a
  scrim only if needed).
- **Palette fidelity:** warm golden devotional feel; not cold, garish, or muddy.
- **Clean:** no baked text, no watermark, no stray artifacts, no accidental logos.
- **Brief fit:** unmistakably a warm Christian devotional, not generic stock or a travel
  poster.

Write results to `covers/qualification.json` (one record per image: path, seed, checks,
pass/fail, notes).

---

## 5. Ranking engine (confidence + rationale)

For every PASS image, compute a **Confidence 0–100** = weighted rubric:

| Criterion | Weight | What it measures |
|---|---:|---|
| Genre fit | 30 | Reads instantly as a warm Christian devotional in Lady D's world |
| Thumbnail clarity | 25 | Distinct, legible, and pulling at ~300 px |
| Fidelity to brief | 25 | Golden-hour, hopeful, surrender-to-love feel; her motifs done well |
| Visual distinction | 20 | Stands apart; not a stock cliché; memorable |

- Pick the **best variation per direction** → ten finalists.
- Rank the ten by confidence; write a one-sentence **rationale** for each (like the Joyce
  deck: name the specific strength and any reservation).
- Record everything in `covers/ranking.json`. Ranks and scores are **derived from the real
  images**, never assigned before generation.

---

## 6. Decision deck (build the page Lady D chooses from)

Build an interactive selection deck modeled on the Joyce
`matched-cover-prompt-pack-v3` page, reusing the visual language of
`Lady-D-Cover-Design-Studio.html`:

- A **main stage** showing the currently-selected cover large (real PNG), with its
  editorial note, **Confidence xx/100**, **Rank #n**, and **Shortlist** + **Download PNG**.
- A **1–10 selector** and a **"Compare Every Cover"** grid of all ten real thumbnails.
- A **Ranking & Comparison table**: Rank | Cover | Confidence | Rationale.
- A **shortlist** with **Copy Selection** (so Lady D can send back her picks).
- One line stating the rubric ("Confidence reflects genre fit, visual distinction,
  thumbnail clarity, and fidelity to Lady D's brief").
- Warm golden theme, light + dark, no horizontal overflow, self-contained.

Save as `lady-d-cover-deck.html` and deploy to the Lady D review site alongside the other
pages. Verify with Playwright/headless: all 10 real images load, no broken assets, no
console errors, deck works at mobile + desktop.

---

## 7. Winner assembly (after Lady D shortlists — or prepare top-3 in advance)

For each shortlisted direction, produce the **matched trilogy set**:

- Apply the winning direction to **all three volumes** (same art language, each volume's
  light/lane and accent), so they read as a family on a shelf.
- Build the **full wraparound** per volume at print spec: front + **spine** (wine, gold
  script: "*Title* · Susan Damon"; width from final interior page count via the KDP
  calculator) + **back cover** carrying **Lady D's poem** (below) and the ISBN barcode
  (2 × 1.2 in clear zone) + publisher mark.
- Deliver per volume: **front (ebook)**, **full wrap (print, CMYK-safe)**, and a **3D
  render**.

**Lady D's back-cover poem (verbatim):**
> Sometimes we don't see how deeply we are loved.
> Sometimes we settle for less than what we deserve.
> But when you surrender to **GOD'S LOVE**, you will never settle again.
> You'll walk in your worth, live in your purpose, and become everything **HE** created you to be.
> — Susan "Lady D" Damon

---

## 8. Evidence discipline (arch — nothing crosses a gate on claims alone)

- Keep **every** raw render (don't discard rejects) plus `qualification.json`,
  `ranking.json`, and a top-level `covers/manifest.json` (each image: direction, seed,
  params, sha256, qualification result, confidence, rank, final filename).
- A cover is **`generated` → `qualified` → `ranked` → `shortlisted` → `final`**. Only move a
  cover to `final` after the wraparound is built AND Lady D has shortlisted it. Never label
  a render "selected" on your own judgment.
- The deck must be built from the **real** PNGs; if any image is a placeholder, mark it
  `unverified` and say so — do not present a mockup as generated art.

---

## 9. Definition of done

- [ ] 10 directions × 3 variations generated for Volume I, all captured.
- [ ] Every image passed the qualification gate (or was regenerated); results logged.
- [ ] Ten finalists ranked with confidence scores + rationale.
- [ ] `lady-d-cover-deck.html` built (real images), deployed, and browser-verified.
- [ ] Top-3 (or Lady D's shortlist) rendered as matched trilogy wraparounds with her poem,
      spine, and ISBN zone at 300 DPI print spec.
- [ ] `covers/manifest.json` complete with hashes and status per image.
- [ ] A short report: what was generated, the ranking, and the exact link to the deck.

---

## 10. Kickoff line (first message to Codex)

> Read `/Users/IDC2.5/Documents/LADY D/_synthesis-2026-07-19/Lady-D-Cover-Codex-Handoff.md`
> and execute it end to end: generate the ten cover directions (3 variations each) for
> *Surrendering to God's Love* using your image tool, run the qualification gate, rank them
> with confidence scores and rationale, build the `lady-d-cover-deck.html` selection deck
> from the real images (modeled on the Joyce matched-cover deck), deploy it to the Lady D
> review site, and prepare the top-3 as matched trilogy wraparounds with Lady D's poem,
> spine, and ISBN. Keep a hashed manifest; mark nothing "final" until the deck is built
> from real renders. Report back with the deck link and the ranking table.
