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

This script started as a direct, cleaned-up port of the authors' original
`Summary Statistics.ipynb` (which ran on Google Colab against files on
Google Drive), adapted to run locally against files in this folder.
A Colab-notebook version of this same step is in notebooks/01_build_dataset.ipynb.

DATING METHOD (`interpolated_year`): we interpolate as follows. The first
responsum in any volume by an author is assumed to have been written
MIN_AGE (30) years after the author's birth year. The last responsum in
any volume is assumed to be written in the author's year of death. Since
volumes are often arranged by topic rather than chronologically, every
volume by a single author is interpolated by this same rule independently
-- we do NOT assume that some volumes were written earlier than other
volumes by the same author (i.e. volumes are not chained/sequenced; each
one spans the full [birth+30, death] range on its own). When the year of
death is missing, we assume the author dies at age 60.

Implementation note: "first" and "last" are taken as the 0th and (N-1)th
responsum within (author, volume) by TRUE POSITION IN THE VOLUME (N =
number of responsa in that volume) -- i.e. responsum i of N is placed at
birth+30 + (i/(N-1)) * (death - birth - 30). A volume with only a single
responsum has no distinct first/last, so it is placed at the midpoint of
[birth+30, death].

True position is recovered from the `unit` column, which records each
responsum's siman (paragraph) number, or occasionally a chapter/part/
sermon/etc. number, as printed in the original volume (e.g. "סימן שכח" =
Siman 328) -- see parse_unit() below. This matters because the raw data's
ROW ORDER is not the same as volume order: it turns out the rows are
overwhelmingly sorted by word_length instead (row order vs. word_length
rank correlates ~0.97-1.0 across large volumes; the correlation between
the TRUE siman number and word_length is ~0.01, i.e. no relationship).
Using row order as a stand-in for volume order, as earlier versions of
this script did, therefore systematically dated an author's SHORTEST
responsa to early in life and LONGEST responsa to near death, dataset-
wide -- an artifact of the data export, not a real biographical pattern.
parse_unit() decodes the printed number where possible; where the `unit`
text has no decodable number (front matter like a preface or table of
contents, back matter like addenda or notes, or a bare section label with
no attached number -- about 3.2% of rows combined), the responsum is
placed at the start (front matter), end (back matter), or -- when there is
no positional signal at all -- dispersed uniformly at random across the
author's range (fixed seed, for reproducibility) rather than guessing a
false position or collapsing every such responsum onto a single shared
year. An earlier version of this script placed all no-signal responsa at
the exact midpoint of the author's range; that collapsed any author with
many such responsa (e.g. one whose volumes are indexed by plain letter/
item number rather than siman number, which parse_unit() cannot decode)
onto a single artificial year, distorting Figure 1's smoothed curves
around that year.

Exception: one entry, "תשובות הגאונים" (birth_year=850), is a modern
anthology of several distinct scholarly editions of Geonic responsa, not
an individual -- see DATE_RANGE_OVERRIDE below for its date range and the
reasoning behind it. Its internal ordering still uses true siman position,
per the same parse_unit() logic as everything else.

Run this script from the Lengths/ folder:
    python scripts/01_build_dataset.py
