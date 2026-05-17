# IPEDS STEM Completion Equity Analysis

Analysis supporting the case study at `quarto/work/stem-completion-equity-analysis.qmd`.

---

## Directory structure

```
ipeds/
├── README.md               ← this file
├── ipeds_analysis.py       ← loads, filters, and aggregates raw data (IPEDS CSVs)
├── make_charts.py          ← generates figures
├── data/                   ← raw IPEDS files (not committed to git if large)
│   ├── c2013_a.csv         ← IPEDS Completions, 2013 (extracted from zip)
│   ├── c2014_a.csv         ← IPEDS Completions, 2014 — TRUNCATED, excluded from analysis
│   ├── c2015_a.csv         ← IPEDS Completions, 2015
│   ├── c2016_a.csv         ← IPEDS Completions, 2016
│   ├── c2017_a.csv         ← IPEDS Completions, 2017
│   ├── C2016_A.zip         ← original zip (retained; CSV extracted from this)
│   ├── C2017_A.zip         ← original zip (retained; CSV extracted from this)
│   ├── hd2022.csv          ← IPEDS Institutional Characteristics, 2022
│   ├── c2022_a.xlsx        ← Completions data dictionary (downloaded separately — see below)
│   └── hd2022.xlsx         ← HD data dictionary (downloaded separately — see below)
└── figures/
    ├── fig1_stem_share_trend.png       ← STEM share by race/ethnicity, 2013-2017
    ├── fig2_stem_growth_indexed.png    ← Indexed growth in STEM bachelor's
    ├── fig3_field_breakdown.png        ← Black & Hispanic share by STEM field
    ├── fig4_sector_breakdown.png       ← STEM share by institution control type
    ├── stem_annual.csv                 ← aggregated STEM counts by year (analysis output)
    ├── total_annual.csv                ← aggregated total bachelor's by year (denominator)
    ├── sector_share.csv                ← STEM share by year and control type
    └── field_df.csv                    ← STEM degree counts/shares by field, 2013 & 2017
```

The QMD (`../stem-completion-equity-analysis.qmd`) generates the public page. It references figures as `ipeds/figures/fig*.png` (where the * is the figure number) relative to `quarto/work/`. Scripts use `os.path.dirname(__file__)` to locate `data/` and `figures/` relative to themselves, so they run correctly from any working directory.

---

## Data sources
**Base IPEDS data URL:** `https://nces.ed.gov/ipeds/use-the-data`

### IPEDS Completions survey (C_A files)
**URL:** `https://nces.ed.gov/ipeds/datacenter/data/C{YEAR}_A.zip`  
**Example:** `https://nces.ed.gov/ipeds/datacenter/data/C2022_A.zip`

Each zip contains two files:
- `c{year}_a.csv` — the data file (~50–60 MB uncompressed)
- `c{year}_a_rv.csv` — the revised version of the same data (minor corrections post-release)

**Important:** The URL has no underscore before the year and no trailing underscore — `C2022_A.zip`, not `C_2022_A_.zip`. This was confirmed by HEAD request after 404 errors on the wrong format.

### IPEDS Institutional Characteristics (HD files)
**URL:** `https://nces.ed.gov/ipeds/datacenter/data/HD{YEAR}.zip`  
**Example:** `https://nces.ed.gov/ipeds/datacenter/data/HD2022.zip`

Contains one record per institution with sector, Carnegie classification, control type (public, private (nonprofit/for-profit)), location, etc.

### Data dictionaries
Dictionaries are **separate downloads** — they are not included in the data zips. The URL pattern is:

- Completions: `https://nces.ed.gov/ipeds/datacenter/data/C{YEAR}_A_Dict.zip`
- HD: `https://nces.ed.gov/ipeds/datacenter/data/HD{YEAR}_Dict.zip`

When extracted, the files are named without `_dict` — `c2022_a.xlsx` and `hd2022.xlsx` respectively. Both are already downloaded and in `data/`.

