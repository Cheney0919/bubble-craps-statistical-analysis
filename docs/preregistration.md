# Preregistration

## Scope

This is an observational study of one physical bubble-craps machine (machine A), observed in a single formal session. One collector will record the entire session. If machine A becomes unavailable partway through, the session continues on one pre-designated fallback machine (machine B). The study tests two player claims: that the same dice combination comes up again on the next roll more often than chance (and, by extension, the same total), and that 7s occur more often in the game phase where they cost a pass-line bettor money. Conclusions apply only to the machine(s) observed during that visit; they do not generalize to other machines, other days, or other venues.

The study does not test whether casinos intentionally respond to bets, whether all bubble-craps machines are fair, or whether a betting strategy is profitable.

### Sampling

This is a convenience sample, a form of non-probability sampling: one casino, one day, chosen because it is accessible to the collector. Machine A is chosen at random from the qualifying machines available on arrival, which avoids picking a machine for how it seems to be rolling, but that random choice covers only the machines at this casino on this day. The sample is therefore the sequence of rolls from the observed machine(s) during the session, and conclusions describe that machine and session, not bubble-craps machines in general.

## Sample and stopping rule

Formal data collection consists of one machine observed in one session of 1,000 rolls, collected in a single visit. At an expected rate of about 5 rolls per minute, this is roughly 3 hours 20 minutes of logging, or about 4 hours including verification and short breaks. The collection visit is to Caesars Virginia on November 1, 2026.

The machine's history display shows roughly the last 20 rolls (the exact number is noted at the arrival check). The session starts on a come-out roll. Before the first live roll, the collector logs the most recent pre-session roll from the history display as row 0 and confirms it matches the physical dice at rest. If they disagree, the history display is not trusted for that machine until the discrepancy is resolved and documented. Row 0 does not count toward the 1,000 rolls. It gives roll 1 a known predecessor, so the session yields up to 1,000 adjacent pairs for repeat analyses. Each `gap` row removes the pairs on either side of it.

There is no pilot. The collector's prior observation of the machine already established the roll rate and history display. A short on-arrival check, with nothing recorded, confirms the display works before row 0 (see the field protocol). We will not stop early because a result looks significant. Deviations are documented before analysis.

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

A roll the collector did not see live but read from the history display is flagged `R` in the raw log (`recovered_from_history` in the cleaned data). This covers row 0, a roll missed during live logging, and rolls that happened during a break. Recovered rows:

- are genuine rolls of the machine, so they are part of the H1/H2 sequence and the total-distribution sanity check;
- count toward the 1,000 rolls, except row 0;
- have no phase entered. The preprocessing script reconstructs the phase of every roll from the roll sequence (see the preprocessing plan). A roll is used in H3 only if its phase can be determined.

### Breaks

The collector may take short breaks, such as a bathroom break, and aims to return before any roll occurs. On return, the collector stays on the same machine. Before the next roll, the collector reads the history display and finds the last rolls they logged:

1. **The last logged rolls are still in the history.** Match the last 3 logged rolls, in order, to a single position in the history. If 3 rolls match more than one position, extend the match until it is unique. Log every roll after that position, flagged `R`. No gap is logged and the sequence is unbroken. If no rolls occurred, there is nothing to log.
2. **The last logged rolls are no longer in the history, or no unique match is found.** Rolls were lost. Log one `GAP` row with `break` in the notes, then log the rolls visible in the history, oldest first, flagged `R`, skipping the 3 oldest. If fewer than 3 of the last logged rolls are visible, any that are can only be among the 3 oldest, so skipping them guarantees no roll is logged twice.

Then resume live logging on whatever phase the machine is in. At about 5 rolls per minute, a 20-roll history covers a break of roughly 3–4 minutes with no lost rolls. Longer breaks are still allowed, but they will create a gap.

### Power analysis

A power analysis links four quantities: effect size, sample size, significance level, and power. Fixing any three determines the fourth. Here the sample size is fixed at 1,000 rolls by what one collector can record in a single visit, α is 0.05 per claim, and power is set to the conventional 80%. The analysis therefore solves for the **smallest effect each test can reliably detect**.

No pilot study is needed to estimate effect sizes. A pilot is normally used to estimate the baseline and the expected effect, but here the baselines under the null hypothesis are known exactly from probability (fair, independent dice), and the question is which departures from them the study can detect.

