"""
Robustness check on Table 2 (Rishonim period region effects on responsa word
length): coarser time and region resolution.

Motivation: Table 2's 4-region, half-century-dummy specification has two
weaknesses when the sample is thinly spread. First, one of its four regions
(Italy and the Balkans) has only 124 responsa in this period, all from a
single author (see data/processed/table2_region_regression.csv) -- so that
coefficient reflects one person's writing, not a regional pattern. Second,
half-century dummies use up degrees of freedom the data may not support this
finely.

This script instead:
  1. Bins time by century rather than half-century (floor(year/100)*100).
  2. Collapses regions into two broad groups instead of four: "Ashkenaz"
     (Central and Western Europe) vs. "Sepharad + North Africa" (Iberia and
     North Africa combined -- the Sephardic and North African orbit).
     Italy and the Balkans is dropped from this comparison (it doesn't
     belong cleanly to either broad group, and per above is a single-author
     sample here).

Sample, dependent variable, and clustering are otherwise identical to
Table 2: word_length >= 11, responsa written 1000-1350 CE (interpolated_year),
OLS with standard errors clustered by author. "Sepharad + North Africa" is
the omitted category, so the reported coefficient is Ashkenaz's average
word-length difference from Sepharad + North Africa, holding century fixed.

Run 01_build_dataset.py first:
    python scripts/01_build_dataset.py
    python scripts/07_table2_robustness_coarse_bins.py
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PERIOD_START, PERIOD_END = 1000, 1350
OMITTED_GROUP = "Sepharad + North Africa"

GROUP_MAP = {
    "Central and Western Europe": "Ashkenaz (Central/Western Europe)",
    "Iberia": OMITTED_GROUP,
    "North Africa": OMITTED_GROUP,
}


def stars(p):
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")

# Same "responsa sample" used throughout the paper: word_length >= 11
df = df[df["word_length"] >= 11].copy()
df = df.dropna(subset=["interpolated_year", "region", "author_name"])

sub = df[(df["interpolated_year"] >= PERIOD_START) & (df["interpolated_year"] < PERIOD_END)].copy()

# Collapse region into the two broad groups; drop everything else
# (Italy and the Balkans, and any region not in GROUP_MAP for this period).
sub["group"] = sub["region"].map(GROUP_MAP)
dropped = sub[sub["group"].isna()]["region"].value_counts()
sub = sub.dropna(subset=["group"]).copy()

# Century bins instead of half-century bins
sub["century"] = (np.floor(sub["interpolated_year"] / 100) * 100).astype(int)

other_groups = sorted(g for g in sub["group"].unique() if g != OMITTED_GROUP)
sub["group"] = pd.Categorical(sub["group"], categories=[OMITTED_GROUP] + other_groups)

model = smf.ols(
    "word_length ~ C(group, Treatment(reference='Sepharad + North Africa')) + C(century)",
    data=sub,
)
res = model.fit(cov_type="cluster", cov_kwds={"groups": sub["author_name"]})

rows = []
prefix = "C(group, Treatment(reference='Sepharad + North Africa'))[T."
for group in other_groups:
    key = f"{prefix}{group}]"
    coef = res.params[key]
    se = res.bse[key]
    p = res.pvalues[key]
    rows.append({"group": group, "estimate": coef, "std_err": se, "p_value": p, "stars": stars(p)})
results = pd.DataFrame(rows)

title = "Robustness check: Rishonim period, century bins, 2 broad region groups"
print(f"\n{title}")
print("-" * len(title))
print(f"Period: {PERIOD_START}-{PERIOD_END} CE | N = {len(sub):,} responsa | "
      f"{sub['century'].nunique()} century dummies | omitted group: {OMITTED_GROUP}")
if len(dropped):
    print(f"Dropped from this comparison (not part of either broad group): "
          f"{dict(dropped)}")
print(f"\nGroup sizes:")
print(sub["group"].value_counts().to_string())
print(f"\nAuthors per group:")
print(sub.groupby("group", observed=True)["author_name"].nunique().to_string())
print(f"\n{'Group':<38}{'Estimate':>12}{'':<4}{'(SE)':>12}")
for _, r in results.iterrows():
    est = f"{r['estimate']:.2f}{r['stars']}"
    se = f"({r['std_err']:.2f})"
    print(f"{r['group']:<38}{est:>12}{'':<4}{se:>12}")
print("Note: * p<0.10, ** p<0.05, *** p<0.01. Linear regression of responsum")
print(f"word length on a region-group dummy (omitted: {OMITTED_GROUP}) and a")
print("dummy for each century in the sample. SEs clustered by author.")

os.makedirs("data/processed", exist_ok=True)
out_path = "data/processed/table2_robustness_century_region_groups.csv"
results.to_csv(out_path, index=False)
print(f"\nWrote {out_path}")