Each dictionary Excel file has the following sheets:
- **varlist** — one row per variable: variable name, data type, field width, and short title. Quick reference.
- **Description** — full variable definitions including code labels. This is the sheet to use for looking up what a value means.
- **Frequencies** — value counts from the actual data
- **Statistics** — summary stats for continuous variables
- **Introduction** — survey overview and file documentation

The dictionaries were consulted after the initial analysis to verify variable meanings (see below).

---

## How the schema was inferred (and where it was wrong)

### What was done
The schema was not read from the data dictionary. Instead, the first few rows of each file were loaded and inspected directly:

```python
df = pd.read_csv(path, nrows=5, encoding='latin1')
print(list(df.columns))
print(df.head(3).to_string())
```

This produced the actual column names and sample values, from which the following was inferred:

| Variable | Inferred meaning | Basis |
|---|---|---|
| `AWLEVEL` | Award level (degree type) | Values 1–19 visible in data; 5 appeared for institutions clearly awarding bachelor's degrees |
| `MAJORNUM` | First or second major | Values 1 and 2 only; semantically obvious |
| `CIPCODE` | CIP field code (6-digit) | Recognizable format (e.g., `14.0101` = engineering) |
| `CTOTALT` | Total completions | Column name pattern; "T" suffix = total, "M" = male, "W" = female across all demographic columns |
| `CBKAAT` | Black/African American total | Prefix `C` = completions, `BKAA` = Black/African American, `T` = total |
| `CHISPT` | Hispanic total | `HISP` = Hispanic |
| `CASIAT` | Asian total | `ASIA` = Asian |
| `CWHITT` | White total | `WHIT` = White |
| `CAIANT` | American Indian/Alaska Native | `AIAN` = AIAN |
| `CNHPIT` | Native Hawaiian/Pacific Islander | `NHPI` = NHPI |
| `C2MORT` | Two or more races | `2MOR` = two or more races |
| `CNRALT` | Nonresident alien | `NRAL` = nonresident alien |
| `CUNKNT` | Race unknown | `UNKN` = unknown |

The `X`-prefixed versions of each column (`XCTOTALT`, `XCBKAAT`, etc.) are imputation flags. Values include `R` (reported), `Z` (zero — not imputed, genuinely zero), and `A` (withheld for privacy). These were not used in the analysis; the count columns were used directly, with non-numeric values coerced to 0.

**Dictionary verification (post-analysis):** All variable name inferences above were confirmed against `c2022_a.xlsx` (Description sheet). The official variable titles match the inferred meanings exactly. `AWLEVEL=5` for bachelor's degrees was also confirmed — the Description sheet lists award levels in order, with bachelor's degree as the 6th entry, corresponding to code 5. The `CONTROL` codes for HD were confirmed as 1 = Public, 2 = Private not-for-profit, 3 = Private for-profit.

The official IPEDS racial/ethnic definitions (from the Description sheet, relevant if the analysis writeup gets more precise):
- **Hispanic or Latino** — a person of Cuban, Mexican, Puerto Rican, South or Central American, or other Spanish culture or origin, *regardless of race*
- **Black or African American** — a person having origins in any of the black racial groups of Africa
- **Asian** — a person having origins in any of the original peoples of the Far East, Southeast Asia, or the Indian Subcontinent
- **American Indian or Alaska Native** — a person having origins in any of the original peoples of North and South America (including Central America) who maintains cultural identification through tribal affiliation or community attachment
- **Native Hawaiian or Other Pacific Islander** — a person having origins in any of the original peoples of Hawaii, Guam, Samoa, or other Pacific Islands
- **White** — a person having origins in any of the original peoples of Europe, the Middle East, or North Africa

### Where the initial inference was wrong: Carnegie classification

The first attempt at Carnegie stratification used a hand-written mapping of `C21BASIC` codes (the 2021 Carnegie Basic Classification variable in HD2022) that was incorrect. The mapping assumed:
- Codes 10–12 = Baccalaureate colleges
- Codes 13–15 = Master's universities
- Codes 16–19 = Doctoral universities

