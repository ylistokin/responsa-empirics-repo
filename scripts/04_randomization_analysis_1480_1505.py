"""
Randomization analysis: how likely is the 1481-1505 paucity of responsa
under a random (uniform) null model?

Question: over the sample period 1250-1650, is it surprising -- if
responsa were simply produced/dated at a constant average rate across
that whole period -- to see as few responsa as we actually observe in
the 25-year window 1481-1505 (a true 25-calendar-year span: 1481, 1482,
..., 1505)?

Data: `interpolated_year` from data/processed/bi_plus_geonim.csv, built
by 01_build_dataset.py (first responsum in a volume -> birth+30, last ->
death, each volume interpolated independently; see that script's
docstring for the full rule). Uses the same "responsa sample" as every
other figure/table in the paper: word_length >= 11 (Section III.A,
"Excluding Non-Responsa"), so citations/footnotes aren't counted as
responsa when assessing how sparse 1481-1505 is.

Four comparisons are reported. 1481-1505 was picked BECAUSE it looks sparse
in the real data, so testing only that one fixed window overstates
significance (the "look-elsewhere" / multiple-comparisons problem) --
Tests 1-2 use a uniform-random null and correct for that; Test 3 sidesteps
the uniformity assumption entirely by comparing against the data itself.
A preliminary, even simpler comparison (0, below) is reported first: the
observed count against the plain period-wide average responsa count per
25-year span, with no simulation or tiling choices involved at all.

0. SIMPLE PERIOD-WIDE AVERAGE (no assumptions, no simulation)
   1250-1650 is exactly 400 years, i.e. exactly 16 non-overlapping 25-year
   spans. Since those 16 spans partition the whole sample period with no
   remainder, their counts must sum to N -- so their mean is *exactly*
   N/16, an arithmetic fact rather than an estimate. This is the plainest
   possible yardstick: how does the observed 1481-1505 count compare to
   the average 25-year span anywhere in 1250-1650?

1. FIXED-WINDOW TEST (assumes uniformity)
   Null: each of the N responsa dated in 1250-1650 is an independent
   draw from Uniform(1250, 1650). Under that null, the count landing in
   any fixed 25-year sub-window follows Binomial(N, 25/400). We simulate
   this directly (randomization: draw N uniform years, count how many
   fall in [1480, 1505)) and also report the exact Binomial p-value as a
   cross-check.
   p_fixed = P(count in [1480,1505) <= observed count)

2. GLOBAL / SLIDING-WINDOW TEST (assumes uniformity, look-elsewhere corrected)
   Null: same as above, but instead of checking only the 1480-1505
   window, each simulated draw records the MINIMUM count over every
   possible 25-year window in 1250-1650 (sliding the window start year
   by year). This asks: how often does a random draw of N points produce
   *some* 25-year window at least as empty as the emptiest window we
   actually observe -- which is the fair comparison, since we did not
   pick 1480-1505 before looking at the data.
   p_global = P(sparsest simulated 25-yr window count <= observed sparsest window count)

3. EMPIRICAL COMPARISON TO OTHER OBSERVED WINDOWS (no uniformity assumption)
   Instead of simulating anything, tile the ACTUAL sample period into
   non-overlapping 25-year windows anchored on 1480-1505 itself (so
   1480-1505 is exactly one of the tiles, and neighboring tiles are
   1455-1480, 1505-1530, etc., extending in both directions to the edges
   of the sample period). Non-overlapping tiles are used deliberately --
   sliding by 1 year, as in Tests 1-2, makes adjacent windows almost
   identical and isn't a fair comparison of independent windows. This
   asks a different, weaker-assumption question than Tests 1-2: relative
   to the actual historical variation in 25-year responsa counts (which
   may be clumpier than a uniform/Poisson process, e.g. due to wars,
   plagues, or waves of publication), how unusual is 1480-1505? We report
   its rank among all the tiles, and a z-score computed from the other
   tiles' own empirical mean and standard deviation (leave-one-out) --
   i.e. "how many empirical standard deviations below the OTHER windows'
   average is this window", with no distributional assumption at all.

Run 01_build_dataset.py first:
    python scripts/01_build_dataset.py
    python scripts/04_randomization_analysis_1480_1505.py
"""
import numpy as np
import pandas as pd
from scipy.stats import binom, norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PERIOD_START, PERIOD_END = 1250, 1650     # sample period used for the test
WINDOW_START, WINDOW_END = 1481, 1506     # the window of interest ("the gap"):
                                           # calendar years 1481-1505 inclusive
                                           # (half-open [1481, 1506) so the
                                           # window covers the whole of 1505)
