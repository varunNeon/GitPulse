from pipeline.transform import transform_repos


def test_transform_repos_removes_duplicates_by_repo_id():
    raw_repos = [
        {"id": 1, "name": "repo-a", "full_name": "owner/repo-a"},
        {"id": 1, "name": "repo-a", "full_name": "owner/repo-a"},
        {"id": 2, "name": "repo-b", "full_name": "owner/repo-b"},
    ]

    cleaned = transform_repos(raw_repos)

    assert len(cleaned) == 2
    assert {repo["repo_id"] for repo in cleaned} == {1, 2}
