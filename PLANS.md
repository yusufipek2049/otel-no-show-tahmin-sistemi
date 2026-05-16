# PLANS.md

## Execution plan for the first usable release

This file exists to support long-running Codex work. Use it when the task is large, multi-step, or ambiguous.

---

## Project goal
Build the first end-to-end internal no-show prediction system using the current hotel booking dataset and the rules in `AGENTS.md`.

---

## Non-goals for the first release
Do not attempt all of these in v1:

- production-grade authentication provider integration
- online learning
- advanced feature store infrastructure
- MLOps platform integration
- hyperparameter optimization at scale
- perfect UI polish
- cancellation prediction mixed into the no-show objective

---

## Major phases

### Phase 1 — Project skeleton
Deliverables:
- backend scaffold
- frontend scaffold
- database scaffold
- docker compose
- docs wired into the repo

Done when:
- project boots
- health endpoint exists
- repo structure is clear

### Phase 2 — Raw import and cleaning
Deliverables:
- raw CSV import
- text trimming and null normalization
- clean reservation table or clean dataframe layer
- import batch logging

Done when:
- H1.csv and H2.csv can be imported reproducibly
- bad rows are traceable
- clean columns are documented

### Phase 3 — Feature pipeline
Deliverables:
- booking-time-safe feature builder
- excluded leakage features documented in code
- train/validation dataset creation

Done when:
- feature builder runs end to end
- feature matrix excludes disallowed columns
- derived features are unit-tested

### Phase 4 — Modeling baseline
Deliverables:
- baseline classifier(s)
- CatBoost training pipeline
- evaluation report
- model artifact persistence

Done when:
- CatBoost and at least one simple baseline are trained
- PR-AUC, precision, recall, F1 are reported
- split strategy is documented

### Phase 5 — Prediction persistence and APIs
Deliverables:
- predictions table
- batch scoring job
- risk list API
- reservation detail API

Done when:
- predictions are saved with score, class, timestamp, version
- list/detail APIs work

### Phase 6 — Operations workflow
Deliverables:
- action logging
- audit log
- dashboard views
- reporting endpoints

Done when:
- an operator can view risky reservations
- an operator can record an action
- reports render basic business and model metrics

---

## Working principles
When working on a large task:
1. plan first
2. list affected files
3. implement in small verified steps
4. run tests after each meaningful slice
5. update docs if assumptions changed

If a requirement is unclear:
- do the smallest safe thing
- leave a TODO
- document the assumption explicitly

---

## Suggested order for Codex
1. repo scaffold
2. DB schema
3. import pipeline
4. feature builder
5. baseline model
6. CatBoost model
7. scoring persistence
8. risk APIs
9. dashboard
10. reporting and hardening
