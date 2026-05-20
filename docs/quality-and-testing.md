# Quality And Testing Guide

This guide replaces the previous static-analysis report and the separate implementation/testing notes.

## Dynamic Tests

Backend dynamic tests use pytest.

Latest result from the current review:

```text
36 passed
```

Main coverage:

- health endpoint
- dashboard and report API smoke tests
- reservation artifact fallback views
- action creation, listing, and update through real HTTP requests with SQLite
- temporal train/test split
- leakage policy enforcement
- arrival failure target construction
- evaluation metrics, threshold behavior, calibration, and fixed-list capture
- training dataset smoke path
- prediction persistence to SQLite
- logging helpers and request logging middleware

Important action-flow test:

- `backend/tests/test_actions_api.py`

This test creates a reservation, persists a prediction, creates a follow-up action, lists actions, updates the action to `completed`, and checks that missing reservations return `404`.

Run:

```bash
cd backend
pytest
python3 -m compileall app
```

## Frontend Checks

Run:

```bash
cd frontend
npm run typecheck
npm run build
```

The current frontend has type coverage for API responses, reports, charts, reservation detail, and follow-up components. A future improvement would be Playwright smoke tests for `/dashboard`, `/reservations`, `/reports`, and one reservation detail page.

## Static And Security Checks

Commands used during review:

```bash
ruff check backend
mypy backend/app --ignore-missing-imports
bandit -r backend/app -x backend/tests
semgrep scan --config auto .
pip-audit -l
```

Latest static/security status:

- Ruff: passed
- mypy with ignored third-party imports: passed
- Bandit: passed
- Semgrep: passed
- pip-audit local environment: found vulnerable packages in the local Python environment

pip-audit local findings:

| Package | Installed version | Finding | Fix version |
| --- | --- | --- | --- |
| `idna` | `3.11` | `CVE-2026-45409` | `3.15` |
| `joblib` | `1.5.3` | `PYSEC-2024-277` | not listed by pip-audit |
| `PyJWT` | `2.12.1` | `PYSEC-2025-183` | not listed by pip-audit |

Notes:

- `pip-audit -r backend/requirements.txt` was blocked locally because `ensurepip` / `python3-venv` was missing.
- `mypy backend/app` without `--ignore-missing-imports` is blocked by missing third-party stubs for libraries such as `pandas`, `sklearn`, `joblib`, and `catboost`.
- SonarQube was not run because Java and `sonar-scanner` were not installed.
- OWASP ZAP Baseline was not run because Docker was not available inside the WSL distro.

## Engineering Notes

The project uses a modular monolith:

- FastAPI API routes handle HTTP.
- Services coordinate business workflows.
- Repositories isolate database and artifact access.
- Pydantic schemas define API contracts.
- Training modules handle ingestion, features, split, evaluation, model training, calibration, and persistence.

Frontend uses component-based architecture with Next.js and React:

- page routes live under `frontend/app`
- shared UI pieces live under `frontend/components`
- API clients and presentation helpers live under `frontend/lib`

Clean code practices applied:

- clear naming for services, repositories, schemas, and components
- small reusable UI components such as `MetricCard`, `PanelCard`, and `RiskBadge`
- central API client and fallback handling in `frontend/lib/api.ts`
- stage-specific feature policy and explicit leakage guards
- typed API responses in backend and frontend

## Recommended Next Testing Work

1. Add Playwright smoke tests for main frontend routes.
2. Add a lockfile or pinned dependency set for repeatable `pip-audit` runs.
3. Add a mypy config for third-party libraries instead of relying on CLI flags.
4. Run SonarQube and OWASP ZAP in an environment with Java and Docker.
