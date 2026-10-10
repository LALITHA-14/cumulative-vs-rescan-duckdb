import argparse
import csv
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parent

DB_PATH = Path(
    os.getenv(
        "DUCKDB_PATH",
        ROOT / "runtime/benchmark.duckdb"
    )
)

RESULTS_DIR = Path(
    os.getenv(
        "RESULTS_DIR",
        ROOT / "results"
    )
)

DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        ROOT / "data/events"
    )
)

START_DATE = os.getenv(
    "START_DATE",
    "2023-01-01"
)


def partition_file(target_date):
    return (
        DATA_DIR
        / f"date={target_date}"
        / "events.parquet"
    )


def read_sql(filename):
    return (
        ROOT
        / "sql"
        / filename
    ).read_text(
        encoding="utf-8"
    )


def run_backfill(
    corrupted_date,
    current_date,
    window_days=30
):
    start = time.perf_counter()

    conn = duckdb.connect(
        str(DB_PATH)
    )

    # Delete poisoned state.
    conn.execute(
        """
        DELETE FROM cumulative_state
        WHERE target_date >= ?
          AND target_date <= ?
        """,
        [
            corrupted_date,
            current_date
        ]
    )

    days = (
        current_date
        - corrupted_date
    ).days + 1

    for offset in range(days):

        target_date = (
            corrupted_date
            + timedelta(days=offset)
        )

        previous_date = (
            target_date
            - timedelta(days=1)
        )

        staging_sql = read_sql(
            "cumulative_staging.sql"
        )

        staging_sql = staging_sql.format(
            today_file=str(
                partition_file(
                    target_date
                )
            ).replace("\\", "/")
        )

        conn.execute(
            staging_sql
        )

        join_sql = read_sql(
            "cumulative_join.sql"
        )

        join_sql = join_sql.format(
            target_date=target_date,
            previous_date=previous_date,
            window_days=window_days
        )

        conn.execute(
            join_sql
        )

    elapsed = (
        time.perf_counter()
        - start
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = (
        RESULTS_DIR
        / "backfill.csv"
    )

    with open(
        output,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "corrupted_date",
                "days_affected",
                "detect_date",
                "backfill_runs",
                "backfill_wall_s"
            ]
        )

        writer.writeheader()

        writer.writerow(
            {
                "corrupted_date":
                    corrupted_date,

                "days_affected":
                    days,

                "detect_date":
                    current_date,

                "backfill_runs":
                    days,

                "backfill_wall_s":
                    round(
                        elapsed,
                        3
                    )
            }
        )

    conn.close()

    print(
        f"Backfill completed: {days} days"
    )

    print(
        f"Time: {elapsed:.3f} seconds"
    )

    print(
        f"Result: {output}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--corrupted-date",
        default=None
    )

    parser.add_argument(
        "--detect-date",
        default=None
    )

    args = parser.parse_args()

    if args.corrupted_date is None:
        start_date = pd.Timestamp(
            START_DATE
        ).date()

        chaos_day = int(
            os.getenv(
                "CHAOS_DAY",
                "120"
            )
        )

        corrupted_date = (
            start_date
            + timedelta(
                days=chaos_day - 1
            )
        )

    else:
        corrupted_date = (
            pd.Timestamp(
                args.corrupted_date
            ).date()
        )

    if args.detect_date is None:

        forward_days = int(
            os.getenv(
                "CHAOS_FORWARD_DAYS",
                "30"
            )
        )

        current_date = (
            corrupted_date
            + timedelta(
                days=forward_days
            )
        )

    else:
        current_date = (
            pd.Timestamp(
                args.detect_date
            ).date()
        )

    run_backfill(
        corrupted_date,
        current_date,
        window_days=30
    )


if __name__ == "__main__":
    main()