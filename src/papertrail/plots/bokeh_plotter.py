"""Interactive Bokeh plots for papertrail metrics.

The first plotting set mirrors common ADS-style author views:

- publications per year
- citations per year
- refereed vs non-refereed breakdown (when available)

Plots can be exported as standalone HTML for interactive sharing or as Bokeh
JSON items for embedding into a web page.
"""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Literal

from bokeh.embed import json_item
from bokeh.io import output_file, save
from bokeh.io.export import export_png
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Div, HoverTool, TabPanel, Tabs
from bokeh.plotting import figure
from bokeh.transform import dodge
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from papertrail.exceptions import ExportError
from papertrail.models import AuthorMetrics

PlotFormat = Literal["html", "json", "png", "pdf"]
INTERACTIVE_TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
COUNT_FIELD = "@count"


def build_publications_per_year_plot(metrics: AuthorMetrics) -> object:
    """Build an interactive bar chart of publications per year.

    Args:
        metrics: Computed author metrics.

    Returns:
        A Bokeh figure.
    """
    years, counts = _sorted_year_mapping(metrics.publications_per_year)
    source = ColumnDataSource({"year": years, "count": counts})
    plot = figure(
        title="Publications per year",
        x_axis_label="Year",
        y_axis_label="Publications",
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )
    plot.vbar(x="year", top="count", width=0.8, source=source, color="#2B6CB0")
    plot.add_tools(
        HoverTool(tooltips=[("Year", "@year"), ("Publications", COUNT_FIELD)])
    )
    plot.xaxis.ticker = years
    return plot


def build_citations_per_year_plot(metrics: AuthorMetrics) -> object:
    """Build an interactive line chart of citations per publication year.

    Args:
        metrics: Computed author metrics.

    Returns:
        A Bokeh figure.
    """
    years, counts = _sorted_year_mapping(metrics.citations_per_year)
    source = ColumnDataSource({"year": years, "count": counts})
    plot = figure(
        title="Citations per year",
        x_axis_label="Year",
        y_axis_label="Citations",
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )
    plot.line(x="year", y="count", line_width=3, source=source, color="#C05621")
    plot.scatter(x="year", y="count", size=8, source=source, color="#C05621")
    plot.add_tools(HoverTool(tooltips=[("Year", "@year"), ("Citations", COUNT_FIELD)]))
    plot.xaxis.ticker = years
    return plot


def build_refereed_breakdown_plot(metrics: AuthorMetrics) -> object | None:
    """Build a bar chart comparing refereed and non-refereed publication counts.

    Args:
        metrics: Computed author metrics.

    Returns:
        A Bokeh figure when refereed metadata is available, otherwise ``None``.
    """
    if (
        metrics.refereed_publications is None
        or metrics.non_refereed_publications is None
    ):
        return None

    labels = ["Refereed", "Non-refereed"]
    counts = [metrics.refereed_publications, metrics.non_refereed_publications]
    source = ColumnDataSource(
        {
            "label": labels,
            "count": counts,
            "color": ["#2F855A", "#718096"],
        }
    )
    plot = figure(
        x_range=labels,
        title="Refereed breakdown",
        x_axis_label="Category",
        y_axis_label="Publications",
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )
    plot.vbar(
        x="label",
        top="count",
        width=0.6,
        source=source,
        fill_color="color",
        line_color="color",
    )
    plot.add_tools(HoverTool(tooltips=[("Category", "@label"), ("Count", COUNT_FIELD)]))
    return plot


def build_publication_type_breakdown_plot(metrics: AuthorMetrics) -> object | None:
    """Build a bar chart of publication counts by ADS/OpenAlex type."""
    if not metrics.publication_types:
        return None

    top_items = Counter(metrics.publication_types).most_common(10)
    labels = [item[0] for item in top_items]
    values = [item[1] for item in top_items]

    source = ColumnDataSource(
        {
            "label": labels,
            "count": values,
            "color": ["#4A5568"] * len(labels),
        }
    )
    plot = figure(
        x_range=labels,
        title="Publication type breakdown",
        x_axis_label="Type",
        y_axis_label="Publications",
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )
    plot.vbar(
        x="label",
        top="count",
        width=0.75,
        source=source,
        fill_color="color",
        line_color="color",
    )
    plot.xaxis.major_label_orientation = 0.8
    plot.add_tools(HoverTool(tooltips=[("Type", "@label"), ("Count", COUNT_FIELD)]))
    return plot


