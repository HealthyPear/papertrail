"""Interactive Bokeh server app for browsing local papertrail user data."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from bokeh.layouts import column, row
from bokeh.models import (
    Button,
    ColumnDataSource,
    CustomJS,
    DataTable,
    Div,
    Select,
    TableColumn,
)


def build_user_data_document(db_path: Path) -> Any:
    """Return a document-builder callback for Bokeh server."""

    def _modify_doc(doc: Any) -> None:
        if not db_path.exists():
            doc.add_root(
                Div(
                    text=(
                        f"<h2>papertrail user-data browser</h2>"
                        f"<p>No user-data database found at <code>{db_path}</code>. "
                        "Run a fetch first (e.g. <code>papertrail metrics ...</code>)."
                        "</p>"
                    )
                )
            )
            return

        author_rows = _query_all(
            db_path,
            "SELECT DISTINCT author_key, author_name FROM authors ORDER BY author_name",
        )
        if not author_rows:
            doc.add_root(
                Div(text="<h2>papertrail user-data browser</h2><p>No authors found.</p>")
            )
            return

        author_map = {row["author_name"]: row["author_key"] for row in author_rows}
        initial_author = next(iter(author_map.keys()))
        initial_data = _load_publications(db_path, author_map[initial_author])

        source = ColumnDataSource(initial_data)

        author_select = Select(
            title="Author",
            options=list(author_map.keys()),
            value=initial_author,
        )

        columns = [
            TableColumn(field="title", title="Title"),
            TableColumn(field="year", title="Year"),
            TableColumn(field="citation_count", title="Citations"),
            TableColumn(field="journal_name", title="Journal"),
            TableColumn(field="impact_metric_value", title="Impact"),
            TableColumn(field="impact_metric_year", title="Impact Year"),
            TableColumn(field="impact_metric_source", title="Impact Source"),
            TableColumn(field="doi", title="DOI"),
        ]

        table = DataTable(
            source=source,
            columns=columns,
            sizing_mode="stretch_width",
            height=520,
            index_position=None,
        )

        summary = Div(
            text=(
                "<h2>papertrail user-data browser</h2>"
                "<p>Browse stored publications and export the visible table.</p>"
            )
        )

        export_csv_button = Button(label="Export CSV", button_type="primary")
        export_json_button = Button(label="Export JSON", button_type="success")

        export_csv_button.js_on_click(
            CustomJS(
                args={"source": source},
                code="""
                const data = source.data;
                const columns = Object.keys(data);
                const n = data[columns[0]] ? data[columns[0]].length : 0;
                const rows = [columns.join(',')];
                for (let i = 0; i < n; i++) {
                  const row = columns.map((c) => {
                    const v = data[c][i];
                    const text = (v === null || v === undefined) ? '' : String(v);
                    return '"' + text.replace(/"/g, '""') + '"';
                  });
                  rows.push(row.join(','));
                }
                const blob = new Blob([rows.join('\n')], {type: 'text/csv;charset=utf-8;'});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'papertrail_user_data_export.csv';
                link.click();
                URL.revokeObjectURL(link.href);
                """,
            )
        )

        export_json_button.js_on_click(
            CustomJS(
                args={"source": source},
                code="""
                const data = source.data;
                const columns = Object.keys(data);
                const n = data[columns[0]] ? data[columns[0]].length : 0;
                const rows = [];
                for (let i = 0; i < n; i++) {
                  const obj = {};
                  for (const c of columns) {
                    obj[c] = data[c][i];
                  }
                  rows.push(obj);
                }
                const blob = new Blob([JSON.stringify(rows, null, 2)], {type: 'application/json;charset=utf-8;'});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'papertrail_user_data_export.json';
                link.click();
                URL.revokeObjectURL(link.href);
                """,
            )
        )

        def _refresh_for_author(_: str, __: str, new_author_name: str) -> None:
            author_key = author_map[new_author_name]
            source.data = _load_publications(db_path, author_key)

        author_select.on_change("value", _refresh_for_author)

        controls = row(author_select, export_csv_button, export_json_button)
        doc.add_root(column(summary, controls, table, sizing_mode="stretch_width"))
        doc.title = "papertrail user-data"

    return _modify_doc


def build_cache_document(db_path: Path) -> Any:
    """Backward-compatible alias for older imports."""
    return build_user_data_document(db_path)


def _query_all(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def _load_publications(db_path: Path, author_key: str) -> dict[str, list[Any]]:
    rows = _query_all(
        db_path,
        """
        SELECT
            publication_id,
            title,
            year,
            doi,
            citation_count,
            publication_type,
            refereed,
            journal_name,
            impact_metric_value,
            impact_metric_year,
            impact_metric_source,
            fetched_at
        FROM publications
        WHERE author_key = ?
        ORDER BY year DESC, citation_count DESC, title ASC
        """,
        (author_key,),
    )

    fields = [
        "publication_id",
        "title",
        "year",
        "doi",
        "citation_count",
        "publication_type",
        "refereed",
        "journal_name",
        "impact_metric_value",
        "impact_metric_year",
        "impact_metric_source",
        "fetched_at",
    ]

    return {field: [row.get(field) for row in rows] for field in fields}
