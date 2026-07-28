# Original notebooks

These are the authors' original Google Colab notebooks, unmodified except
for removal of Google Drive mount cells being unnecessary here (they still
reference `/content/gdrive/...` paths and will not run as-is outside Colab).

They are kept for provenance/transparency. For a clean, locally-runnable
reproduction of the paper's figures and tables, use the scripts in
`../scripts/` instead, which are direct, path-adjusted ports of the logic
in these notebooks:

- `Summary Statistics.ipynb` -> `../scripts/01_build_dataset.py` (data
  cleaning/merging) and `../scripts/02_summary_statistics.py` (Table 1)
- `Responsa_time.ipynb` -> `../scripts/03_figures.py` (Figures 1-2) and
  `../scripts/04_regressions.py` (Tables 2-3)
- `Responsa.ipynb` -- exploratory/superseded by the above
