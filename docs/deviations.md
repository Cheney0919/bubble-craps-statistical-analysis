# Data Collection Deviations

## Row 0 history-display mismatch

- **What happened:** The row 0 note records physical dice `3-6`, while the history display was recorded as showing `2-5`.
- **Original rule affected:** Row 0 should be the most recent pre-session roll from the history display and should match the physical dice at rest.
- **When discovered:** During post-collection cleaning on November 1, 2026.
- **Handling:** The raw export is retained unchanged. The cleaning script uses the logged physical value (`3-6`) as row 0, so it creates the first adjacent pair with roll 1 (`2-3`). The alternative displayed value (`2-5`) would also create neither an exact-combination nor a same-total repeat with roll 1. Thus, the discrepancy affects neither H1 nor H2; row 0 is excluded from H3.
- **Interpretation:** Confirmatory analyses are unaffected. The discrepancy remains documented in the raw note and here for auditability.
