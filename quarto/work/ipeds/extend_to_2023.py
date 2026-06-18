#!/usr/bin/env python3
"""
extend_to_2023.py
=================
Downloads IPEDS completions data for 2018–2023, re-runs the equity
analysis, and regenerates all four figures.

Run from the ipeds/ directory:
    python extend_to_2023.py

Requires: pandas, numpy, matplotlib, requests
    pip install pandas numpy matplotlib requests

────────────────────────────────────────────────────────────────
TROUBLESHOOTING LOG — what broke and why, so you don't redo it
────────────────────────────────────────────────────────────────

PROBLEM 1: Wrong download URL
  First attempt used: https://nces.ed.gov/ipeds/data/zip/c{year}_a.zip
  All years returned HTTP 404. NCES moved their file hosting.
  Fix: correct base path is /ipeds/datacenter/data/, not /ipeds/data/zip/
  Working URL: https://nces.ed.gov/ipeds/datacenter/data/C{year}_A.zip
  Confirmed via HEAD request before writing the downloader.

PROBLEM 2: Column name casing varies by year
  Files from 2013–2017 (downloaded earlier) use lowercase filenames
  (c2013_a.csv, c2015_a.csv, etc.). Files from 2018–2023 use uppercase
  (C2018_A.csv, C2019_A.csv, etc.). Both sets have uppercase column
  names inside, BUT passing usecols=NEEDED_COLS directly still fails
  on some years because pandas is strict about exact matches.
  Fix: peek at headers first with nrows=0, build a case-insensitive
  lookup dict (upper_map), and resolve the actual column names before
  calling read_csv with usecols.

PROBLEM 3: C2016_A is a directory, not a file
  The data/ directory contains a folder called C2016_A (leftover from
  a manual unzip of C2016_A.zip). os.path.exists('C2016_A.csv') returns
  False for the directory because the name doesn't match exactly, so
  this was not the direct cause of failures — but os.path.isfile() was
  added defensively to the filename search loop to prevent any future
  case where a directory name collides with a filename we're looking for.

PROBLEM 4: 2014 file is truncated — causes ParserError mid-read
  The c2014_a.csv file hits EOF inside a quoted string at row 253,038.
  pandas' C parser raises ParserError even with on_bad_lines='skip'
  because the error occurs at the tokenizer level, before bad-line
  handling kicks in.
  Fix: catch pd.errors.ParserError (in addition to TypeError) and fall
  back to engine='python', which handles the truncation more gracefully
  and skips the bad rows. The recovered file covers ~2,014 institutions
  vs ~2,600–2,800 for complete years, so 2014 is excluded from all
  trend analyses (EXCLUDE_YEARS = [2014]).

PROBLEM 5: pandas version mismatch — on_bad_lines vs error_bad_lines
  on_bad_lines='skip' was added in pandas 1.3.0 (2021). The user's
  environment runs Python 3.8 with an older Anaconda pandas that uses
  error_bad_lines=False / warn_bad_lines=False instead.
  Fix: try on_bad_lines first; catch TypeError (raised when the kwarg
  is unrecognised) and fall back to the old API.

PROBLEM 6: C2023_A.csv has a UTF-8 BOM on the first column
  The 2023 file starts with the byte sequence EF BB BF (UTF-8 BOM),
  which makes the first column name appear as '﻿UNITID' instead of
  'UNITID' when read with encoding='latin1'. The upper_map lookup then
  fails to find 'UNITID', the column is silently dropped from usecols,
  and subsequent df['UNITID'] references raise KeyError.
  Fix 1: try utf-8-sig encoding in the header peek (utf-8-sig strips
          the BOM automatically).
  Fix 2: also call .str.lstrip('﻿') on column names as a belt-and-
          suspenders guard in case the BOM survives encoding handling.
  Fix 3: use encoding='utf-8-sig' when reading 2023 data (year >= 2023).
  Note: earlier years must stay on latin1 — they contain characters
  (e.g. accented institution names) that are not valid UTF-8.
"""

import io, os, sys, zipfile
import warnings
warnings.filterwarnings('ignore')

import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FIG_DIR  = os.path.join(BASE_DIR, "figures")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIG_DIR,  exist_ok=True)