def build_top_journals_plot(metrics: AuthorMetrics) -> object | None:
    """Build a bar chart of top journals/venues by publication count."""
    if not metrics.journals_per_publication:
        return None

    top_items = Counter(metrics.journals_per_publication).most_common(10)
    labels = [item[0] for item in top_items]
    values = [item[1] for item in top_items]

    source = ColumnDataSource(
        {
            "label": labels,
            "count": values,
            "color": ["#805AD5"] * len(labels),
        }
    )
    plot = figure(
        y_range=list(reversed(labels)),
        title="Top journals / venues",
        x_axis_label="Publications",
        y_axis_label="Venue",
        sizing_mode="stretch_width",
        height=360,
        tools=INTERACTIVE_TOOLS,
    )
    plot.hbar(
        y="label",
        right="count",
        height=0.7,
        source=source,
        fill_color="color",
        line_color="color",
    )
    plot.add_tools(HoverTool(tooltips=[("Venue", "@label"), ("Count", COUNT_FIELD)]))
    return plot


def build_citation_distribution_plot(metrics: AuthorMetrics) -> object | None:
    """Build ADS-like citation bucket distribution from publication citation counts."""
    if not metrics.citation_distribution:
        return None

    labels = list(metrics.citation_distribution.keys())
    values = list(metrics.citation_distribution.values())
    source = ColumnDataSource(
        {
            "bucket": labels,
            "count": values,
            "color": ["#D69E2E"] * len(labels),
        }
    )

    plot = figure(
        x_range=labels,
        title="Citation distribution",
        x_axis_label="Citations per paper",
        y_axis_label="Publications",
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )
    plot.vbar(
        x="bucket",
        top="count",
        width=0.75,
        source=source,
        fill_color="color",
        line_color="color",
    )
    plot.add_tools(HoverTool(tooltips=[("Citations", "@bucket"), ("Count", COUNT_FIELD)]))
    return plot


