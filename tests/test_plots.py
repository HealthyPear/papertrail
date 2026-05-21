"""Tests for Bokeh plotting helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from papertrail.metrics.bibliometric import compute_metrics
from papertrail.models import Publication
from papertrail.plots import bokeh_plotter
from papertrail.plots.bokeh_plotter import (
    build_author_dashboard,
    build_citation_distribution_plot,
    build_citations_per_year_plot,
    build_index_snapshot_plot,
    build_index_timeseries_plots,
    build_publication_type_breakdown_plot,
    build_publications_per_year_plot,
    build_refereed_year_comparison_plot,
    build_refereed_breakdown_plot,
    build_top_journals_plot,
    export_dashboard,
)


def test_build_publications_per_year_plot(
    sample_publications: list[Publication],
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_publications_per_year_plot(metrics)
    assert plot.title.text == "Publications per year"


def test_build_citations_per_year_plot(
    sample_publications: list[Publication],
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_citations_per_year_plot(metrics)
    assert plot.title.text == "Citations per year"


def test_build_refereed_breakdown_plot_missing_data(
    sample_publications: list[Publication],
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_refereed_breakdown_plot(metrics)
    assert plot is None


def test_build_refereed_breakdown_plot_with_data() -> None:
    publications = [
        Publication(id="1", title="A", year=2020, refereed=True),
        Publication(id="2", title="B", year=2021, refereed=False),
        Publication(id="3", title="C", year=2021, refereed=True),
    ]
    metrics = compute_metrics("Jane Doe", publications)

    plot = build_refereed_breakdown_plot(metrics)

    assert plot is not None
    renderer = plot.renderers[0]
    source_data = renderer.data_source.data
    assert source_data["color"] == ["#2F855A", "#718096"]
    assert renderer.glyph.fill_color == "color"
    assert renderer.glyph.line_color == "color"


def test_build_citation_distribution_plot(
    sample_publications: list[Publication],
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_citation_distribution_plot(metrics)
    assert plot is not None
    assert plot.title.text == "Citation distribution"


def test_build_publication_type_breakdown_plot(
    sample_publications: list[Publication],
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_publication_type_breakdown_plot(metrics)
    assert plot is not None
    assert plot.title.text == "Publication type breakdown"


def test_build_top_journals_plot(sample_publications: list[Publication]) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_top_journals_plot(metrics)
    assert plot is not None
    assert plot.title.text == "Top journals / venues"


def test_build_refereed_year_comparison_plot_grouped_total() -> None:
    publications = [
        Publication(id="1", title="A", year=2020, citation_count=2, refereed=True),
        Publication(id="2", title="B", year=2020, citation_count=1, refereed=False),
    ]
    metrics = compute_metrics("Jane Doe", publications)
    plot = build_refereed_year_comparison_plot(
        metrics,
        value="publications",
        mode="grouped",
        normalized=False,
    )
    assert plot is not None
    assert plot.title.text == "Publications vs year (Grouped, Total)"


def test_build_refereed_year_comparison_plot_stacked_normalized() -> None:
    publications = [
        Publication(id="1", title="A", year=2020, citation_count=2, refereed=True),
        Publication(id="2", title="B", year=2020, citation_count=1, refereed=False),
    ]
    metrics = compute_metrics("Jane Doe", publications)
    plot = build_refereed_year_comparison_plot(
        metrics,
        value="citations",
        mode="stacked",
        normalized=True,
    )
    assert plot is not None
    assert plot.title.text == "Citations vs year (Stacked, Normalized)"


def test_build_index_timeseries_plots(sample_publications: list[Publication]) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_index_timeseries_plots(metrics)
    assert plot is not None
    assert plot.title.text == "Indices vs time (all in one, total vs refereed)"


def test_build_index_snapshot_plot(sample_publications: list[Publication]) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    plot = build_index_snapshot_plot(metrics)
    assert plot is not None
    assert plot.title.text == "Index snapshot (Total vs Refereed)"


def test_build_author_dashboard(sample_publications: list[Publication]) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    dashboard = build_author_dashboard(metrics)
    assert len(dashboard.children) == 2
    tabs_widget = dashboard.children[1]
    assert hasattr(tabs_widget, "tabs")
    assert len(tabs_widget.tabs) >= 5
    tab_titles = [tab.title for tab in tabs_widget.tabs]
    assert "Indices Over Time" in tab_titles


def test_export_dashboard_html(
    sample_publications: list[Publication], tmp_path: Path
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    destination = tmp_path / "dashboard.html"
    export_dashboard(metrics, destination, fmt="html")
    assert destination.exists()
    assert "Jane Doe" in destination.read_text(encoding="utf-8")


def test_export_dashboard_json(
    sample_publications: list[Publication], tmp_path: Path
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    destination = tmp_path / "dashboard.json"
    export_dashboard(metrics, destination, fmt="json")
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["target_id"] == "papertrail-dashboard"


def test_export_dashboard_png(
    sample_publications: list[Publication],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    destination = tmp_path / "dashboard.png"

    def fake_export_png(_: object, filename: Path) -> None:
        filename.write_bytes(b"PNG")

    monkeypatch.setattr(bokeh_plotter, "export_png", fake_export_png)

    export_dashboard(metrics, destination, fmt="png")

    assert destination.exists()
    assert destination.read_bytes() == b"PNG"


def test_export_dashboard_pdf(
    sample_publications: list[Publication],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = compute_metrics("Jane Doe", sample_publications)
    destination = tmp_path / "dashboard.pdf"

    def fake_export_png_dashboard(_: object, filename: Path) -> None:
        filename.write_bytes(b"PNG")

    def fake_write_pdf_from_png(_: Path, pdf_path: Path) -> None:
        pdf_path.write_bytes(b"PDF")

    monkeypatch.setattr(
        bokeh_plotter,
        "_export_png_dashboard",
        fake_export_png_dashboard,
    )
    monkeypatch.setattr(
        bokeh_plotter,
        "_write_pdf_from_png",
        fake_write_pdf_from_png,
    )

    export_dashboard(metrics, destination, fmt="pdf")

    assert destination.exists()
    assert destination.read_bytes() == b"PDF"
