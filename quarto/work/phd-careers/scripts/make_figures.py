"""
Generate figures for the PhD careers project.

Figure 1: Position distribution for biology/ag/life sciences PhDs (all years)
Figure 2: Position distribution for the 6-10 years post-degree cohort (all fields)

Both figures use the same reverse-calculation logic:
  N_in_cell = col_N * (pct_in_col / 100)
  pct_of_group_in_position = N_in_cell / group_N * 100

Figure 1 uses bio_position_dist.csv (already computed in clean_ecdcs_data.py).
Figure 2 is computed here from position_type_full.csv, since choosing the 6-10 year
cohort is an analytical decision made at the visualization stage.

Note on interpretation: Figure 1 includes many postdoctoral scholars because postdocs
are a common intermediate step, not a career endpoint. Figure 2 (6-10 years out) shows
where PhD holders are more likely to have settled into permanent roles.
"""

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

out_dir = Path("../output/figures")
out_dir.mkdir(parents=True, exist_ok=True)

# ── Style constants ────────────────────────────────────────────────────────────
TEXT_COLOR   = "#333333"
COLOR_BIO        = "#50838f"   # teal — bio PhD figure
COLOR_BIO_LIGHT  = "#8bbec8"   # lighter teal — bio PhD excl. postdocs
COLOR_COHORT     = "#8f6650"   # terra cotta — 6-10 year cohort figure
FIGSIZE      = (8, 5)

POSITION_COLS = [
    "tenured_faculty",
    "tenure_track_faculty",
    "non_tenure_track_faculty_with_rank",
    "other_faculty_no_rank_or_tenure",
    "post_doctoral_scholar",
    "research_scientist_or_nonfaculty_researcher",
    "all_other_positions",
]

POSITION_LABELS = {
    "tenured_faculty":                           "Tenured\nfaculty",
    "tenure_track_faculty":                      "Tenure-track\nfaculty",
    "non_tenure_track_faculty_with_rank":        "Non-tenure track\nfaculty (ranked)",
    "other_faculty_no_rank_or_tenure":           "Other faculty\n(no rank)",
    "post_doctoral_scholar":                     "Postdoctoral\nscholar",
    "research_scientist_or_nonfaculty_researcher": "Research\nscientist",
    "all_other_positions":                       "Other\npositions",
}


# ── Helper: styled bar chart ───────────────────────────────────────────────────

def bar_chart(values, labels, color, title, subtitle=None, outfile=None):
    fig, ax = plt.subplots(figsize=FIGSIZE)

    bars = ax.bar(labels, values, color=color, edgecolor="black", linewidth=0.8)

    ax.set_ylabel("% of group", color=TEXT_COLOR, fontsize=11)
    ax.set_title(title, color=TEXT_COLOR, fontweight="bold", fontsize=12, pad=14)
    if subtitle:
        ax.text(
            0.5, 1.01, subtitle,
            transform=ax.transAxes,
            ha="center", va="bottom",
            fontsize=9, color="#666666",
            style="italic"
        )

    ax.tick_params(axis="x", colors="#111111", labelsize=9)
    ax.tick_params(axis="y", colors="#111111")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#111111")
    ax.spines["bottom"].set_color("#111111")
    ax.yaxis.grid(True, linestyle="--", linewidth=0.5, color="#dddddd")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(values) * 1.18)

    for bar, val in zip(bars, values):
        if pd.notna(val):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{val:.1f}%",
                ha="center", va="bottom",
                color=TEXT_COLOR, fontsize=9
            )

    plt.tight_layout()
    if outfile:
        fig.savefig(outfile, dpi=150, bbox_inches="tight")
        print(f"Saved {outfile}")
    plt.show()
    return fig


# ── Figure 1: Bio/ag/life PhDs by position (all years) ────────────────────────

bio_dist = pd.read_csv("../data/processed/ecdcs/bio_position_dist.csv")

# Focus on the broadest biology grouping
focal = bio_dist[
    bio_dist["field"] == "Biological, agricultural, and environmental life sciences"
].iloc[0]

fig1_values = [focal[f"pct_in_{col}"] for col in POSITION_COLS]
fig1_labels = [POSITION_LABELS[col] for col in POSITION_COLS]

bar_chart(
    values=fig1_values,
    labels=fig1_labels,
    color=COLOR_BIO,
    title="Positions Held by Biology, Agriculture &\nLife Sciences PhD Holders",
    subtitle="All early-career doctorates (within 10 years of degree) · Source: ECDS 2017",
    outfile=out_dir / "fig1_bio_positions_all_years.png",
)


# ── Figure 2: 6-10 year cohort by position (all fields) ───────────────────────
# Reverse calculation: of people who are 6-10 years post-degree, what % are in each position?

full = pd.read_csv("../data/processed/ecdcs/position_type_full.csv")

n_row = full[full["characteristic"].str.strip() == "Number of early career doctorates"].iloc[0]
total_n = float(n_row["total"])

cohort_row = full[full["characteristic"].str.strip() == "6–10 years"].iloc[0]
cohort_pct_of_total = float(cohort_row["total"])
cohort_n = total_n * cohort_pct_of_total / 100

fig2_values = []
for col in POSITION_COLS:
    col_n     = float(n_row[col])       if pd.notna(n_row[col])      else np.nan
    pct_in_col = float(cohort_row[col]) if pd.notna(cohort_row[col]) else np.nan
    if pd.notna(col_n) and pd.notna(pct_in_col):
        n_in_cell = col_n * pct_in_col / 100
        fig2_values.append(round(n_in_cell / cohort_n * 100, 1))
    else:
        fig2_values.append(np.nan)

print(f"\n6-10 year cohort position distribution (row sum: {sum(v for v in fig2_values if pd.notna(v)):.1f}%)")
for col, val in zip(POSITION_COLS, fig2_values):
    print(f"  {col}: {val}")

