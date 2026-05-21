"""SQLite-backed local user-data storage for fetched publications and metrics."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from papertrail.models import AuthorInfo, AuthorMetrics, Publication


class LocalMetricsCache:
    """Persist fetched publication and metrics data in a local SQLite file."""

    def __init__(self, path: Path | None = None) -> None:
        if path is not None:
            self.path = path
        else:
            default_path = Path.cwd() / ".papertrail" / "user-data.sqlite3"
            legacy_path = Path.cwd() / ".papertrail" / "cache.sqlite3"
            self.path = legacy_path if legacy_path.exists() and not default_path.exists() else default_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def save_fetch(
        self,
        *,
        author_name: str,
        author_info: AuthorInfo | None,
        publications: list[Publication],
        metrics: AuthorMetrics,
        fetcher_name: str,
    ) -> None:
        """Store the latest fetch result for an author."""
        author_key = self._author_key(author_name, author_info)
        timestamp = datetime.now(tz=timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO authors (
                    author_key,
                    author_name,
                    author_id,
                    orcid,
                    fetcher,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(author_key) DO UPDATE SET
                    author_name=excluded.author_name,
                    author_id=excluded.author_id,
                    orcid=excluded.orcid,
                    fetcher=excluded.fetcher,
                    updated_at=excluded.updated_at
                """,
                (
                    author_key,
                    author_name,
                    author_info.id if author_info else None,
                    author_info.orcid if author_info else None,
                    fetcher_name,
                    timestamp,
                ),
            )

            conn.execute("DELETE FROM publications WHERE author_key = ?", (author_key,))
            for publication in publications:
                conn.execute(
                    """
                    INSERT INTO publications (
                        author_key,
                        publication_id,
                        title,
                        year,
                        doi,
                        citation_count,
                        publication_type,
                        refereed,
                        open_access,
                        url,
                        journal_name,
                        journal_issn,
                        impact_metric_value,
                        impact_metric_year,
                        impact_metric_kind,
                        impact_metric_source,
                        fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        author_key,
                        publication.id,
                        publication.title,
                        publication.year,
                        publication.doi,
                        publication.citation_count,
                        publication.type,
                        1 if publication.refereed is True else 0 if publication.refereed is False else None,
                        1 if publication.open_access else 0,
                        publication.url,
                        publication.journal.name if publication.journal else None,
                        ",".join(publication.journal.issn)
                        if publication.journal and publication.journal.issn
                        else None,
                        publication.journal.impact_factor
                        if publication.journal
                        else None,
                        publication.journal.impact_factor_year
                        if publication.journal
                        else None,
                        "impact_factor_or_proxy"
                        if publication.journal and publication.journal.impact_factor is not None
                        else None,
                        self._impact_metric_source(publication, fetcher_name),
                        timestamp,
                    ),
                )

            conn.execute(
                """
                INSERT INTO author_metrics_snapshots (
                    author_key,
                    captured_at,
                    metrics_json
                ) VALUES (?, ?, ?)
                """,
                (author_key, timestamp, metrics.model_dump_json()),
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS authors (
                    author_key TEXT PRIMARY KEY,
                    author_name TEXT NOT NULL,
                    author_id TEXT,
                    orcid TEXT,
                    fetcher TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS publications (
                    author_key TEXT NOT NULL,
                    publication_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    doi TEXT,
                    citation_count INTEGER NOT NULL,
                    publication_type TEXT,
                    refereed INTEGER,
                    open_access INTEGER NOT NULL,
                    url TEXT,
                    journal_name TEXT,
                    journal_issn TEXT,
                    impact_metric_value REAL,
                    impact_metric_year INTEGER,
                    impact_metric_kind TEXT,
                    impact_metric_source TEXT,
                    fetched_at TEXT NOT NULL,
                    PRIMARY KEY (author_key, publication_id),
                    FOREIGN KEY (author_key) REFERENCES authors(author_key) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS author_metrics_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_key TEXT NOT NULL,
                    captured_at TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    FOREIGN KEY (author_key) REFERENCES authors(author_key) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_publications_author_key
                    ON publications(author_key);

                CREATE INDEX IF NOT EXISTS idx_metrics_author_key
                    ON author_metrics_snapshots(author_key);
                """
            )

    @staticmethod
    def _author_key(author_name: str, author_info: AuthorInfo | None) -> str:
        if author_info and author_info.id:
            return author_info.id
        return author_name.strip().lower()

    @staticmethod
    def _impact_metric_source(publication: Publication, fetcher_name: str) -> str | None:
        if publication.journal is None or publication.journal.impact_factor is None:
            return None

        if fetcher_name == "OpenAlexFetcher":
            return "openalex_2yr_mean_citedness_proxy"
        if fetcher_name == "ADSFetcher":
            return "ads_metric"
        if publication.journal.impact_factor_year == publication.year:
            return "historical_database_exact_year"
        return "source_metric"
