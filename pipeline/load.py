from sqlalchemy import text
from warehouse.db import get_engine
from datetime import date

def load_repos(cleaned_repos: list):
    engine = get_engine()
    inserted = 0
    updated = 0

    with engine.connect() as conn:
        for repo in cleaned_repos:
            existing = conn.execute(text(
                "SELECT repo_id FROM dim_repos WHERE repo_id = :repo_id"
            ), {"repo_id": repo["repo_id"]}).fetchone()

            if existing:
                conn.execute(text("""
                    UPDATE dim_repos SET
                        name = :name,
                        full_name = :full_name,
                        description = :description,
                        language = :language,
                        topics = :topics,
                        updated_at = :updated_at
                    WHERE repo_id = :repo_id
                """), repo)
                updated += 1
            else:
                conn.execute(text("""
                    INSERT INTO dim_repos (
                        repo_id, name, full_name, description,
                        language, topics, created_at, updated_at, html_url
                    ) VALUES (
                        :repo_id, :name, :full_name, :description,
                        :language, :topics, :created_at, :updated_at, :html_url
                    )
                """), repo)
                inserted += 1

        conn.commit()

    print(f"✅ Loaded repos — {inserted} inserted, {updated} updated")


def load_repo_stats(cleaned_repos: list):
    engine = get_engine()
    today = date.today()

    with engine.connect() as conn:
        for repo in cleaned_repos:
            conn.execute(text("""
                INSERT INTO fact_repo_stats (
                    repo_id, snapshot_date, stars, forks,
                    watchers, open_issues, contributors_count, commit_count_last30
                ) VALUES (
                    :repo_id, :snapshot_date, :stars, :forks,
                    :watchers, :open_issues, 0, 0
                )
            """), {
                "repo_id": repo["repo_id"],
                "snapshot_date": today,
                "stars": repo["stars"],
                "forks": repo["forks"],
                "watchers": repo["watchers"],
                "open_issues": repo["open_issues"]
            })

        conn.commit()

    print(f"✅ Loaded stats snapshot for {len(cleaned_repos)} repos — date: {today}")