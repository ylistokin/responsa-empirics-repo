"""
Reproduce Figure 1 (responsa density + smoothed median word length over
time) and Figure 2 (share of responsa by region per half-century).

Run 01_build_dataset.py first. Matplotlib output is saved to figures/.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.makedirs("figures", exist_ok=True)
df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")

# ---------------------------------------------------------------------------
# Figure 1
# ---------------------------------------------------------------------------
df_plot = df[["interpolated_year", "word_length"]].dropna().sort_values("interpolated_year")
lower, upper = df_plot["word_length"].quantile([0.1, 0.9])
df_plot = df_plot[df_plot["word_length"].between(lower, upper)]

years = df_plot["interpolated_year"].values
lengths = df_plot["word_length"].values
grid_years = np.linspace(years.min(), years.max(), 1500)

k = 1500
median_smoothed = []
for year in grid_years:
    distances = np.abs(years - year)
    nearest = np.argpartition(distances, k)[:k]
    median_smoothed.append(np.median(lengths[nearest]))

plt.figure(figsize=(10, 6))
plt.scatter(years, lengths, alpha=0.1, s=10, label="Bar-Ilan Responsa Data")
plt.plot(grid_years, median_smoothed, color="darkred", linewidth=2,
         label=f"Smoothed Median ({k} Nearest Neighbors)")
plt.axhline(250, color="gray", linestyle="--", linewidth=1.5, label="Word Length = 250")
plt.axvline(1492, color="green", linestyle="--", linewidth=1.3, label="late 15th century gap")
plt.xlabel("Estimated Year of Responsum")
plt.ylabel("Word Length")
plt.title("Figure 1: Responsa Density and Smoothed Median Word Length Over Time")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("figures/figure1.png", dpi=150)
plt.close()
print("Wrote figures/figure1.png")

# ---------------------------------------------------------------------------
# Figure 2
# ---------------------------------------------------------------------------
df_region = df[["interpolated_year", "region"]].dropna()
df_region = df_region[df_region["interpolated_year"].between(700, 2020)]
df_region["half_century"] = ((df_region["interpolated_year"] // 50) * 50).astype(int)

counts = df_region.groupby(["half_century", "region"]).size().unstack(fill_value=0)
region_shares = counts.div(counts.sum(axis=1), axis=0)

plt.figure(figsize=(14, 7))
region_shares.plot.area(colormap="tab10", alpha=0.85)
plt.title("Figure 2: Share of Responsa by Region for Each Half-Century, 700-2010")
plt.xlabel("Year")
plt.ylabel("Share of Total Responsa")
plt.ylim(0, 1)
plt.xlim(700, 2010)
plt.grid(True)
plt.legend(title="Region", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.savefig("figures/figure2.png", dpi=150)
plt.close()
print("Wrote figures/figure2.png")
