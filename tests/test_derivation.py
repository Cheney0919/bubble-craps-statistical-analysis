"""Phase reconstruction, analysis blocks, pairs, and sample counting."""

import pytest
from conftest import MINIMAL, write_log

import craps_core as core
import simulate_log as sim


def cleaned_for(raw_dir, rows, machine="A"):
    write_log(raw_dir, machine, rows)
    prepared = core.prepare(raw_dir)
    assert prepared.issues == []
    return prepared.cleaned


@pytest.mark.parametrize(
    "state, total, expected",
    [
        ("CO", 7, "CO"), ("CO", 11, "CO"), ("CO", 2, "CO"), ("CO", 12, "CO"),
        ("CO", 6, 6), ("CO", 10, 10),
        (6, 6, "CO"), (6, 7, "CO"), (6, 8, 6), (6, 11, 6),
        (None, 7, "CO"), (None, 6, None),
    ],
)
def test_next_state(state, total, expected):
    assert core.next_state(state, total) == expected


def test_phase_sequence(raw_dir):
    # row 0 = 9 (phase unknown); roll 1 CO rolls 6 -> point 6; 8 keeps point;
    # 6 makes the point -> come-out; 7 on come-out -> come-out.
    rows = [("45", "R", "", "2:00 PM"), ("15", "", "CO"), ("44",), ("33",), ("34", "", "", "2:01 PM")]
    df = cleaned_for(raw_dir, rows)
    assert df["phase_before_roll"].tolist() == ["", "come_out", "point_set", "point_set", "come_out"]
    assert df["point_value_before_roll"].tolist()[2:4] == [6, 6]
    assert df["h3_eligible"].tolist() == [False, True, True, True, True]


def test_phase_known_after_seven_following_gap(raw_dir):
    # After a GAP, recovered rows start with an unknown phase until a 7 appears.
    rows = MINIMAL[:3] + [("", "GAP", "", "2:10 PM"), ("15", "R"), ("34", "R"), ("22", "R"),
                          ("44", "", "P4"), ("16", "", "", "2:11 PM")]
    df = cleaned_for(raw_dir, rows)
    after_gap = df.iloc[4:]
    # 15 (unknown), 34 = 7 (unknown before it), 22 rolls a 4 on come-out (known), recorded P4 agrees.
    assert after_gap["phase_before_roll"].tolist() == ["", "", "come_out", "point_set", "point_set"]
    assert not df["phase_mismatch"].any()


def test_phase_mismatch_detected(raw_dir):
    # Roll 1 CO rolls a 6 (point 6), then a GAP-free row records P8: mismatch.
    rows = [("45", "R", "", "2:00 PM"), ("15", "", "CO"), ("44", "", "P8"), ("23", "", "", "2:01 PM")]
    write_log(raw_dir, "A", rows)
    prepared = core.prepare(raw_dir)
    assert prepared.cleaned["phase_mismatch"].tolist() == [False, False, True, False]
    assert core.summarize(prepared)["phase_mismatch_rows"][0]["roll_number"] == 2


def test_dice_sorted_and_combined(raw_dir):
    df = cleaned_for(raw_dir, [("52", "R", "", "2:00 PM"), ("43", "", "CO"), ("34", "", "", "2:01 PM")])
    assert df["combination"].tolist() == ["2-5", "3-4", "3-4"]
    assert df["total"].tolist() == [7, 7, 7]
    assert df["exact_repeat"].tolist()[1:] == [False, True]
    assert df["total_repeat"].tolist()[1:] == [True, True]


def test_gap_splits_blocks_and_pairs(raw_dir):
    rows = MINIMAL[:3] + [("", "GAP", "", "2:10 PM"), ("51", "R"), ("51", "", "CO"), ("23", "", "", "2:11 PM")]
    df = cleaned_for(raw_dir, rows)
    assert df["analysis_block_id"].tolist() == ["A-1", "A-1", "A-1", "", "A-2", "A-2", "A-2"]
    # Row 0 pairs with roll 1; the first roll after the gap has no pair.
    assert df["valid_pair"].tolist() == [False, True, True, False, False, True, True]
    # 51 then 51 across the gap is never a repeat; 51 -> 51 after the gap is.
    assert df.loc[5, "exact_repeat"]
    assert int(df["valid_pair"].sum()) == 4


