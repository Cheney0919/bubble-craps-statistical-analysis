# Data Collection Deviations

## Row 0 history-display mismatch

- **What happened:** The row 0 note records physical dice `3-6`, while the history display was recorded as showing `2-5`.
- **Original rule affected:** Row 0 should be the most recent pre-session roll from the history display and should match the physical dice at rest.
- **When discovered:** During post-collection cleaning on November 1, 2026.
- **Handling:** The raw export is retained unchanged. The cleaning script uses the logged physical value (`3-6`) as row 0, so it creates the first adjacent pair with roll 1 (`2-3`). The alternative displayed value (`2-5`) would also create neither an exact-combination nor a same-total repeat with roll 1. Thus, the discrepancy affects neither H1 nor H2; row 0 is excluded from H3.
- **Interpretation:** Confirmatory analyses are unaffected. The discrepancy remains documented in the raw note and here for auditability.

## Roll 853 corrected from session video

- **What happened:** Roll 853 (sheet row 855) was logged as `5-5` but was actually `4-4`.
- **Original rule affected:** Logging errors were to be caught at the 10-roll checks against the history display and flagged `C`. This error was not caught during the session.
- **When discovered:** During post-collection cleaning on November 1, 2026. Replaying the $3 pass line bets from the log gave an ending balance of $49, but the balance recorded at the end of the session was $40. Single-roll errors that could explain the $9 difference were listed and checked against the point numbers recorded at the checkpoints. Roll 853 was one of several candidates, and the session video confirmed it as `4-4`.
- **Handling:** The initial Google Sheet export is retained unchanged as `data/raw/roll_log_A_original_export.csv`. The reconciled `data/raw/roll_log_A.csv` changes this row from `55` to `44`, flags it `C`, and links here in its note. The flag records a documented correction from post-session video rather than a 10-roll check. The cleaned file was regenerated with `--force`. With the correction, the replayed ending balance is $40 and every recorded checkpoint phase matches the reconstructed phase.
- **Effect:** H1 and H2 are unaffected, because neither `5-5` nor `4-4` repeats the roll before (`4-5`) or after (`2-4`) in combination or total. For H3, the point of 10 now stays open after roll 853, so rolls 854, 859 and 864 move from come-out to point set. None of these is a 7, so no 7 changes phase; the point-set and come-out roll counts change by 3. The totals table changes by one roll (one fewer 10, one more 8).

## Log verification: 10-roll checks replaced by 50-roll videos

- **What happened:** For roughly the first 100 rolls, the collector compared the log with the machine's history display every 10 rolls, as planned. The history display turned out to keep the last 50 rolls rather than the roughly 20 expected, so from then on the collector recorded a short video of the history display about every 50 rolls instead, framed to show only the machine and no people. The phase shown by the machine was also logged, with the time, at about every 50th roll. After the session, the collector checked the log against the videos.
- **Original rule affected:** Field protocol step 4: compare the last 10 entries with the history display every 10 rolls and flag fixes `C`. The privacy rule (no video of other people) was kept.
- **When discovered:** During the session, after about the first 100 rolls.
- **Handling:** No entries were corrected during the session. The one error found afterwards is roll 853 (entry above). Every phase logged at a checkpoint matches the phase reconstructed from the dice (`results/validation_summary.md`: 0 phase mismatches), and replaying the pass-line bets from the $100 starting balance reproduces the recorded $40 ending balance (`results/supplementary_report.md`).
- **Effect:** None on the analysis plan. Data quality is reported as the errors detected and corrected in the post-session audit (1 in 1,000 rolls) rather than as in-session corrections. The audit cannot establish the true error rate: an error missed in the video review that also left the replayed balance and the checkpoint phases unchanged would go undetected.

## Pre-collection commit merged after the session started

- **What happened:** The checklist records `bdd214e` as the commit immediately before formal collection. That merge commit is timestamped 2:13 PM EST on November 1, ten minutes after row 0 (2:03 PM). Its content is identical to `d7d255c` (October 31, 4:29 PM EDT), the last commit of the analysis-scripts pull request: `git diff d7d255c bdd214e` is empty. The checklist sign-off commit `c1371dd` (2:42 PM) was also made during the session.
- **Original rule affected:** Checklist section F: commit all agreed protocol documents before formal collection begins.
- **When discovered:** November 2, 2026, while preparing the report.
- **Handling:** The report cites `d7d255c` as the commit that fixed the hypotheses, tests, and analysis code before data collection. After it, the scripts changed only in report wording (`git diff bdd214e HEAD -- scripts/` shows label edits and the removal of a timestamp, plus the separate supplementary script added after the analysis).
- **Effect:** None on any analysis. Only the commit cited as evidence of pre-registration changes.
