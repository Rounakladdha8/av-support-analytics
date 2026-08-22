# Data Dictionary

## `clean_rides` (source: real Kaggle NCR ride booking dataset, cleaned)

| Field | Type | Description |
|---|---|---|
| booking_id | TEXT (PK) | Unique ride booking identifier |
| customer_id | TEXT | Unique customer identifier |
| booking_ts | TIMESTAMP | Combined date+time of the booking |
| booking_status | TEXT | Completed / Cancelled by Customer / Cancelled by Driver / No Driver Found / Incomplete |
| vehicle_type | TEXT | eBike, Auto, Bike, Go Mini, Go Sedan, Premier Sedan, Uber XL |
| pickup_location | TEXT | Pickup area name |
| drop_location | TEXT | Drop-off area name |
| avg_vtat_min | FLOAT | Avg. vehicle time to arrival at pickup (minutes) |
| avg_ctat_min | FLOAT | Avg. customer time to arrival/trip time (minutes) |
| cancelled_by_customer_flag | FLOAT | 1 if cancelled by customer, else null |
| customer_cancel_reason | TEXT | Reason given for customer cancellation |
| cancelled_by_driver_flag | FLOAT | 1 if cancelled by driver, else null |
| driver_cancel_reason | TEXT | Reason given for driver cancellation |
| incomplete_flag | FLOAT | 1 if ride was incomplete, else null |
| incomplete_reason | TEXT | Reason ride was left incomplete |
| booking_value | FLOAT | Fare value (local currency) |
| ride_distance_km | FLOAT | Ride distance in km |
| driver_rating | FLOAT | Driver rating given by customer (1–5) |
| customer_rating | FLOAT | Customer rating given by driver (1–5) |
| payment_method | TEXT | UPI / Cash / Credit Card / Debit Card / Uber Wallet |
| is_suspect_completed | INTEGER | Flag: 1 if a "Completed" ride had non-positive value/distance (data quality flag) |

## `support_tickets` (simulated, linked to real rides)

| Field | Type | Description |
|---|---|---|
| ticket_id | TEXT (PK) | Unique ticket identifier |
| booking_id | TEXT (FK -> clean_rides.booking_id) | Ride the ticket relates to |
| customer_id | TEXT | Customer who filed the ticket |
| category | TEXT | Refund Request / Driver Complaint / Vehicle Issue / Ride Safety Concern / Billing Dispute / Service Availability Complaint / Service Quality Complaint / General Inquiry |
| severity | TEXT | Low / Medium / High / Critical |
| workflow | TEXT | `legacy_manual` or `auto_routing` — A/B test arm |
| created_ts | TIMESTAMP | Ticket creation time |
| resolved_ts | TIMESTAMP | Ticket resolution time |
| first_response_hours | FLOAT | Hours to first agent response |
| resolution_hours | FLOAT | Hours to full resolution |
| csat_score | INTEGER | Post-resolution satisfaction score (1–5) |
| escalated_flag | INTEGER (0/1) | Whether the ticket was escalated |

### Generation logic summary (see `python/02_generate_support_tickets.py`)

Ticket existence, category, and severity are all conditioned on **real**
ride-level signals: booking status, customer/driver ratings, and the
`is_suspect_completed` data-quality flag. Resolution time, CSAT, and
escalation are then simulated as a function of severity and the assigned
A/B workflow, with random noise — not independent random draws.
