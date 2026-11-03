"""Supplementary analyses for the final report.

Usage (from the repository root, after scripts/prepare_data.py):

    python scripts/supplementary_analysis.py

The confirmatory tests and their decisions (H1, H2, H3) come only from
scripts/analyze.py, as fixed in docs/preregistration.md. This script re-runs
those analyses with the same seed (so its numbers match
results/analysis_report.md exactly) and adds what the written report needs on
top of them. Nothing here changes a confirmatory decision.

1. Effect sizes for the pre-registered comparisons: Cohen's h for proportions,
   Cohen's w for the chi-square goodness-of-fit check, risk and odds ratios.
2. What the data rule out: one-sided 95% upper bounds on the exact-combination
   repeat rate, translated into "stickiness" (the share of rolls that copy the
   previous combination) and compared with the betting strategy's break-even.
3. Sensitivity analysis for the design actually run (1,000 pairs; 702
   point-set and 298 come-out rolls): the smallest effect each test detects with
   80% power, using the normal approximation with Cohen's h (the same
   calculation as statsmodels' NormalIndPower), plus a simulation of the
   permutation test and z-test. This is not post hoc "observed power".
4. Exploratory analyses, reported without decisions and tagged by source.
   Listed in the preregistration: repeats after a 2/12 and after a 3/11 (the
   motivating strategy), consecutive rolls sharing a face, first vs. second half
   of the session, and repeats by combination. Added after data collection
   (hypothesis-generating only): a weighted repeat count and face/combination
   frequency tests.
5. Data-quality check: a replay of the $3 pass-line bets from the $100 start,
   compared with the recorded ending balance.

Writes results/supplementary_report.md, results/supplementary_results.json and
three figures in results/. All randomness uses fixed seeds.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write image files without a display
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

import analyze as an  # noqa: E402
import craps_core as core  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

ALPHA = an.ALPHA
POWER = 0.80
SEED = an.SEED
N_PERMUTATIONS = an.N_PERMUTATIONS
N_BOOTSTRAP = an.N_BOOTSTRAP
N_SIMULATIONS = 1_000          # simulated sessions per scenario (permutation test)
N_SIM_SHUFFLES = 999           # shuffles per simulated session (the real analysis uses 10,000)
N_SIMULATIONS_H3 = 4_000       # simulated sessions per scenario (z-test)
STICKINESS_GRID = [0.0, 0.005, 0.01, 0.02, 0.03]

STARTING_BALANCE = 100
BET = 3
RECORDED_ENDING_BALANCE = 40

# One-roll bets that motivated the study: payout (to 1) and fair chance of the total.
STRATEGY_BETS = {
    "2 or 12": {"totals": (2, 12), "payout": 30, "fair_rate": 1 / 36},
    "3 or 11": {"totals": (3, 11), "payout": 15, "fair_rate": 2 / 36},
}
FAIR_PASS_LINE_WIN = 244 / 495  # probability a pass-line round wins with fair dice

COMBO_PROBS = np.array([an.FAIR_COMBINATION_PROBS[c] for c in an.COMBINATIONS])
COMBO_TOTALS = np.array([int(c[0]) + int(c[2]) for c in an.COMBINATIONS], dtype=np.int8)
COMBO_FACES = np.array([[int(c[0]), int(c[2])] for c in an.COMBINATIONS], dtype=np.int8)
# Weighted repeat count: a repeat counts 1 / (fair chance of that combination),
# scaled so a repeated non-double counts 1 and a repeated double counts 2.
REPEAT_WEIGHTS = (2 / 36) / COMBO_PROBS

# Where each analysis comes from. "Listed in the preregistration" refers to
# docs/preregistration.md ("Effect sizes and reporting"), which names early vs.
# late, individual combinations, shared die faces, and betting-strategy
# estimates as exploratory. Everything else here was added after the data were
# collected and is descriptive or hypothesis-generating only.
PREREGISTERED = "listed in the preregistration"
POST_HOC = "added after data collection"
ROLES = {
    "effect_sizes": "descriptive; " + POST_HOC + " to meet the reporting requirements",
    "interval_comparison": POST_HOC + ", as a reporting check",
    "ruled_out": POST_HOC + " (planned in earlier drafts; the final preregistration specifies two-sided intervals)",
    "power_for_design_run": "sensitivity analysis for the achieved design (not post hoc observed power)",
    "simulation_check": "checks how the tests behave; not an analysis of the data",
    "exploratory.strategy_repeats": PREREGISTERED + " as betting-strategy estimates",
    "exploratory.weighted_repeat_count": POST_HOC + "; a supporting check in planning drafts, not in the final "
                                         "preregistration",
    "exploratory.shared_face": PREREGISTERED + " as shared die faces",
    "exploratory.first_vs_second_half": PREREGISTERED + " as early vs. late",
    "exploratory.repeats_by_combination": PREREGISTERED + " as individual combinations",
    "exploratory.bias_checks": POST_HOC,
    "data_quality_balance_replay": "data-quality check (see docs/deviations.md); the win rate is descriptive, "
                                   + POST_HOC,
}

COLOR_SERIES = an.COLOR_SERIES
COLOR_SERIES_2 = "#eb6834"     # categorical slot 2 of the reference palette
COLOR_REFERENCE = an.COLOR_REFERENCE
COLOR_TEXT = an.COLOR_TEXT
COLOR_GRID = an.COLOR_GRID
COLOR_SURFACE = an.COLOR_SURFACE


# ---------------------------------------------------------------------------
# Effect sizes and conversions
# ---------------------------------------------------------------------------


def cohen_h(p1: float, p0: float) -> float:
    """Cohen's h: difference between two proportions on the arcsine scale."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p0))


def from_cohen_h(p0: float, h: float) -> float:
    """The proportion that lies `h` above `p0` on the arcsine scale."""
    return math.sin(math.asin(math.sqrt(p0)) + h / 2) ** 2


def cohen_w(chi_square: float, n: int) -> float:
    """Cohen's w for a chi-square goodness-of-fit test."""
    return math.sqrt(chi_square / n)


def rate_from_stickiness(s: float, base: float) -> float:
    """Repeat rate when a share `s` of rolls copy the previous combination."""
    return s + (1 - s) * base


def stickiness_from_rate(rate: float, base: float) -> float:
    """Inverse of rate_from_stickiness; negative when the rate is below `base`."""
    return (rate - base) / (1 - base)


def break_even(payout: int, fair_rate: float) -> dict:
    """Win probability and stickiness at which a one-roll bet paying `payout` to 1 breaks even."""
    p_break_even = 1 / (payout + 1)
    s = stickiness_from_rate(p_break_even, fair_rate)
    return {"payout_to_1": payout, "fair_rate": fair_rate, "break_even_rate": p_break_even,
            "break_even_stickiness": s,
            "overall_combination_repeat_rate": rate_from_stickiness(s, an.FAIR_EXACT_REPEAT),
            "expected_return_per_dollar_fair": fair_rate * (payout + 1)}


def exact_interval(k: int, n: int) -> list[float]:
    """Two-sided 95% Clopper-Pearson (exact) interval."""
    ci = stats.binomtest(k, n).proportion_ci(confidence_level=0.95, method="exact")
    return [float(ci.low), float(ci.high)]


def exact_upper_bound(k: int, n: int, confidence: float = 0.95) -> float:
    """One-sided exact (Clopper-Pearson) upper confidence bound."""
    return 1.0 if k >= n else float(stats.beta.ppf(confidence, k + 1, n - k))


def z(q: float) -> float:
    return float(stats.norm.ppf(q))


# ---------------------------------------------------------------------------
# Power: smallest detectable effects for the design actually run
# ---------------------------------------------------------------------------


def mde_one_sample(n: int, p0: float, alpha: float = ALPHA, power: float = POWER,
                   two_sided: bool = False) -> dict:
    """Smallest rate above p0 detected with the given power (normal approximation, Cohen's h).

    Same calculation as statsmodels NormalIndPower(effect_size, nobs1=n, ratio=0).
    """
    z_alpha = z(1 - alpha / 2) if two_sided else z(1 - alpha)
    h = (z_alpha + z(power)) / math.sqrt(n)
    return {"n": n, "p0": p0, "h": h, "p1": from_cohen_h(p0, h)}


