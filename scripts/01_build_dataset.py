"""
Build the analysis dataset for "Trends in Responsa from the 7th Century to
the Present: An Empirical Analysis" (Listokin, Morsel-Eisenberg, Schler &
Sharan).

Inputs  (data/raw/):
    full_stats_with_missing.xlsx   Bar-Ilan Responsa Project metadata
                                    (author, book, unit, word_length,
                                    birth/death year, city/country)
    geonim_len_stats.xlsx          Metadata for Geonic-era responsa

Output (data/processed/):
    bi_plus_geonim.csv              Cleaned, merged, region- and
                                     year-annotated dataset used to build
                                     Figures 1-2 and Tables 1-3.

This script is a direct, cleaned-up port of `Summary Statistics.ipynb`,
adapted to run locally (the original ran on Google Colab against files on
Google Drive).
"""
import numpy as np
import pandas as pd

RAW = "data/raw"
OUT = "data/processed"

# ---------------------------------------------------------------------------
# 1. Load and concatenate the two raw metadata files
# ---------------------------------------------------------------------------
df = pd.read_excel(f"{RAW}/full_stats_with_missing.xlsx")
df_geonim = pd.read_excel(f"{RAW}/geonim_len_stats.xlsx")

df["source"] = "dataset_1"       # Bar-Ilan Responsa Project (Rishonim/Acharonim)
df_geonim["source"] = "dataset_2"  # Geonim-era responsa

df = pd.concat([df, df_geonim], ignore_index=True)

# Order of each responsum within (author, book) -- used to interpolate years
df["unit_index"] = df.groupby(["author_name", "book_name"]).cumcount() + 1

# ---------------------------------------------------------------------------
# 2. Manually fill in birth year / country for ~45 authors missing metadata
#    (hand-collected by the authors; see Summary Statistics.ipynb cell 5)
# ---------------------------------------------------------------------------
manual_fill = {
    "ר' יעקב ישראל חגיז": (1620, "ארץ ישראל"),
    "ר' יוסף חיים אל חכם": (1851, "עיראק"),
    "ר' אריה ליבוש ליפשיץ": (1760, "פולין"),
    "ר' משה יהושע יהודה לייב דיסקין": (1817, "ליטא, ארץ ישראל"),
    "ר' יוסף משאש": (1892, "מרוקו, ישראל"),
    "ר' יהודה אריה גרוסנס": (1870, "פולין"),
    "ר' פסח אליהו פלק": (1878, "פולין"),
    "ר' משה גרינוולד": (1853, "הונגריה"),
    "ר' אריה צבי פרומר": (1884, "פולין"),
    "ר' יואב יהושע וינגרטן": (1845, "פולין"),
    "ר' שמואל יצחק שור": (1873, "פולין"),
    "ר' ברוך לאווסקי": (1867, "פולין"),
    "ר' מאיר די בוטון": (1575, "טורקיה"),
    "ר' מרדכי זיסקינד רוטנברג": (1830, "פולין"),
    "ר' שמואל ענגיל": (1853, "פולין"),
    "ר' יוסף אליהו הנקין": (1881, 'בלארוס, ארה"ב'),
    "ר' שלום משאש": (1909, "מרוקו, ישראל"),
    "ר' יהודה הרצל הנקין": (1945, 'ארה"ב, ישראל'),
    "ר' יצחק אבולעפיה": (1824, "ארץ ישראל"),
    "ר' שמואל אבוהב": (1610, "איטליה"),
    "ר' שלמה יהודה טאבאק": (1832, "הונגריה"),
    "ר' שלמה זלמן ליפשיץ": (1765, "פולין"),
    "ר' יעקב אבן יחיא": (1470, "פורטוגל"),
    "ר' יחיאל באסן": (1653, "איטליה"),
    "ר' סיני ספיר": (1820, "ליטא"),
    "ר' יחזקאל קצנלנפוגן": (1668, "פולין"),
    "ר' יוסף אירגאס": (1685, "איטליה"),
    "ר' אברהם פיוטרקובסקי": (1897, "פולין"),
    "ר' רפאל כץ": (1770, "פולין"),
    "ר' יעקב מאיר פאדווא": (1890, "הונגריה, אנגליה"),
    "ר' אברהם ליטש רוזנבוים": (1860, "הונגריה"),
    "ר' ישראל בעלסקי": (1938, 'ארה"ב'),
    "ר' יעקב ברוכין": (1879, "פולין"),
    "ר' מרדכי פארהאנד": (1872, "הונגריה"),
    "ר' יחיאל העליר": (1814, "הונגריה"),
    "ר' אברהם ישראל זאבי": (1869, "פולין"),
    "ר' אליהו בקשי דורון": (1941, "ישראל"),
    "ר' ישראל ניסן קופרשטוך": (1900, "פולין"),
    "ר' בן ציון בלום": (1908, "הונגריה"),
    "ר' אהרן לפפא": (1790, "פולין"),
    'ר\' חיים ב"ר שמחה הכהן רפפורט': (1700, "פולין"),
    "ר' משה שטרן": (1914, 'הונגריה, ארה"ב'),
    'ר\' ראובן ב"ר בצלאל הכהן רפפורט': (1750, "פולין"),
    "ר' אריה יהודה ליב תאומים": (1813, "הונגריה"),
    'ר\' שלמה ב"ר יצחק לבית לוי': (1020, "צרפת"),
    "ר' מאיר אריק": (1855, "פולין"),
}

