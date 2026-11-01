"""Run the pre-registered analyses on the cleaned dataset.

Usage (from the repository root, after scripts/prepare_data.py):

    python scripts/analyze.py

Runs, in the order fixed by docs/preregistration.md:

0. Descriptive statistics: frequency tables, summary statistics, and a
   histogram of totals, before any test.
1. Sanity check: chi-square goodness of fit of totals to fair dice, per machine.
2. H1: one-sided within-block permutation test for excess exact-combination repeats.
3. H2: the same test for same-total repeats, formally tested only if H1 is significant.
4. H3: one-sided two-proportion z-test that 7s are more common on point-set rolls
   than on come-out rolls, with Fisher's exact test when an expected cell count
   is below 5, and a sensitivity check.
5. Exploratory: the 7 rate in each phase against the fair rate of 1/6.

A result is significant when p <= alpha (0.05 per claim). The report also notes
whether each formal result would pass the stricter Bonferroni threshold of 0.025.
Descriptive 95% intervals use a moving-block bootstrap. All randomness uses a
fixed seed, so results are reproducible. Writes results/analysis_report.md,
results/analysis_results.json, and results/totals_histogram.png.
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

import craps_core as core

REPO_ROOT = Path(__file__).resolve().parent.parent

ALPHA = 0.05            # per claim; see "Multiple comparisons" in docs/preregistration.md
BONFERRONI_ALPHA = 0.025  # reported for reference only: 0.05 split across the two claims
SEED = 20261101
N_PERMUTATIONS = 10_000
N_BOOTSTRAP = 10_000
BOOTSTRAP_BLOCK_LENGTH = 50
MIN_ROLLS_FOR_CHI_SQUARE_B = 180  # every expected count >= 5 (180 / 36 = 5)
PERMUTATION_CHUNK = 2_000

FAIR_TOTAL_PROBS = {t: (6 - abs(t - 7)) / 36 for t in range(2, 13)}
FAIR_SEVEN = 1 / 6
FAIR_TOTAL_MEAN = 7.0
FAIR_TOTAL_SD = math.sqrt(35 / 6)  # about 2.42
FAIR_EXACT_REPEAT = 66 / 1296   # sum of squared combination probabilities
FAIR_TOTAL_REPEAT = 146 / 1296  # sum of squared total probabilities
COMBINATIONS = [f"{a}-{b}" for a in range(1, 7) for b in range(a, 7)]
COMBINATION_CODE = {c: i for i, c in enumerate(COMBINATIONS)}
FAIR_COMBINATION_PROBS = {c: (1 if c[0] == c[2] else 2) / 36 for c in COMBINATIONS}

# Chart colors (see the dataviz reference palette): one series hue, neutral reference ink.
COLOR_SERIES = "#2a78d6"
COLOR_REFERENCE = "#52514e"
COLOR_TEXT = "#0b0b0b"
COLOR_GRID = "#e4e3df"
COLOR_SURFACE = "#fcfcfb"


def is_significant(p: float, alpha: float = ALPHA) -> bool:
    """Ch. 3, step 6: reject the null when p <= alpha."""
    return bool(p <= alpha)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def rolls_only(df: pd.DataFrame) -> pd.DataFrame:
    """All non-gap rows, in log order."""
    return df.loc[df["verification_status"] != "gap"].reset_index(drop=True)


def blocks(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Contiguous analysis blocks, in log order."""
    rolls = rolls_only(df)
    order = list(dict.fromkeys(rolls["analysis_block_id"]))
    return [rolls.loc[rolls["analysis_block_id"] == b].reset_index(drop=True) for b in order]


# ---------------------------------------------------------------------------
# Descriptive statistics (Ch. 1: describe before testing)
# ---------------------------------------------------------------------------


