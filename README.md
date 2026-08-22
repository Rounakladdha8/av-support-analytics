# Ride-Share Customer Support Analytics & Experimentation Framework

An end-to-end analytics project simulating the kind of work a Data Analyst
would do supporting customer support operations for a ride-hailing / AV
platform: source-to-target data mapping, metric definition, SQL validation
and reconciliation, A/B test design and analysis, and a self-service
dashboard.

## Why this project

Built to demonstrate skills directly relevant to support/ops analytics roles
at ride-hailing and mobility companies: translating support and product
workflows into data requirements, reconciling data across systems, and
designing experiments to evaluate operational changes.

## Data & methodology (read this first)

This project intentionally combines **real** and **simulated** data, and is
explicit about which is which:

- **`clean_rides` — real data.** 150,000 ride bookings from the public
  [NCR Uber ride analytics dataset](https://www.kaggle.com/datasets/yashdevladdha/uber-ride-analytics-dashboard)
  (Kaggle, 2024). This is genuine ride-hailing data with real messiness:
  malformed IDs, duplicate keys, inconsistent nulls, and outlier records —
  all documented and cleaned in `python/01_clean_rides.py` /
  `docs/data_quality_log.md`.

- **`support_tickets` — simulated, but signal-linked, not random.** No
  public dataset of real customer-support tickets exists (for good privacy
  reasons). Rather than inventing a disconnected fake table, ticket
  existence, category, and severity are all **conditioned on real fields**
  from the ride data — cancellation type, low ratings, incomplete rides,
  and a data-quality flag for suspect "completed" rides. See
  `python/02_generate_support_tickets.py` for the exact logic. This keeps
  the support layer grounded in real ride outcomes rather than being purely
  synthetic.

- **The A/B test is simulated but designed like a real one**: two support
  triage workflows (`legacy_manual` vs `auto_routing`) are randomly assigned
  per ticket, and the effect on resolution time / CSAT / escalation is
  deliberately modest (~15–25%) rather than an unrealistically large,
  obviously-fake effect. Full statistical writeup in
  `docs/ab_test_report.md`.

I'm being upfront about this because the whole point of the project is to
demonstrate real analytical process, not to claim access to Uber's actual
support data.

## Project structure

```
av-support-analytics/
├── data/
│   ├── raw/                     # original Kaggle CSV
│   └── clean/                   # cleaned rides, linked tickets, SQLite DB
├── sql/
│   ├── 01_schema.sql
│   └── 02_validation_reconciliation.sql
├── python/
│   ├── 01_clean_rides.py            # source-to-target cleaning + QA log
│   ├── 02_generate_support_tickets.py  # linked synthetic ticket layer
│   ├── 03_ab_test.py                # A/B test: t-tests, chi-square, Mann-Whitney
│   └── 04_build_db_and_run_sql.py   # builds SQLite DB, runs & saves SQL results
├── docs/
│   ├── data_quality_log.md          # every issue found + how it was fixed
│   ├── data_dictionary.md
│   ├── metric_definitions.md        # metric specs (FRT, resolution rate, CSAT, etc.)
│   ├── sql_validation_results.md    # actual query outputs
│   └── ab_test_report.md            # actual test statistics
└── dashboard/
    └── looker_studio_export.csv     # joined table, ready for Looker Studio
```

## How to run it end to end

```bash
pip install pandas numpy scipy tabulate

cd python
python3 01_clean_rides.py              # -> data/clean/clean_rides.csv
python3 02_generate_support_tickets.py # -> data/clean/support_tickets.csv
python3 03_ab_test.py                  # -> docs/ab_test_report.md
python3 04_build_db_and_run_sql.py     # -> data/clean/support_analytics.db, docs/sql_validation_results.md
```

## Key results

- **6 real data quality issues** found and resolved in the source export
  (malformed IDs, 1,233 duplicate booking IDs, literal-string nulls, type
  mismatches, out-of-range ratings, non-positive values on completed rides)
  — see `docs/data_quality_log.md`.
- **Ticket rate varies sharply by ride outcome**: 72.4% of incomplete rides
  generate a ticket vs. 2.0% of completed rides — validating that the
  linked ticket layer behaves the way a real support system would.
- **A/B test**: the `auto_routing` triage workflow shows a statistically
  significant ~20% reduction in resolution time (p < 0.001), a lower
  escalation rate (11.3% vs 16.9%), and higher CSAT — with an effect size
  well above the minimum detectable effect for this sample size.
- **Zero referential integrity failures** between the two linked tables
  after cleaning (see `docs/sql_validation_results.md`).

## Dashboard

Import `dashboard/looker_studio_export.csv` into
[Looker Studio](https://datastudio.google.com/reporting/ace1a48e-59c5-436a-9f71-d9ce109f3065) for a self-service view
filterable by vehicle type, booking status, category, severity, and
workflow.

## Limitations

This is a portfolio project, not production analysis. The support ticket
layer is simulated (see methodology above), the "workflows" are not real
Uber processes, and the A/B test is illustrative of experimental design
methodology rather than a real operational finding.