# ── Constants (unchanged from original analysis) ───────────────────────────────
STEM_CIP_2DIGIT = {
    '03': 'Natural Resources & Conservation',
    '11': 'Computer & Information Sciences',
    '14': 'Engineering',
    '15': 'Engineering Technologies',
    '26': 'Biological & Biomedical Sciences',
    '27': 'Mathematics & Statistics',
    '40': 'Physical Sciences',
    '41': 'Science Technologies',
}

DEMO_COLS = {
    'CTOTALT': 'Total',
    'CAIANT':  'American Indian / AK Native',
    'CASIAT':  'Asian',
    'CBKAAT':  'Black / African American',
    'CHISPT':  'Hispanic',
    'CNHPIT':  'Native Hawaiian / Pacific Islander',
    'CWHITT':  'White',
    'C2MORT':  'Two or More Races',
    'CNRALT':  'Nonresident Alien',
    'CUNKNT':  'Race Unknown',
}

NEEDED_COLS = ['UNITID', 'CIPCODE', 'MAJORNUM', 'AWLEVEL'] + list(DEMO_COLS.keys())

FOCUS_GROUPS = {
    'CBKAAT': 'Black / African American',
    'CHISPT': 'Hispanic',
    'CASIAT': 'Asian',
    'CWHITT': 'White',
}

COLORS = {
    'Black / African American': '#C0392B',
    'Hispanic':                  '#E67E22',
    'Asian':                     '#2980B9',
    'White':                     '#7F8C8D',
}

ALL_YEARS     = list(range(2013, 2024))   # 2013–2023
EXCLUDE_YEARS = [2014]                    # truncated file, see original analysis
ANALYSIS_YEARS = [y for y in ALL_YEARS if y not in EXCLUDE_YEARS]

# COVID window — shade on time-series charts
COVID_START, COVID_END = 2019.5, 2021.5

plt.rcParams.update({
    'font.family':       'sans-serif',
    'font.sans-serif':   ['Helvetica Neue', 'Arial', 'DejaVu Sans'],
    'font.size':         11,
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'axes.linewidth':    0.8,
    'axes.edgecolor':    '#CCCCCC',
    'xtick.color':       '#555555',
    'ytick.color':       '#555555',
    'text.color':        '#333333',
    'figure.facecolor':  'white',
    'axes.facecolor':    'white',
    'grid.color':        '#EEEEEE',
    'grid.linewidth':    0.6,
})


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Download new IPEDS completions files (2018–2023)
# ══════════════════════════════════════════════════════════════════════════════
# TROUBLESHOOTING 1: URL path
# First attempt used /ipeds/data/zip/ — all years returned 404.
# The correct NCES path is /ipeds/datacenter/data/.
# Two patterns handle the capitalisation difference across years.
URL_PATTERNS = [
    "https://nces.ed.gov/ipeds/datacenter/data/C{year}_A.zip",
    "https://nces.ed.gov/ipeds/datacenter/data/c{year}_a.zip",
]

def download_year(year):
    target = os.path.join(DATA_DIR, f"C{year}_A.csv")
    if os.path.exists(target):
        size = os.path.getsize(target)
        print(f"  {year}: already present ({size/1e6:.1f} MB), skipping")
        return True

    for pattern in URL_PATTERNS:
        url = pattern.format(year=year)
        try:
            print(f"  {year}: fetching {url} ...", end=" ", flush=True)
            r = requests.get(url, timeout=180, stream=True)
            if r.status_code != 200:
                print(f"HTTP {r.status_code}")
                continue
            raw = b"".join(r.iter_content(chunk_size=1 << 16))
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                names = z.namelist()
                csv_name = next(
                    (n for n in names
                     if n.lower().endswith('.csv') and '_a' in n.lower()),
                    None
                )
                if not csv_name:
                    print(f"no *_a.csv in zip (contents: {names})")
                    continue
                with z.open(csv_name) as f:
                    data = f.read()
            with open(target, 'wb') as out:
                out.write(data)
            print(f"✓  {len(data)/1e6:.1f} MB")
            return True
        except Exception as e:
            print(f"failed — {e}")

    print(f"\n  ✗ Could not auto-download {year}.")
    print(f"    Get it manually:")
    print(f"    1. Go to https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx")
    print(f"    2. Select Completions → {year} → Complete data file → Download")
    print(f"    3. Unzip and put C{year}_A.csv (or c{year}_a.csv) in {DATA_DIR}/")
    return False


