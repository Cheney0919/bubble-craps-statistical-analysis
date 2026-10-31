"""Validation rules from docs/preprocessing_plan.md."""

import pytest
from conftest import MINIMAL, write_log

import craps_core as core


def issues_for(raw_dir, rows, machine="A"):
    write_log(raw_dir, machine, rows)
    return [str(i) for i in core.prepare(raw_dir).issues]


def test_minimal_log_is_valid(raw_dir):
    assert issues_for(raw_dir, MINIMAL) == []


def test_case_and_spaces_are_normalized(raw_dir):
    rows = [(" 25 ", "r", "", "2:00 PM"), ("34", "", "co"), ("", " gap ", "", "2:05 PM"),
            ("15", "R"), ("44", "", "p8", "2:06 PM")]
    assert issues_for(raw_dir, rows) == []


def test_blank_rows_are_dropped(raw_dir):
    rows = MINIMAL[:3] + [("", "", "", "", "")] + MINIMAL[3:]
    write_log(raw_dir, "A", rows)
    prepared = core.prepare(raw_dir)
    assert prepared.issues == []
    assert prepared.blank_rows_dropped["A"] == 1
    assert len(prepared.cleaned) == len(MINIMAL)


@pytest.mark.parametrize("dice", ["37", "3", "345", "3-4", "07", "ab"])
def test_bad_dice_rejected(raw_dir, dice):
    rows = MINIMAL[:2] + [(dice,)] + MINIMAL[3:]
    assert any("dice" in i for i in issues_for(raw_dir, rows))


def test_bad_flag_rejected(raw_dir):
    rows = MINIMAL[:2] + [("51", "X")] + MINIMAL[3:]
    assert any("flag 'X'" in i for i in issues_for(raw_dir, rows))


def test_bad_phase_rejected(raw_dir):
    rows = MINIMAL[:2] + [("51", "", "P7")] + MINIMAL[3:]
    assert any("phase 'P7'" in i for i in issues_for(raw_dir, rows))


def test_row_0_must_be_recovered_with_time(raw_dir):
    rows = [("25", "", "", "")] + MINIMAL[1:]
    found = issues_for(raw_dir, rows)
    assert any("must be flagged R" in i for i in found)
    assert any("row 0 (the first row) must have a time" in i for i in found)


def test_final_row_needs_time(raw_dir):
    rows = MINIMAL[:-1] + [("23",)]
    assert any("final row must have a time" in i for i in issues_for(raw_dir, rows))


def test_gap_rules(raw_dir):
    rows = MINIMAL[:3] + [("44", "GAP", "", "")] + [("15", "", "CO")] + MINIMAL[4:]
    found = issues_for(raw_dir, rows)
    assert any("GAP row must have no dice" in i for i in found)
    assert any("GAP row must have a time" in i for i in found)


def test_phase_not_allowed_on_recovered_or_gap(raw_dir):
    rows = MINIMAL[:2] + [("51", "R", "P6")] + MINIMAL[3:]
    assert any("must not be entered on an R or GAP row" in i for i in issues_for(raw_dir, rows))


def test_roll_1_needs_come_out(raw_dir):
    rows = [MINIMAL[0], ("34",)] + MINIMAL[2:]
    assert any("first live roll in the file needs a phase" in i for i in issues_for(raw_dir, rows))
    rows = [MINIMAL[0], ("34", "", "P6")] + MINIMAL[2:]
    assert any("roll 1 on machine A must have phase CO" in i for i in issues_for(raw_dir, rows))


def test_phase_needed_after_gap(raw_dir):
    rows = MINIMAL[:3] + [("", "GAP", "", "2:10 PM"), ("15", "R"), ("44",)] + MINIMAL[4:]
    assert any("first live roll after a GAP needs a phase" in i for i in issues_for(raw_dir, rows))


def test_recovered_rows_after_gap_do_not_need_phase(raw_dir):
    rows = MINIMAL[:3] + [("", "GAP", "", "2:10 PM"), ("15", "R"), ("44", "", "P6")] + MINIMAL[4:]
    assert issues_for(raw_dir, rows) == []


def test_machine_b_needs_switch_note_on_a(raw_dir):
    write_log(raw_dir, "A", MINIMAL[:-1] + [("23", "", "", "2:01 PM", "")])
    write_log(raw_dir, "B", [("11", "R", "", "2:05 PM"), ("34", "", "P5"), ("44", "", "", "2:06 PM")])
    assert any("A's final row has no note" in str(i) for i in core.prepare(raw_dir).issues)

    write_log(raw_dir, "A", MINIMAL[:-1] + [("23", "", "", "2:01 PM", "machine serviced")])
    assert core.prepare(raw_dir).issues == []


def test_machine_b_first_roll_need_not_be_come_out(raw_dir):
    write_log(raw_dir, "A", MINIMAL[:-1] + [("23", "", "", "2:01 PM", "display broke")])
    write_log(raw_dir, "B", [("11", "R", "", "2:05 PM"), ("34", "", "P5"), ("44", "", "", "2:06 PM")])
    assert core.prepare(raw_dir).issues == []


def test_missing_machine_a_file(raw_dir):
    assert any("not found" in str(i) for i in core.prepare(raw_dir).issues)


def test_wrong_headers(raw_dir):
    (raw_dir / "roll_log_A.csv").write_text("die,flag,phase,time,notes\n25,R,,2:00 PM,\n")
    assert any("columns must be exactly" in str(i) for i in core.prepare(raw_dir).issues)