def mde_two_sample(n1: int, n2: int, p0: float, alpha: float = ALPHA, power: float = POWER,
                   two_sided: bool = False) -> dict:
    """Smallest rate in group 1 detected against p0 in group 2 (Cohen's h, two groups)."""
    z_alpha = z(1 - alpha / 2) if two_sided else z(1 - alpha)
    h = (z_alpha + z(power)) / math.sqrt(n1 * n2 / (n1 + n2))
    return {"n1": n1, "n2": n2, "p0": p0, "h": h, "p1": from_cohen_h(p0, h)}


def mde_null_se(n_eff_inverse: float, p0: float, alpha: float = ALPHA, power: float = POWER) -> float:
    """The preregistration's quick approximation: shift = (z_alpha + z_power) x SE under the null.

    `n_eff_inverse` is 1/n for one sample or 1/n1 + 1/n2 for two groups.
    """
    return p0 + (z(1 - alpha) + z(power)) * math.sqrt(p0 * (1 - p0) * n_eff_inverse)


def power_one_sample(p1: float, p0: float, n: int, alpha: float = ALPHA) -> float:
    """Power of a one-sided one-sample test of p0 against p1 > p0 (Cohen's h)."""
    return float(stats.norm.sf(z(1 - alpha) - cohen_h(p1, p0) * math.sqrt(n)))


def overlap_variance_inflation(probs, n_pairs: int) -> float:
    """Extra variance of a repeat count from overlapping pairs, relative to the binomial formula.

    Under independence, each pair repeats with q = sum(p^2), and neighbouring
    pairs (which share a roll) both repeat with probability sum(p^3), so
    Var = n q (1 - q) + 2 (n - 1) (sum(p^3) - q^2). Returns Var / (n q (1 - q)) - 1.
    """
    p = np.asarray(probs, dtype=float)
    q = float((p ** 2).sum())
    cov = float((p ** 3).sum()) - q ** 2
    return 2 * (n_pairs - 1) * cov / (n_pairs * q * (1 - q))


def pairs_needed(p1: float, p0: float, alpha: float = ALPHA, power: float = POWER) -> int:
    return math.ceil(((z(1 - alpha) + z(power)) / cohen_h(p1, p0)) ** 2)


def power_analysis(main: dict) -> dict:
    """Smallest detectable effects at alpha = 0.05 (one-sided) and 80% power, for the achieved sample."""
    h1, h3 = main["h1_exact_repeats"], main["h3_badly_timed_sevens"]
    n_pairs = h1["valid_pairs"]
    n_point = h3["main"]["point_set_rolls"]
    n_come_out = h3["main"]["come_out_rolls"]
    n_come_out_check = h3["sensitivity_come_out_not_after_seven"]["come_out_rolls"]
    out = {}

    for key, p0 in (("h1_exact_repeats", an.FAIR_EXACT_REPEAT), ("h2_total_repeats", an.FAIR_TOTAL_REPEAT)):
        one = mde_one_sample(n_pairs, p0)
        two = mde_one_sample(n_pairs, p0, two_sided=True)
        bonf = mde_one_sample(n_pairs, p0, alpha=an.BONFERRONI_ALPHA)
        out[key] = {
            "pairs": n_pairs, "fair_rate": p0,
            "detectable_rate_one_sided": one["p1"], "cohen_h": one["h"],
            "detectable_stickiness": stickiness_from_rate(one["p1"], p0),
            "detectable_rate_two_sided": two["p1"],
            "detectable_rate_bonferroni_0_025": bonf["p1"],
            "preregistration_approximation": mde_null_se(1 / n_pairs, p0),
        }

    fair7 = an.FAIR_SEVEN
    for key, n_co in (("h3_point_vs_come_out", n_come_out), ("h3_check_come_out_after_non_seven", n_come_out_check)):
        one = mde_two_sample(n_point, n_co, fair7)
        out[key] = {
            "point_set_rolls": n_point, "come_out_rolls": n_co, "fair_rate": fair7,
            "detectable_point_set_rate": one["p1"], "detectable_difference": one["p1"] - fair7,
            "cohen_h": one["h"],
            "detectable_point_set_rate_two_sided": mde_two_sample(n_point, n_co, fair7, two_sided=True)["p1"],
            "detectable_point_set_rate_bonferroni_0_025":
                mde_two_sample(n_point, n_co, fair7, alpha=an.BONFERRONI_ALPHA)["p1"],
            "preregistration_approximation": mde_null_se(1 / n_point + 1 / n_co, fair7),
        }
    one = mde_one_sample(n_point, fair7)
    out["exploratory_point_set_vs_one_sixth"] = {"rolls": n_point, "detectable_rate": one["p1"],
                                                 "cohen_h": one["h"]}
    # How much the formulas' independent-pairs assumption understates the variance.
    out["overlap_variance_inflation"] = {
        "combinations": overlap_variance_inflation(COMBO_PROBS, n_pairs),
        "totals": overlap_variance_inflation([an.FAIR_TOTAL_PROBS[t] for t in range(2, 13)], n_pairs),
    }

    # The strategy's break-even, under stickiness that applies equally to every combination.
    be = break_even(15, 2 / 36)
    r = be["overall_combination_repeat_rate"]
    out["strategy_break_even_3_or_11"] = {
        "stickiness": be["break_even_stickiness"], "overall_repeat_rate": r,
        "cohen_h": cohen_h(r, an.FAIR_EXACT_REPEAT),
        "power_with_this_sample": power_one_sample(r, an.FAIR_EXACT_REPEAT, n_pairs),
        "pairs_needed_for_80_percent_power": pairs_needed(r, an.FAIR_EXACT_REPEAT),
    }
    out["h1_power_by_stickiness"] = {
        f"{s:.3f}": power_one_sample(rate_from_stickiness(s, an.FAIR_EXACT_REPEAT), an.FAIR_EXACT_REPEAT, n_pairs)
        for s in [0.0025, 0.005, 0.0074, 0.01, 0.015, 0.02, 0.025, 0.03]
    }
    return out


# ---------------------------------------------------------------------------
# Simulation check of the tests themselves
# ---------------------------------------------------------------------------


def sticky_sequence(n_rolls: int, stickiness: float, rng: np.random.Generator) -> np.ndarray:
    """Combination codes from fair dice where each roll copies the previous one with probability s."""
    fresh = rng.choice(len(COMBO_PROBS), size=n_rolls, p=COMBO_PROBS).astype(np.int8)
    copy = rng.random(n_rolls) < stickiness
    seq = fresh.copy()
    for i in range(1, n_rolls):
        if copy[i]:
            seq[i] = seq[i - 1]
    return seq


def permutation_p_value(seq: np.ndarray, n_shuffles: int, rng: np.random.Generator) -> float:
    observed = an.count_repeats(seq)
    shuffled = rng.permuted(np.tile(seq, (n_shuffles, 1)), axis=1)
    counts = (shuffled[:, 1:] == shuffled[:, :-1]).sum(axis=1)
    return (1 + int((counts >= observed).sum())) / (n_shuffles + 1)


def simulate_h1_power(n_rolls: int, n_sims: int, n_shuffles: int, seed: int) -> list[dict]:
    """Share of simulated sessions in which the H1 permutation test rejects at alpha = 0.05."""
    out = []
    for i, s in enumerate(STICKINESS_GRID):
        rng = np.random.default_rng([seed, 1, i])
        rejections = sum(an.is_significant(permutation_p_value(sticky_sequence(n_rolls, s, rng), n_shuffles, rng))
                         for _ in range(n_sims))
        rate = rejections / n_sims
        out.append({"stickiness": s, "repeat_rate": rate_from_stickiness(s, an.FAIR_EXACT_REPEAT),
                    "rejection_rate": rate, "monte_carlo_se": math.sqrt(rate * (1 - rate) / n_sims),
                    "analytic_power": power_one_sample(rate_from_stickiness(s, an.FAIR_EXACT_REPEAT),
                                                       an.FAIR_EXACT_REPEAT, n_rolls - 1),
                    "sessions": n_sims, "shuffles_per_session": n_shuffles})
    return out


