# Data Dictionary

Each row is one observed roll. Use these exact column names in `data/raw/roll_log.csv`.

| Column | Required | Allowed values | Meaning |
|---|---:|---|---|
| `machine_id` | Yes | `A`, `B` | Non-identifying machine label. `B` is used only if the session switches to the fallback machine. |
| `collector_id` | Yes | text | Identifier for the person who recorded the session. |
| `session_id` | Yes | `A_01`, `B_01` | Session label; one per machine. Must match `machine_id`. |
| `roll_number` | Yes | integer ≥ 0 | `0` for the pre-session roll on each machine; then consecutive row numbers within that `session_id`, including `gap` rows. |
| `timestamp` | Yes | ISO date/time | When the result was logged. |
| `die_low` | Yes except `gap` | 1-6 | Lower displayed die value. |
| `die_high` | Yes except `gap` | 1-6 | Higher displayed die value. |
| `total` | Yes except `gap` | 2-12 | Must equal `die_low + die_high`. |
| `phase_before_roll` | Yes | `come_out`, `point_set`, `unknown` | Game phase before this roll, as seen live. `unknown` only on `recovered_from_history` and `gap` rows. |
| `point_value_before_roll` | Conditional | blank or 4,5,6,8,9,10 | Point number on a `point_set` row; blank otherwise. |
| `other_players_betting` | Yes | `yes`, `no`, `unknown` | Whether another player had a bet on the machine. |
| `verification_status` | Yes | `verified`, `corrected_from_history`, `recovered_from_history`, `gap` | `verified` = logged live and matched the history; `corrected_from_history` = logged live, then corrected against the history; `recovered_from_history` = not seen live, read from the history (row 0, missed rolls, breaks); `gap` = roll(s) lost. |
| `notes` | No | text | Interruption, `break`, service, display issue, or other event. |

## Derived fields

The preparation script creates the following fields rather than entering them by hand:

- `combination`: `die_low-die_high`, such as `3-4`.
- `previous_combination` and `previous_total`.
- `exact_repeat` and `total_repeat`.
- `analysis_block_id`: separates contiguous observed runs within the session when a gap (including a break) occurs.
- `valid_pair`: false for the first roll in a session or block and for either side of a logged gap. Row 0 is the first roll of each `session_id`, so roll 1 forms a valid pair with it. Pairs never span the two machines.
- `counts_toward_sample`: true for every non-gap row except each machine's row 0. The 1,000-roll target is the total across both machines.
- `phase_used`: the recorded phase for live rows, or the reconstructed phase for recovered rows (blank if it cannot be reconstructed). H3 uses only rows with a non-blank `phase_used`, excluding row 0.

