# Hotel No-Show Codex Docs Pack

This folder contains a starter markdown pack for Codex-driven development of a hotel no-show prediction system.

## Files
- `AGENTS.md` — repo-wide durable guidance for Codex
- `PLANS.md` — execution plan for long-running tasks
- `docs/feature-policy.md` — leakage and feature-availability policy
- `docs/data-mapping.md` — raw-to-clean mapping and target rules
- `docs/modeling-plan.md` — modeling objective, baseline sequence, metrics, and CatBoost guidance
- `docs/backlog.md` — implementation sequence
- `docs/acceptance-criteria.md` — done criteria by module

## How to use with Codex
1. Put these files at the root of your repository.
2. Add your actual codebase around them.
3. Start Codex in the repo.
4. Ask Codex to read:
   - `AGENTS.md`
   - `docs/modeling-plan.md`
   - `docs/feature-policy.md`
   - `docs/data-mapping.md`
5. Then give a scoped task such as:
   - build import pipeline
   - build feature builder
   - train CatBoost baseline
   - create risk API

## Suggested first Codex task
"""
Read AGENTS.md, docs/modeling-plan.md, docs/feature-policy.md, docs/data-mapping.md, and docs/acceptance-criteria.md.

Implement the raw import and clean reservation pipeline for H1.csv and H2.csv.

Requirements:
- preserve raw rows
- normalize padded strings
- convert NULL-like placeholders to missing values
- build no_show_flag from ReservationStatus
- exclude Canceled rows from the first training dataset
- do not use ReservationStatus, ReservationStatusDate, IsCanceled, BookingChanges, DaysInWaitingList, or AssignedRoomType in the booking-time feature set

Add tests and document assumptions.
"""