print("=" * 60)
print("STEP 1: Downloading 2018–2023 IPEDS completions data")
print("=" * 60)
new_years = [y for y in range(2018, 2024)]
download_ok = {}
for yr in new_years:
    download_ok[yr] = download_year(yr)

missing = [y for y, ok in download_ok.items() if not ok]
if missing:
    print(f"\n⚠  Missing years: {missing}")
    print("   Analysis will continue with whatever is available.")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Load all years
# ══════════════════════════════════════════════════════════════════════════════
def load_year(year):
    # TROUBLESHOOTING 2: filename casing varies by year
    # 2013–2017 files downloaded earlier use lowercase (c2013_a.csv).
    # 2018–2023 files from the new downloader use uppercase (C2018_A.csv).
    # Try all four capitalisation combinations in order.
    #
    # TROUBLESHOOTING 3: C2016_A is a directory in data/
    # A previous manual unzip left a folder named C2016_A (no .csv extension).
    # os.path.exists() returns False for it anyway since the name doesn't match,
    # but os.path.isfile() is added defensively so a future naming collision
    # can't accidentally try to read a directory as a CSV.
    for fname in [f"C{year}_A.csv", f"c{year}_a.csv",
                  f"C{year}_a.csv", f"c{year}_A.csv"]:
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path) and os.path.isfile(path):
            break
    else:
        print(f"  [skip] {year} — file not found")
        return None

    # TROUBLESHOOTING 6: 2023 file has a UTF-8 BOM on the first column
    # C2023_A.csv starts with EF BB BF (UTF-8 BOM). When read with
    # encoding='latin1', the first column appears as '﻿UNITID' instead
    # of 'UNITID'. pandas then can't match it against NEEDED_COLS,
    # silently drops UNITID from usecols, and df['UNITID'] raises KeyError.
    #
    # Fix: try utf-8-sig first — Python's utf-8-sig codec strips the BOM
    # automatically. Fall back to latin1 for older files that contain
    # characters invalid in UTF-8 (e.g. accented institution names).
    #
    # TROUBLESHOOTING 2 (continued): column name casing inside the file
    # Even when the file is found, passing usecols=NEEDED_COLS directly
    # fails if the actual column names differ in case. Build a case-
    # insensitive lookup (upper_map) from the real headers, then resolve
    # the actual names before calling read_csv with usecols.
    for enc in ('utf-8-sig', 'latin1'):
        try:
            raw_header = pd.read_csv(path, nrows=0, encoding=enc)
            break
        except Exception:
            continue
    # Belt-and-suspenders: strip whitespace and any residual BOM character
    # in case the codec didn't fully remove it (seen on some platforms).
    raw_header.columns = raw_header.columns.str.strip().str.lstrip('﻿')
    upper_map = {c.upper(): c for c in raw_header.columns}
    usecols = [upper_map[c.upper()] for c in NEEDED_COLS if c.upper() in upper_map]
    missing = [c for c in NEEDED_COLS if c.upper() not in upper_map]
    if missing:
        print(f"  {year}: ⚠ columns not found and skipped: {missing}")

    # TROUBLESHOOTING 6 (continued): use utf-8-sig when reading 2023 data too,
    # not just for the header peek — otherwise the BOM reappears in the data.
    # Earlier years must stay on latin1 (they have non-UTF-8 characters).
    encoding = 'utf-8-sig' if year >= 2023 else 'latin1'
    read_kwargs = dict(usecols=usecols, encoding=encoding)

    # TROUBLESHOOTING 4 & 5: 2014 truncation + pandas version differences
    #
    # The 2014 file hits EOF inside a quoted string at row 253,038.
    # on_bad_lines='skip' does NOT prevent this — the C parser raises
    # ParserError at the tokenizer level before bad-line handling runs.
    # Fix: catch ParserError and retry with engine='python', which tolerates
    # mid-file truncation and skips broken rows instead of aborting.
    #
    # Separately: on_bad_lines='skip' was added in pandas 1.3.0 (2021).
    # Older Anaconda environments (Python 3.8) use error_bad_lines=False
    # instead. Catch TypeError (raised when an unrecognised kwarg is passed)
    # and fall back to the old API.
    try:
        df = pd.read_csv(path, on_bad_lines='skip', **read_kwargs)
    except (TypeError, pd.errors.ParserError):
        try:
            df = pd.read_csv(path, engine='python', on_bad_lines='skip', **read_kwargs)
        except TypeError:
            # Pandas <1.3 — use the legacy bad-lines API
            df = pd.read_csv(path, engine='python',
                             error_bad_lines=False, warn_bad_lines=False, **read_kwargs)

    # Normalise all column names to uppercase so downstream code
    # (which references e.g. df['UNITID']) works regardless of source year.
    df.columns = [c.upper() for c in df.columns]

    df.columns = df.columns.str.strip()
    df = df[(df['AWLEVEL'] == 5) & (df['MAJORNUM'] == 1)].copy()
    df['CIP2']    = df['CIPCODE'].astype(str).str.split('.').str[0].str.zfill(2)
    df['CIP_FIELD'] = df['CIP2'].map(STEM_CIP_2DIGIT)
    df['IS_STEM'] = df['CIP2'].isin(STEM_CIP_2DIGIT.keys())
    for col in DEMO_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    df['YEAR'] = year
    print(f"  {year}: {len(df):,} rows, {df['UNITID'].nunique():,} institutions")
    return df


