from sqlalchemy import text

from common.logging_config import get_logger
from warehouse.db import get_engine


logger = get_logger(__name__)


def create_tables():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_repos (
                repo_id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                full_name VARCHAR(255),
                description TEXT,
                language VARCHAR(100),
                topics TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                html_url TEXT
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                name VARCHAR(255),
                company VARCHAR(255),
                location VARCHAR(255),
                followers INT,
                following INT,
                public_repos INT,
                created_at TIMESTAMP
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_repo_stats (
                id SERIAL PRIMARY KEY,
                repo_id BIGINT REFERENCES dim_repos(repo_id),
                snapshot_date DATE NOT NULL,
                stars INT NOT NULL,
                forks INT NOT NULL,
                watchers INT NOT NULL,
                open_issues INT NOT NULL,
                contributors_count INT NOT NULL DEFAULT 0,
                commit_count_last30 INT NOT NULL DEFAULT 0
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_repo_scores (
                id SERIAL PRIMARY KEY,
                repo_id BIGINT REFERENCES dim_repos(repo_id),
                snapshot_date DATE NOT NULL,
                star_velocity FLOAT NOT NULL,
                fork_score FLOAT NOT NULL DEFAULT 0,
                issue_score FLOAT NOT NULL DEFAULT 0,
                impact_score FLOAT NOT NULL
            );
        """))

        conn.execute(text("""
            DELETE FROM fact_repo_stats a
            USING fact_repo_stats b
            WHERE a.repo_id = b.repo_id
              AND a.snapshot_date = b.snapshot_date
              AND a.id < b.id;
        """))

        conn.execute(text("""
            DELETE FROM fact_repo_scores a
            USING fact_repo_scores b
            WHERE a.repo_id = b.repo_id
              AND a.snapshot_date = b.snapshot_date
              AND a.id < b.id;
        """))

        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_repo_stats_repo_date
            ON fact_repo_stats (repo_id, snapshot_date);
        """))

        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_repo_scores_repo_date
            ON fact_repo_scores (repo_id, snapshot_date);
        """))

        # Keep older column names usable for already-provisioned databases.
        conn.execute(text("""
            ALTER TABLE fact_repo_scores
            ADD COLUMN IF NOT EXISTS fork_score FLOAT;
        """))

        conn.execute(text("""
            ALTER TABLE fact_repo_scores
            ADD COLUMN IF NOT EXISTS issue_score FLOAT;
        """))

        logger.info("All tables created successfully.")


if __name__ == "__main__":
    create_tables()
