# Does the Bubble Repeat Itself?

## A pre-registered observational study of repeated rolls and badly timed sevens in bubble craps

**Course:** AIPI 510 Project 2  
**Authors:** Cheney Li and Nicholas Wang  
**Status:** Draft for team review. This draft uses the reconciled log and generated results on the proposed correction branch. Confirm all numbers again after the correction and audit-trail pull requests merge.

## Abstract

Players sometimes claim that a bubble-craps machine repeats the same dice outcome or produces more sevens after a point has been established. We observed 1,000 consecutive rolls from one machine during one session and analyzed the data using a pre-registered plan. The primary test asked whether exact unordered dice combinations repeated more often than expected under independence. We observed 43 repeats in 1,000 adjacent pairs (4.30%). A one-sided permutation test gave *p* = 0.8894, so we failed to reject the null hypothesis of no excess exact-combination repeats. We also compared the rate of sevens during the point-set and come-out phases. The point-set rate was 17.38% and the come-out rate was 17.11%. The one-sided two-proportion test gave *p* = 0.4597, so we failed to reject the null hypothesis of equal seven rates across phases. The observed total distribution also did not differ significantly from the fair-dice distribution (*χ*²(10) = 12.59, *p* = 0.2474). These results do not prove that the machine is fair. They show that this single session did not provide evidence for either pre-registered player claim.

## 1. Introduction

Bubble craps is an electronic version of craps in which dice roll inside a transparent chamber. Some players believe that outcomes repeat more often than chance or that sevens occur at especially unfavorable times. These claims can be separated into testable statistical questions.

This study examines one machine during one observed session. It does not test whether all bubble-craps machines are fair. It also does not test whether a casino intentionally changes outcomes in response to bets. Our conclusions apply only to the observed machine and session.

We pre-registered two player claims before formal data collection:

1. **H1, primary claim:** Exact unordered dice combinations repeat on consecutive rolls more often than expected if rolls are independent.
2. **H3, secondary claim:** Sevens occur more often after a point is established than during come-out rolls.

We also planned a descriptive fair-dice check and a gated secondary analysis of repeated totals. The total-repeat analysis would receive a formal test only if H1 was significant.

## 2. Methods

### 2.1 Study design and sample

This was a pre-registered observational study. One collector observed one bubble-craps machine in a single session at Caesars Virginia on November 1, 2026. The planned and achieved sample was 1,000 counted rolls. A pre-session history-display entry, called row 0, supplied the predecessor for roll 1 but did not count toward the sample size.

The study used a convenience sample. Therefore, the results describe this machine during this session. They should not be generalized to other machines, dates, casinos, or venues.

### 2.2 Data recording and cleaning

The collector recorded the two dice, flag, game phase, time, and notes in a Google Sheet. The analysis pipeline preserved an initial export and created a reconciled log for a documented recording correction. The final cleaned dataset contained 1,001 rows: row 0 plus 1,000 counted rolls.

The validation process found no gaps, no phase mismatches, and no use of a fallback machine. One outcome was corrected using session video: roll 853 was recorded as 5-5 but verified as 4-4. This correction did not change the H1 or H2 repeat counts. It changed the reconstructed phase of three later non-seven rolls. The raw discrepancy and the correction are documented in `docs/deviations.md`.

### 2.3 Statistical analyses

All analyses followed the pre-registered plan. The code used a fixed random seed of 20261101, 10,000 permutations, and 10,000 bootstrap resamples.

For H1, we used a one-sided within-session permutation test. The test shuffled the observed outcomes within the continuous session and counted exact-combination repeats. This preserves the machine's observed outcome distribution while removing serial dependence. The alternative hypothesis was that repeats occur more often than expected under independence.

For H3, we used a one-sided two-proportion *z*-test. The test compared the proportion of sevens on point-set rolls with the proportion on come-out rolls. The alternative hypothesis was that the point-set seven rate is higher.

We used *α* = 0.05 for each of the two separate claims. We did not apply a Bonferroni correction across H1/H2 and H3. The plan reports the resulting family-wise false-positive risk of about 9.75% when both claims are null. H2 was gated behind H1, so it is reported descriptively because H1 was not significant.

Because dice outcomes are categorical, a *t*-test was not appropriate. For the descriptive total-distribution check, we used a chi-square goodness-of-fit test against the expected distribution of two fair dice.