def describe_rolls(rolls: pd.DataFrame) -> dict:
    """Frequency tables and summary statistics for a set of non-gap rolls."""
    n = int(len(rolls))
    totals = rolls["total"].astype(int)
    counted = rolls.loc[rolls["counts_toward_sample"]]
    phase = counted["phase_before_roll"].replace("", "unknown")
    out = {
        "rolls": n,
        "totals": {
            t: {"observed": int((totals == t).sum()), "expected": round(n * FAIR_TOTAL_PROBS[t], 1)}
            for t in range(2, 13)
        },
        "combinations": {
            c: {"observed": int((rolls["combination"] == c).sum()),
                "expected": round(n * FAIR_COMBINATION_PROBS[c], 1)}
            for c in COMBINATIONS
        },
        "phase_counts": {k: int((phase == k).sum()) for k in ("come_out", "point_set", "unknown")},
    }
    if n:
        modes = totals.mode().tolist()
        out["total_summary"] = {
            "mean": float(totals.mean()), "median": float(totals.median()),
            "mode": [int(m) for m in modes], "sd": float(totals.std(ddof=1)) if n > 1 else float("nan"),
            "fair_mean": FAIR_TOTAL_MEAN, "fair_median": 7.0, "fair_mode": [7], "fair_sd": FAIR_TOTAL_SD,
        }
    return out


def descriptives(df: pd.DataFrame) -> dict:
    """Descriptive statistics pooled and, if machine B was used, per machine."""
    rolls = rolls_only(df)
    status = df["verification_status"].value_counts().to_dict()
    out = {
        "pooled": describe_rolls(rolls),
        "data_quality": {k: int(status.get(k, 0)) for k in
                         ("verified", "corrected_from_history", "recovered_from_history", "gap")},
    }
    machines = sorted(rolls["machine_id"].unique())
    if len(machines) > 1:
        out["by_machine"] = {m: describe_rolls(rolls.loc[rolls["machine_id"] == m]) for m in machines}
    return out


def plot_totals_histogram(df: pd.DataFrame, path: Path) -> Path:
    """Observed count of each total, with the fair-dice expected count marked.

    One panel per machine (small multiples) if machine B was used.
    """
    rolls = rolls_only(df)
    machines = sorted(rolls["machine_id"].unique())
    fig, axes = plt.subplots(1, len(machines), figsize=(6.5 * len(machines), 4), squeeze=False,
                             facecolor=COLOR_SURFACE)
    totals = list(range(2, 13))
    for ax, m in zip(axes[0], machines):
        g = rolls.loc[rolls["machine_id"] == m, "total"].astype(int)
        n = len(g)
        observed = [int((g == t).sum()) for t in totals]
        expected = [n * FAIR_TOTAL_PROBS[t] for t in totals]
        ax.set_facecolor(COLOR_SURFACE)
        ax.bar(totals, observed, width=0.55, color=COLOR_SERIES, label="Observed", zorder=2)
        ax.scatter(totals, expected, marker="_", s=420, linewidths=2, color=COLOR_REFERENCE,
                   label="Expected (fair dice)", zorder=3)
        ax.set_xticks(totals)
        ax.set_xlabel("Total of the two dice", color=COLOR_TEXT)
        ax.set_ylabel("Number of rolls", color=COLOR_TEXT)
        title = f"Totals rolled, machine {m} ({n} rolls)" if len(machines) > 1 else f"Totals rolled ({n} rolls)"
        ax.set_title(title, loc="left", color=COLOR_TEXT, fontsize=12)
        ax.grid(axis="y", color=COLOR_GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(COLOR_REFERENCE)
        ax.tick_params(colors=COLOR_TEXT, length=0)
        ax.legend(frameon=False, loc="upper right", labelcolor=COLOR_TEXT)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor=COLOR_SURFACE)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Sanity check
# ---------------------------------------------------------------------------


def sanity_check(df: pd.DataFrame) -> dict:
    """Chi-square goodness of fit of totals 2-12 to fair dice, per machine."""
    out = {}
    for machine, g in rolls_only(df).groupby("machine_id", sort=True):
        totals = g["total"].astype(int)
        n = int(len(totals))
        observed = np.array([(totals == t).sum() for t in range(2, 13)])
        expected = np.array([n * FAIR_TOTAL_PROBS[t] for t in range(2, 13)])
        result = {
            "rolls": n,
            "observed": {t: int(o) for t, o in zip(range(2, 13), observed)},
            "expected": {t: round(float(e), 2) for t, e in zip(range(2, 13), expected)},
        }
        if machine == "B" and n < MIN_ROLLS_FOR_CHI_SQUARE_B:
            result.update(tested=False, reason=f"fewer than {MIN_ROLLS_FOR_CHI_SQUARE_B} rolls; reported descriptively")
        elif n == 0:
            result.update(tested=False, reason="no rolls")
        else:
            chi2, p = stats.chisquare(observed, expected)
            result.update(tested=True, chi_square=float(chi2), df=10, p_value=float(p),
                          differs_from_fair=is_significant(p),
                          small_expected_counts=bool((expected < 5).any()))
        out[machine] = result
    return out


