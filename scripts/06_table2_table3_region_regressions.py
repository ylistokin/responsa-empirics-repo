"""
Reproduce Table 2 ("Rishonim Period Region Effects on Responsa Word Length")
and Table 3 ("Acharonim Period Region Effects on Responsa Word Length").

Per the paper (Section on "Regional Differences in Responsa"): comparisons
of mean/median responsa word length across regions confound geography with
the general upward time trend in responsa length (Figure 1), and region
composition itself shifts hugely over time (Figure 2). To separate the two,
the paper regresses word length on region dummies *within* two narrow
periods, controlling flexibly for time with a half-century dummy for each
half-century in the window:

    word_length_i = alpha + sum_r beta_r * Region_r,i + sum_t gamma_t * HalfCentury_t,i + e_i

North Africa is the omitted region (it has the longest continuous span of
responsa in the database -- see Figure 2), so every reported region
coefficient is that region's average responsa word-length difference from
North Africa, holding the half-century fixed. Standard errors are clustered
by author to account for serial correlation within an author's own responsa.

Table 2 uses the period 1000-1350 CE (the Rishonim). Table 3 uses 1550-1800
CE (the early Acharonim). Both periods, like Figures 1-2, use
`interpolated_year` (see 01_build_dataset.py) rather than author birth year.
Both use the same "responsa sample" as the rest of the paper: word_length >= 11
(Section III.A, "Excluding Non-Responsa").

Run 01_build_dataset.py first:
    python scripts/01_build_dataset.py
    python scripts/06_table2_table3_region_regressions.py
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

OMITTED_REGION = "North Africa"


def stars(p):
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def run_region_regression(df, period_start, period_end, table_label, table_title):
    """Fit word_length ~ region dummies (omit North Africa) + half-century
    dummies on the responsa written in [period_start, period_end), with
    standard errors clustered by author. Returns a tidy results DataFrame."""
    sub = df[(df["interpolated_year"] >= period_start) & (df["interpolated_year"] < period_end)].copy()

    regions_present = sub["region"].unique().tolist()
    if OMITTED_REGION not in regions_present:
        raise ValueError(f"{OMITTED_REGION} not present in {period_start}-{period_end} sample")
    other_regions = sorted(r for r in regions_present if r != OMITTED_REGION)
    sub["region"] = pd.Categorical(sub["region"], categories=[OMITTED_REGION] + other_regions)

    model = smf.ols(
        "word_length ~ C(region, Treatment(reference='North Africa')) + C(half_century)",
        data=sub,
    )
    res = model.fit(cov_type="cluster", cov_kwds={"groups": sub["author_name"]})

    rows = []
    prefix = "C(region, Treatment(reference='North Africa'))[T."
    for region in other_regions:
        key = f"{prefix}{region}]"
        coef = res.params[key]
        se = res.bse[key]
        p = res.pvalues[key]
        rows.append({
            "region": region,
            "estimate": coef,
            "std_err": se,
            "p_value": p,
            "stars": stars(p),
        })
    results = pd.DataFrame(rows).sort_values("estimate", ascending=False).reset_index(drop=True)

    n_half_centuries = sub["half_century"].nunique()
    print(f"\n{table_title}")
    print("-" * len(table_title))
    print(f"Period: {period_start}-{period_end} CE | N = {len(sub):,} responsa | "
          f"{len(other_regions) + 1} regions | {n_half_centuries} half-century dummies | "
          f"omitted region: {OMITTED_REGION}")
    print(f"{'Region':<32}{'Estimate':>12}{'':<4}{'(SE)':>12}")
    for _, r in results.iterrows():
        est = f"{r['estimate']:.2f}{r['stars']}"
        se = f"({r['std_err']:.2f})"
        print(f"{r['region']:<32}{est:>12}{'':<4}{se:>12}")
    print("Note: * p<0.10, ** p<0.05, *** p<0.01. Linear regression on region dummies")
    print(f"(omitted: {OMITTED_REGION}) and half-century dummies. SEs clustered by author.")

    os.makedirs("data/processed", exist_ok=True)
    out_path = f"data/processed/{table_label}_region_regression.csv"
    results.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")
    return results


df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")

# Same "responsa sample" used throughout the paper: word_length >= 11
df = df[df["word_length"] >= 11].copy()
df = df.dropna(subset=["interpolated_year", "region", "author_name"])

# Same half-century binning as Figure 2
df["half_century"] = (np.floor(df["interpolated_year"] / 50) * 50).astype(int)

table2 = run_region_regression(
    df, 1000, 1350,
    table_label="table2",
    table_title="Table 2: Rishonim Period Region Effects on Responsa Word Length",
)

table3 = run_region_regression(
    df, 1550, 1800,
    table_label="table3",
    table_title="Table 3: Acharonim Period Region Effects on Responsa Word Length",
)
