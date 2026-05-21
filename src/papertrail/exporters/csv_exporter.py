"""CSV exporters for publications and metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from papertrail.exceptions import ExportError
from papertrail.models import AuthorMetrics, Publication


def export_publications_csv(publications: list[Publication], path: Path) -> None:
    """Write publications to a CSV file.

    Each row represents one publication.  Authors are joined with ``"; "``.

    Args:
        publications: List of publications to export.
        path: Destination file path (will be created or overwritten).

    Raises:
        ExportError: If the file cannot be written.
    """
    rows = [
        {
            "id": p.id,
            "title": p.title,
            "year": p.year,
            "doi": p.doi,
            "authors": "; ".join(a.name for a in p.authors),
            "journal": p.journal.name if p.journal else None,
            "journal_issn": p.journal.issn[0] if p.journal and p.journal.issn else None,
            "impact_factor": p.journal.impact_factor if p.journal else None,
            "impact_factor_year": p.journal.impact_factor_year if p.journal else None,
            "citation_count": p.citation_count,
            "type": p.type,
            "open_access": p.open_access,
            "url": p.url,
        }
        for p in publications
    ]
    try:
        pd.DataFrame(rows).to_csv(path, index=False)
    except OSError as exc:
        raise ExportError(f"Could not write publications CSV to '{path}'") from exc


def export_metrics_csv(metrics: AuthorMetrics, path: Path) -> None:
    """Write author metrics to a CSV file (one row).

    Args:
        metrics: Computed author metrics.
        path: Destination file path (will be created or overwritten).

    Raises:
        ExportError: If the file cannot be written.
    """
    row = {
        "author_name": metrics.author_name,
        "openalex_id": metrics.openalex_id,
        "orcid": metrics.orcid,
        "total_publications": metrics.total_publications,
        "total_citations": metrics.total_citations,
        "h_index": metrics.h_index,
        "i10_index": metrics.i10_index,
        "avg_citations_per_paper": metrics.average_citations_per_paper,
        "refereed_publications": metrics.refereed_publications,
        "non_refereed_publications": metrics.non_refereed_publications,
        "most_cited_paper": metrics.most_cited_paper_title,
        "most_cited_paper_citations": metrics.most_cited_paper_citations,
        "avg_impact_factor": metrics.avg_impact_factor,
        "median_impact_factor": metrics.median_impact_factor,
    }
    try:
        pd.DataFrame([row]).to_csv(path, index=False)
    except OSError as exc:
        raise ExportError(f"Could not write metrics CSV to '{path}'") from exc
