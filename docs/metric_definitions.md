# Support Analytics — Metric Definitions & Reporting Specification

This document defines the core metrics used in the support analytics reporting
layer, their calculation logic, and their source fields. It is written the
way a metric spec would be documented for a stakeholder-facing reporting
project: name, plain-English definition, calculation logic, source table/field,
and grain.

---

## First Response Time (FRT)

- **Definition:** Time elapsed between a support ticket being created and the
  first agent response.
- **Calculation:** `first_response_hours` (hours, float)
- **Source:** `support_tickets.first_response_hours`
- **Grain:** One value per ticket
- **Business use:** Core SLA metric; tracked by category/severity/workflow to
  identify bottlenecks in triage.

## Resolution Time

- **Definition:** Total time elapsed between ticket creation and ticket
  resolution (closure).
- **Calculation:** `resolved_ts - created_ts`, stored directly as
  `resolution_hours`
- **Source:** `support_tickets.resolution_hours`
- **Grain:** One value per ticket
- **Business use:** Primary throughput metric for support operations;
  compared across workflow variants (A/B test target metric).

## Resolution Rate

- **Definition:** Share of tickets resolved (vs. abandoned/open) within a
  given reporting window.
- **Calculation:** `COUNT(resolved_ts IS NOT NULL) / COUNT(*)`
- **Source:** `support_tickets`
- **Grain:** Aggregate, by day/category/workflow
- **Business use:** Operational health check on the support queue.

## Escalation Rate

- **Definition:** Share of tickets that were escalated beyond first-line
  support.
- **Calculation:** `AVG(escalated_flag)`
- **Source:** `support_tickets.escalated_flag`
- **Grain:** Aggregate, by category/severity/workflow
- **Business use:** Proxy for whether first-line triage is correctly sized
  to handle incoming issues; a leading indicator of process breakdowns.

## CSAT Score

- **Definition:** Post-resolution customer satisfaction rating (1–5 scale).
- **Calculation:** `AVG(csat_score)` for aggregate reporting; individual
  scores retained at ticket grain for distribution analysis.
- **Source:** `support_tickets.csat_score`
- **Grain:** One value per resolved ticket
- **Business use:** Primary quality-of-support outcome metric.

## Ticket Rate (by ride outcome)

- **Definition:** Share of rides in a given booking-status segment that
  generate a support ticket.
- **Calculation:** `COUNT(DISTINCT ticket_id) / COUNT(DISTINCT booking_id)`,
  grouped by `booking_status`
- **Source:** join of `clean_rides.booking_status` and
  `support_tickets.booking_id`
- **Grain:** Aggregate, by booking_status / vehicle_type / region
- **Business use:** Identifies which ride failure modes (cancellation types,
  incomplete rides) are the largest drivers of support volume, so process
  fixes can be prioritized upstream of the ticket itself.

## Ride Completion Rate

- **Definition:** Share of ride requests that end in a completed trip.
- **Calculation:** `COUNT(booking_status = 'Completed') / COUNT(*)`
- **Source:** `clean_rides.booking_status`
- **Grain:** Aggregate, by vehicle_type / date / pickup region
- **Business use:** Upstream operational health metric; low completion rate
  in a segment is a leading indicator of downstream support volume.

---

## Data Sources / System Map

| Logical system | Table | Real vs. simulated |
|---|---|---|
| Ride events / trip system | `clean_rides` | **Real** — NCR ride booking data (Kaggle, 2024) |
| Customer support ticketing system | `support_tickets` | **Simulated**, conditioned on real ride outcome fields (see `docs/README.md` methodology) |

Both tables share a common key, `booking_id`, enabling source-to-target
mapping and joined reporting across the two systems.