WINDOW_LEN = WINDOW_END - WINDOW_START    # 25 years
N_SIMS = 50_000
SEED = 20260907  # fixed seed for reproducibility

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# 1. Load data, restrict to the sample period
# ---------------------------------------------------------------------------
df = pd.read_csv("data/processed/bi_plus_geonim.csv", low_memory=False)
df["word_length"] = pd.to_numeric(df["word_length"], errors="coerce")

# Same "responsa sample" used throughout the paper: word_length >= 11
df = df[df["word_length"] >= 11].copy()
df = df.dropna(subset=["interpolated_year"])

period = df[(df["interpolated_year"] >= PERIOD_START) & (df["interpolated_year"] < PERIOD_END)]
years = period["interpolated_year"].values
N = len(years)

observed_count = int(np.sum((years >= WINDOW_START) & (years < WINDOW_END)))

print(f"Sample period: {PERIOD_START}-{PERIOD_END}  (N = {N:,} responsa)")
print(f"Window of interest: {WINDOW_START}-{WINDOW_END}  (observed count = {observed_count})")
p_window = WINDOW_LEN / (PERIOD_END - PERIOD_START)
print(f"Expected count under uniform null: N * ({WINDOW_LEN}/{PERIOD_END - PERIOD_START}) = {N * p_window:.1f}")

# ---------------------------------------------------------------------------
# 0. Simple period-wide average: N split evenly across the exact number of
#    non-overlapping 25-year spans that tile 1250-1650 with no remainder.
# ---------------------------------------------------------------------------
n_period_tiles = (PERIOD_END - PERIOD_START) // WINDOW_LEN
assert (PERIOD_END - PERIOD_START) % WINDOW_LEN == 0, \
    "sample period does not divide evenly into WINDOW_LEN-year spans"
period_wide_mean = N / n_period_tiles
pct_of_mean = 100 * observed_count / period_wide_mean

print(f"\n--- Test 0: simple period-wide average (no assumptions) ---")
print(f"  {PERIOD_START}-{PERIOD_END} is exactly {n_period_tiles} non-overlapping "
      f"{WINDOW_LEN}-year spans; their counts must sum to N = {N:,},")
print(f"  so their mean is exactly N/{n_period_tiles} = {period_wide_mean:.1f} responsa per {WINDOW_LEN}-year span.")
print(f"  Observed {WINDOW_START}-{WINDOW_END} count ({observed_count}) is "
      f"{pct_of_mean:.1f}% of that period-wide average "
      f"({period_wide_mean:.1f}) -- i.e. {period_wide_mean / observed_count:.1f}x fewer than the typical span.")


def window_counts(sorted_arr, starts, length):
    """Count of points in [start, start+length) for every start, via binary search."""
    lo = np.searchsorted(sorted_arr, starts, side="left")
    hi = np.searchsorted(sorted_arr, starts + length, side="left")
    return hi - lo


# All possible 25-year window start years within the sample period (sliding, step=1yr)
window_starts = np.arange(PERIOD_START, PERIOD_END - WINDOW_LEN + 1)

# ---------------------------------------------------------------------------
# 2. Actual data: sliding-window counts, and the sparsest window observed
# ---------------------------------------------------------------------------
sorted_years = np.sort(years)
actual_counts = window_counts(sorted_years, window_starts, WINDOW_LEN)
actual_min = int(actual_counts.min())
actual_min_window = int(window_starts[np.argmin(actual_counts)])

print(f"\nSparsest 25-yr window actually observed in {PERIOD_START}-{PERIOD_END}: "
      f"{actual_min_window}-{actual_min_window + WINDOW_LEN}  (count = {actual_min})")

# ---------------------------------------------------------------------------
# 3. Randomization (Monte Carlo): redraw N years ~ Uniform(period), repeat
# ---------------------------------------------------------------------------
sim_fixed_counts = np.empty(N_SIMS, dtype=np.int64)
sim_min_counts = np.empty(N_SIMS, dtype=np.int64)

for i in range(N_SIMS):
    sim_years = rng.uniform(PERIOD_START, PERIOD_END, size=N)
    sim_fixed_counts[i] = np.sum((sim_years >= WINDOW_START) & (sim_years < WINDOW_END))
    sim_sorted = np.sort(sim_years)
    sim_min_counts[i] = window_counts(sim_sorted, window_starts, WINDOW_LEN).min()

p_fixed_mc = float(np.mean(sim_fixed_counts <= observed_count))
p_global_mc = float(np.mean(sim_min_counts <= actual_min))

