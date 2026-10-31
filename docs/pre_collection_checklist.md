# Pre-Collection Checklist

Complete this checklist together before the first formal roll. Check an item only after the group has agreed on it and recorded the decision below. Items marked *(on site)* are completed at the casino before row 0.

## A. Scope and statistical decisions

- [ ] We agree that H1 is the primary result: a **one-sided** test of whether exact-combination repeats occur more often than under independence.
- [ ] We agree that H2 is also one-sided (excess same-total repeats) and is formally tested only after a significant H1.
- [ ] We agree that H3 is a **one-sided** test of the specific claim that point-set rolls have more 7s than come-out rolls.
- [ ] We understand that a non-significant result means “fail to reject,” not “prove fair.”
- [ ] We will report H1/H2 as sequential-dependence results and H3 as a phase-association result; we will not combine them into one broad claim that a machine is unfair.
- [ ] We agree to use alpha = 0.05 for H1/H2 and alpha = 0.05 for H3, and to state the resulting roughly 9.75% study-wide false-positive risk across those two claim families.

## B. Sample and stopping decisions

- [ ] We confirm the planned sample: one machine × one session × 1,000 rolls, with one fallback machine only if the first becomes unavailable.
- [ ] We understand that conclusions apply only to that machine during that session.
- [ ] We confirm that the formal session starts on a come-out roll.
- [ ] We agree not to stop early because an observed pattern looks convincing.
- [ ] We agree that an early-ended session is analyzed as-is, with no replacement session.
- [ ] We agree on the break procedure: if the last 3 logged rolls are uniquely found in the history, recover every later roll with no gap; otherwise log a `gap`, then every visible history roll.
- [ ] We agree to log the most recent pre-session roll from the history as row 0 and check it against the physical dice.
- [ ] We agree to stay on machine A after breaks, and to switch once to fallback machine B only if A becomes unavailable (serviced, dice changed, display unusable, or can't get back to it).
- [ ] We have chosen the rule for selecting machine A and fallback machine B: random choice by phone random-number generator among machines with an open seat and a working history display (full rule in the preregistration).
- [ ] We have chosen the session date: November 1, 2026. Start time: [fill on site].

## C. Arrival check (replaces the pilot)

- [ ] We agree there is no pilot. The roll rate (about 5 rolls/minute) and history display (about 20 rolls) are known from prior observation, giving an expected session of about 3h 20m of logging and about 4h with breaks.
- [ ] *(on site)* Machine A was chosen by the selection rule.
- [ ] *(on site)* Machine A's history display works and matches the physical dice at rest.
- [ ] *(on site)* Number of rolls the history display keeps: [fill on site].

## D. Venue, financial, and privacy checks

- [ ] We confirmed the casino: Caesars Virginia.
- [ ] We confirmed that phone use is permitted at the machine, so the log can be kept on a phone.
- [ ] We confirmed the pass-line table minimum: $3. No bankroll cap is set.
- [ ] We will not vary the stake, chase losses, or bet on 2, 3, 11, or 12 as part of the study.
- [ ] We will not record names, faces, video, other players’ financial information, or any sensitive information.

## E. Logging readiness

- [ ] We reviewed [`data_dictionary.md`](data_dictionary.md) and agree on the raw log (`dice`, `flag`, `phase`, `time`, `notes`) and the derived cleaned fields.
- [ ] We set up a Google Sheet with tabs `A` and `B`, using the headers from [`../data/templates/roll_log_template.csv`](../data/templates/roll_log_template.csv).
- [ ] We confirmed the time convention: local clock time, Eastern Standard Time (UTC−05:00) on November 1, 2026, entered only for row 0, gaps, breaks, a machine switch, and the final row.
- [ ] We understand that dice may be typed in either order (`34` or `43`); the script sorts them.
- [ ] We understand that a missed outcome may be recovered only from the history display, while it is still visible.
- [ ] We understand that an unrecoverable outcome is marked `GAP`, never guessed.
- [ ] We confirmed storage and backup: the Google Sheets app saves and syncs automatically; after the session each tab is exported unchanged to `data/raw/roll_log_A.csv` (and `roll_log_B.csv`).

## F. GitHub and audit trail

- [ ] All agreed protocol documents are committed before formal collection begins.
- [ ] The commit hash immediately before formal collection is: [fill before row 0].
- [ ] The repository is private and the teammate has access.
- [ ] We will retain raw data, cleaned data, scripts, and documented deviations so the final report is reproducible.
- [ ] We understand the course requirement that each group member makes at least one pull request; the group will decide work naturally rather than pre-assigning tasks.

## Final sign-off

Formal data collection may begin only when every applicable item above is checked.

Date of sign-off: [fill]

Group members: Nicholas Wang, Cheney Li