| Test | Expected under fair, independent dice | Smallest reliably detectable value |
|---|---|---|
| H1 exact-combination repeats (about 1,000 pairs) | 5.1% (about 51 repeats) | about 6.8% (+1.7 percentage points) |
| H2 same-total repeats (about 1,000 pairs) | 11.3% (about 113 repeats) | about 13.8% (+2.5 percentage points) |
| H3 7s on point-set vs. come-out rolls (about 704 vs. 296 rolls) | 16.7% in both phases | point-set rate about 6.4 percentage points higher |
| Exploratory: point-set 7s vs. 1/6 (about 704 rolls) | 16.7% | about 20.2% |

These figures use the normal approximation with one-sided tests, 80% power, and no gaps. Smaller real effects may exist and go undetected: a non-significant result means the study could not detect an effect of this size, not that there is no effect. The report states these limits.

## H1 Primary test Excess exact-combination repeats

- Null hypothesis: consecutive unordered dice combinations are independent.
- Alternative hypothesis: exact-combination repeats occur more often than expected under independence.
- Test: one-sided (upper-tail), within-session permutation test at alpha = 0.05.
- Statistic: pooled number of adjacent exact-combination repeats across valid pairs.
- Permutations: shuffle outcomes within each contiguous analysis block separately, 10,000 times. Blocks are separated by `gap` rows (including breaks); never shuffle outcomes across a gap. With no gaps, the whole session is one block.
- One-sided p-value: `(1 + number of permutations with at least as many repeats as observed) / (10,000 + 1)`, the upper-tail plus-one correction.

H1 tests the original player claim: the same dice combination tends to come up again on the next roll. The test is one-sided for three reasons:

- the claim is directional;
- excess repeats are what a physical fault such as dice not tumbling properly in the bubble would produce;
- only excess repeats could be exploited by a betting strategy.

An unusually low repeat rate would be reported descriptively, but it does not support the stated claim and is not formally tested.

**Why a permutation test rather than a binomial test.** Under fair, independent dice the number of repeats is roughly binomial, but consecutive pairs share a roll (pair 1–2 and pair 2–3 both contain roll 2), so they are not independent trials. The permutation test is a Monte Carlo simulation of the null hypothesis that avoids this. It shuffles the observed rolls 10,000 times, which destroys any dependence between consecutive rolls while keeping exactly the same set of outcomes, and counts repeats in each shuffle. The p-value is the share of shuffles with at least as many repeats as observed. Because it shuffles the machine's own rolls rather than simulating fair dice, a machine that is biased (for example, rolls too many 7s) but has no memory is not mistaken for a streaky one.

## H2 Secondary test Excess same-total repeats

- Null hypothesis: consecutive totals are independent.
- Alternative hypothesis: same-total repeats occur more often than expected under independence.
- Test: the same one-sided (upper-tail) within-session permutation procedure at alpha = 0.05.
- Gatekeeping: conduct the formal H2 test only if H1 is significant. Otherwise report H2 descriptively without a formal rejection decision.

H2 extends the H1 claim to totals, which is what matters for betting: bets pay on totals, not on exact dice faces. It is directional for the same reasons as H1. Because H2 is a follow-up to the same streakiness claim, fixed-sequence gatekeeping keeps their shared false-positive risk at 5%: totals are formally tested only once excess exact repeats have been shown.

## H3 Secondary test Badly timed sevens

- Null hypothesis: the probability of a 7 is the same on point-set and come-out rolls.
- Alternative hypothesis: 7s occur more often on point-set rolls.
- Test: one-sided two-proportion z-test at alpha = 0.05, on the 2×2 table of phase (point set, come-out) by outcome (7, not 7). This is the one-sided version of the chi-square test of independence for a 2×2 table: z² equals that test's chi-square statistic without a continuity correction. `scipy.stats.chi2_contingency` is two-sided only and applies Yates' continuity correction by default (`correction=True`), so the z form is used, with no continuity correction.
- Small-count check: if any **expected** cell count (row total × column total / grand total) is below 5, also run a one-sided Fisher's exact test, and the Fisher p-value decides H3.
- Sensitivity check: repeat the comparison keeping all point-set rolls but only come-out rolls whose previous roll in the same analysis block exists and was not a 7.
- Eligible rolls: counted rolls (not row 0 or `GAP` rows) whose phase is known.