def simulate_h3_session(n_rolls: int, point_seven_rate: float, rng: np.random.Generator) -> dict:
    """One pass-line session starting on a come-out roll; point-set rolls are 7 with the given chance."""
    totals = np.array([t for t in range(2, 13)])
    fair = np.array([an.FAIR_TOTAL_PROBS[t] for t in totals])
    non_seven = fair.copy()
    non_seven[totals == 7] = 0
    non_seven /= non_seven.sum()
    state = "CO"
    t = {"point_set_rolls": 0, "point_set_sevens": 0, "come_out_rolls": 0, "come_out_sevens": 0}
    u = rng.random(n_rolls)
    fair_draws = rng.choice(totals, size=n_rolls, p=fair)
    other_draws = rng.choice(totals, size=n_rolls, p=non_seven)
    for i in range(n_rolls):
        if state == "CO":
            total = int(fair_draws[i])
            t["come_out_rolls"] += 1
            t["come_out_sevens"] += total == 7
        else:
            total = 7 if u[i] < point_seven_rate else int(other_draws[i])
            t["point_set_rolls"] += 1
            t["point_set_sevens"] += total == 7
        state = core.next_state(state, total)
    return {k: int(v) for k, v in t.items()}


def simulate_h3_power(n_rolls: int, n_sims: int, detectable_rate: float, seed: int) -> list[dict]:
    out = []
    for i, rate in enumerate([an.FAIR_SEVEN, detectable_rate]):
        rng = np.random.default_rng([seed, 2, i])
        rejections, co, diff = 0, [], []
        for _ in range(n_sims):
            table = simulate_h3_session(n_rolls, rate, rng)
            r = an.two_proportion_test(table)
            rejections += an.is_significant(r["p_value_one_sided"])
            co.append(table["come_out_rolls"])
            diff.append(r["rate_difference"])
        p = rejections / n_sims
        # The spread of the observed difference across sessions: the standard error an
        # interval for the difference should reflect.
        out.append({"point_set_seven_rate": rate, "rejection_rate": p,
                    "monte_carlo_se": math.sqrt(p * (1 - p) / n_sims),
                    "mean_come_out_rolls": float(np.mean(co)), "sd_of_difference": float(np.std(diff, ddof=1)),
                    "sessions": n_sims})
    return out


# ---------------------------------------------------------------------------
# Shuffles shared by the exploratory repeat statistics
# ---------------------------------------------------------------------------


def shuffled_statistics(block_list: list[pd.DataFrame], n_perm: int, seed: int) -> dict:
    """Re-create analyze.py's within-block shuffles and compute several statistics on each.

    The random generator is used exactly as in analyze.permutation_repeat_counts,
    so the exact and total repeat counts match the confirmatory test shuffle for
    shuffle. Returns arrays (length n_perm) summed over blocks.
    """
    rng = np.random.default_rng(seed)
    keys = ("exact", "total", "weighted", "shared_face")
    out = {k: np.zeros(n_perm, dtype=float) for k in keys}
    for b in block_list:
        n = len(b)
        if n < 2:
            continue
        comb = b["combination"].map(an.COMBINATION_CODE).to_numpy(dtype=np.int8)
        tot = b["total"].to_numpy(dtype=np.int8)
        done = 0
        while done < n_perm:
            size = min(an.PERMUTATION_CHUNK, n_perm - done)
            idx = rng.permuted(np.tile(np.arange(n, dtype=np.int32), (size, 1)), axis=1)
            c, t = comb[idx], tot[idx]
            same = c[:, 1:] == c[:, :-1]
            out["exact"][done:done + size] += same.sum(axis=1)
            out["total"][done:done + size] += (t[:, 1:] == t[:, :-1]).sum(axis=1)
            out["weighted"][done:done + size] += (same * REPEAT_WEIGHTS[c[:, 1:]]).sum(axis=1)
            out["shared_face"][done:done + size] += shares_face(c[:, :-1], c[:, 1:]).sum(axis=1)
            done += size
    return out


def shares_face(prev_codes: np.ndarray, next_codes: np.ndarray) -> np.ndarray:
    """True where two combinations have at least one face value in common."""
    a, b = COMBO_FACES[prev_codes], COMBO_FACES[next_codes]
    return ((a[..., :1] == b[..., :1]) | (a[..., :1] == b[..., 1:]) |
            (a[..., 1:] == b[..., :1]) | (a[..., 1:] == b[..., 1:]))[..., 0]


def fair_shared_face_rate() -> float:
    """Chance that two independent rolls of fair dice share at least one face value."""
    faces = range(1, 7)
    hits = sum(bool({a, b} & {c, d}) for a in faces for b in faces for c in faces for d in faces)
    return hits / 36 ** 2


def observed_statistics(block_list: list[pd.DataFrame]) -> dict:
    out = {"exact": 0.0, "total": 0.0, "weighted": 0.0, "shared_face": 0.0, "pairs": 0}
    for b in block_list:
        if len(b) < 2:
            continue
        c = b["combination"].map(an.COMBINATION_CODE).to_numpy(dtype=np.int8)
        t = b["total"].to_numpy(dtype=np.int8)
        same = c[1:] == c[:-1]
        out["exact"] += float(same.sum())
        out["total"] += float((t[1:] == t[:-1]).sum())
        out["weighted"] += float((same * REPEAT_WEIGHTS[c[1:]]).sum())
        out["shared_face"] += float(shares_face(c[:-1], c[1:]).sum())
        out["pairs"] += len(b) - 1
    return out


def upper_tail_p(observed: float, shuffled: np.ndarray) -> float:
    return (1 + int((shuffled >= observed - 1e-9).sum())) / (len(shuffled) + 1)


# ---------------------------------------------------------------------------
# What the data rule out
# ---------------------------------------------------------------------------


def bootstrap_repeat_rates(df: pd.DataFrame, n_boot: int, seed: int) -> np.ndarray:
    """Moving-block bootstrap of the exact-repeat rate (same windows as analyze.py)."""
    rolls = an.rolls_only(df)
    valid = rolls["valid_pair"].fillna(False).to_numpy(bool)
    exact = rolls["exact_repeat"].fillna(False).to_numpy(bool) & valid
    ind = np.column_stack([valid, exact]).astype(np.int64)
    cum = np.vstack([np.zeros(2, dtype=np.int64), ind.cumsum(axis=0)])
    block_ids = rolls["analysis_block_id"].to_numpy()
    starts = np.flatnonzero(np.r_[True, block_ids[1:] != block_ids[:-1]])
    ends = np.r_[starts[1:], len(rolls)]
    L = an.BOOTSTRAP_BLOCK_LENGTH
    windows = []
    for s, e in zip(starts, ends):
        if e - s >= L:
            windows.extend(cum[w + L] - cum[w] for w in range(s, e - L + 1))
        else:
            windows.append(cum[e] - cum[s])
    windows = np.array(windows)
    rng = np.random.default_rng([seed, 3])
    draws = rng.integers(0, len(windows), size=(n_boot, math.ceil(len(rolls) / L)))
    sums = windows[draws].sum(axis=1)
    return sums[:, 1] / sums[:, 0]


