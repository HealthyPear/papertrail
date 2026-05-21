"""Tests for ADS fetcher parsing helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from papertrail.fetchers.ads import ADSFetcher


def test_parse_doc_refereed_true() -> None:
    doc = {
        "bibcode": "2020A&A...123A...1P",
        "title": ["A test paper"],
        "author": ["Peresano, M.", "Doe, J."],
        "pub": "Astronomy & Astrophysics",
        "year": "2020",
        "doi": ["10.1234/test"],
        "citation_count": 12,
        "doctype": "article",
        "property": ["REFEREED"],
    }

    pub = ADSFetcher._parse_doc(doc)
    assert pub.id == "2020A&A...123A...1P"
    assert pub.title == "A test paper"
    assert pub.year == 2020
    assert pub.refereed is True
    assert pub.citation_count == 12


def test_parse_year_from_pubdate() -> None:
    year = ADSFetcher._parse_year(None, "2018-05")
    assert year == 2018


def test_init_loads_token_from_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    dotenv_value = "dotenv" + "-token"
    env_file.write_text(f"ADS_API_TOKEN={dotenv_value}\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ADS_API_TOKEN", raising=False)

    fetcher = ADSFetcher()

    assert fetcher._token == dotenv_value


def test_init_prefers_explicit_token_over_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ADS_API_TOKEN=dotenv-" + "token\n", encoding="utf-8")
    explicit_token = "explicit" + "-token"

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ADS_API_TOKEN", raising=False)

    fetcher = ADSFetcher(token=explicit_token)

    assert fetcher._token == explicit_token
