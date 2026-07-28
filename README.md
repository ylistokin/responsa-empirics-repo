# Trends in Responsa from the 7th Century to the Present: An Empirical Analysis

Replication code and derived data for:

> Yair Listokin, Tamara Morsel-Eisenberg, Jonathan Schler, and Roded Sharan.
> "Trends in Responsa from the 7th Century to the Present: An Empirical
> Analysis." *AJS Review* (forthcoming).

This paper presents the first large-scale empirical analysis of over
130,000 responsa (rabbinic legal opinions) from the Bar-Ilan Responsa
Project, examining how responsa length and geographic distribution have
changed over roughly 1,300 years of Jewish legal history.

## What's here

```
data/
  raw/                    Bar-Ilan Responsa Project metadata (inputs)
  processed/              Cleaned/merged dataset and output tables (generated)
scripts/
  01_build_dataset.py     Clean, merge, and annotate the raw metadata
  02_summary_statistics.py  Table 1 (corrected -- see REPRODUCIBILITY_NOTES.md)
  03_figures.py           Figures 1 and 2
  04_regressions.py       Tables 2 and 3 (region regressions)
figures/                  Generated figure images
docs/                     GitHub Pages site (project landing page)
REPRODUCIBILITY_NOTES.md  What reproduces exactly, and two small corrections
```

## Reproducing the results

```bash
python -m venv venv && source venv/bin/activate   # optional
pip install -r requirements.txt

python scripts/01_build_dataset.py       # -> data/processed/bi_plus_geonim.csv
python scripts/02_summary_statistics.py  # -> Table 1 (corrected)
python scripts/03_figures.py             # -> figures/figure1.png, figure2.png
python scripts/04_regressions.py         # -> Tables 2 and 3
```

Each script can be run independently once `01_build_dataset.py` has produced
`data/processed/bi_plus_geonim.csv`.

## Data

`data/raw/` contains two files exported from the Bar-Ilan Responsa Project
(Version 32):

- `full_stats_with_missing.xlsx` -- one row per responsum (Rishonim and
  Acharonim, ca. 1000 CE-present): author, book/collection, unit number,
  word count, author birth/death year, city, and country.
- `geonim_len_stats.xlsx` -- the same, for the Geonic era (ca. 7th-11th
  century CE).

`scripts/01_build_dataset.py` merges these, fills a small number of missing
author birth years/locations from hand-collected data, interpolates a year
of authorship for each responsum from its position within its volume,
excludes citation/footnote-only entries, and assigns each observation to one
of eight world regions. See the paper (Sections III.A-III.B) for the full
methodology and its limitations.

No full responsa text is redistributed here -- only bibliographic metadata
and word counts. See `DATA_LICENSE.md`.

## Corrections relative to the published manuscript

While assembling this repository we found that the manuscript's Table 1 was
generated before a filtering step described in the surrounding text was
applied, and that one coefficient in Table 2 doesn't fully reproduce from
the provided data. Neither affects the paper's substantive conclusions. Full
details, including a side-by-side comparison of every number, are in
[REPRODUCIBILITY_NOTES.md](REPRODUCIBILITY_NOTES.md).

## Citation

```bibtex
@article{listokin_responsa,
  author  = {Listokin, Yair and Morsel-Eisenberg, Tamara and Schler, Jonathan and Sharan, Roded},
  title   = {Trends in Responsa from the 7th Century to the Present: An Empirical Analysis},
  journal = {AJS Review},
  year    = {2026}
}
```

## License

Code (`scripts/`) is released under the [MIT License](LICENSE). Derived
data (`data/`) is released under [CC BY 4.0](DATA_LICENSE.md); see that file
for the underlying database's own terms.
