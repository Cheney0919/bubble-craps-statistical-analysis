"""Supplementary analyses: effect sizes, bounds, power, shuffles, and the balance replay."""

import math

import numpy as np
import pytest

import analyze as an
import craps_core as core
import simulate_log as sim
import supplementary_analysis as sup


def prepared_sim(tmp_path, **kwargs):
    rows, _ = sim.simulate_session(**kwargs)
    sim.write_logs(rows, tmp_path)
    prepared = core.prepare(tmp_path)
    assert prepared.issues == []
    return prepared.cleaned


def test_cohen_h_round_trip():
    h = sup.cohen_h(0.07, 0.05)
    assert h > 0
    assert sup.from_cohen_h(0.05, h) == pytest.approx(0.07)
    assert sup.cohen_h(0.05, 0.05) == 0


def test_cohen_w():
    assert sup.cohen_w(10.0, 1000) == pytest.approx(math.sqrt(0.01))


def test_stickiness_conversions():
    base = an.FAIR_EXACT_REPEAT
    assert sup.rate_from_stickiness(0.0, base) == pytest.approx(base)
    assert sup.rate_from_stickiness(1.0, base) == pytest.approx(1.0)
    assert sup.stickiness_from_rate(sup.rate_from_stickiness(0.02, base), base) == pytest.approx(0.02)


def test_break_even_values():
    three = sup.break_even(15, 2 / 36)
    assert three["break_even_rate"] == pytest.approx(1 / 16)
    assert three["break_even_stickiness"] == pytest.approx((1 / 16 - 2 / 36) / (1 - 2 / 36))
    assert three["expected_return_per_dollar_fair"] == pytest.approx(16 * 2 / 36)
    two = sup.break_even(30, 1 / 36)
    assert two["break_even_rate"] == pytest.approx(1 / 31)
    # The strategy loses about 11-14 cents per dollar with fair dice.
    assert 0.85 < two["expected_return_per_dollar_fair"] < 0.9


def test_power_formula_matches_known_values():
    # 1,984 pairs, one-sided alpha = 0.05, 80% power: about 6.4% (the original two-machine plan).
    assert sup.mde_one_sample(1984, an.FAIR_EXACT_REPEAT)["p1"] == pytest.approx(0.064, abs=0.001)
    # The power at the detectable rate is 80% by construction.
    p1 = sup.mde_one_sample(1000, an.FAIR_EXACT_REPEAT)["p1"]
    assert sup.power_one_sample(p1, an.FAIR_EXACT_REPEAT, 1000) == pytest.approx(0.80)
    # Two-sided needs a bigger effect; a Bonferroni 0.025 one-sided cutoff equals two-sided 0.05.
    two = sup.mde_one_sample(1000, an.FAIR_EXACT_REPEAT, two_sided=True)["p1"]
    bonf = sup.mde_one_sample(1000, an.FAIR_EXACT_REPEAT, alpha=0.025)["p1"]
    assert two > p1 and two == pytest.approx(bonf)


def test_exact_bounds():
    low, high = sup.exact_interval(5, 100)
    assert low < 0.05 < high
    assert sup.exact_upper_bound(5, 100) < high  # one-sided 95% is tighter than two-sided 95%
    assert sup.exact_upper_bound(100, 100) == 1.0


def test_fair_shared_face_rate():
    # Two rolls share no face only if the second roll avoids both faces of the first.
    assert sup.fair_shared_face_rate() == pytest.approx(666 / 1296)


def test_shares_face():
    code = an.COMBINATION_CODE
    prev = np.array([code["1-2"], code["3-3"], code["4-6"]], dtype=np.int8)
    nxt = np.array([code["2-5"], code["1-4"], code["4-6"]], dtype=np.int8)
    assert sup.shares_face(prev, nxt).tolist() == [True, False, True]


def test_shuffles_match_confirmatory_test(tmp_path):
    df = prepared_sim(tmp_path, seed=3)
    blocks = an.blocks(df)
    shuffled = sup.shuffled_statistics(blocks, 300, seed=11)
    confirmatory = an.permutation_repeat_counts(blocks, 300, np.random.default_rng(11))
    for kind in ("exact", "total"):
        expected = sum((v[kind] for v in confirmatory.values()), start=np.zeros(300, dtype=np.int64))
        assert np.array_equal(expected, shuffled[kind].astype(np.int64))
    # A weighted count is at least the plain count; a shared face includes every exact repeat.
    assert (shuffled["weighted"] >= shuffled["exact"]).all()
    assert (shuffled["shared_face"] >= shuffled["exact"]).all()


def test_replay_balance():
    # Come-out 7 wins; come-out 2 loses; point 6 made; point 8 then seven-out.
    r = sup.replay_balance([7, 2, 6, 5, 6, 8, 7], start=100, bet=3)
    assert (r["rounds_won"], r["rounds_lost"]) == (2, 2)
    assert r["ending_balance"] == 100
    assert r["lowest_balance"] == 97  # after placing the bet on the come-out 6
    # A bet still on the table at the end has been taken from the balance.
    r = sup.replay_balance([4, 5], start=100, bet=3)
    assert r["bet_open_at_end"] and r["ending_balance"] == 97


def test_sticky_sequence_copies():
    rng = np.random.default_rng(0)
    seq = sup.sticky_sequence(5000, 1.0, rng)
    assert (seq == seq[0]).all()
    seq = sup.sticky_sequence(20000, 0.0, rng)
    rate = an.count_repeats(seq) / (len(seq) - 1)
    assert rate == pytest.approx(an.FAIR_EXACT_REPEAT, abs=0.006)


def test_end_to_end(tmp_path):
    df = prepared_sim(tmp_path, seed=5)
    results, fig = sup.run_supplementary(df, n_perm=500, n_boot=200, n_sims=5, n_sims_h3=20,
                                         n_sim_shuffles=99)
    assert set(results) >= {"effect_sizes", "ruled_out", "power_for_design_run", "simulation_check",
                            "exploratory", "data_quality_balance_replay"}
    ro = results["ruled_out"]
    assert ro["upper_bound_95_exact_binomial"] > ro["observed_rate"]
    assert len(fig["shuffled_exact"]) == 500


def test_overlap_variance_inflation():
    # Fair dice: about 0.4% extra variance for combination repeats and 3% for total repeats.
    combos = sup.overlap_variance_inflation(sup.COMBO_PROBS, 1000)
    totals = sup.overlap_variance_inflation([an.FAIR_TOTAL_PROBS[t] for t in range(2, 13)], 1000)
    assert combos == pytest.approx(0.0044, abs=0.0003)
    assert totals == pytest.approx(0.0317, abs=0.0005)
    # Check the formula against simulated fair sequences.
    rng = np.random.default_rng(1)
    seqs = rng.choice(len(sup.COMBO_PROBS), size=(4000, 1001), p=sup.COMBO_PROBS)
    counts = (seqs[:, 1:] == seqs[:, :-1]).sum(axis=1)
    q = an.FAIR_EXACT_REPEAT
    binomial_var = 1000 * q * (1 - q)
    assert counts.var(ddof=1) == pytest.approx(binomial_var * (1 + combos), rel=0.08)


def test_every_result_has_a_role():
    assert all(isinstance(v, str) and v for v in sup.ROLES.values())
    assert sup.ROLES["exploratory.strategy_repeats"].startswith(sup.PREREGISTERED)
    assert sup.ROLES["exploratory.weighted_repeat_count"].startswith(sup.POST_HOC)
