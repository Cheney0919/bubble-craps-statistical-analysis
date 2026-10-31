# Data Dictionary

There are two data layers:

1. **Raw log**: what the collector types at the casino. It is kept as small as possible so one person can keep up at about 5 rolls per minute. It is exported once and never edited afterwards.
2. **Cleaned dataset**: created by the preparation script from the raw log. All analyses use this file.

## Raw log

The log is kept in a Google Sheet on the collector's phone, with one tab per machine: `A`, and `B` only if the session switches to the fallback machine. After the session, each tab is downloaded as a CSV and saved unchanged as `data/raw/roll_log_A.csv` (and `data/raw/roll_log_B.csv`). The column headers come from [`../data/templates/roll_log_template.csv`](../data/templates/roll_log_template.csv).

Each row is one roll, or one `GAP` marker, in the order it occurred. Row order is the roll order.

| Column | When to fill | Allowed values | Meaning |
|---|---|---|---|
| `dice` | Every row except `GAP` | Two digits, each 1–6, in either order (e.g. `34` or `43`) | The two displayed dice. |
| `flag` | Only when it applies | blank, `R`, `C`, `GAP` | blank = seen live; `R` = not seen live, read from the history display (row 0, a missed roll, rolls during a break); `C` = seen live, then corrected at a 10-roll check; `GAP` = one or more rolls lost. A `GAP` row has no dice. |
| `phase` | Only on roll 1 and on the first live roll after a `GAP` or machine switch | blank, `CO`, `P4`, `P5`, `P6`, `P8`, `P9`, `P10` | Game phase shown on the machine just before that roll: come-out, or the point number. |
| `time` | Row 0, every `GAP` row, the start and end of breaks, and the final row | Local clock time, e.g. `2:05 PM` | Eastern Time. On November 1, 2026, all session times are Eastern Standard Time (UTC−05:00). |
| `notes` | Optional | text | Session start/end, `break`, machine switch and reason, display issues, or anything unusual. |

The first row of each tab is **row 0**: the most recent pre-session roll, read from the history display and flagged `R`. Its note confirms whether it matched the physical dice.

## Cleaned dataset

The preparation script writes `data/cleaned/analysis_data.csv` with one row per raw row and the following fields.

| Field | Derived from | Meaning |
|---|---|---|
| `machine_id` | file name | `A` or `B`. |
| `session_id` | file name | `A_01` or `B_01`. |
| `roll_number` | row order | `0` for row 0, then consecutive within the file, including `GAP` rows. |
| `die_low`, `die_high` | `dice` | The two dice sorted low to high. |
| `total` | `dice` | `die_low + die_high`. |
| `combination` | `dice` | Unordered combination, e.g. `3-4`. |
| `verification_status` | `flag` | `verified` (blank), `recovered_from_history` (`R`), `corrected_from_history` (`C`), `gap` (`GAP`). |
| `phase_recorded` | `phase` | The phase typed at the casino, if any. |
| `phase_before_roll` | reconstruction | `come_out`, `point_set`, or blank if it cannot be determined (see the preprocessing plan). |
| `point_value_before_roll` | reconstruction | The point when `phase_before_roll` is `point_set`; blank otherwise. |
| `time`, `notes` | raw | Copied unchanged. |
| `analysis_block_id` | `GAP` rows, file | A new block starts at row 0 of each machine and after every `GAP`. |
| `previous_combination`, `previous_total` | previous row in the block | Blank on the first row of a block. |
| `valid_pair` | block | True when this row and the previous row are both rolls in the same block. Roll 1 pairs with row 0. Pairs never span a gap or the two machines. |
| `exact_repeat`, `total_repeat` | valid pairs | Whether the combination or total equals the previous roll's. |
| `counts_toward_sample` | flag, row 0 | True for every non-gap row except each machine's row 0. The 1,000-roll target is the total across both machines. |
| `h3_eligible` | sample, phase | True when `counts_toward_sample` is true and `phase_before_roll` is known. |
