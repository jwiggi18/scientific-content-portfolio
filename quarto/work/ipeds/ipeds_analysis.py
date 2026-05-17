"""
IPEDS STEM Completion Equity Analysis
=====================================
Public data: IPEDS Completions (C) survey, 2013-2017
Institutional Characteristics (HD), 2022

Research question: Where in the STEM bachelor's degree pipeline does
the equity gap live, and how does it vary by institution type?

CIP scope: NSF STEM definition (2-digit CIP families)
Award level: 5 (bachelor's degree), first major only
"""

import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FIG_DIR  = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# 1. NSF STEM CIP crosswalk (2-digit codes)
# Source: NSF STEM-designated degree program list (NSF 22-310)
# Excludes health professions (51) — reported separately to avoid
# gender pattern confounds.
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# 2. Demographic column map
# ──────────────────────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────────────────────
# 3. Load and filter one year
# ──────────────────────────────────────────────────────────────────────────────
def load_year(year):
    path = os.path.join(DATA_DIR, f"C{year}_A.csv")
    if not os.path.exists(path):
        path = os.path.join(DATA_DIR, f"c{year}_a.csv")
    if not os.path.exists(path):
        print(f"  [skip] {year} — file not found")
        return None

    try:
        df = pd.read_csv(path, usecols=NEEDED_COLS, encoding='latin1', on_bad_lines='skip')
    except Exception:
        df = pd.read_csv(path, usecols=NEEDED_COLS, encoding='latin1',
                         engine='python', on_bad_lines='skip')
    df.columns = df.columns.str.strip()

    # Bachelor's degree (AWLEVEL=5), first major only
    df = df[(df['AWLEVEL'] == 5) & (df['MAJORNUM'] == 1)].copy()

    # Filter to STEM CIPs (2-digit match)
    df['CIP2'] = df['CIPCODE'].astype(str).str.split('.').str[0].str.zfill(2)
    df['CIP_FIELD'] = df['CIP2'].map(STEM_CIP_2DIGIT)
    df['IS_STEM'] = df['CIP2'].isin(STEM_CIP_2DIGIT.keys())

    # Convert count columns to numeric (imputation-suppressed values → 0)
    for col in DEMO_COLS.keys():
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['YEAR'] = year
    print(f"  {year}: {len(df):,} rows, {df['UNITID'].nunique():,} institutions")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 4. Load all years
# NOTE: 2014 data file is truncated at row 253,038 (EOF inside string error).
# The resulting dataset covers only ~2,014 institutions vs ~2,600-2,800 for
# every other year. 2014 is loaded but EXCLUDED from trend analyses to avoid
# introducing a data-quality artifact as if it were a real trend.
# ──────────────────────────────────────────────────────────────────────────────
print("=== Loading completions data ===")
YEARS = range(2013, 2018)
EXCLUDE_YEARS = [2014]   # truncated file — see note above
frames = []
for yr in YEARS:
    df = load_year(yr)
    if df is not None:
        frames.append(df)

