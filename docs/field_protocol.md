# Field Protocol

## Setup before the visit

Create a Google Sheet with a tab named `A`, using the column headers from [`../data/templates/roll_log_template.csv`](../data/templates/roll_log_template.csv): `dice`, `flag`, `phase`, `time`, `notes`. Add a tab `B` with the same headers in case the fallback machine is needed. Open the sheet in the Google Sheets app on your phone; it saves as you type, works offline, and syncs when signal returns.

## Arrival check (no data recorded)

There is no pilot. Instead, before row 0, spend a few minutes confirming, without recording anything:

- the bubble craps machines available, so machine A (and a possible machine B) can be chosen by the selection rule in the preregistration;
- that machine A's history display works, shows roughly the last 20 rolls, and matches the physical dice at rest;
- the number of rolls the history keeps, noted in the row 0 `notes`. This sets how long a break can be without losing rolls (about 4 minutes for 20 rolls at 5 rolls per minute).

If the history display is unavailable or doesn't match the physical dice, choose another machine by the same rule. If no machine has a working history display, do not start the formal session.

## What to enter

Most rows are just the two dice. The game phase is entered only in the rare cases in this table: roll 1, and the first live roll after a gap or machine switch. Everything else, including when the point is set and when it ends, is worked out by the script from the dice sequence.

| Situation | `dice` | `flag` | `phase` | `time` |
|---|---|---|---|---|
| Normal live roll | two dice, e.g. `34` | | | |
| Row 0 (session or machine start) | from history | `R` | | yes |
| Roll 1 (first come-out) | two dice | | `CO` | |
| Roll read from the history display (missed roll, break) | from history | `R` | | |
| Entry fixed at a 10-roll check | corrected dice | `C` | | |
| Rolls lost | | `GAP` | | yes |
| First live roll after a `GAP` or machine switch | two dice | | current phase from the machine | |

**Phase codes** describe the machine's state just before that roll:

- `CO`: come-out (no point is on).
- `P4`, `P5`, `P6`, `P8`, `P9`, `P10`: a point is on, and the number is the point.

These are not roll counts: `P6` means "the point is 6." The number matters because after a gap the script cannot otherwise tell when the point is made. Rolling the point number ends the point phase just as a 7 does.

## Formal session procedure

1. **Row 0.** Wait until the machine is about to start a come-out roll. Read the most recent roll from the history display and enter it as row 0: `dice`, flag `R`, the current `time`, and a note confirming it matches the physical dice.
2. **Roll 1** is the come-out roll. Enter its `dice` and phase `CO`.
3. **Every roll after that:** enter only the two dice, e.g. `34`. Record the displayed result. The phase does not need to be entered; the script reconstructs it.
4. **Every 10 rolls:** compare your last 10 entries with the history display. Fix any wrong entry and put `C` in its `flag`.
5. **Missed roll:** enter it from the history display while it is still visible, with flag `R`. If it is no longer visible, add a row with flag `GAP` and the `time`; never guess.
6. **Breaks:** before leaving, enter the `time` and `break` in the notes of your last row. Try to return before any roll occurs, and always return to the same machine. Before the next roll:
   - **No rolls happened:** carry on.
   - **Your last 3 entries are still visible in the history**, at a unique position: enter every roll after them, oldest first, with flag `R`. No gap.
   - **Otherwise:** add a `GAP` row with the `time` and `break`. Then enter the visible history rolls, oldest first, with flag `R`, **skipping the 3 oldest**. Up to 2 of those may already be in your log, so skipping them prevents logging a roll twice.

   If you logged a `GAP`, enter the machine's current phase (`CO`, or `P` + the point number, e.g. `P6`) on the next live roll. If there was no gap, no phase is needed. Aim to keep breaks under about 3 minutes.
7. **Machine switch:** only if machine A becomes unavailable (serviced, dice changed, display unusable, or you can't get back to it). Missed rolls alone are not a reason to switch.
   - Note the reason and `time` on A's last row.
   - Switch to tab `B`. Enter B's row 0 as in step 1, checked against B's physical dice.
   - Enter B's current phase (`CO`, or `P` + the point number) on B's first live roll.
   - Continue until A and B together reach 1,000 rolls (not counting either row 0 or `GAP` rows).
8. **End:** stop at 1,000 rolls. End early only if machine B also becomes unavailable, recording is materially interrupted, or staff ask you to stop. Enter the `time` and the reason on the final row. There is no replacement session.
9. **Export:** after the session, download each tab as a CSV, save it unchanged as `data/raw/roll_log_A.csv` (and `roll_log_B.csv`), and commit it. Do not edit the sheet after export.

## Financial and privacy boundaries

- The collector uses only the $3 table-minimum pass-line bet; do not vary stakes because of outcomes.
- Do not record names, faces, financial details, or video of other people.
- Do not continue logging in conflict with casino staff instructions or venue policy.
