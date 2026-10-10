CREATE OR REPLACE TABLE cumulative_extracted_output AS

SELECT

    user_id,

    target_date,

    CASE
        WHEN list_sum(
            list_slice(
                activity_array,
                1,
                1
            )
        ) > 0
        THEN 1
        ELSE 0
    END AS is_active_today,

    CASE
        WHEN list_sum(
            list_slice(
                activity_array,
                1,
                7
            )
        ) > 0
        THEN 1
        ELSE 0
    END AS is_active_7d,

    CASE
        WHEN list_sum(
            list_slice(
                activity_array,
                1,
                30
            )
        ) > 0
        THEN 1
        ELSE 0
    END AS is_active_30d,

    list_sum(
        list_slice(
            likes_array,
            1,
            30
        )
    ) AS likes_30d,

    list_sum(
        list_slice(
            comments_array,
            1,
            30
        )
    ) AS comments_30d,

    list_sum(
        list_slice(
            shares_array,
            1,
            30
        )
    ) AS shares_30d

FROM cumulative_state

WHERE target_date =
    CAST('{target_date}' AS DATE);