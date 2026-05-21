"""Bibliometric metric computation."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

from papertrail.models import AuthorMetrics, Publication


def compute_h_index(publications: list[Publication]) -> int:
    """Compute the Hirsch *h*-index.

    The h-index is the largest integer *h* such that at least *h* publications
    each have at least *h* citations.

    Args:
        publications: List of publications with citation counts.

    Returns:
        The h-index as a non-negative integer.

    Example:
        >>> from papertrail.models import Publication
        >>> pubs = [
        ...     Publication(id=str(i), title="T", year=2020, citation_count=c)
        ...     for i, c in enumerate([10, 8, 5, 4, 3])
        ... ]
        >>> compute_h_index(pubs)
        4
    """
    citations = sorted((p.citation_count for p in publications), reverse=True)
    h = 0
    for rank, count in enumerate(citations, start=1):
        if count >= rank:
            h = rank
        else:
            break
    return h


def compute_i10_index(publications: list[Publication]) -> int:
    """Compute the i10-index.

    The i10-index is the number of publications with at least 10 citations.

    Args:
        publications: List of publications with citation counts.

    Returns:
        The i10-index as a non-negative integer.

    Example:
        >>> from papertrail.models import Publication
        >>> pubs = [
        ...     Publication(id=str(i), title="T", year=2020, citation_count=c)
        ...     for i, c in enumerate([15, 10, 8, 2])
        ... ]
        >>> compute_i10_index(pubs)
        2
    """
    return sum(1 for p in publications if p.citation_count >= 10)


def compute_i100_index(publications: list[Publication]) -> int:
    """Compute the i100-index.

    The i100-index is the number of publications with at least 100 citations.
    """
    return sum(1 for p in publications if p.citation_count >= 100)


def compute_g_index(publications: list[Publication]) -> int:
    """Compute Egghe's g-index."""
    citations = sorted((p.citation_count for p in publications), reverse=True)
    running = 0
    g = 0
    for rank, count in enumerate(citations, start=1):
        running += count
        if running >= rank * rank:
            g = rank
        else:
            break
    return g


