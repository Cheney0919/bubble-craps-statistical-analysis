#!/usr/bin/env python3
"""Run the preregistered Bubble Craps analyses from cleaned data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chisquare, fisher_exact, norm

RNG_SEED = 5102026
N_SHUFFLES = 10_000
FAIR_TOTAL_PROBABILITIES = np.array([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]) / 36


def count_repeats(values: np.ndarray) -> int:
    return int(np.sum(values[1:] == values[:-1]))


def permutation_test(frame: pd.DataFrame, value_column: str) -> dict[str, float | int]:
    valid = frame.loc[frame["valid_pair"]].copy()
    # Include each session's first roll for shuffling, even though it does not form an observed pair.
    usable = frame.loc[frame["verification_status"].ne("gap")]
    sessions = [
        group[value_column].to_numpy()
        for _, group in usable.groupby(["machine_id", "session_id", "analysis_block_id"], sort=False)
    ]
    observed = sum(count_repeats(values) for values in sessions)
    rng = np.random.default_rng(RNG_SEED)
    shuffled = np.empty(N_SHUFFLES, dtype=int)
    for index in range(N_SHUFFLES):
        shuffled[index] = sum(count_repeats(rng.permutation(values)) for values in sessions)
    p_upper = (1 + np.sum(shuffled >= observed)) / (N_SHUFFLES + 1)
    p_lower = (1 + np.sum(shuffled <= observed)) / (N_SHUFFLES + 1)
    return {
        "observed_repeats": observed,
        "valid_pairs": int(valid.shape[0]),
        "observed_rate": observed / int(valid.shape[0]),
        "permutation_mean": float(shuffled.mean()),
        "p_upper": float(p_upper),
        "p_lower": float(p_lower),
        "p_two_sided": float(min(1, 2 * min(p_upper, p_lower))),
    }


def h3_test(frame: pd.DataFrame) -> dict[str, float | int | str]:
    usable = frame[frame["verification_status"].ne("gap")]
    point = usable[usable["phase_before_roll"] == "point_set"]
    come = usable[usable["phase_before_roll"] == "come_out"]
    x1, n1 = int((point["total"] == 7).sum()), len(point)
    x2, n2 = int((come["total"] == 7).sum()), len(come)
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = ((x1 / n1) - (x2 / n2)) / se
    result: dict[str, float | int | str] = {
        "point_sevens": x1, "point_rolls": n1, "point_rate": x1 / n1,
        "comeout_sevens": x2, "comeout_rolls": n2, "comeout_rate": x2 / n2,
        "difference": (x1 / n1) - (x2 / n2), "z": float(z),
        "one_sided_p": float(norm.sf(z)),
    }
    table = [[x1, n1 - x1], [x2, n2 - x2]]
    if min(value for row in table for value in row) < 5:
        odds_ratio, p_value = fisher_exact(table, alternative="greater")
        result["fisher_one_sided_p"] = float(p_value)
    return result


def fairness_checks(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    result = {}
    for machine, group in frame.loc[frame["verification_status"].ne("gap")].groupby("machine_id"):
        observed = group["total"].value_counts().reindex(range(2, 13), fill_value=0).to_numpy()
        statistic, p_value = chisquare(observed, f_exp=len(group) * FAIR_TOTAL_PROBABILITIES)
        result[str(machine)] = {"chi_square": float(statistic), "p_value": float(p_value)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()
    frame = pd.read_csv(args.input_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "h1_exact_combination": permutation_test(frame, "combination"),
        "h2_same_total": permutation_test(frame, "total"),
        "h3_badly_timed_sevens": h3_test(frame),
        "fairness_checks_by_machine": fairness_checks(frame),
        "notes": [
            "H2 is formally interpreted only if H1 is significant.",
            "H3 is a directional secondary analysis and should not be combined with H1/H2 into one global fairness claim.",
        ],
    }
    path = output_dir / "analysis_summary.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

