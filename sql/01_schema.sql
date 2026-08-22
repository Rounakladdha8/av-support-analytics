-- Target data model: clean_rides + support_tickets
-- One row per booking / one row per ticket, linked by booking_id.

CREATE TABLE IF NOT EXISTS clean_rides (
    booking_id              TEXT PRIMARY KEY,
    customer_id             TEXT NOT NULL,
    booking_ts              TEXT,
    booking_status          TEXT,
    vehicle_type            TEXT,
    pickup_location         TEXT,
    drop_location            TEXT,
    avg_vtat_min            REAL,
    avg_ctat_min            REAL,
    cancelled_by_customer_flag REAL,
    customer_cancel_reason  TEXT,
    cancelled_by_driver_flag REAL,
    driver_cancel_reason    TEXT,
    incomplete_flag         REAL,
    incomplete_reason       TEXT,
    booking_value           REAL,
    ride_distance_km        REAL,
    driver_rating           REAL,
    customer_rating         REAL,
    payment_method          TEXT,
    is_suspect_completed    INTEGER
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id               TEXT PRIMARY KEY,
    booking_id              TEXT NOT NULL REFERENCES clean_rides(booking_id),
    customer_id             TEXT,
    category                TEXT,
    severity                TEXT,
    workflow                TEXT,
    created_ts               TEXT,
    resolved_ts              TEXT,
    first_response_hours    REAL,
    resolution_hours        REAL,
    csat_score               INTEGER,
    escalated_flag           INTEGER
);
