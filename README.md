# Does the Bubble Repeat Itself?

## Testing Player Claims of Repeating Rolls and Badly Timed Sevens on a Bubble Craps Machine

This repository documents a pre-registered observational study of one physical bubble-craps machine, observed for 1,000 consecutive rolls in a single session. It contains the locked protocol, preserved raw log, cleaned dataset, validation record, and reproducible analysis pipeline.

The study tests two player claims: that the same dice combination tends to come up again on the next roll, and that 7s come more often when they cost a pass-line bettor. It does **not** attempt to prove that all bubble-craps machines are fair or unfair, or that a casino intentionally changes outcomes in response to bets.

## Current status

**Formal data collection is complete.** One session was collected from machine A at Caesars Virginia on November 1, 2026. The dataset contains 1,000 counted rolls, with no gaps and no fallback-machine use.

The repository preserves the original Google Sheet export and the reconciled raw log. One video-verified correction was made to roll 853; its rationale and effect on the cleaned data are documented in [`docs/deviations.md`](docs/deviations.md). See [`results/validation_summary.md`](results/validation_summary.md) for the final data-quality checks and [`results/analysis_report.md`](results/analysis_report.md) for generated results.

## Research questions

| Label | Question | Planned interpretation |
|---|---|---|
| H1 primary | Do exact unordered dice combinations repeat on consecutive rolls more often than expected if rolls are independent? | Evidence about the player claim that the same dice come up again. |
| H2 secondary | Do totals repeat on consecutive rolls more often than expected if rolls are independent? | Extends H1 to totals, which is what bets pay on. Tested formally only if H1 is significant. |
| H3 secondary | Are 7s more common after a point is set than on come-out rolls? | Evidence about the specific “badly timed sevens” player claim. |
| Exploratory | Is the 7 rate above 1/6 in each phase? | Helps interpret H3 (bad timing vs. too many 7s overall). No formal decision. |
| Sanity check | Do the observed totals match fair-dice frequencies? | Evidence about bias in total frequencies, not about repeats. |

H1 and H2 test whether consecutive rolls repeat more than chance; they do not simply test whether the dice are biased. H3 compares naturally occurring game phases, so it describes an association and cannot by itself demonstrate intent or causation.

## Key decisions already fixed

- **H1 and H2 are one-sided.** They test the specific claim that repeats happen *more* often than chance. This is also the direction a physical tumbling fault would produce and the only direction a betting strategy could exploit. An unusually low repeat rate is reported descriptively but not formally tested.
- **H2 is gated behind H1.** This limits two versions of the same “streakiness” claim from inflating false positives.
- **H3 is one-sided.** It evaluates the specific pre-stated claim that 7s occur more often when a pass-line bettor loses.
- **No correction across the two claims.** Repeats and sevens are separate questions, each tested at α = 0.05 (reject when p ≤ α). The overall false-positive risk of about 9.75% is stated openly, and the report notes whether each significant result would also pass the Bonferroni threshold of 0.025.
- **Missing a real effect is the larger risk.** With 1,000 rolls fixed, the plan favors sensitivity (Type 2 over Type 1); significant results are reported as evidence worth replicating, never as proof of rigging.
- **Descriptive statistics come first.** Frequency tables and a histogram of totals precede every test.
- **Planned sample:** one machine × one session × 1,000 rolls, in a single visit (about 5 rolls/minute, roughly 3 hours 20 minutes of logging). One collector records the entire session. Conclusions apply only to the machine(s) observed during that visit.
- **No early stopping for exciting results.** The session ends before 1,000 rolls only for documented operational reasons, such as the fallback machine also becoming unavailable or staff instruction.
- **The log is checked against the machine's history display** (about the last 20 rolls) every 10 rolls.
- **The collector stays on the same machine after a break.** The session switches once, to a pre-designated fallback machine, only if the first machine becomes unavailable (serviced, dice changed, display unusable, or taken). Missed rolls alone are not a reason to switch.
- **Short breaks lose nothing.** Rolls that happen during a break are recovered from the history display. Only a break long enough that the history no longer overlaps the log creates a `gap`, which splits the session into separate analysis blocks.
- **Missing results are never guessed.** An unrecoverable result becomes a `gap` that breaks the adjacent sequence.

The full rationale and exact decision rules are in [`docs/preregistration.md`](docs/preregistration.md).

## Protocol and collection documents

These documents record the protocol that was locked before formal collection:

1. [`docs/pre_collection_checklist.md`](docs/pre_collection_checklist.md) — decisions that must be agreed upon and recorded.
2. [`docs/field_protocol.md`](docs/field_protocol.md) — arrival check and in-person logging procedure.
3. [`docs/data_dictionary.md`](docs/data_dictionary.md) — required fields and allowed values for each roll.
4. [`data/templates/roll_log_template.csv`](data/templates/roll_log_template.csv) — column headers for the Google Sheet used at the casino (`dice`, `flag`, `phase`, `time`, `notes`).
5. [`docs/preregistration.md`](docs/preregistration.md) — final study plan to commit before the first formal roll.

## Data and reproducibility

The project retains both the original roll log and the cleaned analysis data. The raw log must never be overwritten, and it must not contain names, faces, video, financial details, or other personal information.

The cleaning and analysis scripts were written and tested on simulated logs **before** data collection, then applied to the reconciled raw log. To reproduce the current validation and analysis outputs, follow [`docs/post_collection_workflow.md`](docs/post_collection_workflow.md):

```bash
pip install -r requirements.txt
python scripts/prepare_data.py   # validate data/raw/, write data/cleaned/analysis_data.csv
python scripts/analyze.py        # run the pre-registered tests, write results/analysis_report.md
```

To try the pipeline on simulated data, or run the tests, see [`scripts/README.md`](scripts/README.md).

```text
data/raw/          Original roll logs; preserved unchanged.
data/templates/    Blank CSV logging template.
data/cleaned/      Analysis-ready dataset created after validation.
data/simulated/    Simulated logs for testing (git-ignored).
docs/              Preregistration, protocols, checklists, and documentation.
scripts/           Cleaning, analysis, and simulation scripts.
tests/             Automated tests (pytest) for the scripts.
results/           Validation summary and analysis report.
```

## Collaboration and course requirements

This is a private group repository. The course requires use of branches and pull requests, including at least one pull request from each group member. Work does not need to be pre-assigned; the group can decide naturally what each person contributes. The important part is that the resulting work and review history are visible in the repository.

