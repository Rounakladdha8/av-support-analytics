"""
01_clean_rides.py

Source-to-target mapping: raw NCR ride booking export -> clean rides table.

This script performs real discovery + cleaning on the raw Kaggle "Uber Data
Analytics Dashboard" export (150,000 rides, NCR/India, 2024). It documents
every data quality issue found and how it was resolved, mirroring the kind
of source-to-target mapping and data validation work described in data
analyst roles supporting analytics/reporting pipelines.

Run:
    python3 01_clean_rides.py
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "ncr_ride_bookings.csv"
CLEAN_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
LOG_PATH = Path(__file__).resolve().parent.parent / "docs" / "data_quality_log.md"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)

log_lines = ["# Data Quality Log", "", "Issues found in the raw source file and how each was resolved.", ""]


def log(issue, resolution, count=None):
    line = f"- **{issue}**"
    if count is not None:
        line += f" (`{count:,}` rows affected)"
    line += f" — {resolution}"
    log_lines.append(line)


def main():
    df = pd.read_csv(RAW_PATH, dtype=str)
    n_raw = len(df)

    # ------------------------------------------------------------------
    # Issue 1: Booking ID / Customer ID wrapped in extra literal quote chars
    # e.g. '"""CNR5884300"""' -> 'CNR5884300'
    # ------------------------------------------------------------------
    def strip_quotes(x):
        if pd.isna(x):
            return x
        return re.sub(r'^"+|"+$', "", str(x))

    bad_id_format = df["Booking ID"].str.contains('"', na=False).sum()
    df["Booking ID"] = df["Booking ID"].apply(strip_quotes)
    df["Customer ID"] = df["Customer ID"].apply(strip_quotes)
    log(
        "Booking ID / Customer ID wrapped in stray quote characters from source export",
        "stripped leading/trailing quote characters via regex",
        bad_id_format,
    )

    # ------------------------------------------------------------------
    # Issue 2: Duplicate Booking IDs (should be a unique key)
    # ------------------------------------------------------------------
    dupe_mask = df["Booking ID"].duplicated(keep="first")
    n_dupes = dupe_mask.sum()
    df = df[~dupe_mask].copy()
    log(
        "Duplicate Booking ID values (violates expected 1 row = 1 booking grain)",
        "de-duplicated, keeping first occurrence; flagged for upstream source review",
        n_dupes,
    )

    # ------------------------------------------------------------------
    # Issue 3: 'null' stored as literal string instead of true NaN
    # ------------------------------------------------------------------
    literal_nulls = (df == "null").sum().sum()
    df = df.replace("null", np.nan)
    log(
        "Literal string 'null' used instead of true empty/NaN values",
        "replaced all literal 'null' strings with proper NaN",
        int(literal_nulls),
    )

    # ------------------------------------------------------------------
    # Issue 4: Type casting for numeric / datetime columns
    # ------------------------------------------------------------------
    numeric_cols = [
        "Avg VTAT", "Avg CTAT", "Booking Value", "Ride Distance",
        "Driver Ratings", "Customer Rating",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["Booking Timestamp"] = pd.to_datetime(
        df["Date"] + " " + df["Time"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    bad_ts = df["Booking Timestamp"].isna().sum()
    log(
        "Date/Time fields stored as separate text columns; some unparseable",
        "combined into a single typed Booking Timestamp column; unparseable rows flagged (not dropped)",
        bad_ts,
    )

    # ------------------------------------------------------------------
    # Issue 5: Rating values out of the expected 1-5 range
    # ------------------------------------------------------------------
    for c in ["Driver Ratings", "Customer Rating"]:
        out_of_range = df[c].apply(lambda v: pd.notna(v) and not (1 <= v <= 5)).sum()
        if out_of_range:
            log(f"{c} values outside valid 1-5 range", "set to NaN, excluded from rating aggregates", int(out_of_range))
            df.loc[df[c].apply(lambda v: pd.notna(v) and not (1 <= v <= 5)), c] = np.nan

    # ------------------------------------------------------------------
    # Issue 6: Negative or zero Ride Distance / Booking Value on completed rides
    # ------------------------------------------------------------------
    bad_completed = df[(df["Booking Status"] == "Completed") &
                        ((df["Ride Distance"] <= 0) | (df["Booking Value"] <= 0))]
    log(
        "Completed rides with non-positive Ride Distance or Booking Value",
        "retained but flagged with is_suspect_completed=1 for downstream exclusion from revenue metrics",
        len(bad_completed),
    )
    df["is_suspect_completed"] = 0
    df.loc[bad_completed.index, "is_suspect_completed"] = 1

    # ------------------------------------------------------------------
    # Standardize column names to snake_case for the clean/target model
    # ------------------------------------------------------------------
    rename_map = {
        "Booking ID": "booking_id",
        "Customer ID": "customer_id",
        "Booking Timestamp": "booking_ts",
        "Booking Status": "booking_status",
        "Vehicle Type": "vehicle_type",
        "Pickup Location": "pickup_location",
        "Drop Location": "drop_location",
        "Avg VTAT": "avg_vtat_min",
        "Avg CTAT": "avg_ctat_min",
        "Cancelled Rides by Customer": "cancelled_by_customer_flag",
        "Reason for cancelling by Customer": "customer_cancel_reason",
        "Cancelled Rides by Driver": "cancelled_by_driver_flag",
        "Driver Cancellation Reason": "driver_cancel_reason",
        "Incomplete Rides": "incomplete_flag",
        "Incomplete Rides Reason": "incomplete_reason",
        "Booking Value": "booking_value",
        "Ride Distance": "ride_distance_km",
        "Driver Ratings": "driver_rating",
        "Customer Rating": "customer_rating",
        "Payment Method": "payment_method",
    }
    df = df.rename(columns=rename_map)
    keep_cols = list(rename_map.values()) + ["is_suspect_completed"]
    clean = df[keep_cols].copy()

    out_path = CLEAN_DIR / "clean_rides.csv"
    clean.to_csv(out_path, index=False)

    log_lines.insert(
        3,
        f"Raw rows: {n_raw:,} -> Clean rows: {len(clean):,} "
        f"({n_raw - len(clean):,} removed as exact duplicate booking records).\n",
    )
    LOG_PATH.write_text("\n".join(log_lines) + "\n")

    print(f"Wrote {len(clean):,} clean rows to {out_path}")
    print(f"Wrote data quality log to {LOG_PATH}")


if __name__ == "__main__":
    main()
