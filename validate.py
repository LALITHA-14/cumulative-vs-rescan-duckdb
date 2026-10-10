from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import duckdb


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent

RUNTIME_DIR = ROOT / "runtime"
DB_PATH = RUNTIME_DIR / "benchmark.duckdb"


# ============================================================
# VALIDATION
# ============================================================

def validate(target_date: date) -> None:

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\n"
            f"Run the pipeline first."
        )

    conn = duckdb.connect(str(DB_PATH))

    try:

        # ----------------------------------------------------
        # Check required tables
        # ----------------------------------------------------

        tables = {
            row[0]
            for row in conn.execute(
                "SHOW TABLES"
            ).fetchall()
        }

        required_tables = {
            "rescan_metrics",
            "cumulative_metrics",
        }

        missing = required_tables - tables

        if missing:
            raise RuntimeError(
                "Required validation table(s) missing: "
                + ", ".join(sorted(missing))
            )

        # ----------------------------------------------------
        # Compare rescan vs cumulative
        # ----------------------------------------------------

        query = """
            SELECT COUNT(*)
            FROM (
                SELECT
                    COALESCE(
                        r.user_id,
                        c.user_id
                    ) AS user_id,

                    r.is_active_today
                        AS r_is_active_today,
                    c.is_active_today
                        AS c_is_active_today,

                    r.is_active_7d
                        AS r_is_active_7d,
                    c.is_active_7d
                        AS c_is_active_7d,

                    r.is_active_30d
                        AS r_is_active_30d,
                    c.is_active_30d
                        AS c_is_active_30d,

                    r.likes_7d
                        AS r_likes_7d,
                    c.likes_7d
                        AS c_likes_7d,

                    r.comments_7d
                        AS r_comments_7d,
                    c.comments_7d
                        AS c_comments_7d,

                    r.shares_7d
                        AS r_shares_7d,
                    c.shares_7d
                        AS c_shares_7d,

                    r.likes_30d
                        AS r_likes_30d,
                    c.likes_30d
                        AS c_likes_30d,

                    r.comments_30d
                        AS r_comments_30d,
                    c.comments_30d
                        AS c_comments_30d,

                    r.shares_30d
                        AS r_shares_30d,
                    c.shares_30d
                        AS c_shares_30d

                FROM rescan_metrics r

                FULL OUTER JOIN cumulative_metrics c
                    ON r.user_id = c.user_id
                   AND r.run_date = c.run_date

                WHERE COALESCE(
                    r.run_date,
                    c.run_date
                ) = ?::DATE
            )

            WHERE
                r_is_active_today
                    IS DISTINCT FROM c_is_active_today

                OR r_is_active_7d
                    IS DISTINCT FROM c_is_active_7d

                OR r_is_active_30d
                    IS DISTINCT FROM c_is_active_30d

                OR r_likes_7d
                    IS DISTINCT FROM c_likes_7d

                OR r_comments_7d
                    IS DISTINCT FROM c_comments_7d

                OR r_shares_7d
                    IS DISTINCT FROM c_shares_7d

                OR r_likes_30d
                    IS DISTINCT FROM c_likes_30d

                OR r_comments_30d
                    IS DISTINCT FROM c_comments_30d

                OR r_shares_30d
                    IS DISTINCT FROM c_shares_30d
        """

        mismatches = conn.execute(
            query,
            [target_date],
        ).fetchone()[0]

        # ----------------------------------------------------
        # Count rows
        # ----------------------------------------------------

        rescan_rows = conn.execute(
            """
            SELECT COUNT(*)
            FROM rescan_metrics
            WHERE run_date = ?
            """,
            [target_date],
        ).fetchone()[0]

        cumulative_rows = conn.execute(
            """
            SELECT COUNT(*)
            FROM cumulative_metrics
            WHERE run_date = ?
            """,
            [target_date],
        ).fetchone()[0]

        # ----------------------------------------------------
        # Print result
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print(
            f"VALIDATION FOR {target_date}"
        )
        print("=" * 70)

        print(
            f"Rescan rows:      {rescan_rows}"
        )

        print(
            f"Cumulative rows:  {cumulative_rows}"
        )

        print(
            f"Mismatches:       {mismatches}"
        )

        if mismatches == 0:

            print()
            print(
                f"VALIDATION PASS: {target_date}"
            )
            print()

            return

        # ----------------------------------------------------
        # Show first mismatches
        # ----------------------------------------------------

        mismatch_query = """
            SELECT
                COALESCE(
                    r.user_id,
                    c.user_id
                ) AS user_id,

                r.is_active_today,
                c.is_active_today,

                r.is_active_7d,
                c.is_active_7d,

                r.is_active_30d,
                c.is_active_30d,

                r.likes_7d,
                c.likes_7d,

                r.comments_7d,
                c.comments_7d,

                r.shares_7d,
                c.shares_7d,

                r.likes_30d,
                c.likes_30d,

                r.comments_30d,
                c.comments_30d,

                r.shares_30d,
                c.shares_30d

            FROM rescan_metrics r

            FULL OUTER JOIN cumulative_metrics c
                ON r.user_id = c.user_id
               AND r.run_date = c.run_date

            WHERE COALESCE(
                r.run_date,
                c.run_date
            ) = ?::DATE

            AND (
                r.is_active_today
                    IS DISTINCT FROM c.is_active_today

                OR r.is_active_7d
                    IS DISTINCT FROM c.is_active_7d

                OR r.is_active_30d
                    IS DISTINCT FROM c.is_active_30d

                OR r.likes_7d
                    IS DISTINCT FROM c.likes_7d

                OR r.comments_7d
                    IS DISTINCT FROM c.comments_7d

                OR r.shares_7d
                    IS DISTINCT FROM c.shares_7d

                OR r.likes_30d
                    IS DISTINCT FROM c.likes_30d

                OR r.comments_30d
                    IS DISTINCT FROM c.comments_30d

                OR r.shares_30d
                    IS DISTINCT FROM c.shares_30d
            )

            ORDER BY 1

            LIMIT 10
        """

        rows = conn.execute(
            mismatch_query,
            [target_date],
        ).fetchall()

        print()
        print(
            "First mismatches:"
        )

        for row in rows:
            print(row)

        raise RuntimeError(
            f"Validation failed for {target_date}: "
            f"{mismatches} mismatch(es)"
        )

    finally:
        conn.close()


# ============================================================
# CLI
# ============================================================

def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Validate rescan_metrics against "
            "cumulative_metrics."
        )
    )

    parser.add_argument(
        "--date",
        required=True,
        help="Date to validate (YYYY-MM-DD).",
    )

    args = parser.parse_args()

    target_date = date.fromisoformat(
        args.date
    )

    validate(target_date)


if __name__ == "__main__":
    main()
