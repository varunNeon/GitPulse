import pandas as pd
from sqlalchemy import text
from warehouse.db import get_engine
from datetime import date

def calculate_impact_scores():
    engine = get_engine()

    with engine.connect() as conn:
        # Fetch latest snapshot per repo — prevents duplicates
        df = pd.read_sql(text("""
            SELECT 
                r.repo_id, r.name, r.full_name, r.language,
                r.topics, s.snapshot_date, s.stars, s.forks,
                s.watchers, s.open_issues
            FROM dim_repos r
            JOIN fact_repo_stats s ON r.repo_id = s.repo_id
            WHERE s.snapshot_date = (
                SELECT MAX(snapshot_date)
                FROM fact_repo_stats
                WHERE repo_id = r.repo_id
            )
        """), conn)

    if df.empty:
        print("❌ No data found. Run the pipeline first.")
        return None

    # Remove any remaining duplicates
    df = df.drop_duplicates(subset=["repo_id"])

    # --- Star Velocity (normalized 0-1) ---
    df["star_velocity"] = (df["stars"] - df["stars"].min()) / (df["stars"].max() - df["stars"].min())

    # --- Fork Score ---
    df["fork_ratio"] = df["forks"] / (df["stars"] + 1)
    df["fork_score"] = (df["fork_ratio"] - df["fork_ratio"].min()) / (df["fork_ratio"].max() - df["fork_ratio"].min())

    # --- Issue Activity Score ---
    df["issue_score"] = (df["open_issues"] - df["open_issues"].min()) / (df["open_issues"].max() - df["open_issues"].min())

    # --- Composite Impact Score: Stars 50%, Forks 30%, Issues 20% ---
    df["impact_score"] = (
        0.50 * df["star_velocity"] +
        0.30 * df["fork_score"] +
        0.20 * df["issue_score"]
    ).round(4)

    # --- Save to database, delete today's scores first to prevent duplicates ---
    engine2 = get_engine()
    with engine2.connect() as conn:
        conn.execute(text("""
            DELETE FROM fact_repo_scores WHERE snapshot_date = :today
        """), {"today": date.today()})

        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_repo_scores (
                    repo_id, snapshot_date, star_velocity,
                    issue_resolution_rate, contributor_growth, impact_score
                ) VALUES (
                    :repo_id, :snapshot_date, :star_velocity,
                    :issue_resolution_rate, :contributor_growth, :impact_score
                )
            """), {
                "repo_id": int(row["repo_id"]),
                "snapshot_date": date.today(),
                "star_velocity": float(row["star_velocity"]),
                "issue_resolution_rate": float(row["fork_score"]),
                "contributor_growth": float(row["issue_score"]),
                "impact_score": float(row["impact_score"])
            })
        conn.commit()

    print(f"✅ Impact scores calculated for {len(df)} repos")

    top10 = df[["name", "language", "stars", "forks", "impact_score"]]\
        .sort_values("impact_score", ascending=False).head(10)
    print("\n🏆 Top 10 Repos by Impact Score:")
    print(top10.to_string(index=False))

    return df


def find_hidden_gems():
    """
    Hidden gems = repos with high fork ratio but below median stars.
    These are underrated repos gaining momentum most people haven't noticed yet.
    """
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

    df = df.drop_duplicates(subset=["full_name"])

    # Gems = below median stars but above average fork ratio
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