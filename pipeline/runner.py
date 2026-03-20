from datetime import datetime
from ingestion.fetch_repos import fetch_all_repos
from pipeline.transform import transform_repos
from pipeline.load import load_repos, load_repo_stats

def run_pipeline():
    print("🚀 GitPulse pipeline starting...\n")

    print("📡 Step 1: Fetching repos from GitHub API...")
    raw_repos = fetch_all_repos()

    print("\n🔧 Step 2: Transforming and cleaning data...")
    cleaned_repos = transform_repos(raw_repos)

    print("\n💾 Step 3: Loading into PostgreSQL...")
    load_repos(cleaned_repos)
    load_repo_stats(cleaned_repos)

    print("\n✅ Pipeline run complete!")

    # Write timestamp of successful pipeline run to file
    with open("last_updated.txt", "w") as f:
        f.write(datetime.now().strftime('%d %b %Y · %H:%M'))

if __name__ == "__main__":
    run_pipeline()