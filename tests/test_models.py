"""Tests for Pydantic data models."""

from __future__ import annotations

from papertrail.models import (
    AuthorInfo,
    AuthorMetrics,
    JournalInfo,
    Publication,
)


def test_publication_defaults() -> None:
    pub = Publication(id="W1", title="Test", year=2023)
    assert pub.citation_count == 0
    assert pub.open_access is False
    assert pub.authors == []
    assert pub.journal is None


def test_journal_info_optional_fields() -> None:
    j = JournalInfo(name="Nature")
    assert j.issn == []
    assert j.impact_factor is None


def test_author_info_affiliations_default() -> None:
    a = AuthorInfo(name="Jane Doe")
    assert a.affiliations == []
    assert a.orcid is None


def test_author_metrics_defaults() -> None:
    m = AuthorMetrics(author_name="Test Author")
    assert m.h_index == 0
    assert m.total_citations == 0
    assert m.publications_per_year == {}


def test_publication_model_copy() -> None:
    pub = Publication(id="W1", title="Title", year=2020, citation_count=5)
    updated = pub.model_copy(update={"citation_count": 10})
    assert updated.citation_count == 10
    assert pub.citation_count == 5  # original unchanged