print("\n" + "=" * 60)
print("STEP 2: Loading all years")
print("=" * 60)
frames = []
for yr in ALL_YEARS:
    frame = load_year(yr)
    if frame is not None:
        frames.append(frame)

all_df = pd.concat(frames, ignore_index=True)
actual_years = sorted(all_df['YEAR'].unique())
print(f"\nYears in dataset: {actual_years}")
print(f"Total rows: {len(all_df):,}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Load HD (institutional characteristics)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 3: Loading institutional characteristics (HD)")
print("=" * 60)
hd_path = os.path.join(DATA_DIR, "hd2022.csv")
if not os.path.exists(hd_path):
    hd_path = next(
        (os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)
         if f.lower().startswith('hd') and f.lower().endswith('.csv')),
        None
    )
if hd_path:
    hd = pd.read_csv(hd_path,
                     usecols=['UNITID', 'SECTOR', 'CONTROL'],
                     encoding='latin1')
    hd.columns = hd.columns.str.strip()
    CONTROL_MAP = {1: 'Public', 2: 'Private nonprofit', 3: 'Private for-profit'}
    hd['CONTROL_LABEL'] = hd['CONTROL'].map(CONTROL_MAP).fillna('Unknown')
    print(f"HD loaded: {len(hd):,} institutions from {hd_path}")
else:
    print("  ⚠ HD file not found — sector analysis will be skipped")
    hd = pd.DataFrame(columns=['UNITID', 'CONTROL_LABEL'])


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Run analyses
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4: Running analyses")
print("=" * 60)

df = all_df.merge(hd[['UNITID', 'CONTROL_LABEL']], on='UNITID', how='left')
df['CONTROL_LABEL'] = df['CONTROL_LABEL'].fillna('Unknown')

stem_df  = df[df['IS_STEM']  & ~df['YEAR'].isin(EXCLUDE_YEARS)]
total_df = df[~df['YEAR'].isin(EXCLUDE_YEARS)]

stem_annual  = stem_df.groupby('YEAR')[list(DEMO_COLS)].sum().reset_index()
total_annual = total_df.groupby('YEAR')[list(DEMO_COLS)].sum().reset_index()

# Sector share
CONTROL_CATS = ['Public', 'Private nonprofit']
sector_rows = []
for cat in CONTROL_CATS:
    for yr in sorted(stem_df['YEAR'].unique()):
        sn = stem_df[(stem_df['CONTROL_LABEL']==cat) & (stem_df['YEAR']==yr)][list(FOCUS_GROUPS)].sum()
        tn = total_df[(total_df['CONTROL_LABEL']==cat) & (total_df['YEAR']==yr)][list(FOCUS_GROUPS)].sum()
        row = {'Sector': cat, 'YEAR': yr}
        for col, label in FOCUS_GROUPS.items():
            row[label] = round(sn[col] / max(tn[col], 1) * 100, 1)
        sector_rows.append(row)
sector_df = pd.DataFrame(sector_rows)

