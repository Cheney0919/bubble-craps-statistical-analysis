# Preregistration

## Scope

This is an observational study of one physical bubble-craps machine (machine A), observed in a single formal session. One collector will record the entire session. If machine A becomes unavailable partway through, the session continues on one pre-designated fallback machine (machine B). The study asks whether the roll sequence shows evidence of dependence and whether 7s occur more often in the game phase where they cost a pass-line bettor money. Conclusions apply only to the machine(s) observed during that visit; they do not generalize to other machines, other days, or other venues.

The study does not test whether casinos intentionally respond to bets, whether all bubble-craps machines are fair, or whether a betting strategy is profitable.

## Sample and stopping rule

Formal data collection consists of one machine observed in one session of 1,000 rolls, collected in a single visit. At an expected rate of about 5 rolls per minute, this is roughly 3 hours 20 minutes of logging, or about 4 hours including verification and short breaks. The pilot confirms the rate.

The machine's history display shows roughly the last 20 rolls (the pilot confirms the exact number). The session starts on a come-out roll. Before the first live roll, the collector logs the most recent pre-session roll from the history display as row 0 and confirms it matches the physical dice at rest. If they disagree, the history display is not trusted for that machine until the discrepancy is resolved and documented. Row 0 does not count toward the 1,000 rolls. It gives roll 1 a known predecessor, so the session yields up to 1,000 adjacent pairs for repeat analyses. Each `gap` row removes the pairs on either side of it.

The pilot is excluded from formal analysis. We will not stop early because a result looks significant. Deviations are documented before analysis.

### Fallback machine

Machine A is considered unavailable if it is serviced, its dice are changed, its result display becomes unusable, or the collector cannot get back to it after a break (for example, another player has taken it). Missing rolls alone do not make it unavailable: those are handled by the break rules below, and the collector stays on machine A.

If machine A becomes unavailable, the collector switches once to machine B, chosen by the same machine-selection rule. Logging on machine B:

- uses a new `session_id`, `B_01`;
- starts with its own row 0, read from B's history display and checked against B's physical dice;
- continues live logging on whatever phase B is in.

Rolls on both machines count toward the combined 1,000. The two machines are never treated as one continuous sequence.

The session ends before 1,000 rolls only if:

- machine B also becomes unavailable;
- recording is materially interrupted;
- venue staff instruct the collector to stop.

If the session ends early, the rolls collected so far are analyzed as-is and the shortfall is reported. There is no replacement session.

### Rolls recovered from the history display

A roll the collector did not see live but read from the history display is logged as `recovered_from_history`. This covers row 0, a roll missed during live logging, and rolls that happened during a break. Recovered rows:

- are genuine rolls of the machine, so they are part of the H1/H2 sequence and the total-distribution sanity check;
- count toward the 1,000 rolls, except row 0;
- are logged with phase `unknown`. The preprocessing script reconstructs their phase from the roll sequence (see the preprocessing plan). A recovered row is used in H3 only if its phase can be reconstructed.

### Breaks

The collector may take short breaks, such as a bathroom break, and aims to return before any roll occurs. On return, the collector stays on the same machine. Before the next roll, the collector reads the history display and finds the last rolls they logged:

1. **The last logged rolls are still in the history.** Match the last 3 logged rolls, in order, to a single position in the history. If 3 rolls match more than one position, extend the match until it is unique. Log every roll after that position as `recovered_from_history` with `break` in the notes. No gap is logged and the sequence is unbroken. If no rolls occurred, there is nothing to log.
2. **The last logged rolls are no longer in the history, or no unique match is found.** Rolls were lost. Log one `gap` row with `break` in the notes, then log every roll visible in the history, oldest first, as `recovered_from_history`.

Then resume live logging on whatever phase the machine is in. At about 5 rolls per minute, a 20-roll history covers a break of roughly 3–4 minutes with no lost rolls. Longer breaks are still allowed, but they will create a gap.

### Sample size rationale

The sample size is set by what one collector can record in a single visit, not by a target effect size. The table below gives the approximate smallest effects the design can reliably detect (80% power, fair-dice baselines, no gaps). These figures are for interpreting a non-significant result, not for choosing which test to emphasize.

| Test | Expected under fair, independent dice | Smallest reliably detectable effect |
|---|---|---|
| H1 exact-combination repeats (about 1,000 pairs) | about 51 repeats (5.1%) | about ±1.9 percentage points |
| H2 same-total repeats (about 1,000 pairs) | about 113 repeats (11.3%) | about ±2.8 percentage points |
| H3 7s on point-set vs. come-out rolls (about 704 vs. 296 rolls) | 16.7% in both phases | about +6.4 percentage points |

