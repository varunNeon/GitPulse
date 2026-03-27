from datetime import date

from sqlalchemy import text

from common.logging_config import get_logger
from warehouse.db import get_engine


logger = get_logger(__name__)


def _validate_snapshot_date(snapshot_date: date) -> None:
    if not isinstance(snapshot_date, date):
        raise ValueError("snapshot_date must be a datetime.date instance.")


def load_repos(cleaned_repos: list):
    if not cleaned_repos:
        raise ValueError("cleaned_repos cannot be empty.")

    engine = get_engine()
    with engine.begin() as conn:
        for repo in cleaned_repos:
            conn.execute(text("""
                INSERT INTO dim_repos (
                    repo_id, name, full_name, description,
                    language, topics, created_at, updated_at, html_url
                ) VALUES (
                    :repo_id, :name, :full_name, :description,
                    :language, :topics, :created_at, :updated_at, :html_url
                )
                ON CONFLICT (repo_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    full_name = EXCLUDED.full_name,
                    description = EXCLUDED.description,
                    language = EXCLUDED.language,
                    topics = EXCLUDED.topics,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at,
                    html_url = EXCLUDED.html_url
            """), repo)

    logger.info("Upserted %s repositories into dim_repos.", len(cleaned_repos))


def load_repo_stats(cleaned_repos: list, snapshot_date: date):
    if not cleaned_repos:
        raise ValueError("cleaned_repos cannot be empty.")
    _validate_snapshot_date(snapshot_date)

    engine = get_engine()
    with engine.begin() as conn:
        for repo in cleaned_repos:
            conn.execute(text("""
                INSERT INTO fact_repo_stats (
                    repo_id, snapshot_date, stars, forks,
                    watchers, open_issues, contributors_count, commit_count_last30
                ) VALUES (
                    :repo_id, :snapshot_date, :stars, :forks,
                    :watchers, :open_issues, 0, 0
                )
                ON CONFLICT (repo_id, snapshot_date) DO UPDATE SET
                    stars = EXCLUDED.stars,
                    forks = EXCLUDED.forks,
                    watchers = EXCLUDED.watchers,
                    open_issues = EXCLUDED.open_issues,
                    contributors_count = EXCLUDED.contributors_count,
                    commit_count_last30 = EXCLUDED.commit_count_last30
            """), {
                "repo_id": repo["repo_id"],
                "snapshot_date": snapshot_date,
                "stars": repo["stars"],
                "forks": repo["forks"],
                "watchers": repo["watchers"],
                "open_issues": repo["open_issues"],
            })

    logger.info(
        "Upserted stats snapshot for %s repos on %s.",
        len(cleaned_repos),
        snapshot_date.isoformat(),
    )