def ruled_out(main: dict, df: pd.DataFrame, n_boot: int, seed: int) -> dict:
    h1 = main["h1_exact_repeats"]
    k, n = h1["observed_repeats"], h1["valid_pairs"]
    base = h1["permutation_baseline_rate"]
    boot = bootstrap_repeat_rates(df, n_boot, seed)
    upper_boot = float(np.percentile(boot, 95))
    upper_exact = exact_upper_bound(k, n)
    strategy = {name: break_even(v["payout"], v["fair_rate"]) for name, v in STRATEGY_BETS.items()}
    return {
        "observed_rate": k / n,
        "permutation_baseline_rate": base,
        "upper_bound_95_block_bootstrap": upper_boot,
        "upper_bound_95_exact_binomial": upper_exact,
        "max_stickiness_block_bootstrap": max(0.0, stickiness_from_rate(upper_boot, base)),
        "max_stickiness_exact_binomial": max(0.0, stickiness_from_rate(upper_exact, base)),
        "strategy_break_even": strategy,
        "break_even_excluded_block_bootstrap": {
            name: bool(upper_boot < v["overall_combination_repeat_rate"]) for name, v in strategy.items()},
        "break_even_excluded_exact_binomial": {
            name: bool(upper_exact < v["overall_combination_repeat_rate"]) for name, v in strategy.items()},
        "note": ("Translating the bound into stickiness assumes the machine, if streaky, copies every "
                 "combination equally often (the assumption stated in the design)."),
    }


# ---------------------------------------------------------------------------
# Effect sizes for the pre-registered comparisons
# ---------------------------------------------------------------------------


def effect_sizes(main: dict) -> dict:
    h1, h2 = main["h1_exact_repeats"], main["h2_total_repeats"]
    out = {}
    for key, r in (("h1_exact_repeats", h1), ("h2_total_repeats_descriptive", h2)):
        out[key] = {
            "observed_rate": r["observed_rate"], "permutation_baseline_rate": r["permutation_baseline_rate"],
            "difference": r["rate_difference"],
            "rate_ratio": r["observed_rate"] / r["permutation_baseline_rate"],
            "cohen_h_vs_baseline": cohen_h(r["observed_rate"], r["permutation_baseline_rate"]),
            "cohen_h_vs_fair": cohen_h(r["observed_rate"], r["fair_dice_rate"]),
        }
    for key, t in (("h3_main", main["h3_badly_timed_sevens"]["main"]),
                   ("h3_check_come_out_after_non_seven",
                    main["h3_badly_timed_sevens"]["sensitivity_come_out_not_after_seven"])):
        x1, n1 = t["point_set_sevens"], t["point_set_rolls"]
        x2, n2 = t["come_out_sevens"], t["come_out_rolls"]
        p1, p2 = x1 / n1, x2 / n2
        out[key] = {
            "point_set_rate": p1, "come_out_rate": p2, "difference": p1 - p2,
            "cohen_h": cohen_h(p1, p2), "risk_ratio": p1 / p2,
            "odds_ratio": (x1 * (n2 - x2)) / ((n1 - x1) * x2),
            "phi": t["z"] / math.sqrt(n1 + n2),
            "difference_wald_95_ci": [p1 - p2 - 1.96 * math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2),
                                      p1 - p2 + 1.96 * math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)],
        }
    sc = main["sanity_check"]["A"] if "A" in main["sanity_check"] else next(iter(main["sanity_check"].values()))
    out["sanity_check_totals"] = {"chi_square": sc["chi_square"], "rolls": sc["rolls"],
                                  "cohen_w": cohen_w(sc["chi_square"], sc["rolls"])}
    out["benchmarks"] = {"cohen_h": "0.2 small, 0.5 medium, 0.8 large",
                         "cohen_w": "0.1 small, 0.3 medium, 0.5 large"}
    return out


def interval_comparison(main: dict) -> dict:
    """Preregistered block-bootstrap intervals next to textbook intervals that assume independent rolls.

    With one session, the block bootstrap estimates the spread from about 20
    non-overlapping stretches of 50 rolls, so its intervals are themselves noisy.
    """
    boot = main["bootstrap_95_intervals"]
    h1, h2 = main["h1_exact_repeats"], main["h2_total_repeats"]
    t = main["h3_badly_timed_sevens"]["main"]
    x1, n1, x2, n2 = t["point_set_sevens"], t["point_set_rolls"], t["come_out_sevens"], t["come_out_rolls"]
    p1, p2 = x1 / n1, x2 / n2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return {
        "exact_repeat_rate": {"estimate": h1["observed_rate"], "block_bootstrap": boot["exact_repeat_rate"],
                              "independence": exact_interval(h1["observed_repeats"], h1["valid_pairs"]),
                              "independence_method": "exact Clopper-Pearson"},
        "total_repeat_rate": {"estimate": h2["observed_rate"], "block_bootstrap": boot["total_repeat_rate"],
                              "independence": exact_interval(h2["observed_repeats"], h2["valid_pairs"]),
                              "independence_method": "exact Clopper-Pearson"},
        "point_set_seven_rate": {"estimate": p1, "block_bootstrap": boot["point_set_seven_rate"],
                                 "independence": exact_interval(x1, n1),
                                 "independence_method": "exact Clopper-Pearson"},
        "come_out_seven_rate": {"estimate": p2, "block_bootstrap": boot["come_out_seven_rate"],
                                "independence": exact_interval(x2, n2),
                                "independence_method": "exact Clopper-Pearson"},
        "seven_rate_difference": {"estimate": p1 - p2, "block_bootstrap": boot["seven_rate_difference"],
                                  "independence": [p1 - p2 - 1.96 * se, p1 - p2 + 1.96 * se],
                                  "independence_method": "unpooled Wald"},
    }


# ---------------------------------------------------------------------------
# Exploratory analyses (no reject / fail-to-reject decisions)
# ---------------------------------------------------------------------------


def strategy_estimate(df: pd.DataFrame) -> dict:
    """After a 2 or 12 (or a 3 or 11), how often does the same total come next?"""
    pairs = an.rolls_only(df)
    pairs = pairs.loc[pairs["valid_pair"].fillna(False).astype(bool)]
    out = {}
    for name, bet in STRATEGY_BETS.items():
        after = pairs.loc[pairs["previous_total"].isin(bet["totals"])]
        n = int(len(after))
        k = int((after["total"] == after["previous_total"]).sum())
        be = break_even(bet["payout"], bet["fair_rate"])
        out[name] = {"rolls_following": n, "repeats": k, "rate": k / n if n else float("nan"),
                     "exact_95_ci": exact_interval(k, n) if n else None,
                     "fair_rate": bet["fair_rate"], "break_even_rate": be["break_even_rate"],
                     "payout_to_1": bet["payout"]}
    return out


def repeats_by_combination(df: pd.DataFrame) -> list[dict]:
    pairs = an.rolls_only(df)
    pairs = pairs.loc[pairs["valid_pair"].fillna(False).astype(bool)]
    rows = []
    for c in an.COMBINATIONS:
        after = pairs.loc[pairs["previous_combination"] == c]
        n = int(len(after))
        rows.append({"combination": c, "times_as_previous_roll": n,
                     "repeats": int((after["combination"] == c).sum()),
                     "expected_repeats_fair": n * an.FAIR_COMBINATION_PROBS[c]})
    return rows


