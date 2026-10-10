from pathlib import Path

import duckdb


def test_generated_partition_schema(
    tmp_path
):
    parquet = (
        tmp_path
        / "events.parquet"
    )

    conn = duckdb.connect()

    conn.execute(
        f"""
        COPY (
            SELECT
                '1'::VARCHAR AS user_id,
                'view'::VARCHAR AS event_type,
                TIMESTAMP '2023-01-01 12:00:00'
                    AS event_ts
        )
        TO '{parquet}'
        (FORMAT PARQUET)
        """
    )

    columns = conn.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{parquet}')
        """
    ).fetchall()

    names = [
        row[0]
        for row in columns
    ]

    assert names == [
        "user_id",
        "event_type",
        "event_ts"
    ]

    conn.close()