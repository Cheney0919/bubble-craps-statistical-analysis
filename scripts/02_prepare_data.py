#!/usr/bin/env python3
"""Create analysis-ready data and flag invalid adjacent pairs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


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
    return frame


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

