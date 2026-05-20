# Session notes — exit plan, not for publication

> This file lives in `_session-notes/` with an underscore prefix so neither Jekyll nor Quarto will render or publish it. It's a private working file. Move or delete whenever.

**Last updated:** 2026-05-20 (writing samples polish session — visual design, SVGs, clinical accuracy fixes)

---

## The situation, in one paragraph

Jodie is a teaching-track associate professor (career-track, full-time faculty, no tenure). Severe burnout, with a prior FMLA episode that disabled her for a full semester. Less than 1 month of cash runway, plus a $10k summer contract for a course rebuild ($5k end of July, $5k end of August) — paid work she actually enjoys, mostly solo. **Medical leave is off the table** — second FMLA in academia would be career-ending and she's not willing to pay that cost. **No fall teaching is a hard line.** Real timeline: out of teaching before mid-August (~3.5 months from 2026-05-07). Destination: as far from academia as possible — industry, ed-tech, foundation, or biotech. Not another academic role.

---

## What's been decided

- **Destination is non-academic.** Industry, ed-tech, foundation, or biotech. Another academic role is NOT on the table. Don't suggest academic alternatives.
- **No medical leave.** Second FMLA in her field would be career-ending and she's not willing to pay that cost. Don't suggest leave or "have you considered FMLA" — that conversation is closed.
- **No fall teaching.** Hard line. Exit must be in motion by ~mid-August 2026.
- **Primary near-term income path:** senior medical writer / scientific content roles (genomics-focused biotech, CROs, comms agencies). Existing portfolio is already strong enough for this market — can pitch this week.
- **Secondary path being built:** scientific data analysis / analytics-translator / curriculum-architect roles. Wider market, higher ceiling, requires 1–2 published data analysis samples on the Quarto site.
- **Voice:** the Quarto site case studies are in the right voice (direct, dry, specific numbers, no corporate-speak). The genomics writing samples in `samples/` are NOT in her voice and need to be rewritten — deferred but real.
- **Data ethics constraint:** no use of student-level institutional data for portfolio work, even de-identified. Public datasets only. Aggregate numbers already published in existing case studies (e.g., 39% → <5% DFW rate) are fine to reuse.
- **Money picture:** <1 month cash now. $10k summer contract bridges through end of August in two installments. Open question still: 9-month vs. 12-month appointment — does regular salary continue through summer?

---

## What's been built

### Session 1 (2026-05-07)
- **`quarto/work/stem-completion-equity-analysis.qmd`** — full case-study scaffold, public IPEDS data, ready to fill in with real analysis when energy allows.
- **`quarto/work/_general-genetics-outcomes-analysis.qmd`** — earlier scaffold using institutional data; renamed with `_` prefix so Quarto won't render it. Kept as a private draft, not published. Don't pursue without IRB / departmental sign-off.

### Session 3 (2026-05-20) — writing samples visual polish

**All three writing samples in `quarto/samples/` substantially redesigned visually and fixed for clinical accuracy.** Summary of what changed:

**`scientific-content-review.qmd`**
- New issue #1 inserted: ACMG/AMP variant classification orientation slide (dark-background pill design, one row per tier, VUS as accent-bordered standout, `data-tier` attributes for animation). Existing issues renumbered 2–5.
- Duplicate "Medical communications" skill pill removed.
- Dek updated to "Five issues identified. Four required revision; one addition recommended."
- Issue #3 (VUS recontact language): fixed clinical accuracy — passive "recontact is appropriate" replaced with explicit patient-initiates direction ("they should follow up with their ordering provider or genetic counselor to check on any VUS result that is more than one to two years old"). Labs do not reliably proactively recontact patients.
- Issue #4 (somatic/germline): recommended revision text replaced with a two-panel dark slide mockup — somatic side (amber, 2/6 cells with mutation markers) vs. germline side (blue, all 6 cells), plus key-takeaway footer bar.
- Richards et al. 2015 (ACMG/AMP framework paper) added as first reference.
- Pull-quote and summary updated to reflect five issues.

