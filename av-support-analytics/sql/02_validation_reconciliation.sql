-- Validation & reconciliation queries between clean_rides and support_tickets.
-- These are the checks a data analyst would run before trusting a joined
-- reporting layer: referential integrity, duplicate keys, orphaned records,
-- and business-logic consistency between the two source-aligned tables.

-- 1. Referential integrity: every ticket must map to a real ride
SELECT COUNT(*) AS orphaned_tickets
FROM support_tickets t
LEFT JOIN clean_rides r ON t.booking_id = r.booking_id
WHERE r.booking_id IS NULL;

-- 2. Duplicate primary keys (should be zero after cleaning)
SELECT booking_id, COUNT(*) AS n
FROM clean_rides
GROUP BY booking_id
HAVING COUNT(*) > 1;

SELECT ticket_id, COUNT(*) AS n
FROM support_tickets
GROUP BY ticket_id
HAVING COUNT(*) > 1;

-- 3. Business-logic consistency: tickets should not exist for rides with no
--    negative signal at all (sanity check on the ticket-generation logic /
--    would catch mis-tagged tickets in a real pipeline)
SELECT COUNT(*) AS unexplained_tickets
FROM support_tickets t
JOIN clean_rides r ON t.booking_id = r.booking_id
WHERE r.booking_status = 'Completed'
  AND r.is_suspect_completed = 0
  AND (r.customer_rating IS NULL OR r.customer_rating > 2)
  AND t.category != 'General Inquiry';

-- 4. Resolution time should never be negative (created_ts <= resolved_ts)
SELECT COUNT(*) AS invalid_resolution_windows
FROM support_tickets
WHERE resolved_ts < created_ts;

-- 5. Reconciliation: ticket rate by booking status
--    (validates the ticket layer is behaving as expected against real ride outcomes)
SELECT
    r.booking_status,
    COUNT(DISTINCT r.booking_id) AS total_rides,
    COUNT(DISTINCT t.ticket_id) AS total_tickets,
    ROUND(100.0 * COUNT(DISTINCT t.ticket_id) / COUNT(DISTINCT r.booking_id), 1) AS ticket_rate_pct
FROM clean_rides r
LEFT JOIN support_tickets t ON r.booking_id = t.booking_id
GROUP BY r.booking_status
ORDER BY ticket_rate_pct DESC;

-- 6. Data completeness check on key reporting fields
SELECT
    SUM(CASE WHEN booking_value IS NULL AND booking_status = 'Completed' THEN 1 ELSE 0 END) AS completed_missing_value,
    SUM(CASE WHEN customer_rating IS NULL AND booking_status = 'Completed' THEN 1 ELSE 0 END) AS completed_missing_rating
FROM clean_rides;