def build_author_dashboard(metrics: AuthorMetrics) -> object:
    """Build the initial multi-plot dashboard for an author.

    Args:
        metrics: Computed author metrics.

    Returns:
        A Bokeh layout containing the available plots.
    """
    header = Div(
        text=(
            f"<h1>{metrics.author_name}</h1>"
            f"<p>Total publications: {metrics.total_publications} | "
            f"Total citations: {metrics.total_citations} | "
            f"h-index: {metrics.h_index}</p>"
        )
    )

    tabs: list[TabPanel] = [
        TabPanel(title="Publications/Year", child=build_publications_per_year_plot(metrics)),
        TabPanel(title="Citations/Year", child=build_citations_per_year_plot(metrics)),
    ]
    refereed_plot = build_refereed_breakdown_plot(metrics)
    if refereed_plot is not None:
        tabs.append(TabPanel(title="Refereed Split", child=refereed_plot))
    pub_grouped_total = build_refereed_year_comparison_plot(
        metrics,
        value="publications",
        mode="grouped",
        normalized=False,
    )
    if pub_grouped_total is not None:
        tabs.append(TabPanel(title="Pubs Grouped Total", child=pub_grouped_total))
    pub_stacked_total = build_refereed_year_comparison_plot(
        metrics,
        value="publications",
        mode="stacked",
        normalized=False,
    )
    if pub_stacked_total is not None:
        tabs.append(TabPanel(title="Pubs Stacked Total", child=pub_stacked_total))
    pub_grouped_norm = build_refereed_year_comparison_plot(
        metrics,
        value="publications",
        mode="grouped",
        normalized=True,
    )
    if pub_grouped_norm is not None:
        tabs.append(TabPanel(title="Pubs Grouped Norm", child=pub_grouped_norm))
    pub_stacked_norm = build_refereed_year_comparison_plot(
        metrics,
        value="publications",
        mode="stacked",
        normalized=True,
    )
    if pub_stacked_norm is not None:
        tabs.append(TabPanel(title="Pubs Stacked Norm", child=pub_stacked_norm))
    cit_grouped_total = build_refereed_year_comparison_plot(
        metrics,
        value="citations",
        mode="grouped",
        normalized=False,
    )
    if cit_grouped_total is not None:
        tabs.append(TabPanel(title="Cites Grouped Total", child=cit_grouped_total))
    cit_stacked_total = build_refereed_year_comparison_plot(
        metrics,
        value="citations",
        mode="stacked",
        normalized=False,
    )
    if cit_stacked_total is not None:
        tabs.append(TabPanel(title="Cites Stacked Total", child=cit_stacked_total))
    cit_grouped_norm = build_refereed_year_comparison_plot(
        metrics,
        value="citations",
        mode="grouped",
        normalized=True,
    )
    if cit_grouped_norm is not None:
        tabs.append(TabPanel(title="Cites Grouped Norm", child=cit_grouped_norm))
    cit_stacked_norm = build_refereed_year_comparison_plot(
        metrics,
        value="citations",
        mode="stacked",
        normalized=True,
    )
    if cit_stacked_norm is not None:
        tabs.append(TabPanel(title="Cites Stacked Norm", child=cit_stacked_norm))
    indices_timeseries_plot = build_index_timeseries_plots(metrics)
    if indices_timeseries_plot is not None:
        tabs.append(TabPanel(title="Indices Over Time", child=indices_timeseries_plot))
    index_snapshot_plot = build_index_snapshot_plot(metrics)
    if index_snapshot_plot is not None:
        tabs.append(TabPanel(title="Indices Snapshot", child=index_snapshot_plot))
    citation_distribution_plot = build_citation_distribution_plot(metrics)
    if citation_distribution_plot is not None:
        tabs.append(TabPanel(title="Citation Distribution", child=citation_distribution_plot))
    publication_type_plot = build_publication_type_breakdown_plot(metrics)
    if publication_type_plot is not None:
        tabs.append(TabPanel(title="Publication Types", child=publication_type_plot))
    top_journals_plot = build_top_journals_plot(metrics)
    if top_journals_plot is not None:
        tabs.append(TabPanel(title="Top Venues", child=top_journals_plot))

    tabs_view = Tabs(tabs=tabs, sizing_mode="stretch_width")
    return column(header, tabs_view, sizing_mode="stretch_width")


def build_refereed_year_comparison_plot(
    metrics: AuthorMetrics,
    *,
    value: Literal["publications", "citations"],
    mode: Literal["grouped", "stacked"],
    normalized: bool,
) -> object | None:
    """Build ADS-style refereed/non-refereed year plot in grouped or stacked mode."""
    if value == "publications":
        if normalized:
            ref_map = metrics.publications_refereed_normalized_per_year
            non_ref_map = metrics.publications_non_refereed_normalized_per_year
        else:
            ref_map = metrics.publications_refereed_per_year
            non_ref_map = metrics.publications_non_refereed_per_year
    else:
        if normalized:
            ref_map = metrics.citations_refereed_normalized_per_year
            non_ref_map = metrics.citations_non_refereed_normalized_per_year
        else:
            ref_map = metrics.citations_refereed_per_year
            non_ref_map = metrics.citations_non_refereed_per_year

    years = sorted(set(ref_map) | set(non_ref_map))
    if not years:
        return None

    x_values = [str(year) for year in years]
    ref_values = [ref_map.get(year, 0) for year in years]
    non_ref_values = [non_ref_map.get(year, 0) for year in years]

    title_value = "Publications" if value == "publications" else "Citations"
    title_mode = "Grouped" if mode == "grouped" else "Stacked"
    title_norm = "Normalized" if normalized else "Total"
    y_label = "Fraction" if normalized else title_value

    source = ColumnDataSource(
        {
            "year": x_values,
            "refereed": ref_values,
            "non_refereed": non_ref_values,
        }
    )

    plot = figure(
        x_range=x_values,
        title=f"{title_value} vs year ({title_mode}, {title_norm})",
        x_axis_label="Year",
        y_axis_label=y_label,
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )

    if mode == "stacked":
        plot.vbar_stack(
            ["refereed", "non_refereed"],
            x="year",
            width=0.75,
            source=source,
            color=["#2F855A", "#718096"],
            legend_label=["Refereed", "Non-refereed"],
        )
        plot.add_tools(
            HoverTool(
                tooltips=[
                    ("Year", "@year"),
                    ("Refereed", "@refereed"),
                    ("Non-refereed", "@non_refereed"),
                ]
            )
        )
    else:
        grouped_source = ColumnDataSource(
            {
                "year": x_values,
                "refereed": ref_values,
                "non_refereed": non_ref_values,
            }
        )
        plot.vbar(
            x=dodge("year", -0.2, range=plot.x_range),
            top="refereed",
            width=0.35,
            source=grouped_source,
            fill_color="#2F855A",
            line_color="#2F855A",
            legend_label="Refereed",
        )
        plot.vbar(
            x=dodge("year", 0.2, range=plot.x_range),
            top="non_refereed",
            width=0.35,
            source=grouped_source,
            fill_color="#718096",
            line_color="#718096",
            legend_label="Non-refereed",
        )
        plot.add_tools(
            HoverTool(
                tooltips=[
                    ("Year", "@year"),
                    ("Refereed", "@refereed"),
                    ("Non-refereed", "@non_refereed"),
                ]
            )
        )

    if plot.legend:
        plot.legend.location = "top_left"
        plot.legend.click_policy = "hide"
    return plot