bar_chart(
    values=fig2_values,
    labels=[POSITION_LABELS[col] for col in POSITION_COLS],
    color=COLOR_COHORT,
    title="Positions Held 6–10 Years After Doctoral Degree\n(all subjects)",
    subtitle="All fields · Source: ECDS 2017",
    outfile=out_dir / "fig2_positions_6_10_years.png",
)


# ── Table: Bio PhD positions excluding postdoctoral scholars ──────────────────
# Postdocs are a training position, not a career endpoint. This table removes
# them and recalculates percentages among the remaining categories.

out_tables = Path("../output/tables")
out_tables.mkdir(parents=True, exist_ok=True)

EXCLUDE = {"post_doctoral_scholar"}
keep_cols = [c for c in POSITION_COLS if c not in EXCLUDE]

focal = bio_dist[
    bio_dist["field"] == "Biological, agricultural, and environmental life sciences"
].iloc[0]

raw_vals  = {col: focal[f"pct_in_{col}"] for col in keep_cols}
total_excl = sum(v for v in raw_vals.values() if pd.notna(v))
rescaled   = {col: round(v / total_excl * 100, 1) for col, v in raw_vals.items() if pd.notna(v)}

table = pd.DataFrame({
    "Position":                  [POSITION_LABELS[c].replace("\n", " ") for c in keep_cols],
    "% (postdocs excluded)":     [rescaled.get(c, np.nan) for c in keep_cols],
    "% (all, including postdocs)": [round(raw_vals[c], 1) for c in keep_cols],
}).sort_values("% (postdocs excluded)", ascending=False).reset_index(drop=True)

table.to_csv(out_tables / "bio_positions_excl_postdoc.csv", index=False)
print("\nBio PhD positions (postdocs excluded):")
print(table.to_string(index=False))
print(f"\nRow sum (rescaled): {table['% (postdocs excluded)'].sum():.1f}%")

# ── Figure 3: Bio PhD positions excluding postdocs ────────────────────────────

FACULTY_COLS = {
    "tenured_faculty",
    "tenure_track_faculty",
    "non_tenure_track_faculty_with_rank",
    "other_faculty_no_rank_or_tenure",
}
COLOR_OUTLINE_FACULTY = "#1e5f6b"   # dark teal — thick outline on faculty bars

fig3_cols   = [c for c in keep_cols if c in rescaled]
fig3_values = [rescaled[c] for c in fig3_cols]
fig3_labels = [POSITION_LABELS[c] for c in fig3_cols]
fig3_is_faculty = [c in FACULTY_COLS for c in fig3_cols]

# Sort descending
sorted_tuples = sorted(zip(fig3_values, fig3_labels, fig3_is_faculty), reverse=True)
fig3_values, fig3_labels, fig3_is_faculty = zip(*sorted_tuples)

faculty_total = sum(v for v, f in zip(fig3_values, fig3_is_faculty) if f)

fig, ax = plt.subplots(figsize=FIGSIZE)

for i, (val, label, is_fac) in enumerate(zip(fig3_values, fig3_labels, fig3_is_faculty)):
    edge_color = COLOR_OUTLINE_FACULTY if is_fac else "black"
    edge_width = 2.5 if is_fac else 0.8
    bar = ax.bar(i, val, color=COLOR_BIO_LIGHT,
                 edgecolor=edge_color, linewidth=edge_width)
    if pd.notna(val):
        ax.text(i, val + 0.5, f"{val:.1f}%",
                ha="center", va="bottom", color=TEXT_COLOR, fontsize=9)

ax.set_xticks(range(len(fig3_labels)))
ax.set_xticklabels(fig3_labels, fontsize=9, color="#111111")
ax.tick_params(axis="y", colors="#111111")
ax.set_ylabel("% of group", color=TEXT_COLOR, fontsize=11)
ax.set_title(
    "Positions Held by Biology, Agriculture &\nLife Sciences PhD Holders (Postdocs Removed)",
    color=TEXT_COLOR, fontweight="bold", fontsize=12, pad=14
)
ax.text(
    0.5, 1.01,
    "Postdoctoral scholars excluded; percentages recalculated · Source: ECDS 2017",
    transform=ax.transAxes, ha="center", va="bottom",
    fontsize=9, color="#666666", style="italic"
)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#111111")
ax.spines["bottom"].set_color("#111111")
ax.yaxis.grid(True, linestyle="--", linewidth=0.5, color="#dddddd")
ax.set_axisbelow(True)
ax.set_ylim(0, max(fig3_values) * 1.25)

# Faculty total annotation
ax.annotate(
    f"Combined faculty roles: {faculty_total:.1f}%",
    xy=(0.98, 0.92), xycoords="axes fraction",
    ha="right", va="top", fontsize=9.5,
    color=COLOR_OUTLINE_FACULTY, fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
              edgecolor=COLOR_OUTLINE_FACULTY, linewidth=1.5)
)

# Legend
fac_patch    = mpatches.Patch(facecolor=COLOR_BIO_LIGHT, edgecolor=COLOR_OUTLINE_FACULTY,
                               linewidth=2.5, label="Faculty role")
nonfac_patch = mpatches.Patch(facecolor=COLOR_BIO_LIGHT, edgecolor="black",
                               linewidth=0.8, label="Non-faculty role")
ax.legend(handles=[fac_patch, nonfac_patch], fontsize=9,
          loc="upper right", bbox_to_anchor=(0.98, 0.80))

plt.tight_layout()
fig.savefig(out_dir / "fig3_bio_positions_excl_postdoc.png", dpi=150, bbox_inches="tight")
print(f"Saved {out_dir / 'fig3_bio_positions_excl_postdoc.png'}")
