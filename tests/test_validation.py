def test_metric_equality():

    rescan = {
        "is_active_today": 1,
        "is_active_7d": 1,
        "is_active_30d": 1,
        "likes_30d": 4,
        "comments_30d": 2,
        "shares_30d": 1,
    }

    cumulative = {
        "is_active_today": 1,
        "is_active_7d": 1,
        "is_active_30d": 1,
        "likes_30d": 4,
        "comments_30d": 2,
        "shares_30d": 1,
    }

    assert rescan == cumulative