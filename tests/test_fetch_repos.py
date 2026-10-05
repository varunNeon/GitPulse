import pytest
import requests

from ingestion.fetch_repos import FetchError, fetch_repos_by_topic


class FakeResponse:
    status_code = 401

    def raise_for_status(self):
        raise requests.exceptions.HTTPError(response=self)


class FakeSession:
    def get(self, *args, **kwargs):
        return FakeResponse()


def test_fetch_repos_raises_clear_error_for_invalid_github_token():
    with pytest.raises(FetchError, match="GITHUB_TOKEN is invalid or expired"):
        fetch_repos_by_topic("machine-learning", session=FakeSession())
