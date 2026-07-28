"""
Reproduce Table 2 (Rishonim period, 1000-1350) and Table 3 (early
Acharonim period, 1550-1800): OLS regressions of responsa word length on
region dummies and half-century dummies, with standard errors clustered by
author. North Africa is the omitted/reference region in both.

Run 01_build_dataset.py first.

NOTE: Table 3 reproduces exactly against the published manuscript. Table 2's
Italy/Balkans and Central & Western Europe coefficients reproduce closely;
the Iberia coefficient comes out ~34 words lower than the published value
(241.8 vs. 275.88), which does not affect the qualitative conclusion (only
Italy and the Balkans is statistically significant in this period). See
REPRODUCIBILITY_NOTES.md.
"""
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")
df = df[df["word_length"] >= 11]  # exclude citations/footnotes, per Section III.A


def region_regression(d, year_lo, year_hi, label):
    d = d[["word_length", "region", "interpolated_year", "author_name"]].dropna()
    d = d[d["interpolated_year"].between(year_lo, year_hi)].copy()
    d["half_century"] = (d["interpolated_year"] // 50) * 50
    d["region"] = pd.Categorical(
        d["region"],
        categories=sorted(d["region"].unique(), key=lambda x: x != "North Africa"),
        ordered=True,
    )
    model = smf.ols("word_length ~ C(region) + C(half_century)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["author_name"]}
    )

    print(f"\n{label}  (n={len(d)}, omitted region = North Africa)")
    print("-" * len(label))
    for name in model.params.index:
        if "C(region)" in name:
            region_name = name.replace("C(region)[T.", "").rstrip("]")
            coef, se, p = model.params[name], model.bse[name], model.pvalues[name]
            stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
            print(f"  {region_name:<30} {coef:8.2f}{stars:<3} ({se:.2f})")
    return model


region_regression(df, 1000, 1350, "Table 2: Rishonim Period (1000-1350) Region Effects on Word Length")
region_regression(df, 1550, 1800, "Table 3: Acharonim Period (1550-1800) Region Effects on Word Length")