country_translation = {
    "ארץ ישראל": "Israel",
    "עיראק": "Iraq",
    "פולין": "Poland",
    "ליטא": "Lithuania",
    "ליטא, ארץ ישראל": "Lithuania",
    "מרוקו, ישראל": "Morocco",
    "מרוקו": "Morocco",
    "הונגריה": "Hungary",
    "איטליה": "Italy",
    'בלארוס, ארה"ב': "United States",
    'ארה"ב': "United States",
    'ארה"ב, ישראל': "Israel",
    "פורטוגל": "Portugal",
    "טורקיה": "Turkey",
    "הונגריה, אנגליה": "Hungary",
    'הונגריה, ארה"ב': "Hungary",
    "צרפת": "France",
}

for name in manual_fill:
    birth, loc = manual_fill[name]
    manual_fill[name] = (birth, country_translation.get(loc, loc))


def fill_missing(row):
    if pd.isna(row["birth_year"]) and row["author_name"] in manual_fill:
        row["birth_year"] = manual_fill[row["author_name"]][0]
    if pd.isna(row["country"]) and row["author_name"] in manual_fill:
        row["country"] = manual_fill[row["author_name"]][1]
    return row


df = df.apply(fill_missing, axis=1)

# ---------------------------------------------------------------------------
# 3. Interpolate a year of authorship for each responsum
#    (evenly distributed across [birth+30, death] by order within the book;
#    a 60-year lifespan is assumed if death_year is missing)
# ---------------------------------------------------------------------------
def interpolate_across_books(group):
    birth = group["birth_year"].iloc[0]
    death = group["death_year"].iloc[0]

    if pd.isna(birth):
        group["interpolated_year"] = np.nan
        return group

    if pd.isna(death):
        death = birth + 60

    start_year = birth + 30
    end_year = death

    max_by_book = group.groupby("book_name")["unit_index"].transform("max")
    group["relative_position"] = group["unit_index"] / max_by_book
    group["interpolated_year"] = start_year + group["relative_position"] * (end_year - start_year)
    return group


df = df.groupby("author_name", group_keys=False).apply(interpolate_across_books)
df["year"] = df["interpolated_year"]
df["age_at_death"] = df["death_year"] - df["birth_year"]

# ---------------------------------------------------------------------------
# 4. Clean word_length; drop citation/footnote-only entries
#    (observations whose book name marks them as a note/gloss, e.g. הערות)
# ---------------------------------------------------------------------------
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")
df_filtered = df[~df["book_name"].str.contains("הערות|הגהות", na=False)].copy()

# ---------------------------------------------------------------------------
# 5. Assign a geographic region from country
# ---------------------------------------------------------------------------
region_map = {
    "Eastern Europe": [
        "Russia", "Poland", "Ukraine", "Lithuania", "Latvia", "Estonia",
        "Belarus", "Hungary", "Czech Republic", "Slovakia", "Romania", "Bulgaria",
    ],
    "Central and Western Europe": [
        "France", "Germany", "Netherlands", "Belgium", "Switzerland",
        "Austria", "United Kingdom", "England", "Ireland",
    ],
    "Italy and the Balkans": [
        "Italy", "Greece", "Yugoslavia", "Bosnia", "Serbia", "Croatia", "Bosnia-Herzegovina",
    ],
    "Iberia": ["Spain", "Portugal"],
    "North Africa": ["Morocco", "Algeria", "Tunisia", "Libya", "Egypt"],
    "Israel/Palestine": [
        "Israel", "Palestine", "Ottoman Palestine", "Mandatory Palestine",
        "Eretz Israel", "ישראל",
    ],
    "West Asia (ex Israel)": [
        "Saudi Arabia", "Yemen", "Oman", "United Arab Emirates", "Arabia", "Hejaz",
        "Syria", "Turkey", "Iraq", "Iran", "Mesopotamia", "Persia",
        "Lebanon", "Jordan", "Qatar", "Bahrain", "Kuwait", "Georgia", "Armenia", "Azerbaijan",
    ],
    "North America/Australia": ["United States", "USA", "Canada", "Mexico", "Australia"],
}


def map_region(country):
    for region, countries in region_map.items():
        if country in countries:
            return region
    return "Other"


df_filtered["region"] = df_filtered["country"].apply(map_region)

# ---------------------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------------------
import os
os.makedirs(OUT, exist_ok=True)
df_filtered.to_csv(f"{OUT}/bi_plus_geonim.csv", index=False)
print(f"Wrote {OUT}/bi_plus_geonim.csv  ({len(df_filtered):,} rows)")
print("Note: this file still includes observations with word_length <= 10")
print("(short citations/footnotes not yet excluded -- see 02_summary_statistics.py")
print("and the paper's Section III.A, 'Excluding Non-Responsa').")
