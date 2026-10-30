# Data Dictionary

Each row is one observed roll. Use these exact column names in `data/raw/roll_log.csv`.

| Column | Required | Allowed values | Meaning |
|---|---:|---|---|
| `machine_id` | Yes | `A`, `B` | Non-identifying machine label. |
| `collector_id` | Yes | text | Identifier for the person who recorded the session; initially one collector. |
| `session_id` | Yes | text | Unique session label, e.g. `A_01`. |
| `roll_number` | Yes | positive integer | Consecutive number within session. |
| `timestamp` | Yes | ISO date/time | When the result was logged. |
| `die_low` | Yes except `gap` | 1-6 | Lower displayed die value. |
| `die_high` | Yes except `gap` | 1-6 | Higher displayed die value. |
| `total` | Yes except `gap` | 2-12 | Must equal `die_low + die_high`. |
| `phase_before_roll` | Yes | `come_out`, `point_set` | Game phase before this roll. |
| `point_value_before_roll` | Conditional | blank or 4,5,6,8,9,10 | Blank on a come-out; point number otherwise. |
| `other_players_betting` | Yes | `yes`, `no`, `unknown` | Whether another player had a bet on the machine. |
| `verification_status` | Yes | `verified`, `corrected_from_history`, `gap` | How the entry was verified. |
| `notes` | No | text | Interruption, service, display issue, or other event. |

## Derived fields

The preparation script creates the following fields rather than entering them by hand:

- `combination`: `die_low-die_high`, such as `3-4`.
- `previous_combination` and `previous_total`.
- `exact_repeat` and `total_repeat`.
- `analysis_block_id`: separates contiguous observed runs within a session when a gap occurs.
- `valid_pair`: false for the first roll in a session or block and for either side of a logged gap.

