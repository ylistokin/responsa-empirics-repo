"""
Reproduce Figure 2 ("Share of Responsa by Region for Each Half-Century").

Per the paper: "Figure 2 tracks the share of the database's responsa
authored in different geographic regions for each half-century from 700
to the present." It is a 100%-stacked area chart: for each 50-year bin,
the bars/areas for all regions sum to 1.0 (share of that half-century's
responsa, not of the whole dataset).

Sample: uses the same "responsa sample" as the rest of the paper --
observations with word_length >= 11 (see Section III.A, "Excluding
Non-Responsa"; this is the same filter used in 02_table1_summary_statistics.py).

Year: uses `interpolated_year` exactly as defined in 01_build_dataset.py
(first responsum in a volume -> birth+30, last -> death, each volume
interpolated independently).

Region: uses the `region` column built in 01_build_dataset.py (8 regions;
Geonic-era authors with no recorded country are mapped to "West Asia (ex
Israel)").

Binning: each responsum is assigned to the half-century bin
floor(interpolated_year / 50) * 50, e.g. 1480-1505 falls in the 1450-1500
bin. Within each bin, each region's count is divided by the bin's total
count to get that region's share (bins sum to 1.0 across regions).

Plot: drawn as a stacked-area chart with sharp (step) transitions at each
half-century boundary rather than smooth diagonal interpolation between
bin centers, to match the paper's figure, which shows a constant share
within each half-century that jumps at the boundary.

Run 01_build_dataset.py first:
    python scripts/01_build_dataset.py
    python scripts/05_figure2_regional_share_over_time.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BIN_WIDTH = 50  # half-century

df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")

# Same "responsa sample" used throughout the paper: word_length >= 11
df = df[df["word_length"] >= 11].copy()
df = df.dropna(subset=["interpolated_year", "region"])

df["half_century"] = (np.floor(df["interpolated_year"] / BIN_WIDTH) * BIN_WIDTH).astype(int)

# Counts per (half_century, region), then convert to within-bin shares
counts = df.groupby(["half_century", "region"]).size().unstack(fill_value=0)
counts = counts.sort_index()
shares = counts.div(counts.sum(axis=1), axis=0)

regions = sorted(shares.columns)
shares = shares[regions]

print(f"Half-century bins: {shares.index.min()}-{shares.index.max() + BIN_WIDTH} "
      f"({len(shares)} bins)")
print(f"Regions ({len(regions)}): {', '.join(regions)}")
print(f"\nShare of total responsa by region, first and last bins:")
print(shares.iloc[[0, -1]].round(3).to_string())

# ---------------------------------------------------------------------------
# Build step-function x/y arrays so each half-century's share is flat within
# the bin and jumps sharply at the boundary (matching the paper's figure),
# rather than linearly interpolating between bin centers.
# ---------------------------------------------------------------------------
bin_starts = shares.index.values
# x_step: [b0, b0+W, b1, b1+W, b2, b2+W, ...] -- each bin's left and right
# edge, so the stackplot holds a flat value across [b_i, b_i+BIN_WIDTH) and
# steps sharply at each boundary rather than interpolating linearly.
x_step = np.repeat(bin_starts, 2)
x_step[1::2] = bin_starts + BIN_WIDTH

y_step = {r: np.repeat(shares[r].values, 2) for r in regions}

fig, ax = plt.subplots(figsize=(11, 6.5))
ax.stackplot(x_step, *[y_step[r] for r in regions], labels=regions, alpha=0.85)
ax.set_xlim(bin_starts.min(), bin_starts.max() + BIN_WIDTH)
ax.set_ylim(0, 1)
ax.set_xlabel("Year")
ax.set_ylabel("Share of Total Responsa")
ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc="upper left")
ax.grid(True, alpha=0.3)

# Use fig.suptitle (centered on the whole figure canvas, including the
# legend's width) rather than ax.set_title (which centers only over the
# axes). With the legend sitting outside the axes to the right, an
# axes-centered title sits left of the true visual center of the saved
# image -- that's what made it look cut off / off-center when pasted
# elsewhere. fig.suptitle keeps it centered on the full image regardless
# of the legend. tight_layout's rect leaves headroom at the top (y<0.94)
# so the title doesn't overlap the plot -- must be called AFTER suptitle,
# since tight_layout only reserves space for elements that already exist.
fig.suptitle("Figure 2: Share of Responsa by Region for Each Half Century",
              fontsize=14, x=0.5, ha="center")
plt.tight_layout(rect=[0, 0, 1, 0.94])

os.makedirs("figures", exist_ok=True)
plt.savefig("figures/figure2.png", dpi=200, bbox_inches="tight")
plt.close()
print("\nWrote figures/figure2.png")

os.makedirs("data/processed", exist_ok=True)
shares_out = shares.reset_index().rename(columns={"half_century": "half_century_start"})
shares_out.to_csv("data/processed/figure2_regional_shares_by_halfcentury.csv", index=False)
print("Wrote data/processed/figure2_regional_shares_by_halfcentury.csv")
