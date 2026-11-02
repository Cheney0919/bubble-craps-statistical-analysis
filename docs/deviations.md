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
