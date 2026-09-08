# Responsa Project — Lengths

Recreating each table and figure in "Trends in Responsa from the 7th
Century to the Present" from the raw Bar-Ilan data, for GitHub.

## Structure

```
data/
  raw/          full_stats_with_missing.xlsx, geonim_len_stats.xlsx (inputs, as uploaded)
  processed/    generated — bi_plus_geonim.csv, table1.csv, etc.
scripts/        plain Python (.py) — run locally: python scripts/01_build_dataset.py
notebooks/      Colab notebooks (.ipynb) — same steps, for Google Drive/Colab
figures/        generated figure images
```

Each numbered script/notebook is a step; run them in order. `01_*` must run
before anything downstream, since it produces `data/processed/bi_plus_geonim.csv`.

## Status

- [x] **Table 1** — Summary Statistics. `02_table1_summary_statistics.{py,ipynb}`.
  Computes dataset-wide counts and shares from `bi_plus_geonim.csv`: number of
  responsa and unique authors, earliest/median author birth year, average and
  median responsa per author, average word length, the share of responsa from
  the Geonic/Rishonim/Acharonim periods (by author birth year, split at 1480),
  and the share of responsa from each of the 8 regions. Excludes citations and
  footnotes (word_length <= 10) per the paper's Section III.A. Output saved to
  `data/processed/table1.csv`.
- [x] **Figure 1** — Responsa Density and Smoothed Median and Mean Word-Length
  Over Time. `03_figure1_density_and_length.{py,ipynb}`. Uses `interpolated_year`
  (see Notes below) with a 1500-nearest-neighbor smoothing window computed on
  the full word_length distribution (no outlier trimming) for both the median
  and mean curves. Reference lines at word length 250 and year 1492. Output
  saved to `figures/figure1.png`.
- [x] **Randomization analysis of the 1480-1505 gap** —
  `04_randomization_analysis_1480_1505.{py,ipynb}`. Tests whether the
  25-year paucity of responsa in 1480-1505 is plausible chance variation,
  using `interpolated_year` over the sample period 1250-1650. Three tests:
  (1) a fixed-window test assuming responsa are produced at a uniform rate
  (Monte Carlo simulation cross-checked against the exact Binomial and a
  Normal approximation); (2) a "look-elsewhere corrected" version of the
  same uniform-rate test that asks how often the emptiest 25-year window
  *anywhere* in a random draw is at least this empty; and (3) an empirical,
  assumption-free test that tiles the actual data into non-overlapping
  25-year windows and ranks 1480-1505 among them directly, with no
  uniformity or Poisson assumption. Results saved to
  `data/processed/randomization_1480_1505_results.csv`; diagnostic plots
  (including a bar chart of every non-overlapping window) saved to
  `figures/randomization_1480_1505.png`.
- [x] **Figure 2** — Share of Responsa by Region for Each Half Century,
  700-present. `05_figure2_regional_share_over_time.{py,ipynb}`. A
  100%-stacked area chart: for each 50-year bin, the 8 regions' shares of
  that half-century's responsa sum to 1.0, using the same word_length>=11
  sample as Table 1 and the `interpolated_year`/`region` columns from
  `01_build_dataset.py`. Drawn with sharp step transitions at each
  half-century boundary (not smooth interpolation). Output saved to
  `figures/figure2.png` and `data/processed/figure2_regional_shares_by_halfcentury.csv`.
  Note: the interactive Google Drive sign-in that `drive.mount()` needs
  only works from a real browser tab (it fails in Cowork's in-app browser
  sandbox, which blocks the popup) — if you hit a "credential propagation
  was unsuccessful" error running this notebook yourself, run it in a
  normal browser tab instead.
- [x] **Table 2 & Table 3** — Region Effects on Responsa Word Length, Rishonim
  (1000-1350 CE) and Acharonim (1550-1800 CE) periods.
  `06_table2_table3_region_regressions.{py,ipynb}`. Regresses `word_length`
  on region dummies (North Africa omitted, since it has the longest
  continuous span of responsa) and a dummy for each half-century in the
  window, to separate regional differences in length from the general
  time trend (Figure 1) and the shifting regional composition of responsa
  over time (Figure 2). Standard errors clustered by author. Uses the same
  word_length>=11 sample and `interpolated_year` as Figures 1-2. Results
  saved to `data/processed/table2_region_regression.csv` and
  `data/processed/table3_region_regression.csv`; formatted versions ready
  to paste into the paper are in `Table2_Rishonim_Region_Regression.docx`
  and `Table3_Acharonim_Region_Regression.docx`.

## Notes

- `01_build_dataset.py` / `.ipynb` includes one addition beyond the
  original notebooks: Geonic-era authors (from `geonim_len_stats.xlsx`)
  have no `country` recorded, so they fell into an "Other" region bucket
  unless assigned somewhere. They're now mapped to "West Asia (ex Israel)"
  (the Geonim were centered in Babylonia, roughly modern Iraq).
- The `.py` scripts and `.ipynb` notebooks are kept logically identical
  (same computation, same column names/output) — only the file-path
  convention differs (relative paths locally vs. `/content/gdrive/MyDrive/Responsa/Lengths/...` in Colab).
- `interpolated_year` dating rule (used by Figures 1-2 and Tables 2-3, not
  by Table 1): the first responsum in any volume is assumed written
  birth+30; the last is assumed written in the author's death year (or
  birth+60 if death is unrecorded). Each volume is interpolated
  independently — volumes are not assumed to be chronologically ordered
  relative to one another, since they may be arranged by topic.

## Google Drive

This folder is mirrored at `Responsa/Lengths` in your Google Drive, for
running the `.ipynb` notebooks in Colab. Because of upload-size limits on
this session's Drive connection, only the small text files (scripts,
notebooks, this README, and the formatted table .docx files) were pushed
automatically — copy the two raw `.xlsx` files from `data/raw/` into
Drive's `Responsa/Lengths/data/raw/` yourself (one-time step);
`data/processed/*.csv` and `figures/*.png` will regenerate when you run
the notebooks there, so those don't need to be copied.

## Publishing to GitHub

This folder (or the mirrored Drive copy) isn't connected to GitHub —
publishing it takes a one-time push from whichever copy you're working
from. From this local folder:

```
cd "path/to/Lengths"
git init
git add .
git commit -m "Initial commit: reproduction scripts, notebooks, and outputs"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Create the empty repo on GitHub first (github.com -> New repository) if it
doesn't exist yet, then swap in its URL for the `git remote add` line. After
that, `git add . && git commit -m "..." && git push` picks up any future
changes — from this folder or a copy of it; the Drive copy itself has no
independent path to GitHub, since Drive and GitHub don't sync directly.
