"""Command-line interface for papertrail."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.table import Table

from papertrail.author import AuthorProfile
from papertrail.exceptions import AuthorNotFoundError, FetchError
from papertrail.fetchers.ads import ADSFetcher
from papertrail.metrics.impact_factor import ImpactFactorDatabase

app = typer.Typer(
    name="papertrail",
    help="Retrieve author publications and compute bibliometric metrics.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()
err_console = Console(stderr=True, style="bold red")

PlotSource = Literal["openalex", "ads"]


# ---------------------------------------------------------------------------
# search sub-command
# ---------------------------------------------------------------------------


@app.command("search")
def search_command(
    name: str = typer.Argument(..., help="Author name to look up."),
    email: str | None = typer.Option(
        None,
        "--email",
        "-e",
        help="Your e-mail for the OpenAlex polite pool (higher rate limits).",
    ),
) -> None:
    """List author candidates matching NAME.

    Useful for disambiguating common names.  Copy the desired OpenAlex ID and
    pass it to the ``metrics`` command with ``--author-id``.
    """
    profile = AuthorProfile(name, email=email)
    with console.status(f"Searching for '{name}'…"):
        try:
            candidates = profile.search_candidates()
        except FetchError as exc:
            err_console.print(f"Error: {exc}")
            raise typer.Exit(1) from exc

    if not candidates:
        console.print(f"[yellow]No authors found for '{name}'.")
        return

    table = Table(title=f"Author candidates for '{name}'")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="cyan")
    table.add_column("OpenAlex ID", style="magenta")
    table.add_column("ORCID")
    table.add_column("Affiliations")

    for i, author in enumerate(candidates, start=1):
        affils = ", ".join(a.name for a in author.affiliations[:3])
        table.add_row(
            str(i),
            author.name,
            author.id or "—",
            author.orcid or "—",
            affils or "—",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# metrics sub-command
# ---------------------------------------------------------------------------


@app.command("metrics")
def metrics_command(
    name: str = typer.Argument(..., help="Author name to retrieve publications for."),
    author_id: str | None = typer.Option(
        None,
        "--author-id",
        "-a",
        help=(
            "Explicit OpenAlex author ID URL "
            "(avoids auto-selection when name is ambiguous)."
        ),
    ),
    max_results: int | None = typer.Option(
        None,
        "--max",
        "-n",
        help="Maximum number of publications to fetch.",
    ),
    email: str | None = typer.Option(
        None,
        "--email",
        "-e",
        help="Your e-mail for the OpenAlex polite pool.",
    ),
    if_csv: Path | None = typer.Option(
        None,
        "--if-csv",
        help=(
            "CSV file with custom impact factors (columns: issn, year, impact_factor)."
        ),
    ),
    if_json: Path | None = typer.Option(
        None,
        "--if-json",
        help="JSON file with custom impact factors.",
    ),
    bib: Path | None = typer.Option(None, "--bib", help="Export BibTeX to FILE."),
    pubs_json: Path | None = typer.Option(
        None, "--pubs-json", help="Export publications to a JSON file."
    ),
    pubs_csv: Path | None = typer.Option(
        None, "--pubs-csv", help="Export publications to a CSV file."
    ),
    metrics_json: Path | None = typer.Option(
        None, "--metrics-json", help="Export metrics to a JSON file."
    ),
    metrics_csv: Path | None = typer.Option(
        None, "--metrics-csv", help="Export metrics to a CSV file."
    ),
    source: PlotSource = typer.Option(
        "openalex",
        "--source",
        help="Publication data source: openalex (default) or ads.",
    ),
    ads_author_query: str | None = typer.Option(
        None,
        "--ads-author-query",
        help=(
            "Explicit ADS author query string (e.g. 'Peresano, M'). "
            "Used only when --source ads."
        ),
    ),
) -> None:
    """Fetch publications for NAME and display bibliometric metrics.

    Optionally export publications and/or metrics to BibTeX, JSON, or CSV.
    """
    if source == "ads":
        profile = _build_profile(name=name, source=source, email=email)
    else:
        profile = _build_profile(name=name, source=source, email=email)

    _apply_impact_factor_database(profile, if_csv=if_csv, if_json=if_json)

    with console.status(f"[bold green]Fetching publications for '{name}'…"):
        try:
            if source == "ads":
                resolved_ads_query = ads_author_query or _to_ads_author_query(name)
                profile.fetch(author_id=resolved_ads_query, max_results=max_results)
            else:
                profile.fetch(author_id=author_id, max_results=max_results)
        except AuthorNotFoundError as exc:
            err_console.print(f"Error: {exc}")
            raise typer.Exit(1) from exc
        except FetchError as exc:
            err_console.print(f"Error: {exc}")
            raise typer.Exit(1) from exc

    m = profile.metrics()

    # Display summary table
    table = Table(title=f"Metrics for {m.author_name}", show_header=True)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Publications", str(m.total_publications))
    table.add_row("Total citations", str(m.total_citations))
    table.add_row("h-index", str(m.h_index))
    table.add_row("i10-index", str(m.i10_index))
    table.add_row("Avg citations / paper", f"{m.average_citations_per_paper:.1f}")
    if m.refereed_publications is not None:
        table.add_row("Refereed publications", str(m.refereed_publications))
    if m.non_refereed_publications is not None:
        table.add_row("Non-refereed publications", str(m.non_refereed_publications))
    if m.avg_impact_factor is not None:
        table.add_row("Avg impact factor", f"{m.avg_impact_factor:.3f}")
    if m.median_impact_factor is not None:
        table.add_row("Median impact factor", f"{m.median_impact_factor:.3f}")
    if m.most_cited_paper_title:
        table.add_row(
            "Most cited paper",
            f"{m.most_cited_paper_title[:60]}… ({m.most_cited_paper_citations} cit.)",
        )
    if profile.author_info and profile.author_info.id:
        source_label = "ADS author query" if source == "ads" else "OpenAlex ID"
        table.add_row(source_label, profile.author_info.id)

    console.print(table)

    # Exports
    if bib:
        profile.export_bibtex(bib)
        console.print(f"[green]BibTeX -> {bib}")
    if pubs_json:
        profile.export_publications(pubs_json, fmt="json")
        console.print(f"[green]Publications JSON -> {pubs_json}")
    if pubs_csv:
        profile.export_publications(pubs_csv, fmt="csv")
        console.print(f"[green]Publications CSV -> {pubs_csv}")
    if metrics_json:
        profile.export_metrics(metrics_json, fmt="json")
        console.print(f"[green]Metrics JSON -> {metrics_json}")
    if metrics_csv:
        profile.export_metrics(metrics_csv, fmt="csv")
        console.print(f"[green]Metrics CSV -> {metrics_csv}")


@app.command("plots")
def plots_command(
    name: str = typer.Argument(..., help="Author name to retrieve publications for."),
    author_id: str | None = typer.Option(
        None,
        "--author-id",
        "-a",
        help=(
            "Explicit OpenAlex author ID URL "
            "(avoids auto-selection when name is ambiguous)."
        ),
    ),
    max_results: int | None = typer.Option(
        None,
        "--max",
        "-n",
        help="Maximum number of publications to fetch.",
    ),
    email: str | None = typer.Option(
        None,
        "--email",
        "-e",
        help="Your e-mail for the OpenAlex polite pool.",
    ),
    if_csv: Path | None = typer.Option(
        None,
        "--if-csv",
        help=(
            "CSV file with custom impact factors "
            "(columns: issn, year, impact_factor)."
        ),
    ),
    if_json: Path | None = typer.Option(
        None,
        "--if-json",
        help="JSON file with custom impact factors.",
    ),
    source: PlotSource = typer.Option(
        "openalex",
        "--source",
        help="Publication data source: openalex (default) or ads.",
    ),
    ads_author_query: str | None = typer.Option(
        None,
        "--ads-author-query",
        help=(
            "Explicit ADS author query string (e.g. 'Peresano, M'). "
            "Used only when --source ads."
        ),
    ),
    html: Path | None = typer.Option(
        None,
        "--html",
        help="Write the interactive Bokeh dashboard as standalone HTML.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json",
        help="Write the dashboard as embeddable Bokeh JSON.",
    ),
    png: Path | None = typer.Option(
        None,
        "--png",
        help="Write a static PNG snapshot of the dashboard.",
    ),
    pdf: Path | None = typer.Option(
        None,
        "--pdf",
        help="Write a static PDF snapshot of the dashboard.",
    ),
) -> None:
    """Fetch publications for NAME and export interactive plots.

    The initial plot set follows common ADS-style author visualisations:
    publications per year, citations per year, and refereed breakdown when
    available.
    """
    profile = _build_profile(name=name, source=source, email=email)
    _apply_impact_factor_database(profile, if_csv=if_csv, if_json=if_json)

    with console.status(f"[bold green]Fetching publications for '{name}'..."):
        try:
            if source == "ads":
                resolved_ads_query = ads_author_query or _to_ads_author_query(name)
                profile.fetch(author_id=resolved_ads_query, max_results=max_results)
            else:
                profile.fetch(author_id=author_id, max_results=max_results)
        except AuthorNotFoundError as exc:
            err_console.print(f"Error: {exc}")
            raise typer.Exit(1) from exc
        except FetchError as exc:
            err_console.print(f"Error: {exc}")
            raise typer.Exit(1) from exc

    html_path = html or Path(f"{_slugify(name)}_dashboard.html")
    profile.export_dashboard(html_path, fmt="html")
    console.print(f"[green]Dashboard HTML -> {html_path}")

    if json_output:
        profile.export_dashboard(json_output, fmt="json")
        console.print(f"[green]Dashboard JSON -> {json_output}")

    if png:
        profile.export_dashboard(png, fmt="png")
        console.print(f"[green]Dashboard PNG -> {png}")

    if pdf:
        profile.export_dashboard(pdf, fmt="pdf")
        console.print(f"[green]Dashboard PDF -> {pdf}")


def _to_ads_author_query(name: str) -> str:
    """Convert a full name into a typical ADS-style author query.

    Example:
        "Marie Curie" -> "Curie, M"
    """
    parts = [p for p in name.strip().split() if p]
    if len(parts) < 2:
        return name
    surname = parts[-1]
    initial = parts[0][0]
    return f"{surname}, {initial}"


def _build_profile(name: str, source: PlotSource, email: str | None) -> AuthorProfile:
    """Create an author profile for the selected data source."""
    if source == "ads":
        return AuthorProfile(name, fetcher=ADSFetcher())
    return AuthorProfile(name, email=email)


def _apply_impact_factor_database(
    profile: AuthorProfile,
    *,
    if_csv: Path | None,
    if_json: Path | None,
) -> None:
    """Attach a custom impact factor database to a profile when provided."""
    if not if_csv and not if_json:
        return
    db = ImpactFactorDatabase()
    if if_csv:
        db.load_csv(if_csv)
    if if_json:
        db.load_json(if_json)
    profile.use_impact_factor_database(db)


def _slugify(name: str) -> str:
    """Convert a name to a file-friendly slug."""
    cleaned = [char.lower() if char.isalnum() else "_" for char in name]
    slug = "".join(cleaned)
    return "_".join(part for part in slug.split("_") if part)
