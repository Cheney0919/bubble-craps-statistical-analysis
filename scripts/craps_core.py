"""Shared logic for the bubble craps study.

Reads the raw roll logs typed at the casino, validates them against the rules
in docs/preprocessing_plan.md, reconstructs the game phase, and derives the
cleaned analysis dataset described in docs/data_dictionary.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RAW_COLUMNS = ["dice", "flag", "phase", "time", "notes"]
POINTS = (4, 5, 6, 8, 9, 10)
VALID_FLAGS = {"", "R", "C", "GAP"}
VALID_PHASES = {"", "CO"} | {f"P{p}" for p in POINTS}
LIVE_FLAGS = {"", "C"}
STATUS = {
    "": "verified",
    "C": "corrected_from_history",
    "R": "recovered_from_history",
    "GAP": "gap",
}
MACHINES = ("A", "B")
TARGET_ROLLS = 1000
DICE_PATTERN = re.compile(r"^[1-6]{2}$")
# The header is spreadsheet row 1, so the first data row (row 0) is row 2.
FIRST_SHEET_ROW = 2

CLEANED_COLUMNS = [
    "machine_id",
    "session_id",
    "roll_number",
    "sheet_row",
    "die_low",
    "die_high",
    "total",
    "combination",
    "verification_status",
    "phase_recorded",
    "phase_before_roll",
    "point_value_before_roll",
    "phase_mismatch",
    "analysis_block_id",
    "previous_combination",
    "previous_total",
    "valid_pair",
    "exact_repeat",
    "total_repeat",
    "counts_toward_sample",
    "h3_eligible",
    "time",
    "notes",
]


@dataclass(frozen=True)
class Issue:
    """A validation problem, located by machine and spreadsheet row."""

    machine: str
    sheet_row: int | None
    message: str

    def __str__(self) -> str:
        where = f"machine {self.machine}"
        if self.sheet_row is not None:
            where += f", sheet row {self.sheet_row}"
        return f"[{where}] {self.message}"


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def raw_log_path(raw_dir: Path, machine: str) -> Path:
    return Path(raw_dir) / f"roll_log_{machine}.csv"


def read_raw_log(path: Path) -> pd.DataFrame:
    """Read one exported Google Sheet tab.

    Surrounding spaces are ignored and `flag`/`phase` are upper-cased, so a
    phone keyboard's `r` or `gap ` is read as `R` or `GAP`. Fully blank rows
    carry no information and are dropped; their count is kept in
    `df.attrs["blank_rows_dropped"]`. `sheet_row` keeps the original
    spreadsheet row number for error messages.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    headers = [str(c).strip().lower() for c in df.columns]
    if headers != RAW_COLUMNS:
        raise ValueError(
            f"{path.name}: columns must be exactly {RAW_COLUMNS}, found {headers}"
        )
    df.columns = RAW_COLUMNS
    for col in RAW_COLUMNS:
        df[col] = df[col].astype(str).str.strip()
    df["flag"] = df["flag"].str.upper()
    df["phase"] = df["phase"].str.upper()
    df["sheet_row"] = range(FIRST_SHEET_ROW, FIRST_SHEET_ROW + len(df))

    blank = (df[RAW_COLUMNS] == "").all(axis=1)
    df = df.loc[~blank].reset_index(drop=True)
    df.attrs["blank_rows_dropped"] = int(blank.sum())
    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_raw_log(df: pd.DataFrame, machine: str) -> list[Issue]:
    """Apply the per-file validation rules from docs/preprocessing_plan.md."""
    issues: list[Issue] = []

    def add(row, message):
        issues.append(Issue(machine, None if row is None else int(row.sheet_row), message))

    if df.empty:
        add(None, "file has no rows")
        return issues

    for row in df.itertuples(index=False):
        if row.flag not in VALID_FLAGS:
            add(row, f"flag '{row.flag}' must be blank, R, C, or GAP")
        if row.flag == "GAP":
            if row.dice:
                add(row, "a GAP row must have no dice")
            if not row.time:
                add(row, "a GAP row must have a time")
        elif not DICE_PATTERN.match(row.dice):
            add(row, f"dice '{row.dice}' must be exactly two digits from 1 to 6")
        if row.phase not in VALID_PHASES:
            add(row, f"phase '{row.phase}' must be blank, CO, P4, P5, P6, P8, P9, or P10")
        if row.phase and row.flag in {"R", "GAP"}:
            add(row, "phase must not be entered on an R or GAP row")

    first = df.iloc[0]
    if first.flag != "R":
        add(first, "row 0 (the first row) must be flagged R")
    if not first.time:
        add(first, "row 0 (the first row) must have a time")
    last = df.iloc[-1]
    if not last.time:
        add(last, "the final row must have a time")

    # A phase is required on the first live roll of the file and on the first
    # live roll after each GAP. On machine A, the first live roll is roll 1 and
    # must be a come-out.
    needs_phase = True
    seen_live = False
    for row in df.itertuples(index=False):
        if row.flag == "GAP":
            needs_phase = True
            continue
        if row.flag not in LIVE_FLAGS:
            continue
        if needs_phase:
            if not row.phase:
                if seen_live:
                    add(row, "the first live roll after a GAP needs a phase")
                else:
                    add(row, "the first live roll in the file needs a phase")
            elif machine == "A" and not seen_live and row.phase != "CO":
                add(row, "roll 1 on machine A must have phase CO")
            needs_phase = False
        seen_live = True
    return issues


