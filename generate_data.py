import argparse
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


EVENT_TYPES = np.array(
    ["like", "comment", "share", "view"]
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate partitioned synthetic user events."
    )

    parser.add_argument(
        "--users",
        type=int,
        default=int(os.getenv("NUM_USERS", "10000"))
    )

    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("DAYS_TO_GENERATE", "365"))
    )

    parser.add_argument(
        "--start-date",
        default=os.getenv("START_DATE", "2023-01-01")
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.getenv("SEED", "42"))
    )

    parser.add_argument(
        "--output",
        default=os.getenv("DATA_DIR", "data/events")
    )

    return parser.parse_args()


def generate_daily_events(
    target_date,
    num_users,
    rng
):
    """
    Generate deterministic synthetic activity for one day.

    The active-user probability contains:
    - weekly seasonality
    - stable user activity propensity
    - churn/reactivation behavior
    """

    date_obj = pd.Timestamp(target_date)

    # Weekly seasonality.
    weekday = date_obj.dayofweek

    weekday_factor = {
        0: 0.90,
        1: 1.00,
        2: 1.05,
        3: 1.10,
        4: 1.20,
        5: 0.80,
        6: 0.70,
    }[weekday]

    # Keep the default resource-friendly.
    # With 1M users this produces a sizeable dataset.
    base_probability = 0.035 * weekday_factor

    user_ids = np.arange(num_users)

    # Stable user propensity makes some users more active than others.
    user_propensity = rng.beta(
        2.0,
        20.0,
        size=num_users
    )

    # Normalize around 1.
    user_factor = np.clip(
        user_propensity / user_propensity.mean(),
        0.20,
        3.0
    )

    probabilities = np.clip(
        base_probability * user_factor,
        0.001,
        0.30
    )

    active_mask = rng.random(num_users) < probabilities

    active_users = user_ids[active_mask]

    if len(active_users) == 0:
        return pd.DataFrame(
            columns=["user_id", "event_type", "event_ts"]
        )

    # Each active user gets 1-3 events.
    events_per_user = rng.integers(
        1,
        4,
        size=len(active_users)
    )

    total_events = int(events_per_user.sum())

    repeated_users = np.repeat(
        active_users,
        events_per_user
    )

    event_types = rng.choice(
        EVENT_TYPES,
        size=total_events,
        p=[
            0.20,  # like
            0.10,  # comment
            0.05,  # share
            0.65,  # view
        ]
    )

    seconds_in_day = 24 * 60 * 60

    offsets = rng.integers(
        0,
        seconds_in_day,
        size=total_events
    )

    base_timestamp = pd.Timestamp(
        date_obj
    )

    timestamps = (
        base_timestamp
        + pd.to_timedelta(offsets, unit="s")
    )

    df = pd.DataFrame(
        {
            "user_id": repeated_users.astype(str),
            "event_type": event_types.astype(str),
            "event_ts": timestamps,
        }
    )

    df = df[
        [
            "user_id",
            "event_type",
            "event_ts",
        ]
    ]

    return df


def main():
    args = parse_args()

    if args.users <= 0:
        raise ValueError("--users must be greater than zero")

    if args.days <= 0:
        raise ValueError("--days must be greater than zero")

    start_date = pd.Timestamp(
        args.start_date
    )

    rng = np.random.default_rng(
        args.seed
    )

    os.makedirs(
        args.output,
        exist_ok=True
    )

    print("=" * 60)
    print("DATA GENERATION")
    print("=" * 60)
    print(f"Users      : {args.users:,}")
    print(f"Days       : {args.days}")
    print(f"Start date : {start_date.date()}")
    print(f"Seed       : {args.seed}")
    print(f"Output     : {args.output}")
    print()

    for day_number in range(args.days):

        target_date = (
            start_date
            + timedelta(days=day_number)
        )

        partition_dir = os.path.join(
            args.output,
            f"date={target_date.strftime('%Y-%m-%d')}"
        )

        os.makedirs(
            partition_dir,
            exist_ok=True
        )

        output_file = os.path.join(
            partition_dir,
            "events.parquet"
        )

        df = generate_daily_events(
            target_date=target_date,
            num_users=args.users,
            rng=rng
        )

        df.to_parquet(
            output_file,
            index=False
        )

        print(
            f"[{day_number + 1:03d}/{args.days}] "
            f"{target_date.date()} -> "
            f"{len(df):,} events"
        )

    print()
    print("Data generation completed.")


if __name__ == "__main__":
    main()