"""Tests for the ImpactFactorDatabase."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from papertrail.metrics.impact_factor import ImpactFactorDatabase
from papertrail.models import JournalInfo, Publication


@pytest.fixture()
def tmp_csv(tmp_path: Path) -> Path:
    content = textwrap.dedent(
        """\
        issn,year,impact_factor
        0028-0836,2018,41.5
        0028-0836,2020,49.96
        0036-8075,2019,41.8
        """
    )
    p = tmp_path / "if_data.csv"
    p.write_text(content)
    return p


@pytest.fixture()
def tmp_json(tmp_path: Path) -> Path:
    data = {
        "0028-0836": {"2018": 41.5, "2020": 49.96},
        "0036-8075": {"2019": 41.8},
    }
    p = tmp_path / "if_data.json"
    p.write_text(json.dumps(data))
    return p


def test_load_csv(tmp_csv: Path) -> None:
    db = ImpactFactorDatabase()
    db.load_csv(tmp_csv)
    assert db.get_impact_factor("0028-0836", 2018) == 41.5


def test_load_json(tmp_json: Path) -> None:
    db = ImpactFactorDatabase()
    db.load_json(tmp_json)
    assert db.get_impact_factor("0028-0836", 2020) == 49.96


def test_tolerance_lookup(tmp_csv: Path) -> None:
    db = ImpactFactorDatabase()
    db.load_csv(tmp_csv)
    # 2019 not in data, but 2018 is within tolerance=1
    result = db.get_impact_factor("0028-0836", 2019, tolerance=1)
    assert result == 41.5


def test_missing_issn(tmp_csv: Path) -> None:
    db = ImpactFactorDatabase()
    db.load_csv(tmp_csv)
    assert db.get_impact_factor("9999-9999", 2020) is None


def test_enrich_publications(tmp_csv: Path) -> None:
    db = ImpactFactorDatabase()
    db.load_csv(tmp_csv)
    pubs = [
        Publication(
            id="W1",
            title="Test",
            year=2018,
            journal=JournalInfo(name="Nature", issn=["0028-0836"]),
            citation_count=10,
        )
    ]
    enriched = db.enrich_publications(pubs)
    assert enriched[0].journal is not None
    assert enriched[0].journal.impact_factor == 41.5
    assert enriched[0].journal.impact_factor_year == 2018


def test_enrich_no_journal() -> None:
    db = ImpactFactorDatabase()
    pubs = [Publication(id="W1", title="No journal", year=2020, citation_count=0)]
    enriched = db.enrich_publications(pubs)
    assert enriched[0].journal is None