# ---------------------------------------------------------------------------
# H1 / H2 permutation tests
# ---------------------------------------------------------------------------


def count_repeats(seq: np.ndarray) -> int:
    return int((seq[1:] == seq[:-1]).sum()) if len(seq) > 1 else 0


def permutation_repeat_counts(block_list: list[pd.DataFrame], n_perm: int,
                              rng: np.random.Generator) -> dict[str, dict[str, np.ndarray]]:
    """Shuffle rolls within each block and count repeats in every permutation.

    Combination and total are shuffled together (the same row order), so H1
    and H2 use the same permutations. Returns per-block arrays of length
    `n_perm` for exact and total repeats, keyed by block id.
    """
    out = {}
    for b in block_list:
        block_id = b["analysis_block_id"].iloc[0]
        n = len(b)
        exact = np.zeros(n_perm, dtype=np.int64)
        total = np.zeros(n_perm, dtype=np.int64)
        if n > 1:
            comb = b["combination"].map(COMBINATION_CODE).to_numpy(dtype=np.int8)
            tot = b["total"].to_numpy(dtype=np.int8)
            done = 0
            while done < n_perm:
                size = min(PERMUTATION_CHUNK, n_perm - done)
                idx = rng.permuted(np.tile(np.arange(n, dtype=np.int32), (size, 1)), axis=1)
                c, t = comb[idx], tot[idx]
                exact[done:done + size] = (c[:, 1:] == c[:, :-1]).sum(axis=1)
                total[done:done + size] = (t[:, 1:] == t[:, :-1]).sum(axis=1)
                done += size
        out[block_id] = {"exact": exact, "total": total}
    return out


def repeat_test(block_list: list[pd.DataFrame], perm_counts: dict, kind: str, n_perm: int) -> dict:
    """Observed vs permutation repeats for `kind` in {'exact', 'total'}."""
    column = "combination" if kind == "exact" else "total"
    observed = sum(count_repeats(b[column].to_numpy()) for b in block_list)
    pairs = sum(max(len(b) - 1, 0) for b in block_list)
    perm = sum((perm_counts[b["analysis_block_id"].iloc[0]][kind] for b in block_list),
               start=np.zeros(n_perm, dtype=np.int64))
    p_upper = (1 + int((perm >= observed).sum())) / (n_perm + 1)
    baseline_rate = float(perm.mean() / pairs) if pairs else float("nan")
    observed_rate = observed / pairs if pairs else float("nan")
    return {
        "valid_pairs": int(pairs),
        "observed_repeats": int(observed),
        "observed_rate": observed_rate,
        "permutation_mean_repeats": float(perm.mean()),
        "permutation_baseline_rate": baseline_rate,
        "permutation_95th_percentile_repeats": float(np.percentile(perm, 95)),
        "rate_difference": observed_rate - baseline_rate,
        "fair_dice_rate": FAIR_EXACT_REPEAT if kind == "exact" else FAIR_TOTAL_REPEAT,
        "p_value_one_sided": p_upper,
    }


# ---------------------------------------------------------------------------
# H3
# ---------------------------------------------------------------------------


def seven_table(rows: pd.DataFrame) -> dict:
    point = rows.loc[rows["phase_before_roll"] == "point_set"]
    come_out = rows.loc[rows["phase_before_roll"] == "come_out"]
    return {
        "point_set_rolls": int(len(point)),
        "point_set_sevens": int((point["total"] == 7).sum()),
        "come_out_rolls": int(len(come_out)),
        "come_out_sevens": int((come_out["total"] == 7).sum()),
    }