## 3. Results

### 3.1 Descriptive results and data quality

The dataset contained 1,000 counted rolls from machine A. The mean total was 7.04, compared with the fair-dice mean of 7.00. The median and mode were both 7. The standard deviation was 2.46, compared with 2.42 for fair dice. The sample contained 298 come-out rolls and 702 point-set rolls.

The total distribution did not differ significantly from fair dice, *χ*²(10) = 12.59, *p* = 0.2474. This result is a descriptive sanity check. It does not establish that the rolls were independent.

### 3.2 H1: Excess exact-combination repeats

Among 1,000 valid adjacent pairs, 43 pairs repeated the same unordered dice combination. The observed repeat rate was 4.30% (95% moving-block bootstrap CI: 3.43% to 5.53%). The permutation baseline was 5.10%, so the observed rate was 0.80 percentage points lower than the baseline.

The one-sided permutation test gave *p* = 0.8894. We therefore failed to reject the null hypothesis. The data did not provide evidence that exact combinations repeated more often than expected under independence.

### 3.3 H2: Repeated totals

The data contained 113 same-total repeats in 1,000 adjacent pairs (11.30%). The permutation baseline was 11.08%, a difference of 0.22 percentage points. Because H1 was not significant, the pre-registered gatekeeping rule prevented a formal H2 decision. We report this result only as descriptive information.

### 3.4 H3: Badly timed sevens

There were 122 sevens in 702 point-set rolls (17.38%) and 51 sevens in 298 come-out rolls (17.11%). The estimated difference was 0.26 percentage points, with a 95% moving-block bootstrap CI from -3.93 to 3.42 percentage points.

The one-sided two-proportion test gave *z* = 0.10 and *p* = 0.4597. We therefore failed to reject the null hypothesis. The data did not provide evidence that sevens were more common during the point-set phase.

As a sensitivity check, we removed come-out rolls that immediately followed a seven. The estimated difference became 2.98 percentage points and the one-sided *p*-value was 0.2066. This sensitivity analysis led to the same conclusion.

### 3.5 Exploratory seven-rate checks

The point-set seven rate was not significantly above the fair rate of one-sixth in the exploratory exact binomial test (*p* = 0.3211). The come-out seven rate was also not significantly above one-sixth (*p* = 0.4418). These exploratory results help interpret H3, but they do not make a confirmatory claim.

## 4. Discussion

This study found no evidence for either pre-registered player claim in the observed session. Exact dice combinations did not repeat more often than the permutation baseline. Sevens also did not occur more often after a point was set than during come-out rolls.

The study also did not find a significant difference between the observed total distribution and the distribution of two fair dice. That check should be interpreted carefully. A non-significant result does not prove that the machine is fair, independent, or free of bias. It only indicates that this sample did not show a statistically detectable departure under the specified test.

The sample size limits what the study could detect. Before data collection, the power analysis showed that 1,000 rolls had about 80% power to detect an exact-combination repeat rate of roughly 6.8%, compared with an expected rate of about 5.1%. For H3, the study could reliably detect a point-set seven rate about 6.4 percentage points higher than the come-out rate. Smaller effects may exist but remain undetected.

This study has several limitations. It used one machine, one session, and a convenience sample. The collector recorded the data manually. Although the project preserved the original export and documented a video-verified correction, manual recording can still introduce measurement error. Finally, the phase comparison is observational. It can describe an association between phase and seven frequency, but it cannot establish intent or causation.

## 5. Conclusion

For this machine and session, the data did not support the claim that exact dice combinations repeated more often than expected under independence. The data also did not support the claim that sevens occurred more often during the point-set phase. These results should be reported as failures to reject the pre-registered null hypotheses, not as proof that bubble-craps machines are fair.

## References and reproducibility

The pre-registered protocol, cleaning rules, raw-data audit trail, analysis scripts, automated tests, and generated outputs are stored in the project repository. Key files include:

- `docs/preregistration.md`
- `docs/deviations.md`
- `results/validation_summary.md`
- `results/analysis_report.md`
- `scripts/prepare_data.py`
- `scripts/analyze.py`

Before submitting the final report, the team should confirm the merged version of the correction and audit-trail pull requests, then regenerate the validation and analysis outputs once from the final `main` branch.
