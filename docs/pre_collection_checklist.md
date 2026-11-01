# Pre-Collection Checklist

Complete this checklist together before the first formal roll. Check an item only after the group has agreed on it and recorded the decision below. Items marked *(on site)* are completed at the casino before row 0.

## A. Scope and statistical decisions

- [x] We agree that H1 is the primary result: a **one-sided** test of whether exact-combination repeats occur more often than under independence.
- [x] We agree that H2 is also one-sided (excess same-total repeats) and is formally tested only after a significant H1.
- [x] We agree that H3 is a **one-sided** test of the specific claim that point-set rolls have more 7s than come-out rolls.
- [x] We understand that a non-significant result means “fail to reject,” not “prove fair.”
- [x] We will report H1/H2 as sequential-dependence results and H3 as a phase-association result; we will not combine them into one broad claim that a machine is unfair.
- [x] We agree to use alpha = 0.05 per claim (reject when p ≤ α) with no correction across the repeats and sevens claims, to state the resulting roughly 9.75% overall false-positive risk, and to report whether each significant result would pass the Bonferroni threshold of 0.025 (see "Multiple comparisons" in the preregistration).
- [x] We agree that a Type 2 error (missing a real pattern) is the larger risk in this study, and that significant results will be reported as evidence worth replicating, not proof of rigging.
- [x] We agree that the comparisons of each phase's 7 rate with 1/6 are exploratory, with no reject/fail-to-reject decision.
- [x] We reviewed the assumptions of each test (see "Assumptions" in the preregistration).

## B. Sample and stopping decisions

- [x] We confirm the planned sample: one machine × one session × 1,000 rolls, with one fallback machine only if the first becomes unavailable.
- [x] We understand that conclusions apply only to that machine during that session.
- [x] We confirm that the formal session starts on a come-out roll.
- [x] We agree not to stop early because an observed pattern looks convincing.
- [x] We agree that an early-ended session is analyzed as-is, with no replacement session.
- [x] We agree on the break procedure: if the last 3 logged rolls are uniquely found in the history, recover every later roll with no gap; otherwise log a `GAP`, then the visible history rolls except the 3 oldest.
- [x] We agree to log the most recent pre-session roll from the history as row 0 and check it against the physical dice.
- [x] We agree to stay on machine A after breaks, and to switch once to fallback machine B only if A becomes unavailable (serviced, dice changed, display unusable, or can't get back to it).
- [x] We have chosen the rule for selecting machine A and fallback machine B: random choice by phone random-number generator among machines with an open seat and a working history display (full rule in the preregistration).
- [ ] We have chosen the session date: November 1, 2026. Start time: [fill on site].

## C. Arrival check (replaces the pilot)

- [x] We agree there is no pilot. The roll rate (about 5 rolls/minute) and history display (about 20 rolls) are known from prior observation, giving an expected session of about 3h 20m of logging and about 4h with breaks.
- [ ] *(on site)* Machine A was chosen by the selection rule.
- [ ] *(on site)* Machine A's history display works and matches the physical dice at rest.
- [ ] *(on site)* Number of rolls the history display keeps: [fill on site].

## D. Venue, financial, and privacy checks

- [x] We confirmed the casino: Caesars Virginia.
- [x] We confirmed that phone use is permitted at the machine, so the log can be kept on a phone.
- [x] We confirmed the pass-line table minimum: $3. No bankroll cap is set.
- [x] We will not vary the stake, chase losses, or bet on 2, 3, 11, or 12 as part of the study.
- [x] We will not record names, faces, video, other players’ financial information, or any sensitive information.

## E. Logging readiness

- [x] We reviewed [`data_dictionary.md`](data_dictionary.md) and agree on the raw log (`dice`, `flag`, `phase`, `time`, `notes`) and the derived cleaned fields.
- [ ] We set up a Google Sheet with tabs `A` and `B`, using the headers from [`../data/templates/roll_log_template.csv`](../data/templates/roll_log_template.csv).
- [x] We confirmed the time convention: local clock time, Eastern Standard Time (UTC−05:00) on November 1, 2026, entered only for row 0, gaps, breaks, a machine switch, and the final row.
- [x] We understand that dice may be typed in either order (`34` or `43`); the script sorts them.
- [x] We understand that a missed outcome may be recovered only from the history display, while it is still visible.
- [x] We understand that an unrecoverable outcome is marked `GAP`, never guessed.
- [x] We confirmed storage and backup: the Google Sheets app saves and syncs automatically; after the session each tab is exported unchanged to `data/raw/roll_log_A.csv` (and `roll_log_B.csv`).

## F. GitHub and audit trail

- [x] All agreed protocol documents are committed before formal collection begins.
- [x] The commit hash immediately before formal collection is: `bdd214e`.
- [x] The repository is private and the teammate has access.
- [x] We will retain raw data, cleaned data, scripts, and documented deviations so the final report is reproducible.
- [x] We understand the course requirement that each group member makes at least one pull request; the group will decide work naturally rather than pre-assigning tasks.

## Final sign-off

Formal data collection may begin only when every applicable item above is checked.

Date of sign-off: November 1, 2026

Group members: Nicholas Wang, Cheney Li