def two_proportion_test(t: dict) -> dict:
    """One-sided z-test: 7-rate on point-set rolls > 7-rate on come-out rolls."""
    n1, x1 = t["point_set_rolls"], t["point_set_sevens"]
    n2, x2 = t["come_out_rolls"], t["come_out_sevens"]
    out = dict(t)
    if n1 == 0 or n2 == 0:
        out.update(tested=False, reason="no rolls in one phase")
        return out
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se if se > 0 else float("nan")
    p = float(stats.norm.sf(z)) if se > 0 else float("nan")
    # Expected cell counts under independence: row total x column total / grand total.
    n, sevens = n1 + n2, x1 + x2
    expected_cells = [n1 * sevens / n, n1 * (n - sevens) / n, n2 * sevens / n, n2 * (n - sevens) / n]
    out.update(tested=True, point_set_seven_rate=p1, come_out_seven_rate=p2,
               rate_difference=p1 - p2, z=z, p_value_one_sided=p,
               smallest_expected_cell=float(min(expected_cells)))
    if min(expected_cells) < 5:
        _, fisher_p = stats.fisher_exact([[x1, n1 - x1], [x2, n2 - x2]], alternative="greater")
        out.update(fisher_exact_p_value_one_sided=float(fisher_p))
    return out


def h3_test(df: pd.DataFrame) -> dict:
    eligible = df.loc[df["h3_eligible"]]
    main = two_proportion_test(seven_table(eligible))
    # Sensitivity: keep only come-out rolls whose previous observed roll was not a 7.
    keep = (eligible["phase_before_roll"] == "point_set") | (
        eligible["valid_pair"] & (eligible["previous_total"].fillna(0) != 7)
    )
    sensitivity = two_proportion_test(seven_table(eligible.loc[keep]))
    return {"main": main, "sensitivity_come_out_not_after_seven": sensitivity}


def sevens_vs_fair(df: pd.DataFrame) -> dict:
    """Exploratory: each phase's 7 rate against the fair rate of 1/6.

    One-sided exact binomial tests (more 7s than fair). Reported without a
    reject / fail-to-reject decision; they help interpret H3 (timing vs.
    overall bias) but are not confirmatory.
    """
    t = seven_table(df.loc[df["h3_eligible"]])
    out = {}
    for phase in ("point_set", "come_out"):
        n, k = t[f"{phase}_rolls"], t[f"{phase}_sevens"]
        result = {"rolls": n, "sevens": k, "fair_rate": FAIR_SEVEN}
        if n:
            result.update(rate=k / n, p_value_one_sided=float(stats.binomtest(k, n, FAIR_SEVEN,
                                                                              alternative="greater").pvalue))
        out[phase] = result
    return out


# ---------------------------------------------------------------------------
# Moving-block bootstrap
# ---------------------------------------------------------------------------


def moving_block_bootstrap(df: pd.DataFrame, rng: np.random.Generator,
                           n_boot: int = N_BOOTSTRAP, block_length: int = BOOTSTRAP_BLOCK_LENGTH) -> dict:
    """95% percentile intervals for the descriptive rates.

    Windows of `block_length` consecutive rolls are drawn with replacement
    from inside each analysis block (never spanning a gap or machine). An
    analysis block shorter than the window length is used whole. Each resample
    draws ceil(n / block_length) windows. Each row carries its own pair and
    phase indicators, so a pair is always a real adjacent pair from the log.
    """
    rolls = rolls_only(df)
    n = len(rolls)
    if n == 0:
        return {}
    valid = rolls["valid_pair"].to_numpy(bool)
    exact = rolls["exact_repeat"].fillna(False).to_numpy(bool) & valid
    total = rolls["total_repeat"].fillna(False).to_numpy(bool) & valid
    elig = rolls["h3_eligible"].to_numpy(bool)
    point = elig & (rolls["phase_before_roll"] == "point_set").to_numpy()
    come_out = elig & (rolls["phase_before_roll"] == "come_out").to_numpy()
    seven = (rolls["total"] == 7).to_numpy(bool)
    indicators = np.column_stack([valid, exact, total, point, point & seven, come_out, come_out & seven]).astype(np.int64)
    cumulative = np.vstack([np.zeros(indicators.shape[1], dtype=np.int64), indicators.cumsum(axis=0)])

    windows = []
    block_ids = rolls["analysis_block_id"].to_numpy()
    starts = np.flatnonzero(np.r_[True, block_ids[1:] != block_ids[:-1]])
    ends = np.r_[starts[1:], n]
    for s, e in zip(starts, ends):
        if e - s >= block_length:
            for w in range(s, e - block_length + 1):
                windows.append(cumulative[w + block_length] - cumulative[w])
        else:
            windows.append(cumulative[e] - cumulative[s])
    windows = np.array(windows)

    k = math.ceil(n / block_length)
    draws = rng.integers(0, len(windows), size=(n_boot, k))
    sums = windows[draws].sum(axis=1)  # (n_boot, n_indicators)
    with np.errstate(divide="ignore", invalid="ignore"):
        exact_rate = sums[:, 1] / sums[:, 0]
        total_rate = sums[:, 2] / sums[:, 0]
        point_rate = sums[:, 4] / sums[:, 3]
        come_out_rate = sums[:, 6] / sums[:, 5]

    def interval(x):
        x = x[np.isfinite(x)]
        if len(x) == 0:
            return [float("nan"), float("nan")]
        return [float(np.percentile(x, 2.5)), float(np.percentile(x, 97.5))]

    return {
        "exact_repeat_rate": interval(exact_rate),
        "total_repeat_rate": interval(total_rate),
        "point_set_seven_rate": interval(point_rate),
        "come_out_seven_rate": interval(come_out_rate),
        "seven_rate_difference": interval(point_rate - come_out_rate),
        "settings": {"resamples": n_boot, "window_length": block_length, "windows_per_resample": k},
    }


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------