def test_counts_exclude_row_0_and_gaps(raw_dir):
    rows = MINIMAL[:3] + [("", "GAP", "", "2:10 PM"), ("51", "R"), ("51", "", "CO"), ("23", "", "", "2:11 PM")]
    df = cleaned_for(raw_dir, rows)
    assert df["counts_toward_sample"].tolist() == [False, True, True, False, True, True, True]


def test_machines_never_pair(raw_dir):
    write_log(raw_dir, "A", MINIMAL[:-1] + [("23", "", "", "2:01 PM", "serviced")])
    write_log(raw_dir, "B", [("23", "R", "", "2:05 PM"), ("23", "", "P5"), ("44", "", "", "2:06 PM")])
    df = core.prepare(raw_dir).cleaned
    b = df.loc[df["machine_id"] == "B"]
    assert b["roll_number"].tolist() == [0, 1, 2]
    assert b["session_id"].iloc[0] == "B_01"
    assert not b["valid_pair"].iloc[0]       # B's row 0 doesn't pair with A's last roll
    assert b["exact_repeat"].iloc[1]         # B roll 1 pairs with B row 0
    assert b["phase_before_roll"].iloc[1] == "point_set"


def test_trim_to_target(raw_dir):
    write_log(raw_dir, "A", MINIMAL)
    prepared = core.prepare(raw_dir, target=2)
    assert prepared.cleaned["counts_toward_sample"].sum() == 2
    assert len(prepared.cleaned) == 3
    assert prepared.rows_beyond_target == 2


@pytest.mark.parametrize("kwargs", [{}, {"switch_after": 400}, {"stuck_prob": 0.05}, {"long_break_rolls": 19}])
def test_reconstruction_matches_simulated_truth(tmp_path, kwargs):
    rows, truth = sim.simulate_session(seed=7, **kwargs)
    sim.write_logs(rows, tmp_path)
    prepared = core.prepare(tmp_path)
    assert prepared.issues == []
    df = prepared.cleaned
    assert df["counts_toward_sample"].sum() == core.TARGET_ROLLS
    for machine, machine_truth in truth.items():
        g = df.loc[df["machine_id"] == machine]
        assert len(g) == len(machine_truth)
        for (_, row), t in zip(g.iterrows(), machine_truth):
            if row["verification_status"] == "gap" or row["phase_before_roll"] == "":
                continue
            true_phase = t[1]
            expected = "come_out" if true_phase == "CO" else "point_set"
            assert row["phase_before_roll"] == expected
            if expected == "point_set":
                assert row["point_value_before_roll"] == true_phase
    # Every live roll's phase is known; unknowns are only row 0 or rows recovered after a gap.
    live = df["verification_status"].isin(["verified", "corrected_from_history"])
    assert (df.loc[live, "phase_before_roll"] != "").all()


def test_long_break_logs_no_duplicates(tmp_path):
    # A break of 19 rolls with a 20-roll history leaves 1 logged roll visible:
    # skipping the 3 oldest after the GAP must avoid re-logging it.
    for length in (17, 18, 19, 20, 35):
        rows, truth = sim.simulate_session(seed=11, long_break_rolls=length)
        serials = [t[0] for t in truth["A"] if t is not None]
        # Strictly increasing machine-roll serials: in order, nothing logged twice.
        assert all(a < b for a, b in zip(serials, serials[1:])), length
        sim.write_logs(rows, tmp_path)
        df = core.prepare(tmp_path).cleaned
        assert df["counts_toward_sample"].sum() == core.TARGET_ROLLS
        assert (df["verification_status"] == "gap").sum() == (0 if length <= 17 else 1)
