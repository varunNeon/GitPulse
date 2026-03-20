import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
BASE_URL = "https://api.github.com"

TOPICS = [
    "machine-learning",
    "deep-learning",
    "llm",
    "computer-vision",
    "data-engineering",
    "mlops",
    "pytorch",
    "transformers"
]

def fetch_repos_by_topic(topic, max_repos=25):
    repos = []
    url = f"{BASE_URL}/search/repositories"
    params = {
        "q": f"topic:{topic} stars:>100",
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        data = response.json()
        repos = data.get("items", [])
        print(f"✅ Fetched {len(repos)} repos for topic: {topic}")
    else:
        print(f"❌ Failed for topic {topic}: {response.status_code}")

    return repos

def fetch_all_repos():
    all_repos = []
    for topic in TOPICS:
        repos = fetch_repos_by_topic(topic)
        all_repos.extend(repos)
    print(f"\n✅ Total repos fetched: {len(all_repos)}")
    return all_repos

if __name__ == "__main__":
    fetch_all_repos()