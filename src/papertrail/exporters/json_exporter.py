"""JSON exporters for publications and metrics."""

from __future__ import annotations

import json
from pathlib import Path

from papertrail.exceptions import ExportError
from papertrail.models import AuthorMetrics, Publication


def export_publications_json(publications: list[Publication], path: Path) -> None:
    """Write publications to a JSON file.

    The output is a JSON array where each element is the Pydantic serialisation
    of a :class:`~papertrail.models.Publication`.

    Args:
        publications: List of publications to export.
        path: Destination file path (will be created or overwritten).

    Raises:
        ExportError: If the file cannot be written.
    """
    payload = [p.model_dump(mode="json") for p in publications]
    try:
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ExportError(f"Could not write publications JSON to '{path}'") from exc


def export_metrics_json(metrics: AuthorMetrics, path: Path) -> None:
    """Write author metrics to a JSON file.

    Args:
        metrics: Computed author metrics.
        path: Destination file path (will be created or overwritten).

    Raises:
        ExportError: If the file cannot be written.
    """
    try:
        path.write_text(
            json.dumps(metrics.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ExportError(f"Could not write metrics JSON to '{path}'") from exc