# Exact Binomial cross-check for the fixed-window test.
# The true tail probability is often astronomically small (the observed
# count can be many standard deviations below the mean), so binom.cdf can
# underflow to 0.0 in floating point -- report it on a log10 scale too,
# cross-checked two ways: the Binomial's own log-CDF, and a Normal
# approximation to the Binomial (valid here since N*p and N*(1-p) are both
# large).
p_fixed_exact = float(binom.cdf(observed_count, N, p_window))
log10_p_fixed_binom = float(binom.logcdf(observed_count, N, p_window)) / np.log(10)
mu_window, sigma_window = N * p_window, np.sqrt(N * p_window * (1 - p_window))
z_fixed = (observed_count - mu_window) / sigma_window
log10_p_fixed_normal = float(norm.logcdf(z_fixed)) / np.log(10)

# ---------------------------------------------------------------------------
# 4. Test 3: empirical comparison to other observed 25-yr windows, with NO
#    assumption of uniformity. Tile the sample period into non-overlapping
#    25-year windows anchored on the window of interest itself, then rank
#    the observed window's count among all the tiles.
# ---------------------------------------------------------------------------
k_min = int(np.ceil((PERIOD_START - WINDOW_START) / WINDOW_LEN))
k_max = int(np.floor((PERIOD_END - WINDOW_LEN - WINDOW_START) / WINDOW_LEN))
tile_starts = WINDOW_START + WINDOW_LEN * np.arange(k_min, k_max + 1)
tile_counts = window_counts(sorted_years, tile_starts, WINDOW_LEN)

is_window_of_interest = (tile_starts == WINDOW_START)
window_tile_count = int(tile_counts[is_window_of_interest][0])
other_tile_counts = tile_counts[~is_window_of_interest]

rank = int(np.sum(tile_counts <= window_tile_count))  # 1 = sparsest
n_tiles = len(tile_counts)
p_empirical_rank = rank / n_tiles

other_mean = float(other_tile_counts.mean())
other_std = float(other_tile_counts.std(ddof=1))
z_empirical = (window_tile_count - other_mean) / other_std if other_std > 0 else np.nan

# ---------------------------------------------------------------------------
# 5. Report
# ---------------------------------------------------------------------------
print(f"\n--- Test 1: fixed window {WINDOW_START}-{WINDOW_END} (assumes uniformity) ---")
print(f"  Randomization p-value (N_sims={N_SIMS:,}): p = {p_fixed_mc:.6f}"
      f"{' (no simulated draw was ever this extreme)' if p_fixed_mc == 0 else ''}")
print(f"  Exact Binomial({N}, {p_window:.5f}) p-value:  p = {p_fixed_exact:.3g}"
      f"  (log10 p = {log10_p_fixed_binom:.1f})")
print(f"  Normal-approximation cross-check:            z = {z_fixed:.1f}"
      f"  (log10 p = {log10_p_fixed_normal:.1f})")
print(f"  (probability of {observed_count} or fewer responsa landing in a *fixed*")
print(f"   25-year window, if responsa were produced at a uniform rate; expected")
print(f"   count under that null is {mu_window:.0f} +/- {sigma_window:.0f})")

print(f"\n--- Test 2: sparsest window anywhere in {PERIOD_START}-{PERIOD_END} "
      f"(assumes uniformity, look-elsewhere corrected) ---")
print(f"  Randomization p-value (N_sims={N_SIMS:,}): p = {p_global_mc:.6f}"
      f"{' (no simulated draw was ever this extreme)' if p_global_mc == 0 else ''}")
print(f"  Simulated sparsest-window counts ranged {sim_min_counts.min()}-{sim_min_counts.max()}, "
      f"mean {sim_min_counts.mean():.0f}")
print(f"  (probability that the emptiest 25-year window found ANYWHERE in a random")
print(f"   draw of {N:,} uniform years is at least as empty as the {actual_min}-responsa")
print(f"   window we actually observe at {actual_min_window}-{actual_min_window + WINDOW_LEN}; even")
print(f"   after correcting for having searched over every possible window, the gap")
print(f"   is far outside anything {N_SIMS:,} random draws ever produced)")

print(f"\n--- Test 3: empirical comparison to other OBSERVED 25-yr windows "
      f"(no uniformity assumption) ---")
print(f"  Sample period {PERIOD_START}-{PERIOD_END} tiled into {n_tiles} non-overlapping")
print(f"  25-year windows, anchored on {WINDOW_START}-{WINDOW_END}:")
print(f"    {WINDOW_START}-{WINDOW_END} count:            {window_tile_count}")
print(f"    other {n_tiles - 1} windows: mean={other_mean:.1f}, std={other_std:.1f}, "
      f"range={other_tile_counts.min()}-{other_tile_counts.max()}")