all_df = pd.concat(frames, ignore_index=True)
print(f"\nTotal rows loaded: {len(all_df):,}")
print(f"Years covered: {sorted(all_df['YEAR'].unique())}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Load HD (institutional characteristics)
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Loading HD (Institutional Characteristics) ===")
hd = pd.read_csv(os.path.join(DATA_DIR, "hd2022.csv"),
                 usecols=['UNITID', 'INSTNM', 'SECTOR', 'CONTROL', 'CCBASIC', 'C21BASIC'],
                 encoding='latin1')
hd.columns = hd.columns.str.strip()
print(f"HD: {len(hd):,} institutions")

# Carnegie classification labels (C21BASIC = 2021 Carnegie Basic Classification)
# Codes verified against NCES HD variable documentation
CARNEGIE_MAP = {
    # Associate's (1-9)
    1:  "Associate's", 2: "Associate's", 3: "Associate's",
    4:  "Associate's", 5: "Associate's", 6: "Associate's",
    7:  "Associate's", 8: "Associate's", 9: "Associate's",
    10: "Associate's",          # Bacc/Associate's mixed, Associate's dominant
    # Doctoral (11-13)
    11: 'Doctoral (R1)',        # Very High Research Activity
    12: 'Doctoral (R2)',        # High Research Activity
    13: 'Doctoral/Professional',
    # Master's (14-16)
    14: "Master's (Large)", 15: "Master's (Medium)", 16: "Master's (Small)",
    # Baccalaureate (17-19)
    17: 'Baccalaureate: Arts & Sciences',
    18: 'Baccalaureate: Diverse Fields',
    19: 'Baccalaureate: Mixed',
    # Special focus and tribal (20+)
    **{k: 'Special Focus / Other' for k in range(20, 35)},
}

CONTROL_MAP = {1: 'Public', 2: 'Private nonprofit', 3: 'Private for-profit'}

hd['CARNEGIE_LABEL'] = hd['C21BASIC'].map(CARNEGIE_MAP).fillna('Other/Unclassified')
hd['CONTROL_LABEL']  = hd['CONTROL'].map(CONTROL_MAP).fillna('Unknown')

# 4-category Carnegie for analysis
def carnegie_4cat(label):
    if 'Doctoral' in label:
        return 'Doctoral / Research'
    elif "Master's" in label:
        return "Master's"
    elif 'Baccalaureate' in label:
        return 'Baccalaureate'
    else:
        return 'Other'

hd['CARNEGIE_4'] = hd['CARNEGIE_LABEL'].apply(carnegie_4cat)

print(f"Carnegie 4-category distribution:\n{hd['CARNEGIE_4'].value_counts()}")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Merge completions with HD
# ──────────────────────────────────────────────────────────────────────────────
df = all_df.merge(hd[['UNITID','CARNEGIE_4','CONTROL_LABEL']], on='UNITID', how='left')
df['CARNEGIE_4'] = df['CARNEGIE_4'].fillna('Other')
print(f"\nAfter merge: {len(df):,} rows")


# ──────────────────────────────────────────────────────────────────────────────
# 7. ANALYSIS A: National STEM bachelor's counts by demographic, by year
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== ANALYSIS A: National STEM bachelor's by demographic ===")

stem_df  = df[df['IS_STEM'] & ~df['YEAR'].isin(EXCLUDE_YEARS)].copy()
total_df = df[~df['YEAR'].isin(EXCLUDE_YEARS)].copy()   # all fields (denominator)

# National aggregate by year
stem_annual  = stem_df.groupby('YEAR')[list(DEMO_COLS.keys())].sum().reset_index()
total_annual = total_df.groupby('YEAR')[list(DEMO_COLS.keys())].sum().reset_index()

print("\nNational STEM bachelor's, 2013-2017:")
print(stem_annual[['YEAR','CTOTALT','CBKAAT','CHISPT','CASIAT','CWHITT']].to_string(index=False))

print("\nAll bachelor's totals (denominator):")
print(total_annual[['YEAR','CTOTALT','CBKAAT','CHISPT','CASIAT','CWHITT']].to_string(index=False))


# ──────────────────────────────────────────────────────────────────────────────
# 8. ANALYSIS B: STEM share of total bachelor's by demographic
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== ANALYSIS B: STEM share by demographic ===")

share_data = {}
for col, label in DEMO_COLS.items():
    if col == 'CTOTALT':
        continue
    stem_n   = stem_annual.set_index('YEAR')[col]
    total_n  = total_annual.set_index('YEAR')[col]
    share    = (stem_n / total_n.replace(0, np.nan) * 100).round(1)
    share_data[label] = share

share_df = pd.DataFrame(share_data)
print(share_df.to_string())

# Focus groups for the gap story
FOCUS_GROUPS = {
    'CBKAAT': 'Black / African American',
    'CHISPT': 'Hispanic',
    'CASIAT': 'Asian',
    'CWHITT': 'White',
}

print("\nSTEM share (%) for focal groups:")
for col, label in FOCUS_GROUPS.items():
    stem_n  = stem_annual.set_index('YEAR')[col]
    total_n = total_annual.set_index('YEAR')[col]
    share   = (stem_n / total_n.replace(0, np.nan) * 100).round(1)
    print(f"  {label}: {share.to_dict()}")


# ──────────────────────────────────────────────────────────────────────────────
# 9. ANALYSIS C: STEM share by institution control (Public / Private nonprofit)
# Control type is stable over time — safer join than Carnegie, which drifts.
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== ANALYSIS C: STEM share by institution control type ===")

ANALYSIS_YEARS  = sorted(stem_df['YEAR'].unique())
CONTROL_CATS    = ['Public', 'Private nonprofit']

sector_rows = []
for cat in CONTROL_CATS:
    for yr in ANALYSIS_YEARS:
        stem_n  = stem_df[(stem_df['CONTROL_LABEL']==cat) & (stem_df['YEAR']==yr)][list(FOCUS_GROUPS.keys())].sum()
        total_n = total_df[(total_df['CONTROL_LABEL']==cat) & (total_df['YEAR']==yr)][list(FOCUS_GROUPS.keys())].sum()
        row = {'Sector': cat, 'YEAR': yr}
        for col, label in FOCUS_GROUPS.items():
            row[label] = round(stem_n[col] / max(total_n[col], 1) * 100, 1)
        sector_rows.append(row)

sector_df = pd.DataFrame(sector_rows)
print(sector_df.to_string(index=False))

# Check merge quality
print(f"\nControl label distribution in merged data:")
print(df['CONTROL_LABEL'].value_counts())


# ──────────────────────────────────────────────────────────────────────────────
# 10. ANALYSIS D: STEM share by CIP field (2013 snapshot, shows field variation)
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== ANALYSIS D: STEM share by field, 2013 vs 2017 ===")

field_rows = []
for field_code, field_name in STEM_CIP_2DIGIT.items():
    for yr in [2013, 2017]:
        field_slice = df[(df['CIP2']==field_code) & (df['YEAR']==yr) & (df['AWLEVEL']==5)]
        total_slice = df[(df['YEAR']==yr) & (df['AWLEVEL']==5)]
        if len(field_slice) == 0: continue
        row = {'Field': field_name, 'Year': yr,
               'Total': int(field_slice['CTOTALT'].sum())}
        for col, label in FOCUS_GROUPS.items():
            row[f'{label}_pct'] = round(
                field_slice[col].sum() / max(field_slice['CTOTALT'].sum(), 1) * 100, 1)
        field_rows.append(row)

field_df = pd.DataFrame(field_rows)
print(field_df.to_string(index=False))


# ──────────────────────────────────────────────────────────────────────────────
# 11. Save processed datasets for charting
# ──────────────────────────────────────────────────────────────────────────────
stem_annual.to_csv(os.path.join(FIG_DIR, "stem_annual.csv"), index=False)
total_annual.to_csv(os.path.join(FIG_DIR, "total_annual.csv"), index=False)
sector_df.to_csv(os.path.join(FIG_DIR, "sector_share.csv"), index=False)
field_df.to_csv(os.path.join(FIG_DIR, "field_df.csv"), index=False)
print("\n✓ Processed data saved to ipeds-figures/")
print("Analysis complete.")
