# Pre-Collection Checklist

Complete this checklist together before the first formal roll. Check an item only after the group has agreed on it and recorded the decision below. The pilot does not count toward the final 2,000 rolls.

## A. Scope and statistical decisions

- [ ] We agree that H1 is the primary result: a **two-sided** test of whether exact-combination repeats differ from independence.
- [ ] We agree that H2 is also two-sided but is formally tested only after a significant H1.
- [ ] We agree that H3 is a **one-sided** test of the specific claim that point-set rolls have more 7s than come-out rolls.
- [ ] We understand that a non-significant result means “fail to reject,” not “prove fair.”
- [ ] We will report H1/H2 as sequential-dependence results and H3 as a phase-association result; we will not combine them into one broad claim that a machine is unfair.
- [ ] We agree to use alpha = 0.05 for H1/H2 and alpha = 0.05 for H3, and to state the resulting roughly 9.75% study-wide false-positive risk across those two claim families.

## B. Sample and stopping decisions

- [ ] We confirm the planned sample: two machines × eight sessions per machine × 125 rolls per session = 2,000 rolls.
- [ ] We confirm that every formal session starts on a come-out roll.
- [ ] We agree not to stop early because an observed pattern looks convincing.
- [ ] We have decided how to replace an interrupted session, if replacement is practical.
- [ ] We have chosen the rule for selecting two machines when more than two are available: [write rule here].
- [ ] We have chosen the rule for selecting session times from mutual availability: [write rule here].

## C. Pilot requirements

- [ ] The collector completed an approximately 50-roll pilot.
- [ ] We recorded the pilot date, machine, duration, and whether a history display was available.
- [ ] We reconciled the pilot log against the machine history display and documented every discrepancy.
- [ ] We decided the maximum number of unreconciled pilot discrepancies allowed before formal collection: [write rule here].
- [ ] We confirmed that 125 rolls is practically achievable in one session.
- [ ] We confirmed that one collector can record the required machine sessions sequentially and estimated the total collection time.
- [ ] We confirmed how many recent outcomes the history display retains and whether checking every 10 rolls is feasible.

## D. Venue, financial, and privacy checks

- [ ] We confirmed the casino and physical machine location: [write here].
- [ ] We confirmed that the venue permits ordinary note-taking and checked whether phone/video rules affect the protocol.
- [ ] We confirmed the pass-line table minimum: $[write amount].
- [ ] We confirmed a per-person bankroll cap: $[write amount].
- [ ] We will not vary the stake, chase losses, or bet on 2, 3, 11, or 12 as part of the study.
- [ ] We will not record names, faces, video, other players’ financial information, or any sensitive information.

## E. Logging readiness

- [ ] We reviewed [`data_dictionary.md`](data_dictionary.md) and agree on every field.
- [ ] We copied [`../data/templates/roll_log_template.csv`](../data/templates/roll_log_template.csv) into `data/raw/roll_log.csv` without changing its column names.
- [ ] We confirmed a single timestamp convention: [for example, local Eastern Time in ISO format].
- [ ] We confirmed that dice are recorded in ascending order, such as `3-4`, never `4-3`.
- [ ] We understand that a missed outcome may be recovered only from the machine history display.
- [ ] We understand that an unrecoverable outcome is marked `gap`, never guessed.
- [ ] We decided where the active log will be stored during a session and how it will be backed up: [write here].

## F. GitHub and audit trail

- [ ] All agreed protocol documents are committed before formal collection begins.
- [ ] The commit hash immediately before formal collection is: [write here].
- [ ] The repository is private and the teammate has access.
- [ ] We will retain raw data, cleaned data, scripts, and documented deviations so the final report is reproducible.
- [ ] We understand the course requirement that each group member makes at least one pull request; the group will decide work naturally rather than pre-assigning tasks.

## Final sign-off

Formal data collection may begin only when every applicable item above is checked.

Date of sign-off: [fill]

Group members: [fill]