def halves(df: pd.DataFrame) -> dict:
    """First half (rolls 1-500) vs. second half (rolls 501-1000) of the session."""
    rolls = an.rolls_only(df)
    counted = rolls.loc[rolls["counts_toward_sample"].fillna(False).astype(bool)].copy()
    n = len(counted)
    counted["half"] = np.where(np.arange(n) < n // 2, "first", "second")
    out = {}
    for half, g in counted.groupby("half"):
        v = g.loc[g["valid_pair"].fillna(False).astype(bool)]
        e = g.loc[g["h3_eligible"].fillna(False).astype(bool)]
        point = e.loc[e["phase_before_roll"] == "point_set"]
        come = e.loc[e["phase_before_roll"] == "come_out"]
        out[half] = {
            "rolls": int(len(g)), "pairs": int(len(v)),
            "exact_repeats": int(v["exact_repeat"].fillna(False).astype(bool).sum()),
            "point_set_rolls": int(len(point)), "point_set_sevens": int((point["total"] == 7).sum()),
            "come_out_rolls": int(len(come)), "come_out_sevens": int((come["total"] == 7).sum()),
        }
        o = out[half]
        o["exact_repeat_rate"] = o["exact_repeats"] / o["pairs"]
        o["point_set_seven_rate"] = o["point_set_sevens"] / o["point_set_rolls"]
        o["come_out_seven_rate"] = o["come_out_sevens"] / o["come_out_rolls"]
    f, s = out["first"], out["second"]
    out["repeat_rate_fisher_p_two_sided"] = float(stats.fisher_exact(
        [[f["exact_repeats"], f["pairs"] - f["exact_repeats"]],
         [s["exact_repeats"], s["pairs"] - s["exact_repeats"]]])[1])
    out["point_set_seven_rate_fisher_p_two_sided"] = float(stats.fisher_exact(
        [[f["point_set_sevens"], f["point_set_rolls"] - f["point_set_sevens"]],
         [s["point_set_sevens"], s["point_set_rolls"] - s["point_set_sevens"]]])[1])
    return out


def bias_checks(df: pd.DataFrame) -> dict:
    """Chi-square goodness of fit for the 21 combinations and the 6 faces (all rolls, as in the totals check)."""
    rolls = an.rolls_only(df)
    n = len(rolls)
    obs_c = np.array([(rolls["combination"] == c).sum() for c in an.COMBINATIONS])
    exp_c = n * COMBO_PROBS
    chi_c, p_c = stats.chisquare(obs_c, exp_c)
    faces = np.concatenate([rolls["die_low"].astype(int).to_numpy(), rolls["die_high"].astype(int).to_numpy()])
    obs_f = np.array([(faces == f).sum() for f in range(1, 7)])
    chi_f, p_f = stats.chisquare(obs_f)
    return {
        "combinations": {"rolls": n, "chi_square": float(chi_c), "df": 20, "p_value": float(p_c),
                         "cohen_w": cohen_w(float(chi_c), n), "smallest_expected": float(exp_c.min())},
        "faces": {"faces": int(len(faces)), "observed": {f: int(o) for f, o in zip(range(1, 7), obs_f)},
                  "chi_square": float(chi_f), "df": 5, "p_value": float(p_f),
                  "cohen_w": cohen_w(float(chi_f), len(faces))},
    }


# ---------------------------------------------------------------------------
# Data quality: replay the pass-line bets
# ---------------------------------------------------------------------------


def replay_balance(totals: list[int], start: int = STARTING_BALANCE, bet: int = BET) -> dict:
    """Replay a $bet pass-line bet on every come-out roll, starting from `start`.

    The machine takes the bet when it is placed and pays back twice the bet on a
    win, so a bet still on the table at the end is not in the displayed balance.
    """
    balance, state = start, "CO"
    wins = losses = 0
    low = start
    for total in totals:
        if state == "CO":
            balance -= bet
            if total in (7, 11):
                balance += 2 * bet
                wins += 1
            elif total in (2, 3, 12):
                losses += 1
        elif total == state:
            balance += 2 * bet
            wins += 1
        elif total == 7:
            losses += 1
        low = min(low, balance)
        state = core.next_state(state, total)
    return {"starting_balance": start, "bet": bet, "ending_balance": balance,
            "bet_open_at_end": state != "CO", "rounds_decided": wins + losses,
            "rounds_won": wins, "rounds_lost": losses, "lowest_balance": low}


def balance_check(df: pd.DataFrame) -> dict:
    counted = df.loc[df["counts_toward_sample"].fillna(False).astype(bool)]
    if counted["machine_id"].nunique() != 1 or (df["verification_status"] == "gap").any():
        return {"replayed": False, "reason": "replay needs one unbroken machine sequence"}
    r = replay_balance(counted["total"].astype(int).tolist())
    n = r["rounds_decided"]
    r.update(replayed=True, recorded_ending_balance=RECORDED_ENDING_BALANCE,
             matches_recording=r["ending_balance"] == RECORDED_ENDING_BALANCE,
             win_rate=r["rounds_won"] / n, win_rate_exact_95_ci=exact_interval(r["rounds_won"], n),
             fair_win_rate=FAIR_PASS_LINE_WIN)
    return r


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def _style(ax) -> None:
    ax.set_facecolor(COLOR_SURFACE)
    ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_REFERENCE)
    ax.tick_params(colors=COLOR_TEXT, length=0)


def plot_permutation_distribution(shuffled_exact: np.ndarray, observed: int, p_value: float,
                                  pairs: int, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 3.6), facecolor=COLOR_SURFACE)
    _style(ax)
    values, counts = np.unique(shuffled_exact.astype(int), return_counts=True)
    ax.bar(values, counts, width=0.8, color=COLOR_SERIES, zorder=2)
    ax.axvline(observed, color=COLOR_TEXT, linewidth=2, zorder=3)
    ax.text(observed - 0.6, counts.max() * 0.97,
            f"Observed: {observed} repeats\n({100 * observed / pairs:.1f}% of pairs)\none-sided p = {p_value:.3f}",
            ha="right", va="top", color=COLOR_TEXT, fontsize=9)
    ax.set_xlabel("Exact-combination repeats in a shuffled copy of the session", color=COLOR_TEXT)
    ax.set_ylabel("Number of shuffles", color=COLOR_TEXT)
    ax.set_title(f"H1: repeats in {len(shuffled_exact):,} shuffled sessions vs. the real order",
                 loc="left", color=COLOR_TEXT, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor=COLOR_SURFACE)
    plt.close(fig)
    return path


def plot_sevens_by_phase(main: dict, path: Path) -> Path:
    t = main["h3_badly_timed_sevens"]["main"]
    boot = main["bootstrap_95_intervals"]
    labels = [f"Come-out rolls\n({t['come_out_rolls']} rolls)", f"Point-set rolls\n({t['point_set_rolls']} rolls)"]
    rates = [t["come_out_seven_rate"], t["point_set_seven_rate"]]
    cis = [boot["come_out_seven_rate"], boot["point_set_seven_rate"]]
    fig, ax = plt.subplots(figsize=(6.5, 3.6), facecolor=COLOR_SURFACE)
    _style(ax)
    x = np.arange(2)
    ax.bar(x, [100 * r for r in rates], width=0.45, color=COLOR_SERIES, zorder=2)
    err = np.array([[100 * (r - c[0]) for r, c in zip(rates, cis)], [100 * (c[1] - r) for r, c in zip(rates, cis)]])
    ax.errorbar(x, [100 * r for r in rates], yerr=err, fmt="none", ecolor=COLOR_TEXT, elinewidth=1.5,
                capsize=6, zorder=3)
    ax.axhline(100 / 6, color=COLOR_REFERENCE, linestyle="--", linewidth=1.2, zorder=1)
    ax.text(1.32, 100 / 6 + 0.3, "Fair dice: 16.7%", color=COLOR_REFERENCE, fontsize=9, ha="left", va="bottom")
    for xi, r in zip(x, rates):
        ax.text(xi, 7, f"{100 * r:.1f}%", color=COLOR_SURFACE, fontsize=11, ha="center", va="center",
                fontweight="bold", zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=COLOR_TEXT)
    ax.set_xlim(-0.6, 1.9)
    ax.set_ylim(0, 25)
    ax.set_ylabel("Share of rolls that were a 7 (%)", color=COLOR_TEXT)
    ax.set_title("H3: rate of 7s by game phase, with 95% block-bootstrap intervals",
                 loc="left", color=COLOR_TEXT, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor=COLOR_SURFACE)
    plt.close(fig)
    return path


