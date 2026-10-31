"""Pre-registered tests: permutation, gatekeeping, H3, bootstrap, and the CLI."""

import json
import math

import numpy as np
import pandas as pd
import pytest
from conftest import write_log

import analyze as an
import craps_core as core
import prepare_data
import simulate_log as sim


def prepared_sim(tmp_path, **kwargs):
    rows, _ = sim.simulate_session(**kwargs)
    sim.write_logs(rows, tmp_path)
    prepared = core.prepare(tmp_path)
    assert prepared.issues == []
    return prepared.cleaned


def test_fair_repeat_constants():
    combos = {}
    for a in range(1, 7):
        for b in range(1, 7):
            key = tuple(sorted((a, b)))
            combos[key] = combos.get(key, 0) + 1 / 36
    assert math.isclose(sum(p * p for p in combos.values()), an.FAIR_EXACT_REPEAT)
    assert math.isclose(sum(p * p for p in an.FAIR_TOTAL_PROBS.values()), an.FAIR_TOTAL_REPEAT)


def test_permutation_keeps_each_block_mix(tmp_path):
    df = prepared_sim(tmp_path, seed=2)
    blocks = an.blocks(df)
    counts = an.permutation_repeat_counts(blocks, 200, np.random.default_rng(0))
    for b in blocks:
        c = counts[b["analysis_block_id"].iloc[0]]
        assert len(c["exact"]) == 200
        # A shuffle can never create more pairs than the block has.
        assert c["exact"].max() <= len(b) - 1
        # Same permutations for both: a total repeat always includes every exact repeat.
        assert (c["total"] >= c["exact"]).all()


def test_p_value_uses_plus_one_upper_tail():
    block = pd.DataFrame({"analysis_block_id": ["A-1"] * 4, "combination": ["1-1"] * 4, "total": [2] * 4})
    perm = {"A-1": {"exact": np.array([0, 3, 3, 1]), "total": np.array([0, 3, 3, 1])}}
    r = an.repeat_test([block], perm, "exact", 4)
    assert r["observed_repeats"] == 3
    assert r["p_value_one_sided"] == pytest.approx((1 + 2) / (4 + 1))


def test_detects_stuck_dice(tmp_path):
    df = prepared_sim(tmp_path, seed=4, stuck_prob=0.05)
    r = an.run_analysis(df, n_perm=2000, n_boot=200)
    assert r["h1_exact_repeats"]["significant"]
    assert r["h2_total_repeats"]["formally_tested"]


def test_gatekeeping_hides_h2_p_value(tmp_path):
    df = prepared_sim(tmp_path, seed=1)
    r = an.run_analysis(df, n_perm=2000, n_boot=200)
    assert not r["h1_exact_repeats"]["significant"]
    assert r["h2_total_repeats"]["formally_tested"] is False
    assert "p_value_one_sided" not in r["h2_total_repeats"]


def test_detects_badly_timed_sevens(tmp_path):
    df = prepared_sim(tmp_path, seed=5, seven_boost=0.12)
    r = an.run_analysis(df, n_perm=500, n_boot=200)
    assert r["h3_badly_timed_sevens"]["main"]["significant"]


def test_two_proportion_test_by_hand():
    t = {"point_set_rolls": 700, "point_set_sevens": 140, "come_out_rolls": 300, "come_out_sevens": 45}
    r = an.two_proportion_test(t)
    pooled = 185 / 1000
    z = (0.2 - 0.15) / math.sqrt(pooled * (1 - pooled) * (1 / 700 + 1 / 300))
    assert r["z"] == pytest.approx(z)
    assert "fisher_exact_p_value_one_sided" not in r


def test_fisher_used_for_small_cells():
    t = {"point_set_rolls": 20, "point_set_sevens": 6, "come_out_rolls": 10, "come_out_sevens": 1}
    r = an.two_proportion_test(t)
    assert "fisher_exact_p_value_one_sided" in r


def test_bootstrap_intervals_contain_estimates(tmp_path):
    df = prepared_sim(tmp_path, seed=8)
    r = an.run_analysis(df, n_perm=200, n_boot=2000)
    ci = r["bootstrap_95_intervals"]["exact_repeat_rate"]
    assert ci[0] <= r["h1_exact_repeats"]["observed_rate"] <= ci[1]
    ci = r["bootstrap_95_intervals"]["point_set_seven_rate"]
    assert ci[0] <= r["h3_badly_timed_sevens"]["main"]["point_set_seven_rate"] <= ci[1]


def test_results_are_reproducible(tmp_path):
    df = prepared_sim(tmp_path, seed=9)
    a = an.run_analysis(df, n_perm=300, n_boot=300)
    b = an.run_analysis(df, n_perm=300, n_boot=300)
    assert a["h1_exact_repeats"]["p_value_one_sided"] == b["h1_exact_repeats"]["p_value_one_sided"]
    assert a["bootstrap_95_intervals"] == b["bootstrap_95_intervals"]


def test_per_machine_results_when_switched(tmp_path):
    df = prepared_sim(tmp_path, seed=3, switch_after=600)
    r = an.run_analysis(df, n_perm=200, n_boot=200)
    assert set(r["per_machine_exploratory"]) == {"A", "B"}
    assert set(r["sanity_check"]) == {"A", "B"}


def test_chi_square_skipped_for_small_machine_b(raw_dir):
    write_log(raw_dir, "A", [("25", "R", "", "2:00 PM"), ("34", "", "CO"), ("51", "", "", "2:01 PM", "serviced")])
    write_log(raw_dir, "B", [("11", "R", "", "2:05 PM"), ("34", "", "P5"), ("44", "", "", "2:06 PM")])
    df = core.prepare(raw_dir).cleaned
    assert an.sanity_check(df)["B"]["tested"] is False


def test_command_line_end_to_end(tmp_path):
    raw = tmp_path / "raw"
    rows, _ = sim.simulate_session(seed=12)
    sim.write_logs(rows, raw)
    cleaned = tmp_path / "cleaned.csv"
    summary = tmp_path / "validation_summary.md"
    assert prepare_data.main(["--raw-dir", str(raw), "--out", str(cleaned), "--summary", str(summary)]) == 0
    # The cleaned file is created once.
    assert prepare_data.main(["--raw-dir", str(raw), "--out", str(cleaned), "--summary", str(summary)]) == 1

    # Round trip through CSV keeps types.
    reloaded = core.load_cleaned(cleaned)
    assert reloaded["counts_toward_sample"].sum() == core.TARGET_ROLLS

    report, results = tmp_path / "report.md", tmp_path / "results.json"
    assert an.main(["--data", str(cleaned), "--report", str(report), "--json", str(results),
                    "--permutations", "300", "--bootstrap", "300"]) == 0
    assert "## H1 (primary)" in report.read_text()
    assert json.loads(results.read_text())["sample"]["counted_rolls"] == core.TARGET_ROLLS


def test_command_line_rejects_invalid_log(raw_dir, tmp_path, capsys):
    write_log(raw_dir, "A", [("25", "", "", ""), ("99",)])
    out = tmp_path / "cleaned.csv"
    assert prepare_data.main(["--raw-dir", str(raw_dir), "--out", str(out),
                              "--summary", str(tmp_path / "s.md")]) == 1
    assert not out.exists()
    assert "Validation failed" in capsys.readouterr().out