# Field breakdown — compare 2013 vs latest available year
latest_year = max(y for y in actual_years if y not in EXCLUDE_YEARS)
field_compare_years = [2013, latest_year]
field_rows = []
for field_code, field_name in STEM_CIP_2DIGIT.items():
    for yr in field_compare_years:
        if yr not in actual_years:
            continue
        fslice = df[(df['CIP2']==field_code) & (df['YEAR']==yr) & (df['AWLEVEL']==5)]
        if len(fslice) == 0:
            continue
        row = {'Field': field_name, 'Year': yr,
               'Total': int(fslice['CTOTALT'].sum())}
        for col, label in FOCUS_GROUPS.items():
            row[f'{label}_pct'] = round(
                fslice[col].sum() / max(fslice['CTOTALT'].sum(), 1) * 100, 1)
        field_rows.append(row)
field_df = pd.DataFrame(field_rows)

# Save CSVs
stem_annual.to_csv(os.path.join(FIG_DIR, "stem_annual.csv"), index=False)
total_annual.to_csv(os.path.join(FIG_DIR, "total_annual.csv"), index=False)
sector_df.to_csv(os.path.join(FIG_DIR, "sector_share.csv"), index=False)
field_df.to_csv(os.path.join(FIG_DIR, "field_df.csv"), index=False)
print("✓ CSVs saved")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Regenerate charts
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 5: Regenerating charts")
print("=" * 60)

plot_years = sorted(y for y in actual_years if y not in EXCLUDE_YEARS)


def add_covid_band(ax, xmin, xmax):
    """Light gray band + label for COVID disruption window."""
    ax.axvspan(COVID_START, min(COVID_END, xmax),
               color='#EEEEEE', alpha=0.7, zorder=0, lw=0)
    ax.text((COVID_START + min(COVID_END, xmax)) / 2, ax.get_ylim()[1] * 0.97,
            'COVID', ha='center', va='top', fontsize=7.5,
            color='#AAAAAA', style='italic')


# ── Chart 1: STEM share trend ─────────────────────────────────────────────────
def chart1():
    years = stem_annual['YEAR'].values
    plot_y = [y for y in years if y not in EXCLUDE_YEARS]
    sa = stem_annual[stem_annual['YEAR'].isin(plot_y)].set_index('YEAR')
    ta = total_annual[total_annual['YEAR'].isin(plot_y)].set_index('YEAR')

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.grid(axis='y', zorder=0)
    ax.axvspan(COVID_START, COVID_END, color='#F5F5F5', zorder=0, lw=0)
    ax.text((COVID_START + COVID_END) / 2, 21.2, 'COVID\ndisruption',
            ha='center', va='top', fontsize=7.5, color='#AAAAAA', style='italic')

    for col, label in FOCUS_GROUPS.items():
        vals = (sa[col] / ta[col].replace(0, np.nan) * 100).values
        color = COLORS[label]
        lw    = 2.5 if label in ('Black / African American', 'Hispanic') else 1.8
        alpha = 1.0 if label in ('Black / African American', 'Hispanic') else 0.75
        ax.plot(plot_y, vals, color=color, lw=lw, alpha=alpha,
                marker='o', ms=4, zorder=3)
        ax.annotate(f'{label}  {vals[-1]:.1f}%',
                    xy=(plot_y[-1], vals[-1]),
                    xytext=(5, 0), textcoords='offset points',
                    va='center', ha='left', fontsize=9.5, color=color,
                    fontweight='bold' if label in ('Black / African American', 'Hispanic') else 'normal')

    ax.set_xlim(plot_y[0] - 0.4, plot_y[-1] + 2.8)
    ax.set_ylim(0, 24)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f%%'))
    ax.set_xticks(plot_y)
    ax.set_xticklabels([str(y) for y in plot_y])
    ax.set_title("STEM share of all bachelor's degrees, by race/ethnicity",
                 fontsize=13, fontweight='bold', loc='left', pad=12)
    ax.set_ylabel("% of group's bachelor's earned in STEM", fontsize=10)
    ax.text(0.0, -0.14,
            f"Source: IPEDS Completions Survey, {plot_y[0]}–{plot_y[-1]}. "
            "STEM defined by NSF CIP crosswalk (excludes health professions). "
            "First majors, bachelor's only.\n"
            "2014 excluded (truncated source file). Shaded band = COVID disruption window.",
            transform=ax.transAxes, fontsize=8, color='#888888', va='top')

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig1_stem_share_trend.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ fig1_stem_share_trend.png")