print(f"    rank of {WINDOW_START}-{WINDOW_END}: {rank} of {n_tiles} "
      f"(1 = sparsest) -> empirical p = {p_empirical_rank:.3f}")
print(f"    z-score vs. the OTHER windows' own empirical mean/std: z = {z_empirical:.1f}")
print(f"  (this compares {WINDOW_START}-{WINDOW_END} only to the actual variability seen")
print(f"   across other {WINDOW_LEN}-year spans of real responsa production in this period --")
print(f"   it does not assume production is uniform, Poisson, or any particular")
print(f"   distribution; it just asks whether this window stands out among its peers)")

# ---------------------------------------------------------------------------
# 6. Save results + a diagnostic plot
# ---------------------------------------------------------------------------
import os
os.makedirs("data/processed", exist_ok=True)
results = pd.DataFrame([{
    "period_start": PERIOD_START, "period_end": PERIOD_END,
    "window_start": WINDOW_START, "window_end": WINDOW_END,
    "n_responsa_in_period": N,
    "observed_count_in_window": observed_count,
    "n_period_wide_tiles": n_period_tiles,
    "period_wide_mean_count_per_window": period_wide_mean,
    "observed_pct_of_period_wide_mean": pct_of_mean,
    "expected_count_under_uniform": N * p_window,
    "sparsest_window_start_actual": actual_min_window,
    "sparsest_window_count_actual": actual_min,
    "n_sims": N_SIMS,
    "p_fixed_window_montecarlo": p_fixed_mc,
    "p_fixed_window_exact_binomial": p_fixed_exact,
    "log10_p_fixed_window_binomial": log10_p_fixed_binom,
    "z_score_fixed_window": z_fixed,
    "log10_p_fixed_window_normal_approx": log10_p_fixed_normal,
    "p_global_sparsest_window_montecarlo": p_global_mc,
    "n_tiles_empirical": n_tiles,
    "window_tile_count": window_tile_count,
    "other_tiles_mean": other_mean,
    "other_tiles_std": other_std,
    "rank_among_tiles": rank,
    "p_empirical_rank": p_empirical_rank,
    "z_empirical_vs_other_windows": z_empirical,
}])
results.to_csv("data/processed/randomization_1480_1505_results.csv", index=False)
print("\nWrote data/processed/randomization_1480_1505_results.csv")

fig, axes = plt.subplots(1, 3, figsize=(17, 5))

axes[0].hist(sim_fixed_counts, bins=40, color="steelblue", alpha=0.8)
axes[0].axvline(observed_count, color="darkred", linewidth=2,
                 label=f"Observed ({observed_count})")
axes[0].axvline(period_wide_mean, color="darkgreen", linewidth=2, linestyle="--",
                 label=f"Period-wide mean ({period_wide_mean:.1f})")
axes[0].set_title(f"Simulated count in fixed window\n{WINDOW_START}-{WINDOW_END} (N_sims={N_SIMS:,})")
axes[0].set_xlabel("Number of responsa in window")
axes[0].set_ylabel("Number of simulations")
axes[0].legend()

axes[1].hist(sim_min_counts, bins=40, color="steelblue", alpha=0.8)
axes[1].axvline(actual_min, color="darkred", linewidth=2,
                 label=f"Observed sparsest window ({actual_min})")
axes[1].set_title(f"Simulated sparsest 25-yr window anywhere\nin {PERIOD_START}-{PERIOD_END} (N_sims={N_SIMS:,})")
axes[1].set_xlabel("Minimum count across all 25-yr windows")
axes[1].set_ylabel("Number of simulations")
axes[1].legend()

bar_colors = ["darkred" if s == WINDOW_START else "steelblue" for s in tile_starts]
axes[2].bar([f"{s}" for s in tile_starts], tile_counts, color=bar_colors)
axes[2].axhline(period_wide_mean, color="darkgreen", linewidth=2, linestyle="--",
                 label=f"Period-wide mean ({period_wide_mean:.1f})")
axes[2].set_title(f"Observed count in EVERY non-overlapping\n25-yr tile, {PERIOD_START}-{PERIOD_END}")
axes[2].set_xlabel("Tile start year")
axes[2].set_ylabel("Number of responsa")
axes[2].tick_params(axis="x", rotation=90)
axes[2].legend()

plt.tight_layout()
os.makedirs("figures", exist_ok=True)
plt.savefig("figures/randomization_1480_1505.png", dpi=200)
plt.close()
print("Wrote figures/randomization_1480_1505.png")
