from sqlalchemy import text
from warehouse.db import get_engine

def clean_duplicates():
    engine = get_engine()

    with engine.connect() as conn:

        # Remove duplicate fact_repo_scores — keep only the latest per repo per date
        conn.execute(text("""
            DELETE FROM fact_repo_scores
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM fact_repo_scores
                GROUP BY repo_id, snapshot_date
            )
        """))

        # Remove duplicate fact_repo_stats — keep only the latest per repo per date
        conn.execute(text("""
            DELETE FROM fact_repo_stats
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM fact_repo_stats
                GROUP BY repo_id, snapshot_date
            )
        """))

        conn.commit()
        print("✅ Duplicates cleaned from database.")

if __name__ == "__main__":
    clean_duplicates()