H3 is directional because it evaluates the specific player claim that 7s are more common when they cost a pass-line bet. A lower point-phase 7 rate will still be reported descriptively, but it does not support this stated claim.

H3 compares the two phases rather than comparing point-set 7s with the fair rate of 1/6. A comparison with 1/6 would be more sensitive, but a machine that rolls too many 7s in every phase would pass it; only the two-phase comparison tests the claim that 7s come at the *worst* time. The comparison with 1/6 is kept as an exploratory analysis below.

H3 is a separate claim from H1/H2. The final report will not combine the tests into one overall statement that the machine is unfair. See "Multiple comparisons" below.

## Exploratory 7 rate in each phase vs. 1/6

For each phase (point set and come-out), a one-sided exact binomial test of whether the 7 rate exceeds the fair rate of 1/6 (`scipy.stats.binomtest`, `alternative="greater"`), on the same eligible rolls as H3. These are exploratory: they are reported with rates and p-values but no reject/fail-to-reject decision, and they are not part of any confirmatory claim. They help interpret H3:

| Point set vs. 1/6 | Come-out vs. 1/6 | Suggests |
|---|---|---|
| High | Normal | 7s concentrated when they cost a pass-line bettor: supports the timing claim |
| High | High | Too many 7s overall: bias rather than timing (the fair-dice check should agree) |
| Normal | Normal | Nothing unusual about 7s |

## Multiple comparisons

The study tests two separate player claims: that consecutive rolls repeat (H1, extended to totals in H2), and that 7s come at the worst time for a pass-line bettor (H3). Each claim is its own research question, answered by its own test, and the report draws a separate conclusion for each. It never combines them into a single claim that the machine is unfair.

- **Within a claim, multiplicity is controlled.** H1 and H2 address the same claim, so H2 is tested only if H1 is significant. This keeps that claim's false-positive risk at 5%.
- **Across the two claims, no correction is applied.** Each claim is tested at α = 0.05. A Bonferroni correction (α = 0.025 per claim) would raise the smallest detectable effect from 6.8% to 7.0% for H1 and from +6.4 to +7.2 percentage points for H3. In a study already fixed at 1,000 rolls, we chose to keep each claim's sensitivity instead.
- **The cost is stated openly.** If both claims are false, the chance that at least one is declared significant is about 9.75% (1 − 0.95²). The report gives exact p-values and notes whether each significant result would also pass the Bonferroni threshold of 0.025, so a reader can apply the stricter standard.
- **Not counted:** the fair-dice sanity check is descriptive. It supports interpretation of the claims and is not itself a claim. The exploratory 1/6 comparisons carry no decision, so they are not counted either.

## Type 1 and Type 2 errors

A Type 1 error would mean concluding the machine repeats rolls or times its 7s badly when it is actually fair. A Type 2 error would mean missing a pattern that is really there. With the sample fixed at 1,000 rolls, the larger risk in this study is a Type 2 error: an underpowered test reporting "fail to reject" for a machine that does have a modest effect. We therefore favor sensitivity: one-sided tests of the directional claims, and α = 0.05 per claim without a correction across claims. We limit the cost of a Type 1 error through how results are stated: a significant result is reported as evidence of a pattern on this machine, worth replicating, never as proof the machine is rigged, and the report notes whether it would also pass the stricter Bonferroni threshold.

## Sanity check Dice-total distribution

Before interpreting repeat rates, run a chi-square goodness-of-fit test comparing the machine's observed totals 2 through 12 with fair-dice probabilities. This check uses alpha = 0.05 and is descriptive of bias, not a prerequisite for H1/H2. If machine B is used, run the check separately for each machine. Run it on machine B only if B has at least 180 rolls, so every expected count is at least 5; otherwise report B's totals descriptively.

If the machine's total distribution differs from fair dice, H1/H2 remain valid because their permutation tests retain the machine's observed distribution. In that case, describe the shuffled permutation distribution rather than presenting 5.1% and 11.3% as the machine's expected repeat rates.

## Assumptions

Every test's assumptions are checked or justified before results are interpreted. The outcomes are categorical (dice totals, combinations, 7 or not), so the tests are categorical-data tests. t-tests compare means of continuous measurements and do not apply.

