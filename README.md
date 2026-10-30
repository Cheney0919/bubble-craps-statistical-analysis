# Does the Bubble Remember

## Testing for Streaks and Badly Timed Sevens on Bubble Craps Machines

This repository documents a pre-registered observational study of two physical bubble-craps machines. It contains the agreed rules for data collection, cleaning, and analysis before formal data are collected.

The study asks whether the observed sequence of dice outcomes is consistent with a machine with no memory. It does **not** attempt to prove that all bubble-craps machines are fair or unfair, or that a casino intentionally changes outcomes in response to bets.

## Current status

**Planning and pilot stage. No formal study data have been collected yet.**

Before the first formal session, the group will complete the pilot, fill in every open decision in the checklist, and commit the final protocol. The pilot is excluded from the final sample.

## Research questions

| Label | Question | Planned interpretation |
|---|---|---|
| H1 primary | Do exact unordered dice combinations repeat more or less often than expected if consecutive rolls are independent? | Evidence for or against sequential independence. |
| H2 secondary | Do totals repeat more or less often than expected if consecutive rolls are independent? | Tested formally only if H1 is significant. |
| H3 secondary | Are 7s more common after a point is set than on come-out rolls? | Evidence about the specific “badly timed sevens” player claim. |
| Sanity check | Do the observed totals match fair-dice frequencies? | Evidence about bias in total frequencies, not about memory. |

H1 and H2 examine whether the sequence has memory; they do not simply test whether the dice are biased. H3 compares naturally occurring game phases, so it describes an association and cannot by itself demonstrate intent or causation.

## Key decisions already fixed

- **H1 and H2 are two-sided.** Both unusually frequent and unusually rare repeats would be evidence that adjacent rolls are not behaving like an independent sequence.
- **H2 is gated behind H1.** This limits two versions of the same “streakiness” claim from inflating false positives.
- **H3 is one-sided.** It evaluates the specific pre-stated claim that 7s occur more often when a pass-line bettor loses.
- **Planned sample:** two machines × eight sessions per machine × 125 rolls = 2,000 rolls total.
- **No early stopping for exciting results.** Sessions end early only for documented operational reasons, such as machine service or an unusable display.
- **Missing results are never guessed.** An unrecoverable result becomes a `gap` that breaks the adjacent sequence.

The full rationale and exact decision rules are in [`docs/preregistration.md`](docs/preregistration.md).

## Before formal data collection

Work through these documents in order:

1. [`docs/pre_collection_checklist.md`](docs/pre_collection_checklist.md) — decisions that must be agreed upon and recorded.
2. [`docs/field_protocol.md`](docs/field_protocol.md) — pilot and in-person logging procedure.
3. [`docs/data_dictionary.md`](docs/data_dictionary.md) — required fields and allowed values for each roll.
4. [`data/templates/roll_log_template.csv`](data/templates/roll_log_template.csv) — blank template for the actual log.
5. [`docs/preregistration.md`](docs/preregistration.md) — final study plan to commit before the first formal roll.

## Data and reproducibility

The project will retain both the original roll log and the cleaned analysis data. The raw log must never be overwritten, and it must not contain names, faces, video, financial details, or other personal information.

After data collection, the group will follow [`docs/post_collection_workflow.md`](docs/post_collection_workflow.md): validate the log, document any corrections or deviations, create the cleaned dataset, then add reproducible scripts for the pre-registered analyses. The course requires scripts rather than notebook-only analysis.

```text
data/raw/          Original roll logs; preserved unchanged.
data/templates/    Blank CSV logging template.
data/cleaned/      Analysis-ready dataset created after validation.
docs/              Preregistration, protocols, checklists, and documentation.
scripts/           Reproducible analysis scripts added after data format is confirmed.
results/           Generated tables, figures, and analysis summaries.
```

## Collaboration and course requirements

This is a private group repository. The course requires use of branches and pull requests, including at least one pull request from each group member. Work does not need to be pre-assigned; the group can decide naturally what each person contributes. The important part is that the resulting work and review history are visible in the repository.

