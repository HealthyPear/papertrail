"""Tests for bibliometric metric computation."""

from __future__ import annotations

from papertrail.metrics.bibliometric import (
    compute_h_index,
    compute_i10_index,
    compute_metrics,
)
from papertrail.models import Publication


def test_h_index_basic(sample_publications: list[Publication]) -> None:
    h = compute_h_index(sample_publications)
    # citations: [120, 45, 8, 2, 0] -> h=3 (3 pubs with >=3 citations)
    assert h == 3


def test_h_index_empty() -> None:
    assert compute_h_index([]) == 0


def test_h_index_single_paper() -> None:
    pubs = [Publication(id="X", title="T", year=2020, citation_count=1)]
    assert compute_h_index(pubs) == 1


def test_i10_index(sample_publications: list[Publication]) -> None:
    # pubs with >=10 citations: W1 (120), W2 (45), W3 (8 - below threshold)
    assert compute_i10_index(sample_publications) == 2


def test_i10_index_empty() -> None:
    assert compute_i10_index([]) == 0


def test_compute_metrics_counts(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    assert m.total_publications == 5
    assert m.total_citations == 120 + 45 + 8 + 2 + 0
    assert m.h_index == 3
    assert m.i10_index == 2


def test_compute_metrics_most_cited(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    assert m.most_cited_paper_title == "A Study on Everything"
    assert m.most_cited_paper_citations == 120


def test_compute_metrics_avg_impact_factor(
    sample_publications: list[Publication],
) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    # Only W1 and W2 have IF data: (64.8 + 47.7) / 2 = 56.25
    assert m.avg_impact_factor is not None
    assert abs(m.avg_impact_factor - 56.25) < 0.01


def test_compute_metrics_empty() -> None:
    m = compute_metrics("Ghost Author", [])
    assert m.total_publications == 0
    assert m.h_index == 0
    assert m.avg_impact_factor is None
    assert m.refereed_publications is None
    assert m.non_refereed_publications is None


def test_publications_per_year(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    assert m.publications_per_year[2020] == 1
    assert m.publications_per_year[2018] == 1


def test_publication_type_counts(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    assert m.publication_types["journal-article"] == 3
    assert m.publication_types["unknown"] == 2


def test_journal_counts(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    assert m.journals_per_publication["Nature"] == 1
    assert m.journals_per_publication["Science"] == 1


def test_citation_distribution(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    assert m.citation_distribution["0"] == 1
    assert m.citation_distribution["1-4"] == 1
    assert m.citation_distribution["5-9"] == 1
    assert m.citation_distribution["10-24"] == 0
    assert m.citation_distribution["25-49"] == 1
    assert m.citation_distribution["50-99"] == 0
    assert m.citation_distribution["100+"] == 1


def test_refereed_yearly_splits_and_normalization() -> None:
    pubs = [
        Publication(id="1", title="A", year=2020, citation_count=10, refereed=True),
        Publication(id="2", title="B", year=2020, citation_count=5, refereed=False),
        Publication(id="3", title="C", year=2021, citation_count=6, refereed=True),
    ]
    m = compute_metrics("Jane Doe", pubs)

    assert m.publications_refereed_per_year[2020] == 1
    assert m.publications_non_refereed_per_year[2020] == 1
    assert abs(m.publications_refereed_normalized_per_year[2020] - 0.5) < 1e-9
    assert abs(m.publications_non_refereed_normalized_per_year[2020] - 0.5) < 1e-9

    assert m.citations_refereed_per_year[2020] == 10
    assert m.citations_non_refereed_per_year[2020] == 5
    assert abs(m.citations_refereed_normalized_per_year[2020] - (10 / 15)) < 1e-9
    assert abs(m.citations_non_refereed_normalized_per_year[2020] - (5 / 15)) < 1e-9


def test_index_timeseries_present(sample_publications: list[Publication]) -> None:
    m = compute_metrics("Jane Doe", sample_publications)
    for index_name in ("h", "m", "g", "i10", "i100"):
        assert index_name in m.index_timeseries_total


def test_ads_indicator_snapshots() -> None:
    pubs = [Publication(id="1", title="A", year=2020, citation_count=10)]
    analysis = {
        "indicators": {"h": 3, "m": 0.6, "riq": 42},
        "indicators refereed": {"h": 2, "m": 0.5, "riq": 30},
    }
    m = compute_metrics("Jane Doe", pubs, source_analysis=analysis)
    assert m.index_indicators_total["h"] == 3
    assert m.index_indicators_total["m"] == 0.6
    assert m.index_indicators_total["riq"] == 42
    assert m.index_indicators_refereed["h"] == 2
    assert m.index_indicators_refereed["m"] == 0.5
    assert m.index_indicators_refereed["riq"] == 30
