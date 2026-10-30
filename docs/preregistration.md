# Preregistration

## Scope

This is an observational study of two physical bubble-craps machines. One collector will record every formal session. The study asks whether roll sequences show evidence of dependence and whether 7s occur more often in the game phase where they cost a pass-line bettor money. Conclusions apply only to the selected machines during the observed sessions.

The study does not test whether casinos intentionally respond to bets, whether all bubble-craps machines are fair, or whether a betting strategy is profitable.

## Sample and stopping rule

Formal data collection consists of two machines, eight sessions per machine, and 125 rolls per session: 2,000 rolls total. The single collector records sessions on one machine at a time; the machines are not observed in parallel. Each session starts on a come-out roll. The 16 first rolls have no previous roll, leaving 1,984 adjacent pairs for repeat analyses.

The pilot is excluded from formal analysis. We will not stop early because a result looks significant. A session may end only for machine service, changed dice, unusable result display, material recording interruption, or venue/staff instruction. Deviations and replacement sessions are documented before analysis.

## H1 Primary test Exact-combination dependence

- Null hypothesis: consecutive unordered dice combinations are independent.
- Alternative hypothesis: exact-combination repeats occur at a rate different from that expected under independence.
- Test: two-sided, within-session permutation test at alpha = 0.05.
- Statistic: pooled number of adjacent exact-combination repeats across valid pairs.
- Permutations: shuffle outcomes within each machine-session separately 10,000 times. Never shuffle across machines or sessions.
- Two-sided p-value: calculate the upper and lower permutation-tail p-values with the plus-one correction, then use `min(1, 2 * min(p_lower, p_upper))`.

This test is two-sided because either excess repetition or unusually low repetition would be evidence that the sequence is not memoryless. The test preserves each session's own outcome mix, so a biased but memoryless machine is not automatically called streaky.

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

Before interpreting repeat rates, run a chi-square goodness-of-fit test separately for each machine, comparing observed totals 2 through 12 with fair-dice probabilities. This check uses alpha = 0.05 and is descriptive of bias, not a prerequisite for H1/H2.

If a machine's total distribution differs from fair dice, H1/H2 remain valid because their permutation tests retain that machine's observed distribution. In that case, describe the shuffled permutation distribution rather than presenting 5.1% and 11.3% as the machine's expected repeat rates.

## Effect sizes and reporting

- Report observed repeat rates, permutation baselines, rate differences, p-values, and confidence intervals.
- Report 95% intervals for descriptive estimates using a session-block bootstrap, not an ordinary independent-pair binomial interval.
- If H1/H2 are non-significant, say "fail to reject the null hypothesis," never "prove the machine is fair."
- Report every pre-specified analysis, corrections, gaps, early stops, and deviations.
- Label comparisons between machines, sessions, individual combinations, shared die faces, and betting-strategy estimates as exploratory.

## DECIDE BEFORE DATA

- Casino and observation dates: [fill before formal data collection]
- Method for randomly choosing session times from available windows: [fill]
- Machine selection procedure if more than two qualifying machines are available: [fill]
- Final table-minimum stake and bankroll confirmation: [fill]
- Pilot reconciliation rule required before formal collection: [fill]
- Name of the raw logging file and timestamp convention: [fill]
- Whether the venue permits the proposed note-taking procedure: [fill]