def run_analysis(df: pd.DataFrame, n_perm: int = N_PERMUTATIONS, n_boot: int = N_BOOTSTRAP,
                 seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    block_list = blocks(df)
    perm_counts = permutation_repeat_counts(block_list, n_perm, rng)

    h1 = repeat_test(block_list, perm_counts, "exact", n_perm)
    h1["significant"] = is_significant(h1["p_value_one_sided"])
    h1["passes_bonferroni_0_025"] = is_significant(h1["p_value_one_sided"], BONFERRONI_ALPHA)

    h2 = repeat_test(block_list, perm_counts, "total", n_perm)
    if h1["significant"]:
        h2["formally_tested"] = True
        h2["significant"] = is_significant(h2["p_value_one_sided"])
        # Under Bonferroni, H2 would only be tested if H1 passed 0.025.
        h2["passes_bonferroni_0_025"] = bool(h1["passes_bonferroni_0_025"]
                                             and is_significant(h2["p_value_one_sided"], BONFERRONI_ALPHA))
    else:
        # Gatekeeping: H2 is reported descriptively, with no p-value or decision.
        h2["formally_tested"] = False
        h2.pop("p_value_one_sided")

    h3 = h3_test(df)
    main = h3["main"]
    if main.get("tested"):
        p = main.get("fisher_exact_p_value_one_sided", main["p_value_one_sided"])
        main["decision_p_value"] = p
        main["decision_test"] = "fisher_exact" if "fisher_exact_p_value_one_sided" in main else "z_test"
        main["significant"] = is_significant(p)
        main["passes_bonferroni_0_025"] = is_significant(p, BONFERRONI_ALPHA)

    results = {
        "settings": {"alpha_per_claim": ALPHA, "bonferroni_reference_alpha": BONFERRONI_ALPHA,
                     "seed": seed, "permutations": n_perm, "bootstrap_resamples": n_boot},
        "sample": {
            "counted_rolls": int(df["counts_toward_sample"].sum()),
            "machines": sorted(df["machine_id"].unique().tolist()),
            "analysis_blocks": len(block_list),
            "gaps": int((df["verification_status"] == "gap").sum()),
        },
        "descriptives": descriptives(df),
        "sanity_check": sanity_check(df),
        "h1_exact_repeats": h1,
        "h2_total_repeats": h2,
        "h3_badly_timed_sevens": h3,
        "exploratory_sevens_vs_fair": sevens_vs_fair(df),
        "bootstrap_95_intervals": moving_block_bootstrap(df, rng, n_boot=n_boot),
    }

    machines = results["sample"]["machines"]
    if len(machines) > 1:
        # Per-machine results alongside the pooled ones (exploratory).
        per_machine = {}
        for m in machines:
            mb = [b for b in block_list if b["machine_id"].iloc[0] == m]
            per_machine[m] = {
                "exact_repeats": repeat_test(mb, perm_counts, "exact", n_perm),
                "total_repeats": repeat_test(mb, perm_counts, "total", n_perm),
                "sevens": two_proportion_test(seven_table(df.loc[df["h3_eligible"] & (df["machine_id"] == m)])),
            }
        results["per_machine_exploratory"] = per_machine
    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def pct(x: float) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.2f}%"


