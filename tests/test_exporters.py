"""Tests for export functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from papertrail.exporters.bibtex import export_bibtex, to_bibtex_entry
from papertrail.exporters.csv_exporter import (
    export_metrics_csv,
    export_publications_csv,
)
from papertrail.exporters.json_exporter import (
    export_metrics_json,
    export_publications_json,
)
from papertrail.metrics.bibliometric import compute_metrics
from papertrail.models import Publication

# ---------------------------------------------------------------------------
# BibTeX
# ---------------------------------------------------------------------------


def test_bibtex_entry_article(sample_publications: list[Publication]) -> None:
    entry = to_bibtex_entry(sample_publications[0])
    assert "@article{" in entry
    assert "A Study on Everything" in entry
    assert "10.1234/everything" in entry
    assert "Nature" in entry


def test_bibtex_entry_cite_key(sample_publications: list[Publication]) -> None:
    entry = to_bibtex_entry(sample_publications[0])
    # cite key should start with last name "Doe" and year 2018
    assert "Doe2018" in entry


def test_bibtex_export_file(
    sample_publications: list[Publication], tmp_path: Path
) -> None:
    dest = tmp_path / "output.bib"
    export_bibtex(sample_publications, dest)
    content = dest.read_text()
    assert content.count("@article{") + content.count("@misc{") == len(
        sample_publications
    )


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------


def test_json_publications(
    sample_publications: list[Publication], tmp_path: Path
) -> None:
    dest = tmp_path / "pubs.json"
    export_publications_json(sample_publications, dest)
    loaded = json.loads(dest.read_text())
    assert isinstance(loaded, list)
    assert len(loaded) == len(sample_publications)
    assert loaded[0]["title"] == sample_publications[0].title


def test_json_metrics(sample_publications: list[Publication], tmp_path: Path) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    dest = tmp_path / "metrics.json"
    export_metrics_json(metrics, dest)
    loaded = json.loads(dest.read_text())
    assert loaded["h_index"] == metrics.h_index
    assert loaded["author_name"] == "Jane Doe"


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------


def test_csv_publications(
    sample_publications: list[Publication], tmp_path: Path
) -> None:
    dest = tmp_path / "pubs.csv"
    export_publications_csv(sample_publications, dest)
    df = pd.read_csv(dest)
    assert len(df) == len(sample_publications)
    assert "title" in df.columns
    assert "citation_count" in df.columns
    assert "impact_factor" in df.columns


def test_csv_metrics(sample_publications: list[Publication], tmp_path: Path) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    dest = tmp_path / "metrics.csv"
    export_metrics_csv(metrics, dest)
    df = pd.read_csv(dest)
    assert df.iloc[0]["h_index"] == metrics.h_index
    assert df.iloc[0]["author_name"] == "Jane Doe"
