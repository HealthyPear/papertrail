"""Abstract base class for publication fetchers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from papertrail.models import AuthorInfo, Publication


class BaseFetcher(ABC):
    """Interface that all data-source fetchers must implement.

    Subclass this to add support for additional bibliographic APIs
    (e.g. Semantic Scholar, Crossref, PubMed).
    """

    @abstractmethod
    def search_authors(self, name: str) -> list[AuthorInfo]:
        """Search for authors matching the given name.

        Args:
            name: Full or partial author name.

        Returns:
            A list of matching :class:`~papertrail.models.AuthorInfo` objects,
            ordered by relevance (most relevant first).

        Raises:
            FetchError: If the underlying API request fails.
        """

    @abstractmethod
    def fetch_publications(
        self,
        author_id: str,
        *,
        max_results: int | None = None,
    ) -> list[Publication]:
        """Fetch all publications for a specific author.

        Args:
            author_id: The unique author identifier understood by this fetcher.
            max_results: Optional cap on the number of publications returned.
                ``None`` means fetch all available.

        Returns:
            A list of :class:`~papertrail.models.Publication` objects.

        Raises:
            FetchError: If the underlying API request fails.
        """

    def fetch_analyze_metrics(
        self,
        publications: list[Publication],
    ) -> dict[str, Any] | None:
        """Fetch optional source-native analysis metrics for publications.

        Most fetchers will return ``None``. Data sources that provide native
        analysis endpoints (e.g. ADS Metrics API) can override this hook.
        """
        return None
