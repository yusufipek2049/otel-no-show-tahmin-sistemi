# V1 / V2 Gap Analysis

## Scope

This repository is a no-show prediction and operations support system.

In scope:

- staged no-show risk scoring
- risk queues
- reservation detail
- action logging
- no-show operations reporting
- model quality reporting

Out of scope:

- traffic analytics
- ad spend / ROAS / CPC / CTR
- generic revenue BI
- marketing attribution without additional data sources

## V1 Definition

V1 means the system can:

- ingest hotel reservation data
- build leakage-safe feature tables
- train active no-show stages
- produce persisted predictions or artifact fallback views
- show operational risk queues
- allow action creation and update when DB-backed
- expose concise model quality summaries

## Current V1 Status

Mostly present:

- ingestion
- clean data layer
- feature generation
- temporal split
- `catboost_with_logistic_score` training
- Logistic Regression feeder score
- isotonic calibration
- artifact persistence
- dashboard
- reservations list
- reservation detail
- action create / update flow
- customer risk page
- reservation risk page
- reports page

Still weak or incomplete:

- true live scoring is not separated from training strongly enough
- artifact fallback is read-only
- authentication and role-based access are not complete
- real CRM/payment/contact/campaign/deposit data is not connected
- synthetic operational signals must be replaced before production claims

## V2 Definition

V2 adds management visibility on top of the operational no-show workflow.

Currently present:

- operations summary
- no-show trend
- cancellation vs no-show summary
- channel breakdown
- segment breakdown
- action effectiveness proxy

Still missing:

- period-over-period comparisons
- deeper drill-downs
- model drift trend UI
- action outcome labels tied to real intervention results
- production monitoring and alerting

## Current Decision

The product is past the old "only benchmark page" state.

The current gap is not "add more candidate models." The current gap is:

1. connect real operational event data
2. separate training from scoring
3. harden persistence and auth
4. monitor drift and action outcomes over time
5. validate the two active stages on real operational data
