"""Tests for AuthorProfile using a mock fetcher."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from papertrail.author import AuthorProfile
from papertrail.fetchers.base import BaseFetcher
from papertrail.models import AuthorInfo, Publication


class MockFetcher(BaseFetcher):
    """Fetcher that returns canned data without network access."""

    def search_authors(self, name: str) -> list[AuthorInfo]:
        return [AuthorInfo(id="https://openalex.org/A9999", name=name)]

    def fetch_publications(
        self,
        author_id: str,
        *,
        max_results: int | None = None,
    ) -> list[Publication]:
        pubs = [
            Publication(
                id=f"W{i}", title=f"Paper {i}", year=2020, citation_count=10 - i
            )
            for i in range(1, 6)
        ]
        return pubs[:max_results] if max_results else pubs


def test_fetch_uses_best_candidate() -> None:
    profile = AuthorProfile("Jane Doe", fetcher=MockFetcher())
    profile.fetch()
    assert len(profile.publications) == 5


def test_fetch_max_results() -> None:
    profile = AuthorProfile("Jane Doe", fetcher=MockFetcher())
    profile.fetch(max_results=2)
    assert len(profile.publications) == 2


def test_metrics_after_fetch() -> None:
    profile = AuthorProfile("Jane Doe", fetcher=MockFetcher())
    profile.fetch()
    m = profile.metrics()
    assert m.total_publications == 5
    assert m.h_index >= 1


def test_fetch_explicit_author_id() -> None:
    profile = AuthorProfile("Jane Doe", fetcher=MockFetcher())
    profile.fetch(author_id="https://openalex.org/A1234")
    assert profile.author_info is not None
    assert profile.author_info.id == "https://openalex.org/A1234"


def test_chaining() -> None:
    profile = AuthorProfile("Jane Doe", fetcher=MockFetcher()).fetch()
    assert isinstance(profile, AuthorProfile)


def test_repr() -> None:
    profile = AuthorProfile("Jane Doe", fetcher=MockFetcher()).fetch()
    assert "Jane Doe" in repr(profile)
    assert "5" in repr(profile)


def test_fetch_writes_local_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "papertrail_cache.sqlite3"
    profile = AuthorProfile(
        "Jane Doe",
        fetcher=MockFetcher(),
        cache_path=cache_path,
    ).fetch()

    assert profile.metrics().total_publications == 5
    assert cache_path.exists()

    with sqlite3.connect(cache_path) as conn:
        author_rows = conn.execute("SELECT COUNT(*) FROM authors").fetchone()
        publication_rows = conn.execute("SELECT COUNT(*) FROM publications").fetchone()
        metric_rows = conn.execute(
            "SELECT COUNT(*) FROM author_metrics_snapshots"
        ).fetchone()

    assert author_rows is not None and author_rows[0] == 1
    assert publication_rows is not None and publication_rows[0] == 5
    assert metric_rows is not None and metric_rows[0] >= 1


def test_disable_local_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "papertrail_cache.sqlite3"
    AuthorProfile(
        "Jane Doe",
        fetcher=MockFetcher(),
        enable_local_cache=False,
        cache_path=cache_path,
    ).fetch()

    assert not cache_path.exists()
