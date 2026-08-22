# Data Quality Log

Issues found in the raw source file and how each was resolved.
Raw rows: 150,000 -> Clean rows: 148,767 (1,233 removed as exact duplicate booking records).


- **Booking ID / Customer ID wrapped in stray quote characters from source export** (`150,000` rows affected) — stripped leading/trailing quote characters via regex
- **Duplicate Booking ID values (violates expected 1 row = 1 booking grain)** (`1,233` rows affected) — de-duplicated, keeping first occurrence; flagged for upstream source review
- **Literal string 'null' used instead of true empty/NaN values** (`0` rows affected) — replaced all literal 'null' strings with proper NaN
- **Date/Time fields stored as separate text columns; some unparseable** (`0` rows affected) — combined into a single typed Booking Timestamp column; unparseable rows flagged (not dropped)
- **Completed rides with non-positive Ride Distance or Booking Value** (`0` rows affected) — retained but flagged with is_suspect_completed=1 for downstream exclusion from revenue metrics
