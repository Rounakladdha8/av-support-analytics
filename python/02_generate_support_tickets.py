"""
02_generate_support_tickets.py

Public datasets with real customer-support ticket data essentially don't
exist (privacy). To build a realistic support-ops layer, this script
generates a SYNTHETIC support ticket table -- but every ticket is anchored
to a REAL ride record and REAL ride outcome fields (cancellation, low
rating, incomplete ride, driver-reported issue) from the cleaned Kaggle
dataset. Ticket probability, category, and severity are all conditioned on
real ride signals rather than drawn independently at random.

This mirrors the real-world problem an AV customer support analytics role
would face: support ticket systems and ride/telemetry systems live in
separate source systems and must be joined and reconciled.

Run:
    python3 02_generate_support_tickets.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

CLEAN_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
RNG = np.random.default_rng(42)

TICKET_CATEGORIES_BY_TRIGGER = {
    "cancelled_by_customer": ["Refund Request", "Booking Issue"],
    "cancelled_by_driver": ["Refund Request", "Driver Complaint"],
    "no_driver_found": ["Service Availability Complaint"],
    "incomplete_ride": ["Ride Safety Concern", "Refund Request", "Vehicle Issue"],
    "low_rating": ["Driver Complaint", "Service Quality Complaint", "Vehicle Issue"],
    "suspect_billing": ["Billing Dispute"],
}


def ticket_probability(row):
    """Real-signal-conditioned probability that a ride generates a ticket."""
    p = 0.02  # base rate: even a normal ride has a small chance of a ticket
    if row["booking_status"] == "Cancelled by Customer":
        p += 0.55
    if row["booking_status"] == "Cancelled by Driver":
        p += 0.60
    if row["booking_status"] == "No Driver Found":
        p += 0.35
    if row["booking_status"] == "Incomplete":
        p += 0.70
    if pd.notna(row["customer_rating"]) and row["customer_rating"] <= 2:
        p += 0.45
    if pd.notna(row["driver_rating"]) and row["driver_rating"] <= 2:
        p += 0.15
    if row["is_suspect_completed"] == 1:
        p += 0.30
    return min(p, 0.95)


def pick_category(row):
    if row["booking_status"] == "Cancelled by Customer":
        return RNG.choice(TICKET_CATEGORIES_BY_TRIGGER["cancelled_by_customer"])
    if row["booking_status"] == "Cancelled by Driver":
        return RNG.choice(TICKET_CATEGORIES_BY_TRIGGER["cancelled_by_driver"])
    if row["booking_status"] == "No Driver Found":
        return RNG.choice(TICKET_CATEGORIES_BY_TRIGGER["no_driver_found"])
    if row["booking_status"] == "Incomplete":
        return RNG.choice(TICKET_CATEGORIES_BY_TRIGGER["incomplete_ride"])
    if row["is_suspect_completed"] == 1:
        return RNG.choice(TICKET_CATEGORIES_BY_TRIGGER["suspect_billing"])
    if pd.notna(row["customer_rating"]) and row["customer_rating"] <= 2:
        return RNG.choice(TICKET_CATEGORIES_BY_TRIGGER["low_rating"])
    return "General Inquiry"


def severity_for_category(cat):
    high = {"Ride Safety Concern", "Driver Complaint"}
    med = {"Billing Dispute", "Refund Request", "Vehicle Issue", "Service Quality Complaint"}
    if cat in high:
        return RNG.choice(["High", "Critical"], p=[0.7, 0.3])
    if cat in med:
        return RNG.choice(["Medium", "High"], p=[0.75, 0.25])
    return RNG.choice(["Low", "Medium"], p=[0.8, 0.2])


def simulate_workflow_assignment(n):
    """
    A/B split: simulate two support triage workflows.
    - legacy_manual: agent manually triages queue (existing process)
    - auto_routing: category/severity based auto-routing to specialized queues (new process)
    Assignment is randomized 50/50 per ticket, as in a real experiment.
    """
    return RNG.choice(["legacy_manual", "auto_routing"], size=n, p=[0.5, 0.5])


def simulate_resolution_time(category, severity, workflow):
    """
    Base resolution time (hours) driven by severity/category, with auto_routing
    producing a genuine, but not enormous, improvement -- so the A/B test has
    a real, non-trivial effect to detect rather than an artificially huge one.
    """
    base = {"Low": 6, "Medium": 14, "High": 26, "Critical": 40}[severity]
    noise = RNG.gamma(shape=2.0, scale=base / 2.0)
    frt = noise * RNG.uniform(0.85, 1.15)

    if workflow == "auto_routing":
        frt *= RNG.uniform(0.72, 0.88)  # ~15-25% faster on average, with variance

    return max(frt, 0.1)


def simulate_csat(severity, resolution_hours, workflow):
    """Synthetic CSAT (1-5) as a function of severity and how fast it was resolved."""
    base = {"Low": 4.3, "Medium": 4.0, "High": 3.5, "Critical": 3.0}[severity]
    speed_penalty = min(resolution_hours / 40.0, 1.0) * 1.2
    workflow_bonus = 0.15 if workflow == "auto_routing" else 0.0
    score = base - speed_penalty + workflow_bonus + RNG.normal(0, 0.4)
    return int(np.clip(round(score), 1, 5))


def main():
    rides = pd.read_csv(CLEAN_DIR / "clean_rides.csv", parse_dates=["booking_ts"])

    probs = rides.apply(ticket_probability, axis=1)
    has_ticket = RNG.random(len(rides)) < probs
    ticket_rides = rides[has_ticket].copy()

    n = len(ticket_rides)
    ticket_rides["ticket_id"] = [f"TCK{100000 + i}" for i in range(n)]
    ticket_rides["category"] = ticket_rides.apply(pick_category, axis=1)
    ticket_rides["severity"] = ticket_rides["category"].apply(severity_for_category)
    ticket_rides["workflow"] = simulate_workflow_assignment(n)

    ticket_rides["resolution_hours"] = ticket_rides.apply(
        lambda r: simulate_resolution_time(r["category"], r["severity"], r["workflow"]), axis=1
    )
    # First response time is a fraction of total resolution time
    ticket_rides["first_response_hours"] = ticket_rides["resolution_hours"] * RNG.uniform(0.15, 0.35, n)

    ticket_rides["csat_score"] = ticket_rides.apply(
        lambda r: simulate_csat(r["severity"], r["resolution_hours"], r["workflow"]), axis=1
    )

    # Escalation: high/critical tickets with slow resolution escalate more often
    def escalated(row):
        p = 0.05
        if row["severity"] in ("High", "Critical"):
            p += 0.20
        if row["resolution_hours"] > 24:
            p += 0.15
        if row["workflow"] == "auto_routing":
            p -= 0.05
        return RNG.random() < max(p, 0.01)

    ticket_rides["escalated_flag"] = ticket_rides.apply(escalated, axis=1)

    ticket_rides["created_ts"] = ticket_rides["booking_ts"] + pd.to_timedelta(
        RNG.uniform(0, 6, n), unit="h"
    )
    ticket_rides["resolved_ts"] = ticket_rides["created_ts"] + pd.to_timedelta(
        ticket_rides["resolution_hours"], unit="h"
    )

    tickets = ticket_rides[[
        "ticket_id", "booking_id", "customer_id", "category", "severity", "workflow",
        "created_ts", "resolved_ts", "first_response_hours", "resolution_hours",
        "csat_score", "escalated_flag",
    ]].reset_index(drop=True)

    out_path = CLEAN_DIR / "support_tickets.csv"
    tickets.to_csv(out_path, index=False)
    print(f"Generated {len(tickets):,} support tickets linked to real ride records -> {out_path}")
    print(f"Ticket rate: {len(tickets) / len(rides):.1%} of all rides")
    print(tickets["workflow"].value_counts())


if __name__ == "__main__":
    main()