The actual coding in the HD2022 file is:
- Codes 1–9 = Associate's colleges
- Code 10 = Baccalaureate/Associate's mixed (Associate's dominant)
- Code 11 = Doctoral: Very High Research Activity (R1)
- Code 12 = Doctoral: High Research Activity (R2)
- Code 13 = Doctoral/Professional
- Codes 14–16 = Master's (large/medium/small programs)
- Codes 17–19 = Baccalaureate colleges
- Codes 20+ = Special focus and tribal

The incorrect mapping produced nonsensical results (e.g., 50% STEM share at "Doctoral" institutions in some years, 0% in others). The mapping was revised after inspecting the actual distribution of `C21BASIC` values in the data.

**However, even with the corrected mapping, Carnegie-stratified results were dropped from the final analysis.** The reason: HD2022 Carnegie codes were merged onto 2013–2017 completions data. Carnegie classification can change as institutions grow or shift mission; using 2022 codes for 2013 behavior introduces misclassification that's difficult to quantify. Institution *control type* (public / private nonprofit / for-profit), stored in the `CONTROL` column, is stable over time and was used for sector stratification instead.

---

## Data quality issues encountered

### 2014 file truncation
The `c2014_a.csv` file produced a `pandas.errors.ParserError: EOF inside string starting at row 253,038` when loaded with the C parser. Switching to `engine='python'` with `on_bad_lines='skip'` allowed the file to load but produced a dataset covering only ~2,014 institutions — compared to ~2,600–2,800 for every other year. This ~28% reduction in institution coverage would introduce a systematic downward bias in all count-based measures for 2014 if included.

**Resolution:** 2014 is loaded by the script (so its presence can be verified) but excluded from all trend analyses via `EXCLUDE_YEARS = [2014]`. The issue is documented in the case study writeup. The 2014 zip file should be re-downloaded from NCES to get a complete copy.

### HD vintage mismatch
Institutional characteristics come from HD2022 but completions data runs 2013–2017. This means any institution that changed control type (public → private or vice versa) between 2013 and 2022 would be misclassified. Control type changes are rare; the sector analysis is treated as approximate, not exact.

---

## To reproduce or extend the analysis

### Requirements
```
pip install pandas matplotlib numpy
```

### Run order
```bash
cd quarto/work/ipeds
python ipeds_analysis.py   # produces processed CSVs in figures/
python make_charts.py      # produces PNG figures in figures/
```

### To extend to 2018–2023
1. Download additional C_A zips from `https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx` (navigate to Completions → Complete Data Files)
2. Extract the CSVs into `data/`
3. In `ipeds_analysis.py`, update the year range: `YEARS = range(2013, 2024)`
4. Also consider re-downloading 2014 to replace the truncated file
5. Re-run both scripts

### To get a matching HD file for a specific year
Download `HD{YEAR}.zip` from the same NCES page and update the HD load path in `ipeds_analysis.py`. Using a year-matched HD file removes the vintage mismatch noted above.

---

## STEM CIP definition

Uses the NSF STEM-designated degree program list (2-digit CIP families):

| CIP | Field |
|---|---|
| 03 | Natural Resources & Conservation |
| 11 | Computer & Information Sciences |
| 14 | Engineering |
| 15 | Engineering Technologies |
| 26 | Biological & Biomedical Sciences |
| 27 | Mathematics & Statistics |
| 40 | Physical Sciences |
| 41 | Science Technologies |

Health professions (CIP 51) are explicitly excluded. Including them shifts the gendered patterns substantially (health professions skew heavily female) and modestly shifts the racial/ethnic patterns.

The NSF list is publicly available as a PDF/spreadsheet; the 2-digit families above are a simplification. A more precise implementation would use the full 6-digit CIP crosswalk, which would exclude some programs within these families (e.g., not all CIP 03 programs are STEM-designated).
