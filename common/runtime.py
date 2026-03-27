import os
from datetime import date, datetime, timezone


def get_run_date() -> date:
    run_date = os.getenv("GITPULSE_RUN_DATE")
    if run_date:
        return datetime.strptime(run_date, "%Y-%m-%d").date()
    return datetime.now(timezone.utc).date()