def validate_switch(raw_logs: dict[str, pd.DataFrame]) -> list[Issue]:
    """Machine B is only allowed with a documented reason on A's final row."""
    issues: list[Issue] = []
    if "B" in raw_logs:
        if "A" not in raw_logs:
            issues.append(Issue("B", None, "roll_log_B.csv exists without roll_log_A.csv"))
        elif raw_logs["A"].empty or not raw_logs["A"].iloc[-1].notes:
            last = None if raw_logs["A"].empty else int(raw_logs["A"].iloc[-1].sheet_row)
            issues.append(
                Issue("A", last, "machine B was used, but A's final row has no note giving the reason")
            )
    return issues


# ---------------------------------------------------------------------------
# Phase rules
# ---------------------------------------------------------------------------


def parse_phase(code: str):
    """'CO' -> 'CO', 'P6' -> 6, '' -> None."""
    if not code:
        return None
    if code == "CO":
        return "CO"
    return int(code[1:])


def next_state(state, total: int):
    """Pass-line phase before the next roll, given this roll's phase and total.

    `state` is None (unknown), 'CO' (come-out), or the point number.
    Any 7 ends the game, so an unknown state becomes known after a 7.
    """
    if state is None:
        return "CO" if total == 7 else None
    if state == "CO":
        return total if total in POINTS else "CO"
    return "CO" if total in (7, state) else state


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------


def derive_machine(df: pd.DataFrame, machine: str) -> pd.DataFrame:
    """Build cleaned rows for one machine from a validated raw log."""
    records = []
    block = 0
    start_new_block = True
    state = None
    prev = None  # (combination, total) of the previous roll in this block

    for roll_number, row in enumerate(df.itertuples(index=False)):
        rec = {
            "machine_id": machine,
            "session_id": f"{machine}_01",
            "roll_number": roll_number,
            "sheet_row": int(row.sheet_row),
            "verification_status": STATUS[row.flag],
            "phase_recorded": {"": "", "CO": "come_out"}.get(row.phase, "point_set"),
            "time": row.time,
            "notes": row.notes,
        }

        if row.flag == "GAP":
            rec.update(
                die_low=pd.NA, die_high=pd.NA, total=pd.NA, combination="",
                phase_before_roll="", point_value_before_roll=pd.NA,
                phase_mismatch=False, analysis_block_id="",
                previous_combination="", previous_total=pd.NA,
                valid_pair=False, exact_repeat=pd.NA, total_repeat=pd.NA,
                counts_toward_sample=False, h3_eligible=False,
            )
            records.append(rec)
            state = None
            prev = None
            start_new_block = True
            continue

        if start_new_block:
            block += 1
            start_new_block = False

        low, high = sorted((int(row.dice[0]), int(row.dice[1])))
        total = low + high
        combination = f"{low}-{high}"

        recorded = parse_phase(row.phase)
        mismatch = False
        if recorded is not None:
            if state is not None and state != recorded:
                mismatch = True
            # The phase shown on the machine is taken as the starting point.
            state = recorded

        counts = roll_number != 0
        rec.update(
            die_low=low,
            die_high=high,
            total=total,
            combination=combination,
            phase_before_roll="" if state is None else ("come_out" if state == "CO" else "point_set"),
            point_value_before_roll=state if isinstance(state, int) else pd.NA,
            phase_mismatch=mismatch,
            analysis_block_id=f"{machine}-{block}",
            previous_combination="" if prev is None else prev[0],
            previous_total=pd.NA if prev is None else prev[1],
            valid_pair=prev is not None,
            exact_repeat=pd.NA if prev is None else combination == prev[0],
            total_repeat=pd.NA if prev is None else total == prev[1],
            counts_toward_sample=counts,
            h3_eligible=counts and state is not None,
        )
        records.append(rec)
        state = next_state(state, total)
        prev = (combination, total)

    out = pd.DataFrame.from_records(records, columns=CLEANED_COLUMNS)
    return enforce_dtypes(out)


def trim_to_target(cleaned: pd.DataFrame, target: int = TARGET_ROLLS) -> tuple[pd.DataFrame, int]:
    """Drop rows logged after the target-th counted roll (A first, then B).

    Returns the trimmed data and the number of rows removed.
    """
    counted = cleaned["counts_toward_sample"].cumsum()
    if counted.empty or counted.iloc[-1] <= target:
        return cleaned, 0
    # Keep everything up to and including the target-th counted roll.
    cut = int(counted.ge(target).idxmax())
    removed = len(cleaned) - (cut + 1)
    return cleaned.iloc[: cut + 1].reset_index(drop=True), removed


def enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["die_low", "die_high", "total", "point_value_before_roll", "previous_total"]:
        df[col] = df[col].astype("Int64")
    for col in ["roll_number", "sheet_row"]:
        df[col] = df[col].astype(int)
    for col in ["exact_repeat", "total_repeat"]:
        df[col] = df[col].astype("boolean")
    for col in ["valid_pair", "counts_toward_sample", "h3_eligible", "phase_mismatch"]:
        df[col] = df[col].astype(bool)
    for col in [
        "machine_id", "session_id", "combination", "verification_status",
        "phase_recorded", "phase_before_roll", "analysis_block_id",
        "previous_combination", "time", "notes",
    ]:
        df[col] = df[col].fillna("").astype(str)
    return df


def load_cleaned(path: Path) -> pd.DataFrame:
    """Read data/cleaned/analysis_data.csv back with the right types."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = set(CLEANED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    def to_int(s):
        return pd.to_numeric(s.replace("", pd.NA)).astype("Int64")

    def to_bool(s):
        return s.map({"True": True, "False": False, "": pd.NA}).astype("boolean")

    for col in ["die_low", "die_high", "total", "point_value_before_roll", "previous_total"]:
        df[col] = to_int(df[col])
    for col in ["exact_repeat", "total_repeat", "valid_pair", "counts_toward_sample",
                "h3_eligible", "phase_mismatch"]:
        df[col] = to_bool(df[col])
    return enforce_dtypes(df[CLEANED_COLUMNS])


# ---------------------------------------------------------------------------
# Whole pipeline
# ---------------------------------------------------------------------------


@dataclass
class PreparedData:
    cleaned: pd.DataFrame
    issues: list[Issue]
    blank_rows_dropped: dict[str, int]
    rows_beyond_target: int


def prepare(raw_dir: Path, target: int = TARGET_ROLLS) -> PreparedData:
    """Validate every raw log in `raw_dir` and, if valid, derive cleaned data."""
    raw_dir = Path(raw_dir)
    raw_logs: dict[str, pd.DataFrame] = {}
    issues: list[Issue] = []

    for machine in MACHINES:
        path = raw_log_path(raw_dir, machine)
        if not path.exists():
            continue
        try:
            raw_logs[machine] = read_raw_log(path)
        except ValueError as exc:
            issues.append(Issue(machine, None, str(exc)))

    if "A" not in raw_logs and not any(i.machine == "A" for i in issues):
        issues.append(Issue("A", None, f"{raw_log_path(raw_dir, 'A')} not found"))

    for machine, df in raw_logs.items():
        issues.extend(validate_raw_log(df, machine))
    issues.extend(validate_switch(raw_logs))

    blank = {m: df.attrs.get("blank_rows_dropped", 0) for m, df in raw_logs.items()}
    if issues:
        return PreparedData(pd.DataFrame(columns=CLEANED_COLUMNS), issues, blank, 0)

    parts = [derive_machine(raw_logs[m], m) for m in MACHINES if m in raw_logs]
    cleaned = pd.concat(parts, ignore_index=True)
    cleaned, removed = trim_to_target(cleaned, target)
    return PreparedData(cleaned, issues, blank, removed)


def summarize(prepared: PreparedData, target: int = TARGET_ROLLS) -> dict:
    """Counts reported in the validation summary."""
    df = prepared.cleaned
    per_machine = {}
    for machine, g in df.groupby("machine_id", sort=True):
        notes = g["notes"].str.lower()
        per_machine[machine] = {
            "rows": int(len(g)),
            "counted_rolls": int(g["counts_toward_sample"].sum()),
            "gaps": int((g["verification_status"] == "gap").sum()),
            "recovered_rolls_excluding_row_0": int(
                ((g["verification_status"] == "recovered_from_history") & (g["roll_number"] != 0)).sum()
            ),
            "corrected_rolls": int((g["verification_status"] == "corrected_from_history").sum()),
            "rows_noting_a_break": int(notes.str.contains("break").sum()),
            "analysis_blocks": int(g.loc[g["analysis_block_id"] != "", "analysis_block_id"].nunique()),
            "valid_pairs": int(g["valid_pair"].sum()),
            "h3_eligible_rolls": int(g["h3_eligible"].sum()),
            "counted_rolls_with_unknown_phase": int(
                (g["counts_toward_sample"] & (g["phase_before_roll"] == "")).sum()
            ),
            "phase_mismatches": int(g["phase_mismatch"].sum()),
            "blank_rows_dropped": int(prepared.blank_rows_dropped.get(machine, 0)),
        }
    total = int(df["counts_toward_sample"].sum())
    return {
        "target_rolls": target,
        "counted_rolls": total,
        "ended_early": total < target,
        "shortfall": max(0, target - total),
        "rows_beyond_target_removed": prepared.rows_beyond_target,
        "machine_switch": "B" in per_machine,
        "machines": per_machine,
        "phase_mismatch_rows": df.loc[
            df["phase_mismatch"], ["machine_id", "roll_number", "sheet_row"]
        ].to_dict("records"),
    }
