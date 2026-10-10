from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_sql(name):
    return (
        ROOT
        / "sql"
        / name
    ).read_text(
        encoding="utf-8"
    ).lower()


def test_rescan_contract():

    sql = read_sql(
        "rescan_metrics.sql"
    )

    assert "event_ts >=" in sql
    assert "group by user_id" in sql
    assert "is_active_today" in sql
    assert "is_active_7d" in sql
    assert "is_active_30d" in sql
    assert "likes_30d" in sql
    assert "comments_30d" in sql


def test_cumulative_join_contract():

    sql = read_sql(
        "cumulative_join.sql"
    )

    assert "full outer join" in sql
    assert "coalesce" in sql
    assert "list_prepend" in sql
    assert "list_slice" in sql


def test_extract_contract():

    sql = read_sql(
        "cumulative_extract.sql"
    )

    assert "list_sum" in sql
    assert "activity_array" in sql
    assert "likes_array" in sql