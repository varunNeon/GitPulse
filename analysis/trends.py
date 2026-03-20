import pandas as pd
from sqlalchemy import text
from warehouse.db import get_engine

def detect_trends():
    engine = get_engine()

    # Pull all historical snapshots for every repo
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT 
                r.name,
                r.full_name,
                r.language,
                r.topics,
                s.snapshot_date,
                s.stars,
                s.forks,
                s.open_issues
            FROM dim_repos r
            JOIN fact_repo_stats s ON r.repo_id = s.repo_id
            ORDER BY r.repo_id, s.snapshot_date ASC
        """), conn)

    if df.empty:
        print("❌ No data found.")
        return None

    # --- Calculate star growth between snapshots ---
    # Group by repo, then calculate difference between consecutive star counts
    df = df.sort_values(["full_name", "snapshot_date"])
    df["star_growth"] = df.groupby("full_name")["stars"].diff()

    # --- Only keep repos with more than one snapshot ---
    # Can't calculate growth with just one data point
    trend_df = df.dropna(subset=["star_growth"])

    if trend_df.empty:
        print("⚠️  Only one day of data available — run the pipeline again tomorrow to see growth trends.")
        print("\n📊 Current snapshot (sorted by stars):")
        snapshot = df[["name", "language", "stars", "forks"]]\
            .sort_values("stars", ascending=False)\
            .head(10)
        print(snapshot.to_string(index=False))
        return df

    # --- Fastest growing repos ---
    latest_growth = trend_df.sort_values("snapshot_date").groupby("full_name").last().reset_index()
    fastest = latest_growth.sort_values("star_growth", ascending=False).head(10)

    print("🚀 Fastest Growing Repos (by star growth):")
    print(fastest[["name", "language", "stars", "star_growth"]].to_string(index=False))

    # --- Anomaly detection --- 
    # A repo is anomalous if its growth is more than 2 standard deviations above the mean
    mean_growth = latest_growth["star_growth"].mean()
    std_growth = latest_growth["star_growth"].std()
    threshold = mean_growth + (2 * std_growth)

    anomalies = latest_growth[latest_growth["star_growth"] > threshold]

    if not anomalies.empty:
        print(f"\n🚨 Anomaly Alert — Unusual growth detected (threshold: +{threshold:.0f} stars):")
        print(anomalies[["name", "stars", "star_growth"]].to_string(index=False))
    else:
        print("\n✅ No anomalies detected — growth patterns look normal.")

    return trend_df

if __name__ == "__main__":
    detect_trends()