def compute_metrics(
    author_name: str,
    publications: list[Publication],
    *,
    openalex_id: str | None = None,
    orcid: str | None = None,
    source_analysis: dict[str, Any] | None = None,
) -> AuthorMetrics:
    """Compute the full set of bibliometric metrics for an author.

    Args:
        author_name: Display name of the author.
        publications: Complete list of the author's publications.
        openalex_id: OpenAlex author ID URL, if resolved.
        orcid: ORCID identifier URL, if available.

    Returns:
        An :class:`~papertrail.models.AuthorMetrics` instance populated with
        all computed fields.

    Example:
        >>> from papertrail.models import Publication
        >>> pubs = [Publication(id="1", title="A", year=2020, citation_count=10)]
        >>> m = compute_metrics("Jane Doe", pubs)
        >>> m.h_index
        1
    """
    if not publications:
        return AuthorMetrics(
            author_name=author_name,
            openalex_id=openalex_id,
            orcid=orcid,
        )

    total_citations = sum(p.citation_count for p in publications)
    h = compute_h_index(publications)
    i10 = compute_i10_index(publications)
    avg_cit = total_citations / len(publications)

    most_cited = max(publications, key=lambda p: p.citation_count)

    pubs_per_year: dict[int, int] = {}
    cites_per_year: dict[int, int] = {}
    pubs_ref_per_year: dict[int, int] = {}
    pubs_non_ref_per_year: dict[int, int] = {}
    cites_ref_per_year: dict[int, int] = {}
    cites_non_ref_per_year: dict[int, int] = {}
    for pub in publications:
        pubs_per_year[pub.year] = pubs_per_year.get(pub.year, 0) + 1
        cites_per_year[pub.year] = cites_per_year.get(pub.year, 0) + pub.citation_count
        if pub.refereed is True:
            pubs_ref_per_year[pub.year] = pubs_ref_per_year.get(pub.year, 0) + 1
            cites_ref_per_year[pub.year] = (
                cites_ref_per_year.get(pub.year, 0) + pub.citation_count
            )
        elif pub.refereed is False:
            pubs_non_ref_per_year[pub.year] = pubs_non_ref_per_year.get(pub.year, 0) + 1
            cites_non_ref_per_year[pub.year] = (
                cites_non_ref_per_year.get(pub.year, 0) + pub.citation_count
            )

    pub_ref_norm_per_year: dict[int, float] = {}
    pub_non_ref_norm_per_year: dict[int, float] = {}
    citation_ref_norm_per_year: dict[int, float] = {}
    citation_non_ref_norm_per_year: dict[int, float] = {}

    for year in sorted(set(pubs_ref_per_year) | set(pubs_non_ref_per_year)):
        ref = pubs_ref_per_year.get(year, 0)
        non_ref = pubs_non_ref_per_year.get(year, 0)
        total = ref + non_ref
        if total:
            pub_ref_norm_per_year[year] = ref / total
            pub_non_ref_norm_per_year[year] = non_ref / total

    for year in sorted(set(cites_ref_per_year) | set(cites_non_ref_per_year)):
        ref = cites_ref_per_year.get(year, 0)
        non_ref = cites_non_ref_per_year.get(year, 0)
        total = ref + non_ref
        if total:
            citation_ref_norm_per_year[year] = ref / total
            citation_non_ref_norm_per_year[year] = non_ref / total

    indices_total = _compute_index_timeseries(publications)
    indices_refereed = _compute_index_timeseries(
        [pub for pub in publications if pub.refereed is True]
    )

    ads_indices_total, ads_indices_refereed = _extract_ads_timeseries(source_analysis)
    for index_name, values in ads_indices_total.items():
        indices_total[index_name] = values
    for index_name, values in ads_indices_refereed.items():
        indices_refereed[index_name] = values

    indicator_total, indicator_refereed = _extract_ads_indicators(source_analysis)

    pub_type_counts = Counter((pub.type or "unknown") for pub in publications)
    journal_counts = Counter(
        pub.journal.name
        for pub in publications
        if pub.journal is not None and pub.journal.name
    )

    citation_distribution = {
        "0": 0,
        "1-4": 0,
        "5-9": 0,
        "10-24": 0,
        "25-49": 0,
        "50-99": 0,
        "100+": 0,
    }
    for pub in publications:
        count = max(pub.citation_count, 0)
        if count == 0:
            citation_distribution["0"] += 1
        elif count <= 4:
            citation_distribution["1-4"] += 1
        elif count <= 9:
            citation_distribution["5-9"] += 1
        elif count <= 24:
            citation_distribution["10-24"] += 1
        elif count <= 49:
            citation_distribution["25-49"] += 1
        elif count <= 99:
            citation_distribution["50-99"] += 1
        else:
            citation_distribution["100+"] += 1

    impact_factors = [
        p.journal.impact_factor
        for p in publications
        if p.journal is not None and p.journal.impact_factor is not None
    ]
    avg_if = statistics.mean(impact_factors) if impact_factors else None
    med_if = statistics.median(impact_factors) if impact_factors else None

    refereed_values = [p.refereed for p in publications if p.refereed is not None]
    refereed_count: int | None = None
    non_refereed_count: int | None = None
    if refereed_values:
        refereed_count = sum(1 for val in refereed_values if val)
        non_refereed_count = sum(1 for val in refereed_values if not val)

    return AuthorMetrics(
        author_name=author_name,
        openalex_id=openalex_id,
        orcid=orcid,
        total_publications=len(publications),
        total_citations=total_citations,
        h_index=h,
        i10_index=i10,
        average_citations_per_paper=round(avg_cit, 2),
        most_cited_paper_title=most_cited.title,
        most_cited_paper_citations=most_cited.citation_count,
        publications_per_year=pubs_per_year,
        citations_per_year=cites_per_year,
        publications_refereed_per_year=pubs_ref_per_year,
        publications_non_refereed_per_year=pubs_non_ref_per_year,
        publications_refereed_normalized_per_year=pub_ref_norm_per_year,
        publications_non_refereed_normalized_per_year=pub_non_ref_norm_per_year,
        citations_refereed_per_year=cites_ref_per_year,
        citations_non_refereed_per_year=cites_non_ref_per_year,
        citations_refereed_normalized_per_year=citation_ref_norm_per_year,
        citations_non_refereed_normalized_per_year=citation_non_ref_norm_per_year,
        index_timeseries_total=indices_total,
        index_timeseries_refereed=indices_refereed,
        index_indicators_total=indicator_total,
        index_indicators_refereed=indicator_refereed,
        publication_types=dict(pub_type_counts),
        journals_per_publication=dict(journal_counts),
        citation_distribution=citation_distribution,
        refereed_publications=refereed_count,
        non_refereed_publications=non_refereed_count,
        avg_impact_factor=round(avg_if, 4) if avg_if is not None else None,
        median_impact_factor=round(med_if, 4) if med_if is not None else None,
    )


