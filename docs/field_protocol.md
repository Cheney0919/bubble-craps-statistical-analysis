# Field Protocol

## Pilot before formal collection

Before formal data collection, the collector records approximately 50 rolls from one machine. The pilot is excluded from the study dataset.

Use the pilot to confirm:

- how many rolls the history display keeps (expected about 20), and in what order it shows them;
- that the displayed dice can be reliably recorded as two faces;
- that every logged outcome can be reconciled with the history display;
- the roll rate (expected about 5 rolls per minute, or about 3 hours 20 minutes of logging for 1,000 rolls), and therefore how long a break the history covers;
- venue rules concerning note-taking, phones, and video.

If a history display is unavailable, do not proceed with the formal session until the group has documented a replacement verification procedure.

## Formal session procedure

1. Record one machine for one session of 1,000 rolls, starting on a come-out roll.
2. Before the first live roll, log the most recent pre-session roll from the history display as row 0 (`recovered_from_history`, phase `unknown`, point blank). Confirm it matches the physical dice at rest, and note any mismatch.
3. Record the displayed result for every roll, not an estimate from watching dice in motion.
4. Record the game phase immediately before each live roll.
5. After every 10 rolls, compare the last 10 entries with the history display and mark corrections as `corrected_from_history`.
6. Recover a missed roll from the history display while it is still visible. Log it as `recovered_from_history` with phase `unknown`. If recovery is impossible, record `gap`; do not guess.
7. Before a break, note the time. Try to return before any roll occurs. On return, stay on the same machine and, before the next roll, follow the break rules in the preregistration:
   - If your last 3 logged rolls are still in the history, log every roll after them as `recovered_from_history`. There is no gap.
   - Otherwise, log a `gap`, then every visible history roll, oldest first.

   Try to keep breaks under about 3 minutes (roughly 15 rolls) so the history still overlaps your log.
8. If machine A becomes unavailable, note the reason in its final row and switch once to fallback machine B. A is unavailable if it is serviced, its dice are changed, its display becomes unusable, or you cannot get back to it. On B:
   - use `machine_id` `B` and `session_id` `B_01`;
   - log B's row 0 from its history and check it against B's physical dice;
   - continue until the combined total reaches 1,000 rolls.

   Missed rolls alone are not a reason to switch.
9. End the session early only if machine B also becomes unavailable, recording is materially interrupted, or staff ask you to stop. Note the reason in the final row. There is no replacement session.

## Financial and privacy boundaries

- The collector uses only the pre-agreed table-minimum pass-line bet; do not vary stakes because of outcomes.
- Do not record names, faces, financial details, or video of other people.
- Do not continue logging in conflict with casino staff instructions or venue policy.