def fmt_p(p: float) -> str:
    return f"{p:.4f}" if p >= 0.0001 else f"{p:.1e}"


def interval_text(ci) -> str:
    return f"[{pct(ci[0])}, {pct(ci[1])}]" if ci else "n/a"


def bonferroni_line(result: dict) -> str:
    if not result.get("significant"):
        return ""
    passes = result.get("passes_bonferroni_0_025")
    return (f"- Bonferroni check (alpha = {BONFERRONI_ALPHA}, for reference only): "
            + ("would also be significant." if passes else "would **not** be significant at this stricter threshold."))


def descriptive_lines(d: dict, figure_name: str | None) -> list[str]:
    pooled = d["pooled"]
    dq = d["data_quality"]
    lines = [
        "## Descriptive statistics",
        "",
        f"Data quality: {dq['verified']} rolls verified live, {dq['corrected_from_history']} corrected at a "
        f"10-roll check, {dq['recovered_from_history']} recovered from the history display (including each "
        f"machine's row 0), {dq['gap']} gap(s). Full counts are in `results/validation_summary.md`.",
        "",
    ]
    if figure_name:
        lines += [f"![Histogram of totals with fair-dice expected counts]({figure_name})", ""]

    ts = pooled.get("total_summary")
    if ts:
        mode = ", ".join(str(m) for m in ts["mode"])
        lines += [
            "| Statistic of the total | Observed | Fair dice |",
            "|---|---|---|",
            f"| Mean | {ts['mean']:.2f} | {ts['fair_mean']:.2f} |",
            f"| Median | {ts['median']:.1f} | {ts['fair_median']:.1f} |",
            f"| Mode | {mode} | 7 |",
            f"| Standard deviation | {ts['sd']:.2f} | {ts['fair_sd']:.2f} |",
            "",
        ]

    n = pooled["rolls"]
    lines += [f"**Frequency of totals** ({n} rolls, all machines):", "",
              "| Total | Observed | Expected | Observed % | Expected % |", "|---|---|---|---|---|"]
    for t, c in pooled["totals"].items():
        lines.append(f"| {t} | {c['observed']} | {c['expected']:.1f} | "
                     f"{pct(c['observed'] / n if n else float('nan'))} | {pct(FAIR_TOTAL_PROBS[int(t)])} |")

    lines += ["", "**Frequency of dice combinations:**", "",
              "| Combination | Observed | Expected |", "|---|---|---|"]
    for c, v in pooled["combinations"].items():
        lines.append(f"| {c} | {v['observed']} | {v['expected']:.1f} |")

    pc = pooled["phase_counts"]
    lines += ["", f"**Game phase of counted rolls:** {pc['come_out']} come-out, {pc['point_set']} point set, "
                  f"{pc['unknown']} unknown (excluded from H3).", ""]
    if "by_machine" in d:
        lines += ["**By machine:**", "", "| Machine | Rolls | Mean total | SD of total |", "|---|---|---|---|"]
        for m, md in d["by_machine"].items():
            s_ = md.get("total_summary", {})
            lines.append(f"| {m} | {md['rolls']} | {s_.get('mean', float('nan')):.2f} | {s_.get('sd', float('nan')):.2f} |")
        lines.append("")
    return lines


