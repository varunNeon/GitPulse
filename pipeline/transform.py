from datetime import datetime, timezone

def parse_repo(repo: dict) -> dict:
    return {
        "repo_id": repo.get("id"),
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "description": repo.get("description", "")[:500] if repo.get("description") else "",
        "language": repo.get("language", "Unknown"),
        "topics": ", ".join(repo.get("topics", [])),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "html_url": repo.get("html_url"),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "watchers": repo.get("watchers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
    }

def transform_repos(raw_repos: list) -> list:
    seen = set()
    cleaned = []

    for repo in raw_repos:
        repo_id = repo.get("id")

        if repo_id in seen:
            continue
        seen.add(repo_id)

        cleaned.append(parse_repo(repo))

    print(f"✅ Transformed {len(cleaned)} unique repos (removed {len(raw_repos) - len(cleaned)} duplicates)")
    return cleaned