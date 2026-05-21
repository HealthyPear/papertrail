"""Shared test fixtures."""

from __future__ import annotations

import pytest

from papertrail.models import AuthorInfo, JournalInfo, Publication

AUTHOR_NAME = "Jane Doe"


@pytest.fixture()
def sample_publications() -> list[Publication]:
    """A small, representative list of publications for unit tests."""
    return [
        Publication(
            id="W1",
            title="A Study on Everything",
            year=2018,
            doi="10.1234/everything",
            authors=[AuthorInfo(name=AUTHOR_NAME), AuthorInfo(name="Bob Smith")],
            journal=JournalInfo(
                name="Nature",
                issn=["0028-0836"],
                impact_factor=64.8,
                impact_factor_year=2018,
            ),
            citation_count=120,
            type="journal-article",
            open_access=True,
        ),
        Publication(
            id="W2",
            title="Deep Dive into Nothing",
            year=2020,
            doi="10.1234/nothing",
            authors=[AuthorInfo(name=AUTHOR_NAME)],
            journal=JournalInfo(
                name="Science",
                issn=["0036-8075"],
                impact_factor=47.7,
                impact_factor_year=2020,
            ),
            citation_count=45,
            type="journal-article",
        ),
        Publication(
            id="W3",
            title="Musing About Something",
            year=2022,
            authors=[AuthorInfo(name=AUTHOR_NAME)],
            citation_count=8,
            type="journal-article",
        ),
        Publication(
            id="W4",
            title="Thoughts on Anything",
            year=2023,
            authors=[AuthorInfo(name=AUTHOR_NAME)],
            citation_count=2,
        ),
        Publication(
            id="W5",
            title="Notes on Nothing Much",
            year=2019,
            authors=[AuthorInfo(name=AUTHOR_NAME)],
            citation_count=0,
        ),
    ]
