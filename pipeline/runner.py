from datetime import datetime, timezone

from common.logging_config import get_logger
from common.runtime import get_run_date
from ingestion.fetch_repos import fetch_all_repos
from pipeline.load import load_repo_stats, load_repos
from pipeline.transform import transform_repos
from warehouse.schema import create_tables


logger = get_logger(__name__)


def run_pipeline():
    run_date = get_run_date()
    logger.info("GitPulse pipeline starting for snapshot date %s.", run_date.isoformat())

    create_tables()

    raw_repos = fetch_all_repos()
    cleaned_repos = transform_repos(raw_repos)

    if not cleaned_repos:
        raise RuntimeError("Pipeline produced no repositories after transformation.")

    load_repos(cleaned_repos)
    load_repo_stats(cleaned_repos, snapshot_date=run_date)

    logger.info("Pipeline run completed successfully for %s.", run_date.isoformat())

    with open("last_updated.txt", "w", encoding="utf-8") as handle:
        handle.write(datetime.now(timezone.utc).strftime("%d %b %Y | %H:%M UTC"))


if __name__ == "__main__":
    run_pipeline()
