"""
Generate publication-quality charts for the IPEDS STEM completion equity analysis.
Styled to match the portfolio aesthetic: clean, minimal, specific numbers, no fluff.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.lines import Line2D

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")

# ── Palette (accessible, consistent with a neutral portfolio site) ────────────
COLORS = {
    'Black / African American': '#C0392B',   # deep red
    'Hispanic':                  '#E67E22',   # amber
    'Asian':                     '#2980B9',   # blue
    'White':                     '#7F8C8D',   # slate gray
}
PALETTE = list(COLORS.values())

# ── Base style ────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# CHART 1: STEM share of all bachelor's degrees, by racial/ethnic group, 2013-2017
# Core finding: the gap is persistent, not closing fast enough
# ─────────────────────────────────────────────────────────────────────────────
def chart1_stem_share_trend():
    stem   = pd.read_csv(os.path.join(FIG_DIR, "stem_annual.csv"))
    total  = pd.read_csv(os.path.join(FIG_DIR, "total_annual.csv"))

    GROUPS = {
        'CBKAAT': 'Black / African American',
        'CHISPT': 'Hispanic',
        'CASIAT': 'Asian',
        'CWHITT': 'White',
    }

    years = stem['YEAR'].values
    shares = {}
    for col, label in GROUPS.items():
        shares[label] = (stem[col] / total[col].replace(0, np.nan) * 100).values

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.grid(axis='y', zorder=0)

    for label, vals in shares.items():
        color = COLORS[label]
        lw = 2.5 if label in ('Black / African American', 'Hispanic') else 1.8
        alpha = 1.0 if label in ('Black / African American', 'Hispanic') else 0.75
        ax.plot(years, vals, color=color, lw=lw, alpha=alpha,
                marker='o', ms=5, zorder=3)
        # End label
        ax.annotate(f'{label}  {vals[-1]:.1f}%',
                    xy=(years[-1], vals[-1]),
                    xytext=(4, 0), textcoords='offset points',
                    va='center', ha='left', fontsize=9.5,
                    color=color, fontweight='bold' if label in ('Black / African American','Hispanic') else 'normal')

    ax.set_xlim(years[0] - 0.3, years[-1] + 2.2)
    ax.set_ylim(0, 22)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f%%'))
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years])

    ax.set_title('STEM share of all bachelor\'s degrees, by race/ethnicity',
                 fontsize=13, fontweight='bold', loc='left', pad=12)
    ax.set_ylabel('% of group\'s bachelor\'s earned in STEM', fontsize=10)
    ax.text(0.0, -0.13,
            'Source: IPEDS Completions Survey, 2013–2017. STEM defined by NSF CIP crosswalk (excludes health professions).\n'
            'First majors, bachelor\'s degrees only (AWLEVEL=5). N institutions per year: ~2,000–2,800.',
            transform=ax.transAxes, fontsize=8, color='#888888', va='top')

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig1_stem_share_trend.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Chart 1 saved: {out}")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 2: STEM bachelor's counts — absolute growth, stacked area
# Shows: the pipeline is growing, but who is growing fastest?
# ─────────────────────────────────────────────────────────────────────────────
def chart2_counts_growth():
    stem = pd.read_csv(os.path.join(FIG_DIR, "stem_annual.csv"))

    GROUPS = {
        'CBKAAT': 'Black / African American',
        'CHISPT': 'Hispanic',
        'CASIAT': 'Asian',
        'CWHITT': 'White',
    }
    years = stem['YEAR'].values

    # Index each group to 2013=100 for growth comparison
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.grid(axis='y', zorder=0)
    ax.axhline(100, color='#CCCCCC', lw=1.0, ls='--', zorder=1)

    for col, label in GROUPS.items():
        vals = stem[col].values
        indexed = vals / vals[0] * 100
        color = COLORS[label]
        lw = 2.5 if label in ('Hispanic',) else 1.8
        ax.plot(years, indexed, color=color, lw=lw, marker='o', ms=5, zorder=3)
        ax.annotate(f'{label}  +{indexed[-1]-100:.0f}%',
                    xy=(years[-1], indexed[-1]),
                    xytext=(4, 0), textcoords='offset points',
                    va='center', ha='left', fontsize=9.5, color=color,
                    fontweight='bold' if label == 'Hispanic' else 'normal')

    ax.set_xlim(years[0] - 0.3, years[-1] + 2.8)
    ax.set_ylim(85, 175)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years])
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f'))
    ax.set_title('Growth in STEM bachelor\'s degrees, indexed to 2013 = 100',
                 fontsize=13, fontweight='bold', loc='left', pad=12)
    ax.set_ylabel('Index (2013 = 100)', fontsize=10)
    ax.text(0.0, -0.13,
            'Source: IPEDS Completions Survey, 2013–2017. Absolute baseline counts: '
            'Black=20,664 · Hispanic=28,633 · Asian=36,136 · White=197,256.',
            transform=ax.transAxes, fontsize=8, color='#888888', va='top')

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig2_stem_growth_indexed.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Chart 2 saved: {out}")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 3: STEM share by field — Black and Hispanic representation, 2013 vs 2017
# The field-level breakdown is where the national average stops being useful
# ─────────────────────────────────────────────────────────────────────────────
def chart3_field_breakdown():
    field_df = pd.read_csv(os.path.join(FIG_DIR, "field_df.csv"))

    df17 = field_df[field_df['Year']==2017].copy()
    df13 = field_df[field_df['Year']==2013].copy()

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
        vals_17 = [df17[df17['Field']==f][col].values[0] for f in order]
        vals_13 = [df13[df13['Field']==f][col].values[0] for f in order]
        y_pos   = np.arange(len(order))

        # Connecting lines — group color for gains, muted for declines
        for i, (v13, v17) in enumerate(zip(vals_13, vals_17)):
            line_color = color if v17 >= v13 else '#AAAAAA'
            ax.hlines(i, v13, v17, color=line_color, lw=2.5, zorder=2)

        # 2013: open circle
        ax.scatter(vals_13, y_pos, color='white', edgecolors=color,
                   s=55, linewidths=2, zorder=4, label='2013')
        # 2017: filled circle
        ax.scatter(vals_17, y_pos, color=color,
                   s=55, zorder=5, label='2017')

        # Value labels: 2017 always to the right of the rightmost dot
        for i, (v13, v17) in enumerate(zip(vals_13, vals_17)):
            right = max(v13, v17)
            ax.text(right + 0.25, i, f'{v17:.1f}%',
                    va='center', fontsize=8.5, color='#333333')
            # For declines, also label the 2013 value to the left
            if v13 > v17:
                ax.text(v13 + 0.25, i + 0.35, f'{v13:.1f}% (\'13)',
                        va='center', fontsize=7.5, color='#888888')

        ax.set_yticks(y_pos)
        ax.set_yticklabels([f.replace(' & ', '\n& ') for f in order], fontsize=9.5)
        ax.set_xlabel('Share of degrees in field (%)', fontsize=10)
        ax.set_xlim(0, max(max(vals_17), max(vals_13)) * 1.55)
        ax.set_title(f'{label}', fontsize=11, fontweight='bold', color=color, pad=8)
        ax.grid(axis='x', zorder=0)
        ax.axvline(0, color='#CCCCCC', lw=0.8)
        ax.legend(fontsize=9, frameon=False, loc='lower right')

    plt.tight_layout()
    fig.text(0.0, -0.05,
             'Source: IPEDS Completions Survey, 2013 and 2017. Share = group\'s degrees in field ÷ all degrees in field.\n'
             'Science Technologies excluded (N<600). Open circle = 2013, filled = 2017. STEM CIP crosswalk per NSF.',
             fontsize=8, color='#888888', va='top')

    out = os.path.join(FIG_DIR, "fig3_field_breakdown.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Chart 3 saved: {out}")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 4: STEM share by sector (public vs private nonprofit), 2013-2017
# ─────────────────────────────────────────────────────────────────────────────
def chart4_sector():
    sector = pd.read_csv(os.path.join(FIG_DIR, "sector_share.csv"))

    GROUPS = ['Black / African American', 'Hispanic', 'Asian', 'White']
    SECTORS = ['Public', 'Private nonprofit']
    years = sorted(sector['YEAR'].unique())

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=False)

    for ax, sect in zip(axes, SECTORS):
        s = sector[sector['Sector'] == sect].sort_values('YEAR')
        ax.grid(axis='y', zorder=0)
        for grp in GROUPS:
            if grp not in s.columns: continue
            vals = s[grp].values
            color = COLORS[grp]
            lw = 2.5 if grp in ('Black / African American', 'Hispanic') else 1.8
            ax.plot(years, vals, color=color, lw=lw, marker='o', ms=4, zorder=3)
            ax.annotate(f'{vals[-1]:.1f}%',
                        xy=(years[-1], vals[-1]),
                        xytext=(4, 0), textcoords='offset points',
                        va='center', ha='left', fontsize=9, color=color)
        ax.set_xlim(years[0]-0.3, years[-1]+1.2)
        ax.set_xticks(years)
        ax.set_xticklabels([str(y) for y in years])
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.0f%%'))
        ax.set_title(sect, fontsize=12, fontweight='bold', pad=8)
        ax.set_ylabel('STEM share of bachelor\'s (%)', fontsize=10)

    # Shared legend
    legend_elements = [Line2D([0], [0], color=COLORS[g], lw=2, label=g) for g in GROUPS]
    fig.legend(handles=legend_elements, loc='lower center', ncol=4,
               fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, -0.08))
    fig.suptitle('STEM share by institution control type: public vs. private nonprofit',
                 fontsize=13, fontweight='bold', x=0.02, ha='left', y=1.03)
    fig.text(0.0, -0.14,
             'Source: IPEDS Completions Survey, 2013–2017, merged with HD2022 institutional characteristics.',
             fontsize=8, color='#888888', va='top')

    plt.tight_layout()
    out = os.path.join(FIG_DIR, "fig4_sector_breakdown.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Chart 4 saved: {out}")


# ─────────────────────────────────────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    chart1_stem_share_trend()
    chart2_counts_growth()
    chart3_field_breakdown()
    chart4_sector()
    print("\nAll charts done.")
    print("Files in figures dir:")
    for f in sorted(os.listdir(FIG_DIR)):
        if f.endswith('.png'):
            print(f"  {f}")
