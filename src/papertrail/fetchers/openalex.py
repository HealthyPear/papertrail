"""OpenAlex fetcher implementation.

Uses the `pyalex <https://github.com/J535D165/pyalex>`_ client to query the
`OpenAlex <https://openalex.org/>`_ API, which is free, open, and requires no
API key (though providing an e-mail address enables the *polite pool* with
higher rate limits).
"""

from __future__ import annotations

import pyalex
from pyalex import Authors, Works

from papertrail.exceptions import FetchError
from papertrail.fetchers.base import BaseFetcher
from papertrail.models import Affiliation, AuthorInfo, JournalInfo, Publication


class OpenAlexFetcher(BaseFetcher):
    """Fetcher backed by the OpenAlex REST API via *pyalex*.

    Args:
        email: Optional e-mail address.  When provided, requests are sent via
            the OpenAlex *polite pool*, which has higher rate limits.

    Example:
        >>> fetcher = OpenAlexFetcher(email="you@example.com")
        >>> authors = fetcher.search_authors("Marie Curie")
        >>> pubs = fetcher.fetch_publications(authors[0].id)
    """

    def __init__(self, email: str | None = None) -> None:
        if email:
            pyalex.config.email = email

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def search_authors(self, name: str) -> list[AuthorInfo]:
        """Search OpenAlex for authors matching *name*.

        Args:
            name: Full or partial author name.

        Returns:
            A list of :class:`~papertrail.models.AuthorInfo` objects sorted by
            relevance score.

        Raises:
            FetchError: If the API request fails.
        """
        try:
            raw_results = Authors().search(name).get()
        except Exception as exc:
            raise FetchError(f"Author search failed for '{name}'") from exc
        results = [item for item in raw_results if isinstance(item, dict)]
        return [self._parse_author(a) for a in results]

    def fetch_publications(
        self,
        author_id: str,
        *,
        max_results: int | None = None,
    ) -> list[Publication]:
        """Fetch publications for an author from OpenAlex.

        Args:
            author_id: OpenAlex author ID URL
                (e.g. ``"https://openalex.org/A123456789"``).
            max_results: Maximum number of publications to return.
                ``None`` fetches all available works.

        Returns:
            A list of :class:`~papertrail.models.Publication` objects ordered
            by descending publication year.

        Raises:
            FetchError: If the API request fails.
        """
        try:
            query = (
                Works()
                .filter(authorships={"author": {"id": author_id}})
                .sort(publication_year="desc")
            )
            publications: list[Publication] = []
            for page in query.paginate(per_page=200):
                for raw in page:
                    if not isinstance(raw, dict):
                        continue
                    publications.append(self._parse_work(raw))
                    if max_results is not None and len(publications) >= max_results:
                        return publications
            return publications
        except Exception as exc:
            raise FetchError(
                f"Failed to fetch publications for author ID '{author_id}'"
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_author(data: dict[str, object]) -> AuthorInfo:
        """Convert a raw OpenAlex author record into an AuthorInfo model."""
        affiliations: list[Affiliation] = []
        raw_insts = data.get("last_known_institutions")
        institutions = raw_insts if isinstance(raw_insts, list) else []
        for inst in institutions:
            if isinstance(inst, dict):
                affiliations.append(
                    Affiliation(
                        name=str(inst.get("display_name", "")),
                        country=OpenAlexFetcher._as_optional_str(
                            inst.get("country_code")
                        ),
                    )
                )
        return AuthorInfo(
            id=str(data.get("id", "")),
            name=str(data.get("display_name", "")),
            orcid=OpenAlexFetcher._as_optional_str(data.get("orcid")),
            affiliations=affiliations,
        )

    @staticmethod
    def _parse_work(data: dict[str, object]) -> Publication:
        """Convert a raw OpenAlex work record into a Publication model."""
        authors = OpenAlexFetcher._parse_authors(data)
        journal = OpenAlexFetcher._parse_journal(data)
        primary_location = data.get("primary_location")
        location = primary_location if isinstance(primary_location, dict) else {}

        # Abstract reconstruction from inverted index
        abstract: str | None = None
        inverted = data.get("abstract_inverted_index")
        if isinstance(inverted, dict):
            validated = {
                str(word): [int(pos) for pos in positions if isinstance(pos, int)]
                for word, positions in inverted.items()
                if isinstance(positions, list)
            }
            abstract = OpenAlexFetcher._reconstruct_abstract(validated)

        # DOI - strip the resolver prefix if present
        doi = data.get("doi")
        if isinstance(doi, str) and doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/") :]

        # Landing page URL
        url = OpenAlexFetcher._as_optional_str(location.get("landing_page_url"))

        publication_year = data.get("publication_year")
        cited_by_count = data.get("cited_by_count")
        open_access = data.get("open_access")
        oa = open_access if isinstance(open_access, dict) else {}
        return Publication(
            id=str(data.get("id", "")),
            title=str(data.get("title") or ""),
            year=int(publication_year) if isinstance(publication_year, int) else 0,
            doi=doi if isinstance(doi, str) else None,
            authors=authors,
            journal=journal,
            citation_count=int(cited_by_count)
            if isinstance(cited_by_count, int)
            else 0,
            abstract=abstract,
            type=OpenAlexFetcher._as_optional_str(data.get("type")),
            open_access=bool(oa.get("is_oa", False)),
            url=url,
        )

    @staticmethod
    def _parse_authors(data: dict[str, object]) -> list[AuthorInfo]:
        """Parse authorship records into a list of authors."""
        raw_authorships = data.get("authorships")
        authorships = raw_authorships if isinstance(raw_authorships, list) else []
        authors: list[AuthorInfo] = []
        for authorship in authorships:
            if not isinstance(authorship, dict):
                continue
            raw_author = authorship.get("author")
            raw_insts = authorship.get("institutions")
            institutions = raw_insts if isinstance(raw_insts, list) else []
            affiliations = [
                Affiliation(
                    name=str(inst.get("display_name", "")),
                    country=OpenAlexFetcher._as_optional_str(inst.get("country_code")),
                )
                for inst in institutions
                if isinstance(inst, dict)
            ]
            if isinstance(raw_author, dict):
                authors.append(
                    AuthorInfo(
                        id=OpenAlexFetcher._as_optional_str(raw_author.get("id")),
                        name=str(raw_author.get("display_name", "")),
                        orcid=OpenAlexFetcher._as_optional_str(raw_author.get("orcid")),
                        affiliations=affiliations,
                    )
                )
        return authors

    @staticmethod
    def _parse_journal(data: dict[str, object]) -> JournalInfo | None:
        """Parse primary source metadata into journal info."""
        primary_location = data.get("primary_location")
        if not isinstance(primary_location, dict):
            return None
        source = primary_location.get("source")
        if not isinstance(source, dict) or not source:
            return None

        raw_issn = source.get("issn")
        if isinstance(raw_issn, str):
            issn_list = [raw_issn]
        elif isinstance(raw_issn, list):
            issn_list = [str(item) for item in raw_issn]
        else:
            issn_list = []

        impact_factor_raw = source.get("2yr_mean_citedness")
        impact_factor = (
            float(impact_factor_raw)
            if isinstance(impact_factor_raw, (float, int))
            else None
        )

        return JournalInfo(
            id=OpenAlexFetcher._as_optional_str(source.get("id")),
            name=str(source.get("display_name", "")),
            issn=issn_list,
            publisher=OpenAlexFetcher._as_optional_str(source.get("publisher")),
            impact_factor=impact_factor,
        )

    @staticmethod
    def _as_optional_str(value: object) -> str | None:
        """Return value as string when possible, otherwise ``None``."""
        return value if isinstance(value, str) else None

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict[str, list[int]]) -> str:
        """Reconstruct plain-text abstract from OpenAlex inverted index.

        Args:
            inverted_index: Mapping of ``word -> [position, ...]``.

        Returns:
            Reconstructed abstract string.
        """
        if not inverted_index:
            return ""
        max_pos = max(pos for positions in inverted_index.values() for pos in positions)
        words: list[str] = [""] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(words)