def build_index_timeseries_plots(
    metrics: AuthorMetrics,
) -> object | None:
    """Build one combined index-vs-time plot with total and refereed overlays."""
    ordered_indices = ["h", "m", "g", "i10", "i100", "tori", "riq", "read10"]
    palette = [
        "#2B6CB0",
        "#2F855A",
        "#C05621",
        "#805AD5",
        "#D69E2E",
        "#4A5568",
        "#E53E3E",
        "#319795",
    ]
    any_series = False
    plot = figure(
        title="Indices vs time (all in one, total vs refereed)",
        x_axis_label="Year",
        y_axis_label="Index value",
        sizing_mode="stretch_width",
        height=420,
        tools=INTERACTIVE_TOOLS,
    )

    for idx, index_name in enumerate(ordered_indices):
        total_map = metrics.index_timeseries_total.get(index_name)
        refereed_map = metrics.index_timeseries_refereed.get(index_name)
        if not total_map and not refereed_map:
            continue

        years = sorted(
            set(total_map.keys() if total_map else [])
            | set(refereed_map.keys() if refereed_map else [])
        )
        if not years:
            continue

        any_series = True
        color = palette[idx % len(palette)]
        total_values = [total_map.get(year, 0.0) if total_map else 0.0 for year in years]
        refereed_values = [
            refereed_map.get(year, 0.0) if refereed_map else 0.0 for year in years
        ]

        total_source = ColumnDataSource(
            {
                "year": years,
                "value": total_values,
                "index": [index_name.upper()] * len(years),
                "scope": ["Total"] * len(years),
            }
        )
        ref_source = ColumnDataSource(
            {
                "year": years,
                "value": refereed_values,
                "index": [index_name.upper()] * len(years),
                "scope": ["Refereed"] * len(years),
            }
        )

        total_renderer = plot.line(
            x="year",
            y="value",
            line_width=2,
            color=color,
            source=total_source,
            legend_label=f"{index_name.upper()} total",
        )
        ref_renderer = plot.line(
            x="year",
            y="value",
            line_width=2,
            line_dash="dashed",
            color=color,
            source=ref_source,
            legend_label=f"{index_name.upper()} refereed",
        )
        plot.add_tools(
            HoverTool(
                renderers=[total_renderer, ref_renderer],
                tooltips=[
                    ("Index", "@index"),
                    ("Scope", "@scope"),
                    ("Year", "@year"),
                    ("Value", "@value"),
                ],
            )
        )

    if not any_series:
        return None

    plot.legend.location = "top_left"
    plot.legend.click_policy = "hide"
    return plot


