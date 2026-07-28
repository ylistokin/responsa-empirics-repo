"""
Reproduce Table 1 ("Responsa Project Summary Statistics by Time Period and
Geographic Region") from the analysis dataset.

Per the paper's Section III.A ("Excluding Non-Responsa"), observations with
a word length of 10 or below are citations/footnotes rather than true
responsa and are excluded from the analysis sample (n=131,869).

NOTE ON THE PUBLISHED TABLE: the Table 1 embedded in the accepted manuscript
was generated from the pre-filter dataframe (n=134,343) -- the word_length
>= 11 filtering step is present in the original notebook but was commented
out before the table was generated. Every number in the paper's prose
(Section III.C, "Summary Statistics") matches the correctly-filtered
n=131,869 sample computed below, not the table. See REPRODUCIBILITY_NOTES.md
for the full comparison.

Run 01_build_dataset.py first.
"""
import pandas as pd

df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")

# Exclude citations/footnotes: word_length <= 10 (paper Section III.A)
df_filtered = df[df["word_length"] >= 11].copy()

num_responsa = len(df_filtered)
unique_authors = df_filtered["author_name"].nunique()
avg_obs_per_author = num_responsa / unique_authors
median_obs_per_author = df_filtered["author_name"].value_counts().median()
avg_word_length = df_filtered["word_length"].mean()

df_time = df_filtered[["birth_year", "source"]].dropna()
geonim_responsa = df_time[df_time["source"] == "dataset_2"].shape[0]
rishonim_responsa = df_time[(df_time["source"] == "dataset_1") & (df_time["birth_year"] <= 1480)].shape[0]
acharonim_responsa = df_time[df_time["birth_year"] > 1480].shape[0]
share_geonim = geonim_responsa / num_responsa * 100
share_rishonim = rishonim_responsa / num_responsa * 100
share_acharonim = acharonim_responsa / num_responsa * 100

df_births = df_filtered[["author_name", "birth_year"]].dropna().drop_duplicates()
earliest_birth = int(df_births["birth_year"].min())
median_birth = round(df_births["birth_year"].median(), 0)
latest_birth = int(df_births["birth_year"].max())

region_counts = df_filtered["region"].value_counts()
region_shares = region_counts / num_responsa * 100

rows = [
    ("Number of responsa", f"{num_responsa:,}"),
    ("Number of unique authors", f"{unique_authors:,}"),
    ("Earliest author birth year", f"{earliest_birth}"),
    ("Median author birth year", f"{median_birth:.0f}"),
    ("Latest author birth year", f"{latest_birth:.0f}"),
    ("Avg. responsa per author", f"{avg_obs_per_author:.0f}"),
    ("Median responsa per author", f"{median_obs_per_author:.0f}"),
    ("Avg. word length", f"{avg_word_length:.0f}"),
    ("Share of Geonic responsa", f"{share_geonim:.1f}%"),
    ("Share of responsa by Rishonim", f"{share_rishonim:.1f}%"),
    ("Share of responsa by Acharonim", f"{share_acharonim:.1f}%"),
]
for region, share in region_shares.items():
    rows.append((f"Share of responsa from {region}", f"{share:.1f}%"))

summary_df = pd.DataFrame(rows, columns=["Statistic", "Result"])

title = "Table 1 (corrected). Responsa Project Summary Statistics by Time Period and Geographic Region"
print(f"\n{title}\n{'-' * len(title)}\n")
for i, (stat, result) in enumerate(rows, start=1):
    print(f"{i:>2}. {stat:<50} {result:>15}")

summary_df.to_csv("data/processed/table1_corrected.csv", index=False)
print("\nWrote data/processed/table1_corrected.csv")
