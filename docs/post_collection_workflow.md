# Post-Collection Workflow

Do not inspect p-values or decide which test to emphasize before completing the steps below.

Commands, run from the repository root:

```bash
pip install -r requirements.txt
python scripts/prepare_data.py   # steps 2-5: validate, reconstruct phases, write cleaned data + summary
python scripts/analyze.py        # step 8: write results/analysis_report.md
```

1. Preserve the original `data/raw/roll_log_A.csv` (and `roll_log_B.csv`, if used) unchanged.
2. Count rolls, gaps, breaks, corrections, recovered rolls, any machine switch, and whether the session ended early.
3. Check all field values against the data dictionary.
4. Reconstruct the game phase from roll results and check it against every phase entered at the casino.
5. Create the cleaned data file and document every change from raw data.
6. Commit the raw data, cleaned data, and `results/validation_summary.md`.
7. Confirm the analysis scripts are unchanged since the pre-collection commit (`git diff <hash> -- scripts/`).
8. Run H1 first, H2 only if H1 is significant, and H3 as the separate directional secondary test.
9. Report every pre-specified test and all deviations, whether significant or not.

## Deviations file

If a rule in the preregistration was not followed, create `docs/deviations.md`. Each entry must state:

- What happened.
- Which original rule was affected.
- When the deviation was discovered.
- How it changes the dataset or interpretation.
- Whether the affected analysis is confirmatory, supporting, or exploratory.

