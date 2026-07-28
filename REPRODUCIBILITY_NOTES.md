# Reproducibility notes

This document records what was checked when this repository was assembled
from the authors' original Google Colab notebooks and data exports, and
flags a few small discrepancies between the data pipeline and the published
manuscript.

## What reproduces exactly

- **Figure 1** and **Figure 2** reproduce pixel-for-pixel from
  `data/processed/bi_plus_geonim.csv` via `scripts/03_figures.py`.
- **Table 3** (Acharonim period, 1550-1800 region regression) reproduces
  exactly via `scripts/04_regressions.py`, once the word_length >= 11 filter
  described in the paper (Section III.A) is applied.

## What needed a correction

**Table 1** in the accepted manuscript (134,343 responsa; avg. word length
1274; etc.) was computed *before* the word-length >= 11 filter described
immediately above it in the paper's text ("Excluding Non-Responsa"). The
filtering line exists in the original `Summary Statistics.ipynb` but was
commented out before the table was generated, so Table 1's own footnote
("Observations with 10 words or less are excluded") does not match its
own numbers.

Every number in the paper's *prose* (Section III.C, "Summary Statistics")
instead matches the correctly-filtered n=131,869 sample:

| Statistic | Published Table 1 | Correct (n=131,869) | Paper's prose |
|---|---|---|---|
| Number of responsa | 134,343 | 131,869 | "almost 131,000" |
| Avg. responsa/author | 419 | 411 | "over 400" |
| Median responsa/author | 172 | 170 | 172 |
| Avg. word length | 1,274 | 1,280 | -- |
| Geonim share | 2.5% | 2.6% | 2.6% |
| Rishonim share | 14.7% | 14.3% | "over 14%" |
| Acharonim share | 82.8% | 83.2% | 83% |
| Eastern Europe | 33.3% | 33.5% | "about one third" |
| Israel/Palestine | 25.4% | 25.3% | "approximately one quarter" |
| North Africa | 10.5% | 10.3% | 10.3% |
| North America/Australia | 7.1% | 7.2% | 7.2% |
| Iberia | 4.7% | 4.4% | 4.4% |
| Italy and the Balkans | 4.2% | 4.3% | 4.3% |

`scripts/02_summary_statistics.py` produces the corrected table
(`data/processed/table1_corrected.csv`).

**Table 2** (Rishonim period, 1000-1350 region regression): recomputing from
`bi_plus_geonim.csv` reproduces the Italy and the Balkans coefficient
closely (734.6 vs. 739.14 published) and Central & Western Europe closely
(225.9 vs. 224.08 published), but the Iberia coefficient comes out at 241.8
rather than the published 275.88 -- about a 34-word gap not explained by
rounding. This does not change the paper's qualitative conclusion (only
Italy and the Balkans is statistically significant in this period, at the
1% level). A leftover file from the original working folder
(`region_regression_results_with_stars.docx`) contains yet a third, much
smaller set of coefficients, suggesting this particular regression was run
more than once during drafting on slightly different snapshots of the data;
it is not included in this repository.

## Two softer, descriptive claims worth a look

- The paper describes the word-length increase from ~1300-1320 to the
  early-17th-century peak as "almost triple." Recomputing the smoothed
  median, the peak (~1618) is about 1,175 words against a baseline of
  ~293-304 words around 1300-1320 -- a ratio closer to 3.9-4x.
- The paper describes responsa length "reaching a new steady state of
  approximately 750 words by the beginning of the 18th century." The
  smoothed median actually dips as low as ~640-680 through much of the
  18th century (e.g., ~676 at 1720, ~638 at 1780) before settling near 750
  around 1800 -- i.e., toward the *end* of the century.

## Files intentionally excluded from this repository

Two files in the original working folder (`sampled_opinions2.xlsx` and
`word11_15_length_sample.xlsx`) contain verbatim Hebrew excerpts pulled from
the Bar-Ilan Responsa Project for the manual spot-checks described in
Section III.A ("random sample of 15... observations"). Because the
underlying database is copyrighted, those excerpts are not redistributed
here; the spot-check methodology is described in the paper's text instead.
Draft/working files (older manuscript drafts, a stray regression export)
were also excluded as clutter unrelated to reproducing the published
results.
