import os
from typing import List

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common.logging_config import get_logger


load_dotenv()
logger = get_logger(__name__)

BASE_URL = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = int(os.getenv("GITHUB_TIMEOUT_SECONDS", "20"))
MIN_FETCH_SUCCESS_RATIO = float(os.getenv("MIN_FETCH_SUCCESS_RATIO", "1.0"))
MIN_EXPECTED_REPOS = int(os.getenv("MIN_EXPECTED_REPOS", "100"))

TOPICS = [
    "machine-learning",
    "deep-learning",
    "llm",
    "computer-vision",
    "data-engineering",
    "mlops",
    "pytorch",
    "transformers",
]


class FetchError(RuntimeError):
    """Raised when GitHub ingestion is incomplete or invalid."""


def _build_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    return headers


def _build_session():
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(_build_headers())
    return session


def fetch_repos_by_topic(topic: str, session: requests.Session, max_repos: int = 25) -> List[dict]:
    url = f"{BASE_URL}/search/repositories"
    params = {
        "q": f"topic:{topic} stars:>100",
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos,
    }

    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        if status_code == 403:
            logger.error("GitHub API rate limit or auth failure for topic '%s'.", topic)
        raise FetchError(f"GitHub request failed for topic '{topic}' with status {status_code}.") from exc
    except requests.exceptions.RequestException as exc:
        raise FetchError(f"GitHub request failed for topic '{topic}'.") from exc

    data = response.json()
    items = data.get("items")
    if not isinstance(items, list):
        raise FetchError(f"GitHub response for topic '{topic}' did not include a valid items list.")

    logger.info("Fetched %s repositories for topic '%s'.", len(items), topic)
    return items


def fetch_all_repos() -> List[dict]:
    session = _build_session()
    all_repos: List[dict] = []
    successful_topics = 0

    for topic in TOPICS:
        repos = fetch_repos_by_topic(topic, session=session)
        all_repos.extend(repos)
        successful_topics += 1

    minimum_successes = max(1, int(len(TOPICS) * MIN_FETCH_SUCCESS_RATIO))
    if successful_topics < minimum_successes:
        raise FetchError(
            f"Only fetched {successful_topics}/{len(TOPICS)} topics successfully. "
            f"Minimum required: {minimum_successes}."
        )

    if len(all_repos) < MIN_EXPECTED_REPOS:
        raise FetchError(
            f"Fetched only {len(all_repos)} repositories, below minimum expected {MIN_EXPECTED_REPOS}."
        )

    logger.info("Fetched %s repositories across %s topics.", len(all_repos), successful_topics)
    return all_repos


if __name__ == "__main__":
    fetch_all_repos()