def write_report(path: Path, r: dict, figure_name: str | None = None) -> None:
    s = r["settings"]
    boot = r["bootstrap_95_intervals"]
    lines = [
        "# Analysis Report",
        "",
        f"Generated by `scripts/analyze.py`: alpha = {s['alpha_per_claim']} per claim (reject when p <= alpha), "
        f"seed = {s['seed']}, {s['permutations']:,} permutations, {s['bootstrap_resamples']:,} bootstrap resamples.",
        "",
        f"Counted rolls: {r['sample']['counted_rolls']}; machines: {', '.join(r['sample']['machines'])}; "
        f"analysis blocks: {r['sample']['analysis_blocks']}; gaps: {r['sample']['gaps']}.",
        "",
    ]
    lines += descriptive_lines(r["descriptives"], figure_name)
    lines += ["## Sanity check: fair-dice totals", ""]
    differs = False
    for m, c in r["sanity_check"].items():
        if c.get("tested"):
            differs |= c["differs_from_fair"]
            lines.append(f"- Machine {m}: chi-square = {c['chi_square']:.2f} (df = 10), p = {fmt_p(c['p_value'])}, "
                         f"{c['rolls']} rolls. " + ("Differs from fair dice." if c["differs_from_fair"]
                                                     else "No significant difference from fair dice.")
                         + (" Some expected counts are below 5, so treat this p-value with caution."
                            if c["small_expected_counts"] else ""))
        else:
            lines.append(f"- Machine {m}: not tested ({c['reason']}).")
    if differs:
        lines += ["", "Because totals differ from fair dice, compare repeat rates with the permutation "
                  "baseline below, not with the fair-dice rates of 5.1% and 11.3%."]

    h1 = r["h1_exact_repeats"]
    lines += [
        "", "## H1 (primary): excess exact-combination repeats", "",
        f"- Observed: {h1['observed_repeats']} repeats in {h1['valid_pairs']} pairs ({pct(h1['observed_rate'])}; "
        f"95% CI {interval_text(boot.get('exact_repeat_rate'))}).",
        f"- Permutation baseline: {pct(h1['permutation_baseline_rate'])} (fair dice: {pct(h1['fair_dice_rate'])}). "
        f"Difference: {100 * h1['rate_difference']:+.2f} percentage points.",
        f"- One-sided permutation p = {fmt_p(h1['p_value_one_sided'])}. "
        + ("**Reject the null**: exact repeats occur more often than under independence."
           if h1["significant"] else "**Fail to reject the null hypothesis.**"),
    ]
    if bonferroni_line(h1):
        lines.append(bonferroni_line(h1))

    h2 = r["h2_total_repeats"]
    lines += [
        "", "## H2 (secondary, gated): excess same-total repeats", "",
        f"- Observed: {h2['observed_repeats']} repeats in {h2['valid_pairs']} pairs ({pct(h2['observed_rate'])}; "
        f"95% CI {interval_text(boot.get('total_repeat_rate'))}).",
        f"- Permutation baseline: {pct(h2['permutation_baseline_rate'])} (fair dice: {pct(h2['fair_dice_rate'])}). "
        f"Difference: {100 * h2['rate_difference']:+.2f} percentage points.",
    ]
    if h2["formally_tested"]:
        lines.append(f"- One-sided permutation p = {fmt_p(h2['p_value_one_sided'])}. "
                     + ("**Reject the null**: same-total repeats occur more often than under independence."
                        if h2["significant"] else "**Fail to reject the null hypothesis.**"))
        if bonferroni_line(h2):
            lines.append(bonferroni_line(h2))
    else:
        lines.append("- Not formally tested because H1 was not significant (gatekeeping). Reported descriptively only.")

    h3 = r["h3_badly_timed_sevens"]["main"]
    lines += ["", "## H3 (secondary): badly timed sevens", ""]
    if h3.get("tested"):
        lines += [
            f"- Point-set rolls: {h3['point_set_sevens']} sevens in {h3['point_set_rolls']} "
            f"({pct(h3['point_set_seven_rate'])}; 95% CI {interval_text(boot.get('point_set_seven_rate'))}).",
            f"- Come-out rolls: {h3['come_out_sevens']} sevens in {h3['come_out_rolls']} "
            f"({pct(h3['come_out_seven_rate'])}; 95% CI {interval_text(boot.get('come_out_seven_rate'))}).",
            f"- Difference: {100 * h3['rate_difference']:+.2f} percentage points "
            f"(95% CI {interval_text(boot.get('seven_rate_difference'))}).",
            f"- One-sided two-proportion z = {h3['z']:.2f}, p = {fmt_p(h3['p_value_one_sided'])}."
            + (f" Fisher's exact (one-sided) p = {fmt_p(h3['fisher_exact_p_value_one_sided'])}, used for the decision "
               "because an expected cell count is below 5." if "fisher_exact_p_value_one_sided" in h3 else ""),
            "- " + ("**Reject the null**: 7s are more common on point-set rolls."
                    if h3["significant"] else "**Fail to reject the null hypothesis.**"),
        ]
        if bonferroni_line(h3):
            lines.append(bonferroni_line(h3))
        sens = r["h3_badly_timed_sevens"]["sensitivity_come_out_not_after_seven"]
        if sens.get("tested"):
            lines.append(f"- Sensitivity (come-out rolls not right after a 7): difference "
                         f"{100 * sens['rate_difference']:+.2f} points, one-sided p = {fmt_p(sens['p_value_one_sided'])}.")
    else:
        lines.append(f"- Not tested ({h3.get('reason')}).")

    ex = r["exploratory_sevens_vs_fair"]
    lines += ["", "## Exploratory: 7 rate in each phase vs. the fair rate of 1/6", "",
              "One-sided exact binomial tests, reported without a reject/fail-to-reject decision. "
              "High in the point phase only points to timing; high in both phases points to too many 7s overall.",
              "", "| Phase | Sevens | Rolls | Rate | Fair rate | One-sided p |", "|---|---|---|---|---|---|"]
    for phase, label in (("point_set", "Point set"), ("come_out", "Come-out")):
        e = ex[phase]
        if e["rolls"]:
            lines.append(f"| {label} | {e['sevens']} | {e['rolls']} | {pct(e['rate'])} | {pct(FAIR_SEVEN)} | "
                         f"{fmt_p(e['p_value_one_sided'])} |")
        else:
            lines.append(f"| {label} | 0 | 0 | n/a | {pct(FAIR_SEVEN)} | n/a |")

    if "per_machine_exploratory" in r:
        lines += ["", "## By machine (exploratory)", "",
                  "| Machine | Exact repeat rate | Total repeat rate | Point-set 7 rate | Come-out 7 rate |",
                  "|---|---|---|---|---|"]
        for m, pm in r["per_machine_exploratory"].items():
            sv = pm["sevens"]
            lines.append(f"| {m} | {pct(pm['exact_repeats']['observed_rate'])} | "
                         f"{pct(pm['total_repeats']['observed_rate'])} | "
                         f"{pct(sv.get('point_set_seven_rate'))} | {pct(sv.get('come_out_seven_rate'))} |")

    lines += ["", "## Notes", "",
              "- H1/H2 (repeats) and H3 (sevens) are separate claims, each tested at alpha = 0.05 with no correction "
              "across them (see \"Multiple comparisons\" in `docs/preregistration.md`). If both nulls are true, "
              "the chance of at least one false positive is about 9.75%. The Bonferroni lines show whether each "
              "significant result would also pass alpha = 0.025.",
              "- A non-significant result means \"fail to reject the null hypothesis,\" not that the machine is fair.",
              "- A significant result is evidence of a pattern on this machine during this session, worth replicating; "
              "it is not proof that the machine is rigged.",
              ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if math.isnan(obj) else float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the pre-registered analyses.")
    parser.add_argument("--data", type=Path, default=REPO_ROOT / "data" / "cleaned" / "analysis_data.csv")
    parser.add_argument("--report", type=Path, default=REPO_ROOT / "results" / "analysis_report.md")
    parser.add_argument("--json", type=Path, default=REPO_ROOT / "results" / "analysis_results.json")
    parser.add_argument("--figure", type=Path, default=None,
                        help="histogram path (default: totals_histogram.png next to the report)")
    parser.add_argument("--permutations", type=int, default=N_PERMUTATIONS)
    parser.add_argument("--bootstrap", type=int, default=N_BOOTSTRAP)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    if not args.data.exists():
        print(f"{args.data} not found. Run scripts/prepare_data.py first.")
        return 1
    df = core.load_cleaned(args.data)
    results = run_analysis(df, n_perm=args.permutations, n_boot=args.bootstrap, seed=args.seed)

    figure = args.figure or args.report.parent / "totals_histogram.png"
    plot_totals_histogram(df, figure)
    # Link the figure relative to the report so it displays on GitHub.
    try:
        figure_name = str(figure.resolve().relative_to(args.report.resolve().parent))
    except ValueError:
        figure_name = str(figure)
    write_report(args.report, results, figure_name)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(to_jsonable(results), indent=2))
    print(f"Wrote {args.report}, {figure}, and {args.json}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
