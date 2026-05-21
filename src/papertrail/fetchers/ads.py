"""NASA ADS fetcher implementation.

This fetcher queries the NASA Astrophysics Data System (ADS) Search API,
which is often more complete for astronomy and astrophysics outputs,
including conference proceedings and non-refereed records.
"""

from __future__ import annotations

import os
from datetime import datetime
import json
from typing import Any
from urllib.request import Request, urlopen

import ads
from dotenv import find_dotenv, load_dotenv

from papertrail.exceptions import FetchError
from papertrail.fetchers.base import BaseFetcher
from papertrail.models import AuthorInfo, JournalInfo, Publication


class ADSFetcher(BaseFetcher):
    """Fetcher backed by the NASA ADS Search API.

    Args:
        token: ADS API token. If omitted, reads ``ADS_API_TOKEN`` from env.

    Raises:
        FetchError: If no token is available.
    """

    def __init__(self, token: str | None = None) -> None:
        load_dotenv(find_dotenv(usecwd=True), override=False)
        resolved_token = token or os.getenv("ADS_API_TOKEN")
        if not resolved_token:
            raise FetchError(
                "NASA ADS token is required. Set ADS_API_TOKEN in your environment "
                "or .env file, or pass a token explicitly."
            )
        self._token = resolved_token
        # Official ADS client uses module-level config.
        ads.config.token = resolved_token

    def search_authors(self, name: str) -> list[AuthorInfo]:
        """Return a single ADS candidate derived from the provided name.

        ADS does not provide a dedicated author-entity endpoint equivalent to
        OpenAlex author search for this package workflow. We therefore return a
        single candidate using the original input string as author query.
        """
        return [AuthorInfo(id=name, name=name)]

    def fetch_publications(
        self,
        author_id: str,
        *,
        max_results: int | None = None,
    ) -> list[Publication]:
        """Fetch ADS publications for an author query string.

        Args:
            author_id: ADS author query string (e.g. ``"Peresano, M"``).
            max_results: Optional cap on returned publications.

        Returns:
            List of parsed publications.
        """
        rows = 200
        publications: list[Publication] = []
        fields = [
            "bibcode",
            "title",
            "author",
            "pub",
            "pubdate",
            "year",
            "doi",
            "citation_count",
            "doctype",
            "property",
        ]
        query = ads.SearchQuery(
            q=f'author:"{author_id}"',
            fl=fields,
            rows=rows,
            sort="date desc",
        )

        try:
            for record in query:
                publications.append(self._parse_doc(record))
                if max_results is not None and len(publications) >= max_results:
                    break
        except Exception as exc:
            raise FetchError(
                f"Failed to fetch publications from ADS for author '{author_id}'"
            ) from exc

        return publications

    def fetch_analyze_metrics(
        self,
        publications: list[Publication],
    ) -> dict[str, Any] | None:
        """Fetch ADS native analyze metrics for the fetched publication set.

        Uses ADS Metrics API to retrieve indicator and time-series payloads
        when bibcodes are available.
        """
        bibcodes = [pub.id for pub in publications if pub.id]
        if not bibcodes:
            return None

        payload = {
            "bibcodes": bibcodes,
            "types": ["indicators", "timeseries", "histograms"],
            "histograms": ["publications", "citations"],
        }

        request = Request(
            "https://api.adsabs.harvard.edu/v1/metrics",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                raw_payload = response.read().decode("utf-8")
            data = json.loads(raw_payload)
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    @staticmethod
    def _parse_doc(doc: object) -> Publication:
        """Parse an ADS document record into a Publication model."""
        data = ADSFetcher._record_to_dict(doc)

        bibcode = str(data.get("bibcode") or "")
        title_list = data.get("title")
        title = ""
        if isinstance(title_list, list) and title_list:
            title = str(title_list[0])

        author_list = data.get("author")
        authors: list[AuthorInfo] = []
        if isinstance(author_list, list):
            authors = [AuthorInfo(name=str(a)) for a in author_list]

        year_raw = data.get("year")
        year = ADSFetcher._parse_year(year_raw, data.get("pubdate"))

        doi_raw = data.get("doi")
        doi: str | None = None
        if isinstance(doi_raw, list) and doi_raw:
            doi = str(doi_raw[0])
        elif isinstance(doi_raw, str):
            doi = doi_raw

        pub_name = data.get("pub")
        journal: JournalInfo | None = None
        if isinstance(pub_name, str) and pub_name:
            journal = JournalInfo(name=pub_name)

        properties = data.get("property")
        property_values: set[str] = set()
        if isinstance(properties, list):
            property_values = {str(p).upper() for p in properties}

        is_refereed = "REFEREED" in property_values

        citation_count_raw = data.get("citation_count")
        citation_count = (
            int(citation_count_raw) if isinstance(citation_count_raw, int) else 0
        )

        pub_type = data.get("doctype")
        pub_url = (
            f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract" if bibcode else None
        )

        return Publication(
            id=bibcode,
            title=title,
            year=year,
            doi=doi,
            authors=authors,
            journal=journal,
            citation_count=citation_count,
            type=str(pub_type) if pub_type is not None else None,
            open_access=False,
            url=pub_url,
            refereed=is_refereed,
        )

    @staticmethod
    def _record_to_dict(record: object) -> dict[str, object]:
        """Normalize ADS record objects and plain dicts to a dictionary."""
        if isinstance(record, dict):
            return record
        # ``ads`` returns Article-like objects exposing ``_raw`` and attribute values.
        raw = getattr(record, "_raw", None)
        if isinstance(raw, dict):
            return raw
        result: dict[str, object] = {}
        for field in (
            "bibcode",
            "title",
            "author",
            "pub",
            "pubdate",
            "year",
            "doi",
            "citation_count",
            "doctype",
            "property",
        ):
            value = getattr(record, field, None)
            if value is not None:
                result[field] = value
        return result

    @staticmethod
    def _parse_year(year_raw: object, pubdate_raw: object) -> int:
        """Extract an integer publication year from ADS fields."""
        if isinstance(year_raw, str) and year_raw.isdigit():
            return int(year_raw)
        if isinstance(year_raw, int):
            return year_raw

        if isinstance(pubdate_raw, str):
            # ADS commonly uses YYYY-MM format.
            try:
                return datetime.strptime(pubdate_raw[:7], "%Y-%m").year
            except ValueError:
                if len(pubdate_raw) >= 4 and pubdate_raw[:4].isdigit():
                    return int(pubdate_raw[:4])

        return 0