def build_index_snapshot_plot(metrics: AuthorMetrics) -> object | None:
    """Build a dedicated ADS-style index snapshot panel (total vs refereed)."""
    ordered_indices = ["h", "m", "g", "i10", "i100", "tori", "riq", "read10"]
    labels: list[str] = []
    total_values: list[float] = []
    refereed_values: list[float] = []

    for index_name in ordered_indices:
        total_value = metrics.index_indicators_total.get(index_name)
        refereed_value = metrics.index_indicators_refereed.get(index_name)

        # Fallback to the latest available timeseries point when snapshot
        # indicators are missing for an index in the current backend payload.
        if total_value is None:
            total_series = metrics.index_timeseries_total.get(index_name, {})
            if total_series:
                total_value = total_series[max(total_series.keys())]
        if refereed_value is None:
            ref_series = metrics.index_timeseries_refereed.get(index_name, {})
            if ref_series:
                refereed_value = ref_series[max(ref_series.keys())]

        if total_value is None and refereed_value is None:
            continue

        labels.append(index_name.upper())
        total_values.append(total_value if total_value is not None else 0.0)
        refereed_values.append(refereed_value if refereed_value is not None else 0.0)

    if not labels:
        return None

    source = ColumnDataSource(
        {
            "index": labels,
            "total": total_values,
            "refereed": refereed_values,
        }
    )

    plot = figure(
        x_range=labels,
        title="Index snapshot (Total vs Refereed)",
        x_axis_label="Index",
        y_axis_label="Value",
        sizing_mode="stretch_width",
        height=320,
        tools=INTERACTIVE_TOOLS,
    )
    plot.vbar(
        x="index",
        top="total",
        width=0.38,
        source=source,
        color="#2B6CB0",
        legend_label="Total",
    )
    plot.vbar(
        x="index",
        top="refereed",
        width=0.24,
        source=source,
        color="#2F855A",
        legend_label="Refereed",
    )
    plot.legend.location = "top_right"
    plot.legend.click_policy = "hide"
    plot.add_tools(
        HoverTool(
            tooltips=[
                ("Index", "@index"),
                ("Total", "@total"),
                ("Refereed", "@refereed"),
            ]
        )
    )
    return plot


def export_dashboard(
    metrics: AuthorMetrics,
    path: str | Path,
    *,
    fmt: PlotFormat,
) -> None:
    """Export the default dashboard as HTML or JSON.

    Args:
        metrics: Computed author metrics.
        path: Output file path.
        fmt: One of ``"html"``, ``"json"``, ``"png"``, or ``"pdf"``.

    Raises:
        ExportError: If the output cannot be written.
    """
    dashboard = build_author_dashboard(metrics)
    output_path = Path(path)
    try:
        if fmt == "html":
            output_file(output_path)
            save(
                dashboard,
                filename=output_path,
                title=f"papertrail - {metrics.author_name}",
            )
            return

        if fmt == "json":
            payload = json_item(dashboard, target="papertrail-dashboard")
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return

        if fmt == "png":
            _export_png_dashboard(dashboard, output_path)
            return

        if fmt == "pdf":
            _export_pdf_dashboard(dashboard, output_path)
            return

        raise ExportError(f"Unsupported plot export format: {fmt!r}")
    except OSError as exc:
        raise ExportError(f"Could not write plot output to '{output_path}'") from exc


def _export_png_dashboard(dashboard: object, path: Path) -> None:
    """Export dashboard as PNG using Bokeh static export."""
    try:
        export_png(dashboard, filename=path)
    except Exception as exc:
        raise ExportError(
            "Could not export PNG dashboard. Ensure Selenium and a headless "
            "browser are installed."
        ) from exc


def _export_pdf_dashboard(dashboard: object, path: Path) -> None:
    """Export dashboard as PDF by converting an intermediate PNG."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        png_path = Path(tmp_dir) / "dashboard.png"
        _export_png_dashboard(dashboard, png_path)
        _write_pdf_from_png(png_path, path)


def _write_pdf_from_png(png_path: Path, pdf_path: Path) -> None:
    """Write a one-page PDF from a PNG image."""
    image = ImageReader(str(png_path))
    width, height = image.getSize()
    document = canvas.Canvas(str(pdf_path), pagesize=(width, height))
    document.drawImage(image, 0, 0, width=width, height=height)
    document.showPage()
    document.save()


def _sorted_year_mapping(year_map: dict[int, int]) -> tuple[list[int], list[int]]:
    """Return parallel sorted year/count lists from a metric mapping."""
    items = sorted(year_map.items())
    years = [year for year, _ in items]
    counts = [count for _, count in items]
    return years, counts
