#!/usr/bin/env python3
"""Create analysis-ready data and flag invalid adjacent pairs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


def add_phase_check(frame: pd.DataFrame) -> pd.DataFrame:
    """Add an auditable rules-based phase reconstruction without altering logs."""
    frame = frame.copy()
    frame["expected_phase_before_roll"] = pd.NA
    frame["phase_match"] = pd.NA
    for _, group in frame.groupby(["machine_id", "session_id"], sort=False):
        phase, point, known = "come_out", None, True
        for index in group.index:
            row = frame.loc[index]
            if row["verification_status"] == "gap":
                known = False
                continue
            logged_phase = row["phase_before_roll"]
            if not known:
                # A logged come-out roll provides a defensible reset after an unknown gap.
                if logged_phase != "come_out":
                    continue
                phase, point, known = "come_out", None, True
            frame.loc[index, "expected_phase_before_roll"] = phase
            frame.loc[index, "phase_match"] = logged_phase == phase
            total = int(row["total"])
            if phase == "come_out":
                if total in {4, 5, 6, 8, 9, 10}:
                    phase, point = "point_set", total
            elif total == 7 or total == point:
                phase, point = "come_out", None
    return frame


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy().sort_values(["machine_id", "session_id", "roll_number"])
    group_cols = ["machine_id", "session_id"]
    is_gap = frame["verification_status"].eq("gap")
    frame["analysis_block_id"] = frame.groupby(group_cols)["verification_status"].transform(lambda column: column.eq("gap").cumsum())
    frame["combination"] = pd.NA
    valid = ~is_gap
    frame.loc[valid, "combination"] = (
        frame.loc[valid, "die_low"].astype(int).astype(str)
        + "-"
        + frame.loc[valid, "die_high"].astype(int).astype(str)
    )
    frame["previous_combination"] = frame.groupby(group_cols)["combination"].shift()
    frame["previous_total"] = frame.groupby(group_cols)["total"].shift()
    frame["previous_status"] = frame.groupby(group_cols)["verification_status"].shift()
    frame["exact_repeat"] = (
        frame["combination"].notna()
        & frame["previous_combination"].notna()
        & frame["combination"].astype("string").eq(frame["previous_combination"].astype("string")).fillna(False)
    )
    frame["total_repeat"] = (
        frame["total"].notna()
        & frame["previous_total"].notna()
        & frame["total"].eq(frame["previous_total"]).fillna(False)
    )
    frame["valid_pair"] = (
        frame["previous_combination"].notna()
        & frame["verification_status"].ne("gap")
        & frame["previous_status"].ne("gap")
    )
    return add_phase_check(frame)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/02_prepare_data.py INPUT.csv OUTPUT.csv")
        return 2
    input_path, output_path = map(Path, sys.argv[1:])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = prepare(pd.read_csv(input_path))
    frame.to_csv(output_path, index=False)
    print(f"Created {output_path} with {int(frame['valid_pair'].sum())} valid adjacent pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