"""
import re

import numpy as np
import pandas as pd

RAW = "data/raw"
OUT = "data/processed"
MIN_AGE = 30  # first responsum in a volume assumed written this many years after birth

# ---------------------------------------------------------------------------
# Decode the `unit` column into a true position within its volume.
#
# `unit` records how each responsum was labeled in the original printed
# volume -- almost always a siman (paragraph) number in Hebrew numerals
# (e.g. "סימן שכח" = Siman 328), occasionally a chapter/part/sermon/etc.
# number instead, and sometimes no number at all (front matter like a
# preface, back matter like addenda, or a bare section label). See the
# module docstring for why this replaces raw row order.
# ---------------------------------------------------------------------------
GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def _gematria(letters):
    return sum(GEMATRIA.get(ch, 0) for ch in letters)


# Word prefixes that introduce a genuine, decodable position number.
_NUMBERED_PREFIXES = [
    "סימן", "פרק", "חלק", "כרך", "דרוש", "מאמר", "שאלה", "קונטרס",
]
# `unit` text indicating front matter (belongs at the very start of a volume).
_FRONT_MATTER_MARKERS = ["הקדמה", "מבוא", "פתיחה", "דברי פתיחה", "תוכן העניינים", "תוכן עניינים"]
# `unit` text indicating back matter (belongs at the very end of a volume).
_BACK_MATTER_MARKERS = ["מילואים", "נספח", "השמטות", "קונטרס אחרון", "הערות", "הגהות", "סיום"]


def parse_unit(unit):
    """Decode a `unit` string into (order_key, category).

    order_key is a float used to rank responsa within a volume:
    -inf for front matter, +inf for back matter, the decoded number for
    anything with a genuine siman/chapter/etc. number, and NaN when no
    position can be recovered at all (handled separately downstream).
    """
    if not isinstance(unit, str):
        return (np.nan, "null")
    s = unit.strip()
    for prefix in _NUMBERED_PREFIXES:
        m = re.match(rf"^{prefix}\s+([א-ת]+)", s)
        if m:
            return (float(_gematria(m.group(1))), "numbered")
    m = re.match(r"^מערכת\s+([א-ת]+)\s+אות\s+([א-ת]+)", s)
    if m:
        # alphabetical-index scheme: combine the two letters into one key
        return (float(_gematria(m.group(1)) * 1000 + _gematria(m.group(2))), "numbered")
    if any(k in s for k in _FRONT_MATTER_MARKERS):
        return (-np.inf, "front_matter")
    if any(k in s for k in _BACK_MATTER_MARKERS):
        return (np.inf, "back_matter")
    return (np.nan, "unrecognized")


# ---------------------------------------------------------------------------
# 1. Load and concatenate the two raw metadata files
# ---------------------------------------------------------------------------
df = pd.read_excel(f"{RAW}/full_stats_with_missing.xlsx")
df_geonim = pd.read_excel(f"{RAW}/geonim_len_stats.xlsx")

df["source"] = "dataset_1"       # Bar-Ilan Responsa Project (Rishonim/Acharonim)
df_geonim["source"] = "dataset_2"  # Geonim-era responsa

df = pd.concat([df, df_geonim], ignore_index=True)

# True position of each responsum within (author, book), decoded from the
# printed siman/chapter/etc. number in `unit` -- see parse_unit() above.
# Replaces the old row-order-based unit_index, which turned out to track
# word_length (the data's actual sort order) rather than volume position.
_parsed = df["unit"].apply(parse_unit)
df["order_key"] = _parsed.apply(lambda t: t[0])
df["order_category"] = _parsed.apply(lambda t: t[1])

# Computed once, vectorized, over the whole dataframe (rather than inside
# the per-author groupby below) to avoid a pandas groupby.apply quirk where
# a group containing only a single book collapses the returned Series into
# a malformed one-row DataFrame. Grouped by (author_name, birth_year,
# book_name) -- birth_year is included because one author_name in this
# dataset ("תשובות הגאונים") covers two distinct birth-year entries that
# happen to share book_name text; keeping birth_year in the key prevents
# their responsa from being ranked against each other.
_group_cols = ["author_name", "birth_year", "book_name"]
_orderable_mask = df["order_category"].isin(["numbered", "front_matter", "back_matter"])

# Responsa with no decodable position at all ("unrecognized" unit text, or
# no unit text/"null") get an independent Uniform(0,1) relative position --
# spreading them across the author's full active period -- rather than a
# single shared value. A fixed seed keeps this reproducible. Drawing
# per-row from a distribution (rather than ranking these rows by anything
# derived from the raw data, e.g. row order) is deliberate: row order is
# known to track word_length (see module docstring), so ranking by it
# would reintroduce exactly the length-vs-position bias parse_unit() was
# built to avoid.
_DISPERSE_SEED = 20260907
_disperse_rng = np.random.default_rng(_DISPERSE_SEED)
_non_orderable_mask = ~_orderable_mask
relative_position_raw = pd.Series(0.5, index=df.index)
relative_position_raw.loc[_non_orderable_mask] = _disperse_rng.uniform(
    0.0, 1.0, size=int(_non_orderable_mask.sum())
)
_orderable = df[_orderable_mask]
_ranks = _orderable.groupby(_group_cols, dropna=False)["order_key"].rank(method="first")
_sizes = _orderable.groupby(_group_cols, dropna=False)["order_key"].transform("size")
relative_position_raw.loc[_orderable.index] = np.where(
    _sizes > 1, (_ranks - 1) / (_sizes - 1).clip(lower=1), 0.5
)
df["relative_position_raw"] = relative_position_raw

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
# 3. Interpolate a year of authorship for each responsum.
#    First responsum in a volume -> birth+MIN_AGE. Last responsum in a
#    volume -> death. Each volume is interpolated independently (volumes
#    are NOT chained/sequenced relative to one another). A 60-year
#    lifespan is assumed if death_year is missing. See module docstring.
#
#    Grouped by (author_name, birth_year) rather than author_name alone:
#    one author_name in the raw data -- "תשובות הגאונים" -- actually
#    covers two distinct entries with different recorded birth years
#    (800 and 850); grouping by author_name alone would silently apply
#    only the first-encountered birth year to every row sharing that
#    name. This is the only author_name in the dataset with more than
#    one distinct birth_year, so this change affects nothing else.
#
#    DATE_RANGE_OVERRIDE below replaces the birth+MIN_AGE/death (or
#    birth+60 default) window for specific (author_name, birth_year)
#    entries that are not individual people:
#
#    "תשובות הגאונים" (birth_year=850, no death_year recorded): this
#    entry is not one person -- it's five 19th-century scholarly
#    editions collecting responsa from many different historical Geonim
#    (Sha'arei Tzedek; Cassel's Geonim Kadmonim; Sha'arei Teshuva; the
#    Musafia and Coronel editions; Harkavy's corpus; and Geonei Mizrach
#    U'Maarav). The named Geonim represented across these editions span
#    roughly Yehudai Gaon (mid-8th century) to Hai Gaon (d. 1038 CE, the
#    last major Gaon). More than half of all surviving Geonic responsa
#    come from the final generation -- Sherira Gaon and his son Hai
#    Gaon, who led the Pumbedita academy from roughly 968-1038 CE -- so
#    the true distribution is weighted heavily toward that later end,
#    not spread evenly across the full 750-1038 window. (The separate
#    "תשובות רב נטרונאי גאון" entry, birth_year=800, is a real
#    individual -- Natronai ben Hilai, Gaon of Sura c. 857-865 -- and
#    keeps the standard birth+30/birth+60 treatment.)
# ---------------------------------------------------------------------------
DATE_RANGE_OVERRIDE = {
    # (author_name, birth_year): (start_year, end_year, skew)
    # skew is the exponent applied to each responsum's relative position
    # within its volume before mapping onto [start_year, end_year]. skew=1
    # is the same plain linear interpolation used everywhere else; skew<1
    # pushes more responsa toward end_year. skew=0.4 is chosen so the
    # MEDIAN interpolated year lands at 968 (the start of Sherira Gaon's
    # tenure) -- i.e. roughly half the responsa fall in the last ~70 of
    # these 288 years, matching the "more than half from Sherira/Hai" fact
    # above (median of Uniform(0,1)**0.4 is 0.5**0.4 ~= 0.76, and
    # 750 + 0.76*(1038-750) ~= 968).
    ("תשובות הגאונים", 850.0): (750, 1038, 0.4),
}


def assign_interpolated_year(group):
    author = group["author_name"].iloc[0]
    birth = group["birth_year"].iloc[0]
    death = group["death_year"].iloc[0]

    if pd.isna(birth):
        group["interpolated_year"] = np.nan
        return group

    override = DATE_RANGE_OVERRIDE.get((author, birth))
    if override is not None:
        start_year, end_year, skew = override
    else:
        if pd.isna(death):
            death = birth + 60
        start_year = birth + MIN_AGE
        end_year = death
        skew = 1.0

    # True position within (author, book), decoded from `unit` rather than
    # raw row order -- computed once for the whole dataframe above (see
    # relative_position_raw), since a per-group groupby.apply here hits a
    # pandas edge case for single-book groups.
    relative_position = group["relative_position_raw"].astype(float) ** skew

    group["interpolated_year"] = start_year + relative_position * (end_year - start_year)
    return group


df = df.groupby(["author_name", "birth_year"], dropna=False, group_keys=False).apply(assign_interpolated_year)
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


def map_region(row):
    country = row["country"]
    for region, countries in region_map.items():
        if country in countries:
            return region
    if pd.isna(country) and row["source"] == "dataset_2":
        # Geonim-era authors have no country recorded in geonim_len_stats.xlsx;
        # the Geonim were centered in Babylonia (modern Iraq).
        return "West Asia (ex Israel)"
    return "Other"


df_filtered["region"] = df_filtered.apply(map_region, axis=1)

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
