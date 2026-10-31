"""Shared test helpers. Makes the modules in scripts/ importable."""

import csv
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import craps_core as core  # noqa: E402


def write_log(directory: Path, machine: str, rows: list[tuple]) -> Path:
    """Write a raw log. Each row is (dice, flag, phase, time, notes); short tuples are padded."""
    path = core.raw_log_path(directory, machine)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(core.RAW_COLUMNS)
        for row in rows:
            writer.writerow(list(row) + [""] * (5 - len(row)))
    return path


@pytest.fixture
def raw_dir(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    return d


# A minimal valid log: row 0, roll 1 (come-out), a few rolls, final time.
MINIMAL = [
    ("25", "R", "", "2:00 PM", "row 0"),
    ("34", "", "CO"),
    ("51",),
    ("66",),
    ("23", "", "", "2:01 PM", "session end"),
]
