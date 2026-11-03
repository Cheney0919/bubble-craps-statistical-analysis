# Scripts

All scripts run from the repository root with Python 3.10+.

```bash
pip install -r requirements.txt
```

| Script | What it does |
|---|---|
| `prepare_data.py` | Validates `data/raw/roll_log_A.csv` (and `_B`), reconstructs game phases, and writes `data/cleaned/analysis_data.csv` and `results/validation_summary.md`. Writes nothing if validation fails. |
| `supplementary_analysis.py` | Adds what the written report needs on top of `analyze.py` without changing any confirmatory decision: effect sizes (Cohen's h and w), one-sided upper bounds on the repeat rate, power for the design actually run (formula and simulation), labelled exploratory analyses, and a replay of the pass-line balance. Writes `results/supplementary_report.md`, `results/supplementary_results.json`, and three figures. Takes a few minutes because of the simulations. |
| `analyze.py` | Runs the pre-registered analyses on the cleaned data: descriptive statistics first, then the fair-dice check, H1, H2 (if H1 is significant), H3, and the exploratory 7-rate comparisons with 1/6. Writes `results/analysis_report.md`, `results/totals_histogram.png`, and `results/analysis_results.json`. |
| `simulate_log.py` | Generates realistic fake raw logs, in the exact Google Sheet format, for testing. |
| `craps_core.py` | Shared logic: reading, validation rules, phase reconstruction, derived fields. |

## After data collection

```bash
python scripts/prepare_data.py
python scripts/analyze.py
python scripts/supplementary_analysis.py   # extra results for the written report
```

If `prepare_data.py` reports problems, it lists each with its spreadsheet row number. Do not edit the raw export; document any resolution in `docs/deviations.md` first (see `docs/preprocessing_plan.md`).

## Try it on simulated data

Simulated logs go to `data/simulated/`, which is git-ignored and never mixed with real data.

```bash
python scripts/simulate_log.py                      # fair machine
python scripts/prepare_data.py --raw-dir data/simulated \
    --out data/simulated/analysis_data.csv --summary data/simulated/validation_summary.md --force
python scripts/analyze.py --data data/simulated/analysis_data.csv \
    --report data/simulated/analysis_report.md --json data/simulated/analysis_results.json
```

Options for `simulate_log.py`:

- `--stuck-prob 0.03`: dice sometimes fail to tumble and repeat exactly (H1 should detect this).
- `--seven-boost 0.08`: extra 7s on point-set rolls (H3 should detect this).
- `--switch-after 600`: machine A becomes unavailable after 600 rolls, so the session switches to B.
- `--seed N`: a different simulated session.

Each simulated session includes row 0, roll 1 with `CO`, two `C` corrections, two missed rolls recovered as `R`, a short break recovered from the history display, and a long break that creates a `GAP`.

## Tests

```bash
python -m pytest
```

The tests cover:

- every validation rule;
- phase reconstruction against the simulator's true game state;
- that gaps and machine switches never create false pairs, and no roll is logged twice;
- the permutation p-value, gatekeeping, the H3 z-test, Fisher's exact test when an expected count is below 5, the p ≤ α decision rule, and the bootstrap;
- the descriptive tables, the exploratory binomial tests against 1/6, and the Bonferroni reference flags;
- the supplementary script: effect sizes, power formulas, exact bounds, the balance replay, and that its shuffles match the confirmatory test's;
- a full end-to-end run.

On 300 simulated fair sessions, H1 and H3 each rejected the null about 4% of the time, close to the expected 5%, so the tests are not biased toward finding an effect.
