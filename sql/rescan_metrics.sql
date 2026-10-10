CREATE OR REPLACE TABLE rescan_output AS

WITH events AS (
    SELECT
        CAST(user_id AS VARCHAR) AS user_id,
        event_type,
        CAST(event_ts AS TIMESTAMP) AS event_ts
    FROM read_parquet(
        '{parquet_glob}',
        hive_partitioning = true
    )
    WHERE event_ts >= CAST('{target_date}' AS DATE)
                      - INTERVAL {window_days} DAY
      AND event_ts < CAST('{target_date}' AS DATE)
                      + INTERVAL 1 DAY
),

metrics AS (
    SELECT
        user_id,

        MAX(
            CASE
                WHEN CAST(event_ts AS DATE)
                     = CAST('{target_date}' AS DATE)
                THEN 1
                ELSE 0
            END
        ) AS is_active_today,

        MAX(
            CASE
                WHEN event_ts >=
                    CAST('{target_date}' AS DATE)
                    - INTERVAL 7 DAY
                THEN 1
                ELSE 0
            END
        ) AS is_active_7d,

        MAX(
            CASE
                WHEN event_ts >=
                    CAST('{target_date}' AS DATE)
                    - INTERVAL 30 DAY
                THEN 1
                ELSE 0
            END
        ) AS is_active_30d,

        SUM(
            CASE
                WHEN event_type = 'like'
                 AND event_ts >=
                     CAST('{target_date}' AS DATE)
                     - INTERVAL 30 DAY
                THEN 1
                ELSE 0
            END
        ) AS likes_30d,

        SUM(
            CASE
                WHEN event_type = 'comment'
                 AND event_ts >=
                     CAST('{target_date}' AS DATE)
                     - INTERVAL 30 DAY
                THEN 1
                ELSE 0
            END
        ) AS comments_30d,

        SUM(
            CASE
                WHEN event_type = 'share'
                 AND event_ts >=
                     CAST('{target_date}' AS DATE)
                     - INTERVAL 30 DAY
                THEN 1
                ELSE 0
            END
        ) AS shares_30d

    FROM events

    GROUP BY user_id
)

SELECT
    user_id,
    CAST('{target_date}' AS DATE) AS target_date,
    CAST(is_active_today AS INTEGER) AS is_active_today,
    CAST(is_active_7d AS INTEGER) AS is_active_7d,
    CAST(is_active_30d AS INTEGER) AS is_active_30d,
    CAST(likes_30d AS BIGINT) AS likes_30d,
    CAST(comments_30d AS BIGINT) AS comments_30d,
    CAST(shares_30d AS BIGINT) AS shares_30d

FROM metrics;