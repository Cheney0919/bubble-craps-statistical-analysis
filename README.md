# Bubble Craps Statistical Analysis

This repository contains the pre-registered protocol, data dictionary, and field procedures for an observational study of two physical bubble-craps machines.

## Study question

The primary question is whether consecutive dice outcomes show evidence of dependence. We test whether exact unordered dice combinations repeat either more **or less** often than expected if rolls are independent. A separate, directional secondary question asks whether 7s occur more often after a point is set than on come-out rolls.

The study concerns only the two observed machines during the recorded sessions. It cannot establish that all bubble-craps machines are fair or unfair, or that a casino intentionally changes outcomes.

## Repository layout

```text
data/raw/          Original logs. Never overwrite or silently edit these files.
data/cleaned/      Cleaned analysis-ready data after collection.
docs/              Protocol, field rules, preprocessing plan, and data dictionary.
scripts/           Analysis scripts added after the final data format is confirmed.
results/           Generated tables, figures, and analysis summaries.
```

## Before any formal data collection

1. Read and agree on [`docs/preregistration.md`](docs/preregistration.md).
2. Run the pilot described in [`docs/field_protocol.md`](docs/field_protocol.md).
3. Complete every `DECIDE BEFORE DATA` item in the preregistration.
4. Commit the final protocol before the first formal roll is recorded.

## Collaboration record

The course requires branches, pull requests, and at least one pull request from each group member. The group may decide organically which work each person performs; this repository does not pre-assign roles.