**`patient-advocate-explainer.qmd`**
- Dense first paragraph broken into three inline SVG visuals:
  1. DNA→protein flow (nucleus, two-strand DNA zigzag with rungs, arrow, protein as connected circles)
  2. Variant comparison (two 5-base sequences in colored blocks, changed base highlighted with dark border and "variant" label)
  3. Chromosome illustration — expanded from 185px to 455px height to include:
     - Top: detailed G-band-style chromosome with 7 coding bands of varying widths, clipPath pill, centromere, legend
     - Bottom: full karyotype of all 23 chromosome pairs (24 types: 1–22, X, Y) as solid warm-gray bars scaled to approximate real chromosome sizes, bottom-aligned per row, mtDNA note
- "Understanding your results" section: variant classifications redesigned with dark pill rows matching the scientific-content-review treatment (3 patient-appropriate categories: pathogenic/LP in red, VUS as blue standout, likely benign/benign in green).
- Draft working notes (Jodie's unpublished text) cleaned up.

**`clinician-brief.qmd`** — back link updated only.

**`index.qmd` (samples index)**
- Back links on all three samples changed from "← All work" to "← Writing samples" pointing to `index.html`
- "← All work" added to samples index pointing to `../work/index.html`
- Teaser text for scientific-content-review updated (was "four issues identified, three requiring revision")

**Visual design system established in `samples/`:**
- Dark-background pill rows: container `#1A1815`, standard rows `#2A2720`, VUS/standout `#1E2238` with `border: 2px solid #4a56c4`
- Each pill row has `data-tier` attribute — ready for CSS/JS animation if desired
- SVG palette: accent `#4a56c4`, ink `#2D2A24`, muted `#7E7567`, cream `#FAF6EE`, warm gray `#8A8078` (karyotype bars), base colors for nucleotides: A=#C07840, T=#4a56c4, G=#5C8870, C=#B85450

---

### Session 2 (2026-05-11) — async work by Claude
**The IPEDS analysis is now substantially complete.** Here's what was built:

**Data downloaded** (in `quarto/work/ipeds-data/`):
- IPEDS Completions (C_A) files: 2013, 2015, 2016, 2017 (extracted CSVs)
- IPEDS Institutional Characteristics (HD): 2022
- Note: 2014 C_A file is truncated at row 253,038 — excluded from analysis, documented in the writeup

**Analysis scripts** (in `quarto/work/`):
- `ipeds_analysis.py` — loads, filters, and aggregates the raw IPEDS CSVs; outputs processed CSVs to `ipeds-figures/`
- `make_charts.py` — generates all four publication-quality charts

**Figures generated** (in `quarto/work/ipeds-figures/`):
- `fig1_stem_share_trend.png` — STEM share of all bachelor's by race/ethnicity, 2013–2017
- `fig2_stem_growth_indexed.png` — Indexed growth in STEM bachelor's counts (2013=100)
- `fig3_field_breakdown.png` — Black and Hispanic share by STEM field, 2013 vs. 2017
- `fig4_sector_breakdown.png` — STEM share by institution control type (public vs. private nonprofit)

**Case study updated** (`quarto/work/stem-completion-equity-analysis.qmd`):
- All placeholders replaced with real findings and real charts
- Real code blocks showing the actual methodology
- Findings sections written in portfolio voice (direct, specific numbers)
- Data quality issues documented honestly (2014 truncation, HD vintage mismatch)

**Work index updated** (`quarto/work/index.qmd`):
- IPEDS case study card added, links to the live page

**Key findings from the analysis:**
1. The STEM share gap is persistent and slightly widening: Black students earn 6.4% of their bachelor's in STEM (2017) vs. 9.9% for White — gap grew from 2.9 pp to 3.5 pp over 2013–2017
2. Hispanic STEM completions grew 56% over the window (fastest of any group) but started from a lower base; STEM share still below White in 2017
3. Computer science is where Black representation declined while the field boomed: 10.7% → 8.4% as CS added ~20K degrees/year
4. Biology is the most diverse major STEM field; Hispanic share in bio reached 13.1% by 2017
5. Public institutions show ~1–1.5 pp higher STEM shares across all groups vs. private nonprofit, but the relative ordering and gap size are similar in both sectors

---

## What still needs to happen to fully publish the IPEDS analysis

**Decision Jodie needs to make:**
- Review the case study page and decide if findings/voice feel right before linking it live. The page renders correctly; it just isn't being promoted anywhere yet beyond the work index.

**Data extension (1–3 hours, mostly waiting for downloads):**
- Download IPEDS C_A files for 2018–2022 (fix the 2014 file too) to extend trend to a full decade. The download script is at `quarto/work/ipeds_analysis.py` — re-run with `YEARS = range(2013, 2024)` after downloading the zips from `https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx`. Files needed: `C2018_A.zip` through `C2023_A.zip`.
- Note: Downloads timed out in the sandbox environment. On a regular laptop with normal internet: each zip is ~7–8 MB and should download in seconds. The analysis pipeline is fully built; adding more years is just adding files and rerunning.

**Minor fixes if desired:**
- The 2022 HD file is used for institution sector (public/private). It's stable but if precision matters, downloading matching-year HD files (e.g., HD2017) would be cleaner.
- Chart 3 (field breakdown) uses 2013 and 2017 as the bookend years. Extending to 2022 would make the trend arc more compelling.

---

## Role-target diagnostic (added 2026-05-07 revision)

Jodie articulated this clearly. Don't re-derive it next session — feed it back to her if needed.

**The constraint set — features the next role can't have:**
- Customer-service dynamics with large groups of disengaged people trying to extract grades
- Performance evaluation systems that punish gender, rigor, or active pedagogy (SSI scores and cousins)
- Institutions that create bad upstream conditions and blame the workers (the AI-in-education example was sharp)
- Surrounded by people who perform caring without practicing it
- High-volume reactive communication, ~90% non-substantive
- Being "on" all day in front of people
- Pay structure that rewards everything except what she's best at

**The design specs — features the next role needs:**
- Remote
- Small team (2–6, not 50)
- Some consistent collaborative ideation meetings, but few of them
- 2–3 parallel projects so she can switch when stuck or bored
- Heads-down deep thinking as the dominant mode
- Restructuring things that don't work — she specifically named that as "hard and fun"
- Working with people who actually care, and where any audience has *opted in*

**Five role categories that match the spec (presented to her, awaiting her pick):**

1. **Curriculum / learning architect at biology-focused ed-tech** — HHMI BioInteractive, Labster, Outlier, Brilliant, Coursera, Khan Academy. ~$90–140K, often fully remote. Best match for "restructuring broken systems" + "motivated learners who opted in."
2. **Senior medical writer at genomics / biotech** — Illumina, Tempus, Natera, GeneDx, Color, 23andMe Therapeutics, Invitae, plus smaller startups. ~$110–160K. Existing portfolio already qualifies — pitchable this week.
3. **Education researcher at a science foundation** — HHMI, Burroughs Wellcome, Sloan, Simons, Gates (life sciences). ~$90–140K. Mission-aligned, very small teams, work that actually changes things.
4. **Computational biologist / scientific data analyst at a biotech** — Ginkgo, Recursion, Insitro, Tempus, Octant, Vant. ~$110–170K. Heads-down data work. Requires more portfolio buildout.
5. **Real-world evidence / health outcomes researcher** — pharma RWE teams, CROs, or specialized firms (Aetion, Komodo, Truveta). ~$120–160K.

**What she explicitly said she loved (positive design data):** her postdoc; Thursday small-group sessions with ~2–6 motivated young women working through homework and content together; data analysis during her PhD; the challenge of completely restructuring General Genetics. *Pattern: small, motivated groups; deep solo intellectual work; building/fixing systems.*

---

## Highest-leverage next moves (updated 2026-05-11)

1. **Pick the top 1–2 role categories** from the five above. This shapes everything that follows — target list, portfolio polish, sample priorities. Even a soft lean is enough to start with.
2. **Confirm the appointment structure** — 9-month or 12-month? Determines whether summer cash flow is a gap or not. (If 9-month, last paycheck is ~end of May and the $10k contract is the only summer income.)
3. **Start pitching senior medical writer roles this week** with the existing portfolio. Don't wait for anything else. Path #2 above is pitchable right now.
4. **Review and optionally publish the IPEDS case study** — it's substantially complete. You can either: (a) publish it as-is with 2013–2017 data and a note that the analysis extends to 2023 when downloads complete, or (b) download the remaining years first (see instructions above) and publish a full-decade version. Either is defensible.

---

## Things ready to start when Jodie returns

Pick whichever matches the energy level of the day.

### A. ✅ IPEDS analysis — DONE (mostly)
Built in Session 2. Needs Jodie's review + decision to publish. See above for the remaining download step if she wants the full decade.

**Prompt to paste if extending to 2023:** *"Read `_session-notes/next-steps.md`, then help me download the remaining IPEDS years and extend the analysis to 2023."*

### B. ✅ Polish the genomics writing samples — DONE (mostly)
Visual redesign and clinical accuracy fixes completed in Session 3. The samples are visually strong — dark pill designs, inline SVGs, correct clinical language. What's still open:
- **Voice rewrite**: the prose in all three samples still reads more corporate/formal than Jodie's natural voice in the case studies. The structure is right; the tone hasn't been touched yet. Low priority if the portfolio is performing, but worth one more pass before pitching heavily.

**Prompt to paste if doing the voice pass:** *"Read `_session-notes/next-steps.md`, then help me rewrite the genomics samples in my real voice — the structure and visuals are set, just the prose tone needs work."*

### C. Build the target employer list
Once she's picked her top 1–2 role categories, draft a list of 15–20 specific employers — real names, current openings where findable, with notes on which to prioritize and why. Tailored to her constraint set (remote, small team, opted-in audience, no customer-service dynamics).

**Prompt to paste:** *"Read `_session-notes/next-steps.md`, then build the target employer list for [category]."*

### D. Draft a senior medical writer pitch package
Cover letter / outreach template + LinkedIn-ready blurb + a short "writing sample tour" intro for the existing portfolio pieces. Designed so she can send 5–10 outreach messages this week with the portfolio she already has.

**Prompt to paste:** *"Read `_session-notes/next-steps.md`, then help me put together a medical writer pitch package."*

---

## Things deliberately deferred

- Target list of 15–20 specific employers/roles to apply to (offered, not yet built — easy to do once portfolio is set or the voice rewrite is done).
- Phylogenetics / sequence-analysis sample (option 2 from earlier brainstorm). Lower priority than the IPEDS piece for now.
- ClinVar / variant trends sample. Same — interesting, but not the fastest path given current energy.
- A standalone "Safe Evolution" case study that `work/index.qmd` already mentions as queued. Jodie's call when/whether to build it.

---

## A note for whoever is reading this

If you're Claude in a future session — Jodie is exhausted, has been here before, and what she needs from you is calm, concrete, low-cognitive-load progress. Don't rebuild the plan from scratch. Don't oversell. Don't pile on options. Pick the one thing she asked for and do it well. **Specifically: do not suggest medical leave, FMLA, "have you considered staying," or another academic role. All of those conversations are closed.** The destination is non-academic, the timeline is mid-August, the constraint set in the diagnostic section above is real and hard-won — use it.

If you're Jodie — the IPEDS analysis is done. The case study is written and linked from the work index. The charts are real data. The findings section uses specific numbers and says something concrete. You can publish it today with the 2013–2017 window and a note about extending it, or you can spend an hour downloading the remaining years first. Either is a good call — what's not useful is leaving it as a scaffold indefinitely. The portfolio needed a data analysis piece and now it has one.