def plot_power_curve(power: dict, simulated: list[dict], n_pairs: int, path: Path) -> Path:
    s_grid = np.linspace(0, 0.04, 161)
    analytic = [power_one_sample(rate_from_stickiness(s, an.FAIR_EXACT_REPEAT), an.FAIR_EXACT_REPEAT, n_pairs)
                for s in s_grid]
    fig, ax = plt.subplots(figsize=(6.5, 3.8), facecolor=COLOR_SURFACE)
    _style(ax)
    ax.plot(100 * s_grid, 100 * np.array(analytic), color=COLOR_SERIES, linewidth=2, zorder=2,
            label="Formula (normal approximation)")
    sx = [100 * r["stickiness"] for r in simulated]
    sy = [100 * r["rejection_rate"] for r in simulated]
    se = [196 * r["monte_carlo_se"] for r in simulated]
    ax.errorbar(sx, sy, yerr=se, fmt="o", color=COLOR_SERIES_2, markersize=6, markeredgecolor=COLOR_SURFACE,
                markeredgewidth=1.5, elinewidth=1.2, capsize=3, zorder=3,
                label=f"Simulated permutation test ({simulated[0]['sessions']:,} sessions each)")
    ax.axhline(80, color=COLOR_REFERENCE, linestyle="--", linewidth=1, zorder=1)
    ax.text(4.0, 81.5, "80% power", color=COLOR_REFERENCE, fontsize=9, ha="right", va="bottom")
    be = power["strategy_break_even_3_or_11"]["stickiness"]
    ax.axvline(100 * be, color=COLOR_REFERENCE, linestyle=":", linewidth=1.2, zorder=1)
    ax.text(100 * be + 0.06, 72, "3/11 bet\nbreaks even", color=COLOR_REFERENCE, fontsize=9, ha="left", va="center")
    mde = power["h1_exact_repeats"]["detectable_stickiness"]
    ax.axvline(100 * mde, color=COLOR_REFERENCE, linestyle=":", linewidth=1.2, zorder=1)
    ax.text(100 * mde + 0.06, 50, "detected 80%\nof the time", color=COLOR_REFERENCE, fontsize=9,
            ha="left", va="center")
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Stickiness: share of rolls that copy the previous combination (%)", color=COLOR_TEXT)
    ax.set_ylabel("Chance H1 is rejected (%)", color=COLOR_TEXT)
    ax.set_title(f"H1 power with {n_pairs:,} pairs (one-sided, alpha = 0.05)", loc="left",
                 color=COLOR_TEXT, fontsize=11)
    ax.legend(frameon=False, loc="lower right", labelcolor=COLOR_TEXT, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=200, facecolor=COLOR_SURFACE)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Run everything
# ---------------------------------------------------------------------------


def run_supplementary(df: pd.DataFrame, n_perm: int = N_PERMUTATIONS, n_boot: int = N_BOOTSTRAP,
                      n_sims: int = N_SIMULATIONS, n_sims_h3: int = N_SIMULATIONS_H3,
                      n_sim_shuffles: int = N_SIM_SHUFFLES, seed: int = SEED) -> tuple[dict, dict]:
    main = an.run_analysis(df, n_perm=n_perm, n_boot=n_boot, seed=seed)
    block_list = an.blocks(df)

    shuffled = shuffled_statistics(block_list, n_perm, seed)
    # The exact and total counts must match the confirmatory test shuffle for shuffle.
    check = an.permutation_repeat_counts(block_list, n_perm, np.random.default_rng(seed))
    for kind in ("exact", "total"):
        expected = sum((v[kind] for v in check.values()), start=np.zeros(n_perm, dtype=np.int64))
        if not np.array_equal(expected, shuffled[kind].astype(np.int64)):
            raise RuntimeError("shuffles do not match analyze.py; check the random-number usage")
    observed = observed_statistics(block_list)
    pairs = observed["pairs"]

    exploratory_repeats = {}
    for key, fair in (("weighted_repeat_count", None), ("shared_face", fair_shared_face_rate())):
        stat = "weighted" if key == "weighted_repeat_count" else "shared_face"
        exploratory_repeats[key] = {
            "observed": observed[stat], "permutation_mean": float(shuffled[stat].mean()),
            "p_value_one_sided": upper_tail_p(observed[stat], shuffled[stat]),
            "pairs": pairs,
        }
        if fair is not None:
            exploratory_repeats[key].update(observed_rate=observed[stat] / pairs,
                                            permutation_rate=float(shuffled[stat].mean()) / pairs,
                                            fair_dice_rate=fair)

    power = power_analysis(main)
    n_rolls = pairs + len(block_list)  # rolls in the analysed sequence (1,001 including row 0)
    simulated_h1 = simulate_h1_power(n_rolls, n_sims, n_sim_shuffles, seed)
    simulated_h3 = simulate_h3_power(main["sample"]["counted_rolls"], n_sims_h3,
                                     power["h3_point_vs_come_out"]["detectable_point_set_rate"], seed)

    results = {
        "settings": {"alpha": ALPHA, "power": POWER, "seed": seed, "permutations": n_perm,
                     "bootstrap_resamples": n_boot, "simulated_sessions_h1": n_sims,
                     "shuffles_per_simulated_session": n_sim_shuffles, "simulated_sessions_h3": n_sims_h3},
        "confirmatory_summary": {
            "h1_p_value": main["h1_exact_repeats"]["p_value_one_sided"],
            "h1_significant": main["h1_exact_repeats"]["significant"],
            "h2_formally_tested": main["h2_total_repeats"]["formally_tested"],
            "h3_p_value": main["h3_badly_timed_sevens"]["main"]["decision_p_value"],
            "h3_significant": main["h3_badly_timed_sevens"]["main"]["significant"],
        },
        "roles": ROLES,
        "effect_sizes": effect_sizes(main),
        "interval_comparison": interval_comparison(main),
        "ruled_out": ruled_out(main, df, n_boot, seed),
        "power_for_design_run": power,
        "simulation_check": {"h1_permutation_test": simulated_h1, "h3_z_test": simulated_h3},
        "exploratory": {
            "strategy_repeats": strategy_estimate(df),
            **exploratory_repeats,
            "first_vs_second_half": halves(df),
            "repeats_by_combination": repeats_by_combination(df),
            "bias_checks": bias_checks(df),
        },
        "data_quality_balance_replay": balance_check(df),
    }
    figures_data = {"main": main, "shuffled_exact": shuffled["exact"], "observed_exact": int(observed["exact"]),
                    "pairs": pairs}
    return results, figures_data


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def pct(x: float, digits: int = 2) -> str:
    return f"{100 * x:.{digits}f}%"


def ci_text(ci, digits: int = 1) -> str:
    return f"[{pct(ci[0], digits)}, {pct(ci[1], digits)}]"


