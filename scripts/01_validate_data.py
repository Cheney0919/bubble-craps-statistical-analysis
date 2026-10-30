#!/usr/bin/env python3
"""Validate the raw Bubble Craps roll log without changing it."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REQUIRED = {
    "machine_id", "session_id", "roll_number", "timestamp", "die_low", "die_high",
    "total", "phase_before_roll", "point_value_before_roll",
    "other_players_betting", "verification_status",
}
ALWAYS_REQUIRED = {"machine_id", "session_id", "roll_number", "timestamp", "phase_before_roll", "other_players_betting", "verification_status"}
POINTS = {4, 5, 6, 8, 9, 10}


def validate(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED - set(frame.columns)
    if missing:
        return [f"Missing required columns: {', '.join(sorted(missing))}"]

    for column in ALWAYS_REQUIRED:
        if frame[column].isna().any():
            errors.append(f"Missing values in required column: {column}")

    non_gap = frame["verification_status"].ne("gap")
    for column in ("die_low", "die_high", "total"):
        if frame.loc[non_gap, column].isna().any():
            errors.append(f"Missing values in non-gap row: {column}")

    for column in ("die_low", "die_high"):
        values = pd.to_numeric(frame.loc[non_gap, column], errors="coerce")
        if (~values.isin(range(1, 7))).any():
            errors.append(f"{column} must contain integers from 1 through 6")

    low = pd.to_numeric(frame["die_low"], errors="coerce")
    high = pd.to_numeric(frame["die_high"], errors="coerce")
    total = pd.to_numeric(frame["total"], errors="coerce")
    if (low[non_gap] > high[non_gap]).any():
        errors.append("die_low must be less than or equal to die_high")
    if (total[non_gap] != low[non_gap] + high[non_gap]).any():
        errors.append("total must equal die_low + die_high")

    if not frame["phase_before_roll"].isin(["come_out", "point_set"]).all():
        errors.append("phase_before_roll must be come_out or point_set")
    if not frame["other_players_betting"].isin(["yes", "no", "unknown"]).all():
        errors.append("other_players_betting must be yes, no, or unknown")
    if not frame["verification_status"].isin(["verified", "corrected_from_history", "gap"]).all():
        errors.append("verification_status has an invalid value")

    for (_, session), group in frame.groupby(["machine_id", "session_id"], sort=False):
        rolls = pd.to_numeric(group["roll_number"], errors="coerce")
        expected = list(range(1, len(group) + 1))
        if rolls.tolist() != expected:
            errors.append(f"Roll numbers must be 1..n within session {session}")

    point_rows = (frame["phase_before_roll"] == "point_set") & non_gap
    point_values = pd.to_numeric(frame.loc[point_rows, "point_value_before_roll"], errors="coerce")
    if not point_values.isin(POINTS).all():
        errors.append("point_set rows need a valid point_value_before_roll")
    come_out_values = frame.loc[(frame["phase_before_roll"] == "come_out") & non_gap, "point_value_before_roll"].fillna("").astype(str).str.strip()
    if (come_out_values != "").any():
        errors.append("come_out rows must have a blank point_value_before_roll")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/01_validate_data.py data/raw/roll_log.csv")
        return 2
    path = Path(sys.argv[1])
    frame = pd.read_csv(path)
    errors = validate(frame)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation passed: {len(frame)} rows in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

