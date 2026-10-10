CREATE OR REPLACE TABLE daily_staging AS

SELECT
    CAST(user_id AS VARCHAR) AS user_id,

    1 AS active_today,

    SUM(
        CASE
            WHEN event_type = 'like'
            THEN 1
            ELSE 0
        END
    )::BIGINT AS likes_today,

    SUM(
        CASE
            WHEN event_type = 'comment'
            THEN 1
            ELSE 0
        END
    )::BIGINT AS comments_today,

    SUM(
        CASE
            WHEN event_type = 'share'
            THEN 1
            ELSE 0
        END
    )::BIGINT AS shares_today

FROM read_parquet(
    '{today_file}'
)

GROUP BY user_id;