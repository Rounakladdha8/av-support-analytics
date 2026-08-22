# SQL Validation & Reconciliation Results

## 1. Referential integrity: every ticket must map to a real ride
```
SELECT COUNT(*) AS orphaned_tickets
FROM support_tickets t
LEFT JOIN clean_rides r ON t.booking_id = r.booking_id
WHERE r.booking_id IS NULL
```

|   orphaned_tickets |
|-------------------:|
|                  0 |

## 2. Duplicate primary keys (should be zero after cleaning)
### Query 1
```
SELECT booking_id, COUNT(*) AS n
FROM clean_rides
GROUP BY booking_id
HAVING COUNT(*) > 1
```

_(no rows returned)_

### Query 2
```
SELECT ticket_id, COUNT(*) AS n
FROM support_tickets
GROUP BY ticket_id
HAVING COUNT(*) > 1
```

_(no rows returned)_

## 3. Business-logic consistency: tickets should not exist for rides with no
```
SELECT COUNT(*) AS unexplained_tickets
FROM support_tickets t
JOIN clean_rides r ON t.booking_id = r.booking_id
WHERE r.booking_status = 'Completed'
  AND r.is_suspect_completed = 0
  AND (r.customer_rating IS NULL OR r.customer_rating > 2)
  AND t.category != 'General Inquiry'
```

|   unexplained_tickets |
|----------------------:|
|                     0 |

## 4. Resolution time should never be negative (created_ts <= resolved_ts)
```
SELECT COUNT(*) AS invalid_resolution_windows
FROM support_tickets
WHERE resolved_ts < created_ts
```

|   invalid_resolution_windows |
|-----------------------------:|
|                            0 |

## 5. Reconciliation: ticket rate by booking status
```
SELECT
    r.booking_status,
    COUNT(DISTINCT r.booking_id) AS total_rides,
    COUNT(DISTINCT t.ticket_id) AS total_tickets,
    ROUND(100.0 * COUNT(DISTINCT t.ticket_id) / COUNT(DISTINCT r.booking_id), 1) AS ticket_rate_pct
FROM clean_rides r
LEFT JOIN support_tickets t ON r.booking_id = t.booking_id
GROUP BY r.booking_status
ORDER BY ticket_rate_pct DESC
```

| booking_status        |   total_rides |   total_tickets |   ticket_rate_pct |
|:----------------------|--------------:|----------------:|------------------:|
| Incomplete            |          8927 |            6463 |              72.4 |
| Cancelled by Driver   |         26789 |           16629 |              62.1 |
| Cancelled by Customer |         10402 |            5908 |              56.8 |
| No Driver Found       |         10401 |            3860 |              37.1 |
| Completed             |         92248 |            1848 |               2   |

## 6. Data completeness check on key reporting fields
```
SELECT
    SUM(CASE WHEN booking_value IS NULL AND booking_status = 'Completed' THEN 1 ELSE 0 END) AS completed_missing_value,
    SUM(CASE WHEN customer_rating IS NULL AND booking_status = 'Completed' THEN 1 ELSE 0 END) AS completed_missing_rating
FROM clean_rides
```

|   completed_missing_value |   completed_missing_rating |
|--------------------------:|---------------------------:|
|                         0 |                          0 |

