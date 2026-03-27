from typing import Optional

import pandas as pd
from sqlalchemy import text

from common.logging_config import get_logger
from common.runtime import get_run_date
from warehouse.db import get_engine


logger = get_logger(__name__)


def _safe_min_max_normalize(series: pd.Series) -> pd.Series:
    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series([0.0] * len(series), index=series.index, dtype="float64")

    denominator = maximum - minimum
    if denominator == 0:
        return pd.Series([0.0] * len(series), index=series.index, dtype="float64")

    return ((series - minimum) / denominator).fillna(0.0)


def calculate_impact_scores(snapshot_date=None) -> Optional[pd.DataFrame]:
    snapshot_date = snapshot_date or get_run_date()
    engine = get_engine()

    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                r.repo_id, r.name, r.full_name, r.language,
                r.topics, s.snapshot_date, s.stars, s.forks,
                s.watchers, s.open_issues
            FROM dim_repos r
            JOIN fact_repo_stats s ON r.repo_id = s.repo_id
            WHERE s.snapshot_date = :snapshot_date
        """), conn, params={"snapshot_date": snapshot_date})

    if df.empty:
        logger.error("No fact_repo_stats rows found for snapshot date %s.", snapshot_date)
        return None

    df = df.drop_duplicates(subset=["repo_id"]).copy()

    df["star_velocity"] = _safe_min_max_normalize(df["stars"])
    df["fork_ratio"] = df["forks"] / (df["stars"] + 1)
    df["fork_score"] = _safe_min_max_normalize(df["fork_ratio"])
    df["issue_score"] = _safe_min_max_normalize(df["open_issues"])

    df["impact_score"] = (
        0.50 * df["star_velocity"] +
        0.30 * df["fork_score"] +
        0.20 * df["issue_score"]
    ).round(4)

    engine = get_engine()
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_repo_scores (
                    repo_id, snapshot_date, star_velocity,
                    fork_score, issue_score, impact_score
                ) VALUES (
                    :repo_id, :snapshot_date, :star_velocity,
                    :fork_score, :issue_score, :impact_score
                )
                ON CONFLICT (repo_id, snapshot_date) DO UPDATE SET
                    star_velocity = EXCLUDED.star_velocity,
                    fork_score = EXCLUDED.fork_score,
                    issue_score = EXCLUDED.issue_score,
                    impact_score = EXCLUDED.impact_score
            """), {
                "repo_id": int(row["repo_id"]),
                "snapshot_date": snapshot_date,
                "star_velocity": float(row["star_velocity"]),
                "fork_score": float(row["fork_score"]),
                "issue_score": float(row["issue_score"]),
                "impact_score": float(row["impact_score"]),
            })

    logger.info("Calculated impact scores for %s repos on %s.", len(df), snapshot_date)

    top10 = (
        df[["name", "language", "stars", "forks", "impact_score"]]
        .sort_values("impact_score", ascending=False)
        .head(10)
    )
    logger.info("Top 10 repos by impact score:\n%s", top10.to_string(index=False))
    return df


def find_hidden_gems():
    engine = get_engine()

    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                r.name, r.full_name, r.language, r.topics, r.html_url,
                s.stars, s.forks, s.open_issues, s.snapshot_date
            FROM dim_repos r
            JOIN fact_repo_stats s ON r.repo_id = s.repo_id
            WHERE s.snapshot_date = (
                SELECT MAX(snapshot_date)
                FROM fact_repo_stats
                WHERE repo_id = r.repo_id
            )
        """), conn)

    if df.empty:
        return pd.DataFrame()

    df = df.drop_duplicates(subset=["full_name"]).copy()
    star_median = df["stars"].median()
    df["fork_ratio"] = df["forks"] / (df["stars"] + 1)
    avg_fork_ratio = df["fork_ratio"].mean()

    gems = df[
        (df["stars"] < star_median) &
        (df["fork_ratio"] > avg_fork_ratio)
    ].sort_values("fork_ratio", ascending=False).head(10)

    return gems


if __name__ == "__main__":
    calculate_impact_scores()
