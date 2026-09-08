"""
Reproduce Figure 1 ("Responsa Density and Smoothed Median and Mean
Word-Length Over Time").

Uses `interpolated_year` exactly as defined in 01_build_dataset.py: the
first responsum in any volume is assumed written birth+30, the last is
assumed written in the author's death year (birth+60 if death is
unrecorded), with each volume interpolated independently (no
chaining/sequencing across volumes by the same author).

Both the smoothed median and the smoothed mean use the same 1500-nearest-
neighbor window (in interpolated_year) at each point on the plotting grid,
computed directly on the full word_length distribution -- no outlier
trimming.

Run 01_build_dataset.py first:
    python scripts/01_build_dataset.py
    python scripts/03_figure1_density_and_length.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

K = 1500  # nearest-neighbor window for both smoothed median and mean

df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")
df = df.dropna(subset=["interpolated_year", "word_length"])

years = df["interpolated_year"].values
lengths = df["word_length"].values

grid_years = np.linspace(years.min(), years.max(), 1200)

median_smoothed = np.empty(len(grid_years))
mean_smoothed = np.empty(len(grid_years))
for i, y in enumerate(grid_years):
    nearest = np.argpartition(np.abs(years - y), min(K, len(years) - 1))[:K]
    median_smoothed[i] = np.median(lengths[nearest])
    mean_smoothed[i] = np.mean(lengths[nearest])

plt.figure(figsize=(11, 6))
plt.scatter(years, lengths, alpha=0.1, s=8, color="steelblue", label="Bar-Ilan Responsa Data")
plt.plot(grid_years, median_smoothed, color="darkred", linewidth=2,
          label=f"Smoothed Median ({K} Nearest Neighbors)")
plt.plot(grid_years, mean_smoothed, color="darkorange", linewidth=2,
          label=f"Smoothed Mean ({K} Nearest Neighbors)")
plt.axhline(250, color="gray", linestyle="--", linewidth=1.5, label="Word Length = 250")
plt.axvline(1492, color="green", linestyle="--", linewidth=1.3, label="late 15th century gap")
plt.ylim(0, 3000)
plt.xlabel("Estimated Year of Responsum")
plt.ylabel("Word Length")
plt.title("Figure 1: Responsa Density and Smoothed Median and Mean Word-Length Over Time")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

os.makedirs("figures", exist_ok=True)
plt.savefig("figures/figure1.png", dpi=300)
plt.close()
print("Wrote figures/figure1.png")
