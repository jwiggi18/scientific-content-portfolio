"""
Clean ECDS position_type and employment_setting data.

The raw tables are cross-tabulations where:
  - rows = characteristics (field of degree, sex, age, etc.)
  - columns = position types (tenured, tenure-track, postdoc, etc.)
  - values = % of that *column's* position type who have that characteristic

This means raw values tell you "X% of postdocs are bio PhDs",
NOT "X% of bio PhDs are postdocs". To get the latter, we use the
column Ns (total counts per position type) to reconstruct position
distributions for each field of study.

Outputs
-------
processed/ecdcs/position_type_full.csv    - full cleaned table (all fields/rows)
processed/ecdcs/bio_position_dist.csv     - position distribution FOR bio PhDs
                                            (i.e., what % of bio PhDs hold each role)
processed/ecdcs/employment_setting_full.csv - full cleaned employment setting table
"""

# %%
import pandas as pd
import numpy as np

base_path = "../data/raw/ecdcs/"
out_path = "../data/processed/ecdcs/"


# %%
# ─── Helpers ──────────────────────────────────────────────────────────────────

def clean_column_names(df):
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )
    return df

def suppress_to_nan(df):
    """Replace NCSES suppression codes (S = too few to report, D = withheld) with NaN."""
    return df.replace({"S": np.nan, "D": np.nan})


# %%
# ─── Position Type ────────────────────────────────────────────────────────────

raw_pos = pd.read_excel(
    base_path + "position_type.xlsx",
    skiprows=4,
    engine="openpyxl"
)

# Rename before cleaning so we control the output names
raw_pos = raw_pos.rename(columns={
    "Unnamed: 0":                        "characteristic",
    "Unnamed: 1":                        "total",
    "Total":                             "faculty_total",       # subtotal — drop
    "Unnamed: 7":                        "post_doctoral_scholar",
    "Total.1":                           "other_total",          # subtotal — drop
    "Other faculty, no rank or tenurea": "other_faculty_no_rank_or_tenure",
    "All other positionsc":              "all_other_positions",
})

# Drop subtotal columns — they're sums of other cols, not independent categories
raw_pos = raw_pos.drop(columns=["faculty_total", "other_total"])

raw_pos = clean_column_names(raw_pos)
raw_pos = raw_pos.dropna(how="all").reset_index(drop=True)
raw_pos = suppress_to_nan(raw_pos)

# Save the full table — filter at analysis time, not here
raw_pos.to_csv(out_path + "position_type_full.csv", index=False)
print("Saved position_type_full.csv")
print(f"  Shape: {raw_pos.shape}")
print(f"  Columns: {list(raw_pos.columns)}\n")


# %%
# ─── Position distribution FOR biology fields ─────────────────────────────────
#
# The raw table tells us "% of each position type who are bio PhDs".
# To flip this to "% of bio PhDs in each position type", use:
#
#   N_in_field           = total_N × (pct_of_total / 100)
#   N_in_field_AND_pos   = col_N[pos] × (pct_in_col / 100)
#   pct_of_field_in_pos  = N_in_field_AND_pos / N_in_field × 100

POSITION_COLS = [
    "tenured_faculty",
    "tenure_track_faculty",
    "non_tenure_track_faculty_with_rank",
    "other_faculty_no_rank_or_tenure",
    "post_doctoral_scholar",
    "research_scientist_or_nonfaculty_researcher",
    "all_other_positions",
]

BIO_FIELDS = [
    "Biological, agricultural, and environmental life sciences",
    "Agricultural and environmental life sciences",
    "Biological and biomedical sciences",
]

# Row 0 contains the column Ns ("Number of early career doctorates")
n_row = raw_pos[
    raw_pos["characteristic"].str.strip() == "Number of early career doctorates"
].iloc[0]

total_n = float(n_row["total"])

results = []
for field in BIO_FIELDS:
    match = raw_pos[raw_pos["characteristic"].str.strip() == field]
    if match.empty:
        print(f"WARNING: field not found — '{field}'")
        continue
    row = match.iloc[0]

    pct_of_total = float(row["total"])       # % of ALL doctorates in this field
    field_n = total_n * pct_of_total / 100   # estimated N

    dist = {
        "field": field,
        "estimated_n": round(field_n),
        "pct_of_all_doctorates": pct_of_total,
    }
    for col in POSITION_COLS:
        col_n = float(n_row[col]) if pd.notna(n_row[col]) else np.nan
        pct_in_col = float(row[col]) if pd.notna(row[col]) else np.nan
        if pd.notna(col_n) and pd.notna(pct_in_col) and field_n > 0:
            n_in_cell = col_n * pct_in_col / 100
            dist[f"pct_in_{col}"] = round(n_in_cell / field_n * 100, 1)
        else:
            dist[f"pct_in_{col}"] = np.nan
    results.append(dist)

bio_pos_dist = pd.DataFrame(results)

# Sanity check: rows should sum to ~100%
pct_cols = [c for c in bio_pos_dist.columns if c.startswith("pct_in_")]
row_sums = bio_pos_dist[pct_cols].sum(axis=1)
print("Row sums (should be ~100):")
for field, s in zip(bio_pos_dist["field"], row_sums):
    print(f"  {field}: {s:.1f}")

bio_pos_dist.to_csv(out_path + "bio_position_dist.csv", index=False)
print("\nSaved bio_position_dist.csv")
print(bio_pos_dist[["field"] + pct_cols].to_string(index=False))


# %%
# ─── Employment Setting ───────────────────────────────────────────────────────

raw_emp = pd.read_excel(
    base_path + "employment_setting.xlsx",
    skiprows=4,
    engine="openpyxl"
)

raw_emp = raw_emp.rename(columns={
    "Unnamed: 0": "characteristic",
    "Unnamed: 1": "total",
    "Unnamed: 6": "ffrdc",
})

raw_emp = clean_column_names(raw_emp)
raw_emp = raw_emp.dropna(how="all").reset_index(drop=True)
raw_emp = suppress_to_nan(raw_emp)

raw_emp.to_csv(out_path + "employment_setting_full.csv", index=False)
print("\nSaved employment_setting_full.csv")
print(f"  Shape: {raw_emp.shape}")
print(f"  Columns: {list(raw_emp.columns)}")
