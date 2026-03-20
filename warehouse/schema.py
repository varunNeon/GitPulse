from sqlalchemy import text
from warehouse.db import get_engine

def create_tables():
    engine = get_engine()
    
    with engine.connect() as conn:
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
                snapshot_date DATE,
                stars INT,
                forks INT,
                watchers INT,
                open_issues INT,
                contributors_count INT,
                commit_count_last30 INT
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_repo_scores (
                id SERIAL PRIMARY KEY,
                repo_id BIGINT REFERENCES dim_repos(repo_id),
                snapshot_date DATE,
                star_velocity FLOAT,
                issue_resolution_rate FLOAT,
                contributor_growth FLOAT,
                impact_score FLOAT
            );
        """))

        conn.commit()
        print("✅ All tables created successfully!")

if __name__ == "__main__":
    create_tables()