# ── Chart 2: Indexed growth ───────────────────────────────────────────────────
def chart2():
    sa = stem_annual[stem_annual['YEAR'].isin(plot_years)].set_index('YEAR')
    base_year = plot_years[0]

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    ax.grid(axis='y', zorder=0)
    ax.axhline(100, color='#CCCCCC', lw=1.0, ls='--', zorder=1)
    ax.axvspan(COVID_START, COVID_END, color='#F5F5F5', zorder=0, lw=0)

    base_label = {col: sa.loc[base_year, col] for col in FOCUS_GROUPS}
    for col, label in FOCUS_GROUPS.items():
        vals = sa[col].values
        indexed = vals / base_label[col] * 100
        color = COLORS[label]
        lw = 2.5 if label == 'Hispanic' else 1.8
        ax.plot(plot_years, indexed, color=color, lw=lw, marker='o', ms=4, zorder=3)
        chg = indexed[-1] - 100
        sign = '+' if chg >= 0 else ''
        ax.annotate(f'{label}  {sign}{chg:.0f}%',
                    xy=(plot_years[-1], indexed[-1]),
                    xytext=(5, 0), textcoords='offset points',
                    va='center', ha='left', fontsize=9.5, color=color,
                    fontweight='bold' if label == 'Hispanic' else 'normal')

    ax.set_xlim(plot_years[0] - 0.4, plot_years[-1] + 3.2)
    ax.set_ylim(75, ax.get_ylim()[1])
    ax.set_xticks(plot_years)
    ax.set_xticklabels([str(y) for y in plot_years])
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f'))
    ax.set_title(f"Growth in STEM bachelor's degrees, indexed to {base_year} = 100",
                 fontsize=13, fontweight='bold', loc='left', pad=12)
    ax.set_ylabel(f"Index ({base_year} = 100)", fontsize=10)

    baselines = ' · '.join(
        f"{FOCUS_GROUPS[c].split('/')[0].strip()}={int(base_label[c]):,}"
        for c in FOCUS_GROUPS
    )
    ax.text(0.0, -0.14,
            f"Source: IPEDS Completions Survey, {plot_years[0]}–{plot_years[-1]}. "
            f"Baseline ({base_year}): {baselines}.\n"
            "2014 excluded. Shaded band = COVID disruption window.",
            transform=ax.transAxes, fontsize=8, color='#888888', va='top')

    ax.text((COVID_START + COVID_END) / 2, ax.get_ylim()[1] * 0.99,
            'COVID', ha='center', va='top', fontsize=7.5,
            color='#AAAAAA', style='italic')

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig2_stem_growth_indexed.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ fig2_stem_growth_indexed.png")


