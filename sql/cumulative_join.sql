INSERT INTO cumulative_state
(
    user_id,
    target_date,
    activity_array,
    likes_array,
    comments_array,
    shares_array
)

WITH joined AS (

    SELECT

        COALESCE(
            t.user_id,
            y.user_id
        ) AS user_id,

        CAST('{target_date}' AS DATE)
            AS target_date,

        list_slice(
            list_prepend(
                COALESCE(
                    t.active_today,
                    0
                ),
                COALESCE(
                    y.activity_array,
                    list_resize(
                        CAST([] AS INTEGER[]),
                        {window_days},
                        0
                    )
                )
            ),
            1,
            {window_days}
        ) AS activity_array,

        list_slice(
            list_prepend(
                COALESCE(
                    t.likes_today,
                    0
                ),
                COALESCE(
                    y.likes_array,
                    list_resize(
                        CAST([] AS BIGINT[]),
                        {window_days},
                        0
                    )
                )
            ),
            1,
            {window_days}
        ) AS likes_array,

        list_slice(
            list_prepend(
                COALESCE(
                    t.comments_today,
                    0
                ),
                COALESCE(
                    y.comments_array,
                    list_resize(
                        CAST([] AS BIGINT[]),
                        {window_days},
                        0
                    )
                )
            ),
            1,
            {window_days}
        ) AS comments_array,

        list_slice(
            list_prepend(
                COALESCE(
                    t.shares_today,
                    0
                ),
                COALESCE(
                    y.shares_array,
                    list_resize(
                        CAST([] AS BIGINT[]),
                        {window_days},
                        0
                    )
                )
            ),
            1,
            {window_days}
        ) AS shares_array

    FROM daily_staging t

    FULL OUTER JOIN cumulative_state y

        ON t.user_id = y.user_id

       AND y.target_date =
           CAST('{previous_date}' AS DATE)
)

SELECT
    user_id,
    target_date,
    activity_array,
    likes_array,
    comments_array,
    shares_array

FROM joined

WHERE list_sum(activity_array) > 0;