def _compute_index_timeseries(publications: list[Publication]) -> dict[str, dict[int, float]]:
    """Compute cumulative index values by publication year."""
    if not publications:
        return {}

    by_year = sorted(publications, key=lambda pub: pub.year)
    first_year = by_year[0].year
    cumulative: list[Publication] = []
    series: dict[str, dict[int, float]] = {
        "h": {},
        "m": {},
        "g": {},
        "i10": {},
        "i100": {},
    }

    for year in sorted({pub.year for pub in by_year}):
        cumulative.extend(pub for pub in by_year if pub.year == year)
        h_index = compute_h_index(cumulative)
        series["h"][year] = float(h_index)
        series["g"][year] = float(compute_g_index(cumulative))
        series["i10"][year] = float(compute_i10_index(cumulative))
        series["i100"][year] = float(compute_i100_index(cumulative))
        span = max(year - first_year + 1, 1)
        series["m"][year] = h_index / span

    return series


def _extract_ads_timeseries(
    source_analysis: dict[str, Any] | None,
) -> tuple[dict[str, dict[int, float]], dict[str, dict[int, float]]]:
    """Extract ADS time-series payloads (total/refereed) into numeric year maps."""
    if not source_analysis:
        return {}, {}

    total_raw = source_analysis.get("time series")
    refereed_raw = source_analysis.get("time series refereed")

    return _normalize_ads_series(total_raw), _normalize_ads_series(refereed_raw)


def _normalize_ads_series(raw: Any) -> dict[str, dict[int, float]]:
    """Normalize ADS series data to ``index -> year(int) -> value(float)``."""
    if not isinstance(raw, dict):
        return {}

    normalized: dict[str, dict[int, float]] = {}
    for index_name, year_map in raw.items():
        if not isinstance(index_name, str) or not isinstance(year_map, dict):
            continue
        parsed: dict[int, float] = {}
        for year, value in year_map.items():
            if not isinstance(year, str) or not year.isdigit():
                continue
            if isinstance(value, (int, float)):
                parsed[int(year)] = float(value)
        if parsed:
            normalized[index_name] = parsed
    return normalized


def _extract_ads_indicators(
    source_analysis: dict[str, Any] | None,
) -> tuple[dict[str, float], dict[str, float]]:
    """Extract ADS indicator snapshot payloads (total/refereed)."""
    if not source_analysis:
        return {}, {}

    total_raw = source_analysis.get("indicators")
    refereed_raw = source_analysis.get("indicators refereed")
    return _normalize_ads_indicators(total_raw), _normalize_ads_indicators(refereed_raw)


def _normalize_ads_indicators(raw: Any) -> dict[str, float]:
    """Normalize ADS indicator payload to ``index -> value`` numeric map."""
    if not isinstance(raw, dict):
        return {}

    normalized: dict[str, float] = {}
    for index_name, value in raw.items():
        if not isinstance(index_name, str):
            continue
        if isinstance(value, (int, float)):
            normalized[index_name] = float(value)
    return normalized