# ── Chart 3: Field breakdown dumbbell (2013 vs latest) ───────────────────────
def chart3():
    df17 = field_df[field_df['Year'] == latest_year].copy()
    df13 = field_df[field_df['Year'] == 2013].copy()

    df17 = df17[df17['Field'] != 'Science Technologies']
    df13 = df13[df13['Field'] != 'Science Technologies']

    order = df17.sort_values('Total')['Field'].tolist()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    fig.suptitle('Racial/ethnic share of STEM degrees varies enormously by field',
                 fontsize=13, fontweight='bold', x=0.05, ha='left', y=1.02)

    panel_data = [
        ('Black / African American_pct', 'Black / African American', '#C0392B'),
        ('Hispanic_pct',                 'Hispanic',                  '#E67E22'),
    ]

    for ax, (col, label, color) in zip(axes, panel_data):
        vals_new = [df17[df17['Field']==f][col].values[0] for f in order]
        vals_old = [df13[df13['Field']==f][col].values[0] for f in order]
        y_pos    = np.arange(len(order))

        for i, (v_old, v_new) in enumerate(zip(vals_old, vals_new)):
            line_color = color if v_new >= v_old else '#AAAAAA'
            ax.hlines(i, v_old, v_new, color=line_color, lw=2.5, zorder=2)

        ax.scatter(vals_old, y_pos, color='white', edgecolors=color,
                   s=55, linewidths=2, zorder=4, label='2013')
        ax.scatter(vals_new, y_pos, color=color,
                   s=55, zorder=5, label=str(latest_year))

        for i, (v_old, v_new) in enumerate(zip(vals_old, vals_new)):
            right = max(v_old, v_new)
            ax.text(right + 0.25, i, f'{v_new:.1f}%',
                    va='center', fontsize=8.5, color='#333333')
            if v_old > v_new:
                ax.text(v_old + 0.25, i + 0.35, f"{v_old:.1f}% ('13)",
                        va='center', fontsize=7.5, color='#888888')

        ax.set_yticks(y_pos)
        ax.set_yticklabels([f.replace(' & ', '\n& ') for f in order], fontsize=9.5)
        ax.set_xlabel('Share of degrees in field (%)', fontsize=10)
        ax.set_xlim(0, max(max(vals_new), max(vals_old)) * 1.55)
        ax.set_title(label, fontsize=11, fontweight='bold', color=color, pad=8)
        ax.grid(axis='x', zorder=0)
        ax.axvline(0, color='#CCCCCC', lw=0.8)
        ax.legend(fontsize=9, frameon=False, loc='lower right')

    plt.tight_layout()
    fig.text(0.0, -0.05,
             f"Source: IPEDS Completions Survey, 2013 and {latest_year}. "
             "Share = group's degrees in field ÷ all degrees in field.\n"
             "Science Technologies excluded (N<600). Open circle = 2013, "
             f"filled = {latest_year}. STEM CIP crosswalk per NSF.",
             fontsize=8, color='#888888', va='top')

    out = os.path.join(FIG_DIR, "fig3_field_breakdown.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ fig3_field_breakdown.png  (2013 vs {latest_year})")


# ── Chart 4: Sector trends ────────────────────────────────────────────────────
def chart4():
    GROUPS   = list(FOCUS_GROUPS.values())
    years    = sorted(sector_df['YEAR'].unique())

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=False)

    for ax, sect in zip(axes, CONTROL_CATS):
        s = sector_df[sector_df['Sector'] == sect].sort_values('YEAR')
        ax.grid(axis='y', zorder=0)
        ax.axvspan(COVID_START, COVID_END, color='#F5F5F5', zorder=0, lw=0)
        ax.text((COVID_START + COVID_END) / 2, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 20,
                'COVID', ha='center', va='top', fontsize=7, color='#AAAAAA', style='italic')

        for grp in GROUPS:
            if grp not in s.columns:
                continue
            vals  = s[grp].values
            syrs  = s['YEAR'].values
            color = COLORS[grp]
            lw    = 2.5 if grp in ('Black / African American', 'Hispanic') else 1.8
            ax.plot(syrs, vals, color=color, lw=lw, marker='o', ms=4, zorder=3)
            ax.annotate(f'{vals[-1]:.1f}%',
                        xy=(syrs[-1], vals[-1]),
                        xytext=(4, 0), textcoords='offset points',
                        va='center', ha='left', fontsize=9, color=color)

        ax.set_xlim(years[0] - 0.4, years[-1] + 1.5)
        ax.set_xticks(years)
        ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right', fontsize=9)
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f%%'))
        ax.set_title(sect, fontsize=12, fontweight='bold', pad=8)
        ax.set_ylabel("STEM share of bachelor's (%)", fontsize=10)

    legend_elements = [Line2D([0], [0], color=COLORS[g], lw=2, label=g) for g in GROUPS]
    fig.legend(handles=legend_elements, loc='lower center', ncol=4,
               fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle('STEM share by institution control type: public vs. private nonprofit',
                 fontsize=13, fontweight='bold', x=0.02, ha='left', y=1.03)
    fig.text(0.0, -0.14,
             f"Source: IPEDS Completions Survey, {years[0]}–{years[-1]}, "
             "merged with HD2022. 2014 excluded. Shaded band = COVID disruption window.",
             fontsize=8, color='#888888', va='top')

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig4_sector_breakdown.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ fig4_sector_breakdown.png")


chart1()
chart2()
chart3()
chart4()

print("\n" + "=" * 60)
print("Done. All figures saved to:", FIG_DIR)
print("=" * 60)
print(f"\nYears in updated analysis: {plot_years}")
print(f"Field comparison: 2013 vs {latest_year}")
print("\nNext: re-render your Quarto site to pick up the new figures.")
print("  quarto render quarto/work/stem-completion-equity-analysis.qmd")