def write_report(path: Path, r: dict, figure_names: dict) -> None:
    s = r["settings"]
    es = r["effect_sizes"]
    ro = r["ruled_out"]
    pw = r["power_for_design_run"]
    sim = r["simulation_check"]
    ex = r["exploratory"]
    bal = r["data_quality_balance_replay"]
    cs = r["confirmatory_summary"]

    lines = [
        "# Supplementary Analysis Report",
        "",
        f"Generated by `scripts/supplementary_analysis.py`: seed = {s['seed']}, {s['permutations']:,} permutations, "
        f"{s['bootstrap_resamples']:,} bootstrap resamples.",
        "",
        "These analyses support the written report. **None of them changes a confirmatory decision**, which come "
        "only from `scripts/analyze.py` (see `results/analysis_report.md`). The script re-runs that analysis with "
        f"the same seed: H1 one-sided p = {cs['h1_p_value']:.4f}, H3 one-sided p = {cs['h3_p_value']:.4f}; "
        "both fail to reject.",
        "",
        "## 1. Effect sizes for the pre-registered comparisons",
        "",
        f"*Role: {ROLES['effect_sizes']}.* For H1 and H2, Cohen's h is the standardized gap between the observed "
        "repeat rate and the shuffled baseline. It describes the size of the difference; the permutation test "
        "remains the formal inference, because adjacent pairs overlap.",
        "",
        f"Benchmarks (Cohen, 1988): h {es['benchmarks']['cohen_h']}; w {es['benchmarks']['cohen_w']}.",
        "",
        "| Comparison | Observed | Reference | Difference | Effect size |",
        "|---|---|---|---|---|",
    ]
    h1, h2 = es["h1_exact_repeats"], es["h2_total_repeats_descriptive"]
    lines += [
        f"| H1 exact-combination repeats | {pct(h1['observed_rate'])} | {pct(h1['permutation_baseline_rate'])} "
        f"(shuffled baseline) | {100 * h1['difference']:+.2f} points | h = {h1['cohen_h_vs_baseline']:.3f}; "
        f"rate ratio {h1['rate_ratio']:.2f} |",
        f"| H2 same-total repeats (descriptive) | {pct(h2['observed_rate'])} | "
        f"{pct(h2['permutation_baseline_rate'])} (shuffled baseline) | {100 * h2['difference']:+.2f} points | "
        f"h = {h2['cohen_h_vs_baseline']:.3f} |",
    ]
    for key, label in (("h3_main", "H3 7s, point set vs. come-out"),
                       ("h3_check_come_out_after_non_seven", "H3 check (come-outs after a non-7)")):
        e = es[key]
        lines.append(f"| {label} | {pct(e['point_set_rate'])} | {pct(e['come_out_rate'])} | "
                     f"{100 * e['difference']:+.2f} points | h = {e['cohen_h']:.3f}; risk ratio "
                     f"{e['risk_ratio']:.2f}; odds ratio {e['odds_ratio']:.2f} |")
    sc = es["sanity_check_totals"]
    lines += [f"| Sanity check: totals vs. fair dice | chi-square = {sc['chi_square']:.2f} | {sc['rolls']} rolls | "
              f"| w = {sc['cohen_w']:.3f} |", ""]

    labels = {"exact_repeat_rate": "H1 exact-repeat rate", "total_repeat_rate": "H2 same-total repeat rate",
              "point_set_seven_rate": "7 rate, point-set rolls", "come_out_seven_rate": "7 rate, come-out rolls",
              "seven_rate_difference": "Difference (point set minus come-out)"}
    lines += [
        f"**95% intervals: preregistered block bootstrap vs. textbook intervals assuming independent rolls** "
        f"(*{ROLES['interval_comparison']}*). "
        "With one session the bootstrap draws on about 20 non-overlapping 50-roll stretches, so it is itself "
        "noisy; here it is mostly narrower than the independence-based intervals. No conclusion depends on which is used.",
        "",
        "| Quantity | Estimate | Block bootstrap | Assuming independence |",
        "|---|---|---|---|",
    ]
    for key, label in labels.items():
        v = r["interval_comparison"][key]
        lines.append(f"| {label} | {pct(v['estimate'])} | {ci_text(v['block_bootstrap'], 2)} | "
                     f"{ci_text(v['independence'], 2)} ({v['independence_method']}) |")
    lines += [""]

    lines += [
        "## 2. What the data rule out (H1)",
        "",
        f"*Role: {ROLES['ruled_out']}.*",
        "",
        f"- Observed exact-repeat rate {pct(ro['observed_rate'])}; shuffled baseline "
        f"{pct(ro['permutation_baseline_rate'])}.",
        f"- One-sided 95% upper bound: {pct(ro['upper_bound_95_block_bootstrap'])} (moving-block bootstrap, "
        f"the preregistered interval method); {pct(ro['upper_bound_95_exact_binomial'])} (exact binomial, "
        "treating pairs as independent).",
        f"- In stickiness terms: at most {pct(ro['max_stickiness_block_bootstrap'])} of rolls copying the previous "
        f"combination (bootstrap); {pct(ro['max_stickiness_exact_binomial'])} (exact).",
        "",
        "| Strategy bet | Payout | Break-even win rate | Stickiness needed | Overall repeat rate needed | "
        "Excluded (bootstrap / exact) |",
        "|---|---|---|---|---|---|",
    ]
    for name, be in ro["strategy_break_even"].items():
        lines.append(f"| Same {name} again | {be['payout_to_1']} to 1 | {pct(be['break_even_rate'])} | "
                     f"{pct(be['break_even_stickiness'])} | {pct(be['overall_combination_repeat_rate'])} | "
                     f"{'yes' if ro['break_even_excluded_block_bootstrap'][name] else 'no'} / "
                     f"{'yes' if ro['break_even_excluded_exact_binomial'][name] else 'no'} |")
    lines += ["", f"Note: {ro['note']}", ""]

    lines += [
        "## 3. Power for the design actually run",
        "",
        "This is a sensitivity analysis for the achieved design: it restates the smallest effect each test detects "
        "with the sample actually collected. It is not post hoc \"observed power\", which would plug in the "
        "observed effect and only restate the p-value.",
        "",
        "One-sided alpha = 0.05 and 80% power, normal approximation with Cohen's h (equivalent to statsmodels' "
        "`NormalIndPower`). The last column is the preregistration's quicker approximation, which uses the "
        "standard error under the null only and so gives slightly smaller values.",
        "",
        "| Test | Sample | Fair value | Smallest effect detected 80% of the time | h | Two-sided | "
        "Bonferroni 0.025 | Preregistration approx. |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key, label in (("h1_exact_repeats", "H1 exact repeats"), ("h2_total_repeats", "H2 total repeats")):
        p = pw[key]
        lines.append(f"| {label} | {p['pairs']:,} pairs | {pct(p['fair_rate'])} | "
                     f"{pct(p['detectable_rate_one_sided'])} (stickiness {pct(p['detectable_stickiness'])}) | "
                     f"{p['cohen_h']:.3f} | {pct(p['detectable_rate_two_sided'])} | "
                     f"{pct(p['detectable_rate_bonferroni_0_025'])} | {pct(p['preregistration_approximation'])} |")
    for key, label in (("h3_point_vs_come_out", "H3 point set vs. come-out"),
                       ("h3_check_come_out_after_non_seven", "H3 check")):
        p = pw[key]
        lines.append(f"| {label} | {p['point_set_rolls']} vs. {p['come_out_rolls']} rolls | {pct(p['fair_rate'])} | "
                     f"point-set rate {pct(p['detectable_point_set_rate'])} "
                     f"({100 * p['detectable_difference']:+.1f} points) | {p['cohen_h']:.3f} | "
                     f"{pct(p['detectable_point_set_rate_two_sided'])} | "
                     f"{pct(p['detectable_point_set_rate_bonferroni_0_025'])} | "
                     f"{pct(p['preregistration_approximation'])} |")
    p = pw["exploratory_point_set_vs_one_sixth"]
    be = pw["strategy_break_even_3_or_11"]
    lines += [
        f"| Exploratory: point-set 7s vs. 1/6 | {p['rolls']} rolls | 16.67% | {pct(p['detectable_rate'])} | "
        f"{p['cohen_h']:.3f} | | | |",
        "",
        f"The stickiness at which the 3/11 bet breaks even ({pct(be['stickiness'])}, an overall repeat rate of "
        f"{pct(be['overall_repeat_rate'])}, h = {be['cohen_h']:.3f}) would be detected only "
        f"{pct(be['power_with_this_sample'], 0)} of the time with this sample; 80% power would need about "
        f"{be['pairs_needed_for_80_percent_power']:,} pairs.",
        "",
        f"The formulas treat pairs as independent. Under independence, overlapping pairs (which share a roll) "
        f"raise the variance of the repeat count by only "
        f"{pct(pw['overlap_variance_inflation']['combinations'], 1)} for combinations and "
        f"{pct(pw['overlap_variance_inflation']['totals'], 1)} for totals; section 4 checks the tests directly.",
        "",
        f"![H1 power curve]({figure_names['power']})",
        "",
        "## 4. Simulation check of the tests",
        "",
        f"*Role: {ROLES['simulation_check']}.*",
        "",
        f"H1: {sim['h1_permutation_test'][0]['sessions']:,} simulated sessions of fair dice per row (1,001 rolls, "
        f"{sim['h1_permutation_test'][0]['shuffles_per_session']} shuffles each), in which each roll copies the "
        "previous combination with the stated probability.",
        "",
        "| Stickiness | Repeat rate | Rejected (simulated) | Monte Carlo SE | Formula |",
        "|---|---|---|---|---|",
    ]
    for row in sim["h1_permutation_test"]:
        lines.append(f"| {pct(row['stickiness'], 1)} | {pct(row['repeat_rate'])} | {pct(row['rejection_rate'], 1)} | "
                     f"{pct(row['monte_carlo_se'], 1)} | {pct(row['analytic_power'], 1)} |")
    lines += ["", "A recording error that copies the previous entry with probability e produces exactly this "
              "sequence model, so the same rows show how often copy errors at rate e would make H1 falsely "
              "significant.", ""]
    lines += ["", "H3: simulated pass-line sessions of 1,000 rolls starting on a come-out roll.", "",
              "| Point-set 7 rate | Rejected (simulated) | Monte Carlo SE | Mean come-out rolls | "
              "SD of the difference in 7 rates |", "|---|---|---|---|---|"]
    for row in sim["h3_z_test"]:
        lines.append(f"| {pct(row['point_set_seven_rate'], 1)} | {pct(row['rejection_rate'], 1)} | "
                     f"{pct(row['monte_carlo_se'], 1)} | {row['mean_come_out_rolls']:.0f} | "
                     f"{100 * row['sd_of_difference']:.2f} points |")
    diff_ci = r["interval_comparison"]["seven_rate_difference"]
    wald_se = (diff_ci["independence"][1] - diff_ci["estimate"]) / 1.96
    boot_se = (diff_ci["block_bootstrap"][1] - diff_ci["block_bootstrap"][0]) / (2 * 1.96)
    lines += ["", f"With fair dice, the simulated spread of the difference ({100 * sim['h3_z_test'][0]['sd_of_difference']:.2f} "
              f"points) is close to the independence-based (Wald) standard error ({100 * wald_se:.2f} points) and "
              f"wider than the block bootstrap implies (about {100 * boot_se:.2f} points), so the Wald interval in "
              "section 1 is the safer reading for H3."]

    lines += ["", "## 5. Exploratory analyses (no reject / fail-to-reject decisions)", "",
              f"Each item is tagged *{PREREGISTERED}* (named as exploratory in `docs/preregistration.md`) or "
              f"*{POST_HOC}* (chosen after seeing the data; hypothesis-generating only).", "",
              f"**Repeats after the strategy's numbers** (exact 95% intervals; *{ROLES['exploratory.strategy_repeats']}*):",
              "",
              "| After a... | Rolls following | Same total again | Rate [95% CI] | Fair | Break-even |",
              "|---|---|---|---|---|---|"]
    for name, v in ex["strategy_repeats"].items():
        lines.append(f"| {name} | {v['rolls_following']} | {v['repeats']} | {pct(v['rate'], 1)} "
                     f"{ci_text(v['exact_95_ci'])} | {pct(v['fair_rate'], 1)} | {pct(v['break_even_rate'], 1)} |")
    w, f = ex["weighted_repeat_count"], ex["shared_face"]
    hv = ex["first_vs_second_half"]
    bc = ex["bias_checks"]
    lines += [
        "",
        f"- **Weighted repeat count** (*{ROLES['exploratory.weighted_repeat_count']}*; a repeated double counts 2, "
        f"any other repeat 1): observed {w['observed']:.0f}, "
        f"shuffled mean {w['permutation_mean']:.1f}, one-sided p = {w['p_value_one_sided']:.3f}.",
        f"- **Consecutive rolls sharing at least one face** (*{ROLES['exploratory.shared_face']}*; single "
        f"sticky die): {pct(f['observed_rate'], 1)} "
        f"observed vs. {pct(f['permutation_rate'], 1)} in shuffles (fair dice {pct(f['fair_dice_rate'], 1)}); "
        f"one-sided p = {f['p_value_one_sided']:.3f}.",
        f"- **First vs. second half** (*{ROLES['exploratory.first_vs_second_half']}*): exact-repeat rate "
        f"{pct(hv['first']['exact_repeat_rate'], 1)} vs. "
        f"{pct(hv['second']['exact_repeat_rate'], 1)} (Fisher two-sided p = {hv['repeat_rate_fisher_p_two_sided']:.2f}); "
        f"point-set 7 rate {pct(hv['first']['point_set_seven_rate'], 1)} vs. "
        f"{pct(hv['second']['point_set_seven_rate'], 1)} (p = {hv['point_set_seven_rate_fisher_p_two_sided']:.2f}).",
        f"- **Combination frequencies** (*{ROLES['exploratory.bias_checks']}*; 21 categories, "
        f"{bc['combinations']['rolls']} rolls): chi-square = "
        f"{bc['combinations']['chi_square']:.2f}, df = 20, p = {bc['combinations']['p_value']:.3f}, "
        f"w = {bc['combinations']['cohen_w']:.3f}.",
        f"- **Face frequencies** (*{ROLES['exploratory.bias_checks']}*; {bc['faces']['faces']} faces): "
        f"chi-square = {bc['faces']['chi_square']:.2f}, "
        f"df = 5, p = {bc['faces']['p_value']:.3f}, w = {bc['faces']['cohen_w']:.3f}; counts "
        + ", ".join(f"{k}: {v}" for k, v in bc["faces"]["observed"].items()) + ".",
        "",
        f"**Repeats by combination** (descriptive; *{ROLES['exploratory.repeats_by_combination']}*):",
        "",
        "| Combination | Times as previous roll | Repeated | Expected (fair) |",
        "|---|---|---|---|",
    ]
    for row in ex["repeats_by_combination"]:
        lines.append(f"| {row['combination']} | {row['times_as_previous_roll']} | {row['repeats']} | "
                     f"{row['expected_repeats_fair']:.1f} |")

    lines += ["", "## 6. Data-quality check: pass-line balance replay", "",
              f"*Role: {ROLES['data_quality_balance_replay']}.*", ""]
    if bal.get("replayed"):
        lines += [
            f"Replaying a ${bal['bet']} pass-line bet on every come-out roll from ${bal['starting_balance']} gives "
            f"an ending balance of ${bal['ending_balance']} (recorded: ${bal['recorded_ending_balance']}; "
            f"{'matches' if bal['matches_recording'] else 'does NOT match'}). "
            f"{bal['rounds_decided']} rounds were decided: {bal['rounds_won']} won, {bal['rounds_lost']} lost "
            f"(win rate {pct(bal['win_rate'], 1)}, exact 95% CI {ci_text(bal['win_rate_exact_95_ci'])}; fair "
            f"{pct(bal['fair_win_rate'], 1)}). Lowest balance during the session: ${bal['lowest_balance']}. "
            f"Bet still open at the end: {'yes' if bal['bet_open_at_end'] else 'no'}.",
        ]
    else:
        lines.append(f"Not replayed: {bal['reason']}.")
    lines += ["", "## Figures", "",
              f"![H1 permutation distribution]({figure_names['permutation']})", "",
              f"![Rate of 7s by phase]({figure_names['sevens']})", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Supplementary analyses for the written report.")
    parser.add_argument("--data", type=Path, default=REPO_ROOT / "data" / "cleaned" / "analysis_data.csv")
    parser.add_argument("--report", type=Path, default=REPO_ROOT / "results" / "supplementary_report.md")
    parser.add_argument("--json", type=Path, default=REPO_ROOT / "results" / "supplementary_results.json")
    parser.add_argument("--simulations", type=int, default=N_SIMULATIONS)
    parser.add_argument("--simulations-h3", type=int, default=N_SIMULATIONS_H3)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    if not args.data.exists():
        print(f"{args.data} not found. Run scripts/prepare_data.py first.")
        return 1
    df = core.load_cleaned(args.data)
    results, fig = run_supplementary(df, n_sims=args.simulations, n_sims_h3=args.simulations_h3, seed=args.seed)

    out_dir = args.report.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "permutation": plot_permutation_distribution(fig["shuffled_exact"], fig["observed_exact"],
                                                     results["confirmatory_summary"]["h1_p_value"], fig["pairs"],
                                                     out_dir / "h1_permutation_distribution.png"),
        "sevens": plot_sevens_by_phase(fig["main"], out_dir / "h3_sevens_by_phase.png"),
        "power": plot_power_curve(results["power_for_design_run"], results["simulation_check"]["h1_permutation_test"],
                                  fig["pairs"], out_dir / "h1_power_curve.png"),
    }
    names = {k: v.name for k, v in paths.items()}
    write_report(args.report, results, names)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(an.to_jsonable(results), indent=2))
    print(f"Wrote {args.report}, {args.json}, and {', '.join(str(p) for p in paths.values())}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