Smaller real effects may exist and go undetected.

## H1 Primary test Exact-combination dependence

- Null hypothesis: consecutive unordered dice combinations are independent.
- Alternative hypothesis: exact-combination repeats occur at a rate different from that expected under independence.
- Test: two-sided, within-session permutation test at alpha = 0.05.
- Statistic: pooled number of adjacent exact-combination repeats across valid pairs.
- Permutations: shuffle outcomes within each contiguous analysis block separately, 10,000 times. Blocks are separated by `gap` rows (including breaks); never shuffle outcomes across a gap. With no gaps, the whole session is one block.
- Two-sided p-value: calculate the upper and lower permutation-tail p-values with the plus-one correction, then use `min(1, 2 * min(p_lower, p_upper))`.

This test is two-sided because either excess repetition or unusually low repetition would be evidence that the sequence is not memoryless. The test preserves each block's own outcome mix, so a biased but memoryless machine is not automatically called streaky.

## H2 Secondary test Same-total dependence

- Null hypothesis: consecutive totals are independent.
- Alternative hypothesis: same-total repeats occur at a rate different from that expected under independence.
- Test: the same two-sided within-session permutation procedure at alpha = 0.05.
- Gatekeeping: conduct the formal H2 test only if H1 is significant. Otherwise report H2 descriptively without a formal rejection decision.

H1 and H2 address the same broad claim of sequential dependence. Fixed-sequence gatekeeping keeps their shared false-positive risk at 5%.

## H3 Secondary test Badly timed sevens

- Null hypothesis: the probability of a 7 is the same on point-set and come-out rolls.
- Alternative hypothesis: 7s occur more often on point-set rolls.
- Test: one-sided two-proportion z-test at alpha = 0.05.
- Small-count check: also run Fisher's exact test if any 2-by-2 table cell is below 5.
- Sensitivity check: repeat the comparison using only come-out rolls whose previous observed roll was not a 7.

H3 is directional because it evaluates the specific player claim that 7s are more common when they cost a pass-line bet. A lower point-phase 7 rate will still be reported descriptively, but it does not support this stated claim.

H3 is a separate claim from H1/H2. The final report will not combine the tests into one overall statement that the machine is unfair. It will state that H1/H2 and H3 each use alpha = 0.05, so at least one false-positive result across the two claim families is possible at roughly 9.75% if both null hypotheses are true.

## Sanity check Dice-total distribution

Before interpreting repeat rates, run a chi-square goodness-of-fit test comparing the machine's observed totals 2 through 12 with fair-dice probabilities. This check uses alpha = 0.05 and is descriptive of bias, not a prerequisite for H1/H2. If machine B is used, run the check separately for each machine. Run it on machine B only if B has at least 180 rolls, so every expected count is at least 5; otherwise report B's totals descriptively.

If the machine's total distribution differs from fair dice, H1/H2 remain valid because their permutation tests retain the machine's observed distribution. In that case, describe the shuffled permutation distribution rather than presenting 5.1% and 11.3% as the machine's expected repeat rates.

## Effect sizes and reporting

- Report observed repeat rates, permutation baselines, rate differences, p-values, and confidence intervals.
- Report 95% intervals for descriptive estimates using a moving-block bootstrap within the session (block length 50 consecutive rolls, 10,000 resamples, blocks never spanning a gap), not an ordinary independent-pair binomial interval.
- If H1/H2 are non-significant, say "fail to reject the null hypothesis," never "prove the machine is fair."
- Report every pre-specified analysis, corrections, gaps, breaks, early stops, and deviations.
- If machine B is used, H1/H2 permutations stay within each machine's blocks, and H3 pools rolls from both machines. Report results for each machine alongside the pooled results.
- Label comparisons between machines A and B, between early and late parts of the session, individual combinations, shared die faces, and betting-strategy estimates as exploratory.

## DECIDE BEFORE DATA

- Casino and observation date: [fill before formal data collection]
- Session start time: [fill]
- Machine selection procedure for machine A and, if needed, fallback machine B: [fill]
- Final table-minimum stake and bankroll confirmation: [fill]
- Pilot reconciliation rule required before formal collection: [fill]
- Name of the raw logging file and timestamp convention: [fill]
- Whether the venue permits the proposed note-taking procedure: [fill]