| Test | Assumptions | How they are met |
|---|---|---|
| Chi-square goodness of fit (sanity check) | Independent observations; mutually exclusive categories; every expected count at least 5 | Each roll has exactly one total. With about 1,000 rolls the smallest expected count (totals 2 and 12) is about 28; machine B is tested only with at least 180 rolls. Independence is what H1/H2 test; if they find dependence, the chi-square p-value is read with caution. |
| Permutation tests (H1, H2) | Under the null, every ordering of the rolls within a block is equally likely (exchangeability) | This is exactly what "independent rolls" means. No normality assumption and no assumption that the dice are fair. Shuffles never cross a gap or a machine switch. |
| Two-proportion z-test (H3) | Independent observations; large enough samples for the normal approximation; mutually exclusive categories | Under the null, rolls are independent. Each roll is in exactly one phase and is either a 7 or not. If any expected cell is below 5, Fisher's exact test, which needs no approximation, decides instead. The sensitivity check removes come-out rolls right after a 7, in case 7s cluster. |
| Exact binomial tests (exploratory) | A fixed number of independent trials with a constant probability of success under the null | Rolls in each phase, each a 7 or not, with probability 1/6 under fair dice. |
| 95% intervals | The textbook z/t interval assumes independent observations | Rolls are time-ordered, and possible dependence is exactly what the study asks about, so intervals use a moving-block bootstrap, which keeps runs of consecutive rolls together. |

## Effect sizes and reporting

- Begin with descriptive statistics, before any test: frequency tables of totals and dice combinations (observed vs. expected), the mean, median, mode, and standard deviation of totals against their fair-dice values, the split of rolls between phases, data-quality counts, and a histogram of totals with fair-dice expected counts marked.
- Report observed repeat rates, permutation baselines, rate differences, p-values, and confidence intervals.
- Report 95% intervals for descriptive estimates using a moving-block bootstrap within the session, not an ordinary independent-pair binomial interval:
  - windows of 50 consecutive rolls, drawn with replacement from inside analysis blocks so they never span a gap or machine;
  - an analysis block shorter than 50 rolls is used whole;
  - each resample draws ceil(n / 50) windows, 10,000 resamples, percentile intervals.
- If H1/H2 are non-significant, say "fail to reject the null hypothesis," never "prove the machine is fair."
- Report every pre-specified analysis, corrections, gaps, breaks, early stops, and deviations.
- If machine B is used, H1/H2 permutations stay within each machine's blocks, and H3 pools rolls from both machines. Report results for each machine alongside the pooled results.
- Label comparisons between machines A and B, between early and late parts of the session, individual combinations, shared die faces, and betting-strategy estimates as exploratory.

## Fixed analysis settings

The analysis is implemented in `scripts/analyze.py` and was written and tested on simulated logs before any data were collected.

- **Significance:** a test is significant when p ≤ 0.05 (reject the null hypothesis). For reference only, each significant result also reports whether p ≤ 0.025, the Bonferroni threshold across the two claims.
- **Randomness:** all permutations and bootstrap resamples use the fixed random seed 20261101, so the results are exactly reproducible.
- **Permutations:** 10,000. H1 and H2 use the same shuffled row orders, with combination and total shuffled together.
- **Bootstrap:** 10,000 resamples, as described above.

## DECIDE BEFORE DATA

- **Casino and observation date:** Caesars Virginia, November 1, 2026.
- **Session start time:** [fill on site, from row 0's `time`]
- **Machine selection procedure:** on arrival, number every bubble-craps machine with an open seat and a working history display that matches its physical dice. Choose machine A with a phone random-number generator. If a fallback is needed, choose machine B the same way from the remaining qualifying machines. If only one machine qualifies, it is machine A and there is no fallback; if it becomes unavailable, the session ends early.
- **Stake:** $3 pass-line table minimum on every bet. No bankroll cap is set.
- **Pilot:** none; replaced by the on-arrival check in the field protocol.
- **Raw logging files:** a Google Sheet on the collector's phone, one tab per machine, exported unchanged after the session to `data/raw/roll_log_A.csv` (and `data/raw/roll_log_B.csv` if used). Google Sheets' cloud sync and version history serve as the backup.
- **Time convention:** local clock time, entered only for row 0, `GAP` rows, breaks, a machine switch, and the final row. All times on November 1, 2026 are Eastern Standard Time (UTC−05:00); daylight saving time ends at 2:00 AM that morning.
- **Venue rules:** phone use at the machine is permitted, so logging on a phone is allowed.

