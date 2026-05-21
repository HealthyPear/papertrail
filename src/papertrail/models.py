"""Pydantic data models for the papertrail package."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Affiliation(BaseModel):
    """Institutional affiliation of an author.

    Attributes:
        name: Full name of the institution.
        country: Two-letter ISO country code, if available.
    """

    name: str
    country: str | None = None


class AuthorInfo(BaseModel):
    """Identifies a single author on a publication.

    Attributes:
        id: Unique identifier (e.g. OpenAlex author ID URL).
        name: Full display name.
        orcid: ORCID identifier URL, if available.
        affiliations: Institutional affiliations associated with this authorship.
    """

    id: str | None = None
    name: str
    orcid: str | None = None
    affiliations: list[Affiliation] = Field(default_factory=list)


class JournalInfo(BaseModel):
    """Journal or venue metadata.

    Attributes:
        id: Unique identifier (e.g. OpenAlex source ID URL).
        name: Full journal/venue name.
        issn: List of ISSN numbers (print and electronic).
        publisher: Publisher name.
        impact_factor: Impact factor or proxy metric (e.g. OpenAlex
            ``2yr_mean_citedness``) at or near the year of publication.
        impact_factor_year: Year the impact factor value corresponds to.
    """

    id: str | None = None
    name: str
    issn: list[str] = Field(default_factory=list)
    publisher: str | None = None
    impact_factor: float | None = None
    impact_factor_year: int | None = None


class Publication(BaseModel):
    """A single scientific publication.

    Attributes:
        id: Unique identifier (e.g. OpenAlex work ID URL).
        title: Publication title.
        year: Publication year.
        doi: Digital Object Identifier (without the ``https://doi.org/`` prefix).
        authors: Ordered list of authors.
        journal: Journal or venue metadata.
        citation_count: Total citations received.
        abstract: Plain-text abstract, if available.
        type: Publication type string (e.g. ``"journal-article"``,
            ``"proceedings-article"``).
        refereed: Whether this record is marked as refereed by the source,
            when available (not provided by all data sources).
        open_access: Whether the publication is openly accessible.
        url: Landing-page URL for the publication.
    """

    id: str
    title: str
    year: int
    doi: str | None = None
    authors: list[AuthorInfo] = Field(default_factory=list)
    journal: JournalInfo | None = None
    citation_count: int = 0
    abstract: str | None = None
    type: str | None = None
    refereed: bool | None = None
    open_access: bool = False
    url: str | None = None


class AuthorMetrics(BaseModel):
    """Aggregated bibliometric metrics for an author.

    Attributes:
        author_name: Display name used to retrieve publications.
        openalex_id: OpenAlex author ID URL, if resolved.
        orcid: ORCID identifier URL, if available.
        total_publications: Total number of retrieved publications.
        total_citations: Sum of citation counts across all publications.
        h_index: Hirsch index.
        i10_index: Number of publications with at least 10 citations.
        average_citations_per_paper: Mean citations per publication.
        most_cited_paper_title: Title of the most-cited publication.
        most_cited_paper_citations: Citation count of the most-cited publication.
        publications_per_year: Mapping of year -> publication count.
        citations_per_year: Mapping of year -> sum of citations for that year's pubs.
        publications_refereed_per_year: Mapping of year -> refereed publication count.
        publications_non_refereed_per_year: Mapping of year -> non-refereed publication count.
        publications_refereed_normalized_per_year: Mapping of year -> refereed
            publication fraction within that year.
        publications_non_refereed_normalized_per_year: Mapping of year ->
            non-refereed publication fraction within that year.
        citations_refereed_per_year: Mapping of year -> citations from refereed
            publications.
        citations_non_refereed_per_year: Mapping of year -> citations from
            non-refereed publications.
        citations_refereed_normalized_per_year: Mapping of year -> refereed
            citation fraction within that year.
        citations_non_refereed_normalized_per_year: Mapping of year ->
            non-refereed citation fraction within that year.
        index_timeseries_total: Mapping of index name -> year -> value.
        index_timeseries_refereed: Mapping of index name -> year -> value.
        index_indicators_total: Mapping of index name -> snapshot value.
        index_indicators_refereed: Mapping of index name -> snapshot value.
        publication_types: Mapping of publication type -> publication count.
        journals_per_publication: Mapping of journal/venue name -> publication count.
        citation_distribution: Mapping of citation bucket -> publication count.
        refereed_publications: Count of publications marked as refereed.
        non_refereed_publications: Count of publications marked as non-refereed.
        avg_impact_factor: Mean impact factor across publications with IF data.
        median_impact_factor: Median impact factor across publications with IF data.
    """

    author_name: str
    openalex_id: str | None = None
    orcid: str | None = None
    total_publications: int = 0
    total_citations: int = 0
    h_index: int = 0
    i10_index: int = 0
    average_citations_per_paper: float = 0.0
    most_cited_paper_title: str | None = None
    most_cited_paper_citations: int = 0
    publications_per_year: dict[int, int] = Field(default_factory=dict)
    citations_per_year: dict[int, int] = Field(default_factory=dict)
    publications_refereed_per_year: dict[int, int] = Field(default_factory=dict)
    publications_non_refereed_per_year: dict[int, int] = Field(default_factory=dict)
    publications_refereed_normalized_per_year: dict[int, float] = Field(
        default_factory=dict
    )
    publications_non_refereed_normalized_per_year: dict[int, float] = Field(
        default_factory=dict
    )
    citations_refereed_per_year: dict[int, int] = Field(default_factory=dict)
    citations_non_refereed_per_year: dict[int, int] = Field(default_factory=dict)
    citations_refereed_normalized_per_year: dict[int, float] = Field(
        default_factory=dict
    )
    citations_non_refereed_normalized_per_year: dict[int, float] = Field(
        default_factory=dict
    )
    index_timeseries_total: dict[str, dict[int, float]] = Field(default_factory=dict)
    index_timeseries_refereed: dict[str, dict[int, float]] = Field(
        default_factory=dict
    )
    index_indicators_total: dict[str, float] = Field(default_factory=dict)
    index_indicators_refereed: dict[str, float] = Field(default_factory=dict)
    publication_types: dict[str, int] = Field(default_factory=dict)
    journals_per_publication: dict[str, int] = Field(default_factory=dict)
    citation_distribution: dict[str, int] = Field(default_factory=dict)
    refereed_publications: int | None = None
    non_refereed_publications: int | None = None
    avg_impact_factor: float | None = None
    median_impact_factor: float | None = None
