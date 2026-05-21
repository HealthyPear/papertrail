"""High-level :class:`AuthorProfile` class - the main entry point for users."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from papertrail.exceptions import AuthorNotFoundError
from papertrail.exporters import bibtex as bibtex_mod
from papertrail.exporters import csv_exporter, json_exporter
from papertrail.fetchers.base import BaseFetcher
from papertrail.fetchers.openalex import OpenAlexFetcher
from papertrail.metrics.bibliometric import compute_metrics
from papertrail.metrics.impact_factor import ImpactFactorDatabase
from papertrail.models import AuthorInfo, AuthorMetrics, Publication
from papertrail.plots.bokeh_plotter import build_author_dashboard, export_dashboard

ExportFormat = Literal["json", "csv"]
PlotFormat = Literal["html", "json", "png", "pdf"]


class AuthorProfile:
    """Retrieve and analyse all publications of a single author.

    ``AuthorProfile`` is the primary API surface of *papertrail*.  It combines
    a :class:`~papertrail.fetchers.base.BaseFetcher` for data retrieval with
    optional :class:`~papertrail.metrics.impact_factor.ImpactFactorDatabase`
    enrichment and a set of export helpers.

    Args:
        name: Author name (full name or last-name prefix).
        fetcher: Custom fetcher instance.  Defaults to
            :class:`~papertrail.fetchers.openalex.OpenAlexFetcher`.
        email: E-mail passed to the default OpenAlex fetcher to enable the
            *polite pool*.  Ignored when *fetcher* is provided explicitly.

    Example:
        >>> profile = AuthorProfile("Marie Curie").fetch()
        >>> m = profile.metrics()
        >>> print(m.h_index)
    """

    def __init__(
        self,
        name: str,
        *,
        fetcher: BaseFetcher | None = None,
        email: str | None = None,
    ) -> None:
        self.name = name
        self._fetcher: BaseFetcher = fetcher or OpenAlexFetcher(email=email)
        self._publications: list[Publication] = []
        self._author_info: AuthorInfo | None = None
        self._if_database: ImpactFactorDatabase | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def publications(self) -> list[Publication]:
        """All retrieved publications (empty until :meth:`fetch` is called)."""
        return self._publications

    @property
    def author_info(self) -> AuthorInfo | None:
        """Resolved author metadata, or ``None`` if not yet fetched."""
        return self._author_info

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def use_impact_factor_database(self, db: ImpactFactorDatabase) -> AuthorProfile:
        """Attach a custom impact factor database.

        If publications have already been fetched, they are enriched
        immediately.  Otherwise, enrichment happens automatically during
        :meth:`fetch`.

        Args:
            db: A pre-loaded
                :class:`~papertrail.metrics.impact_factor.ImpactFactorDatabase`.

        Returns:
            ``self`` for method chaining.
        """
        self._if_database = db
        if self._publications:
            self._publications = db.enrich_publications(self._publications)
        return self

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    def search_candidates(self) -> list[AuthorInfo]:
        """Return candidates matching :attr:`name` without fetching publications.

        Useful for disambiguating common names before committing to a specific
        author ID.

        Returns:
            A list of :class:`~papertrail.models.AuthorInfo` objects.

        Raises:
            FetchError: If the API request fails.
        """
        return self._fetcher.search_authors(self.name)

    def fetch(
        self,
        author_id: str | None = None,
        *,
        max_results: int | None = None,
    ) -> AuthorProfile:
        """Fetch publications for this author.

        Args:
            author_id: Explicit author identifier (e.g. OpenAlex author ID
                URL).  When ``None``, the best-ranked search result for
                :attr:`name` is used automatically.
            max_results: Cap the number of returned publications.  ``None``
                fetches all available works.

        Returns:
            ``self`` for method chaining.

        Raises:
            AuthorNotFoundError: If no author matches the name.
            MultipleAuthorsFoundError: Raised only when *author_id* is ``None``
                and you explicitly call this in strict mode (not raised by
                default - the top result is used).
            FetchError: If an API request fails.

        Example:
            >>> profile = AuthorProfile("Ada Lovelace").fetch()
            >>> len(profile.publications) > 0
            True
        """
        if author_id is None:
            candidates = self._fetcher.search_authors(self.name)
            if not candidates:
                raise AuthorNotFoundError(f"No author found matching '{self.name}'.")
            self._author_info = candidates[0]
            author_id = candidates[0].id or ""
        else:
            # Populate author_info from the ID if not already set
            if self._author_info is None:
                self._author_info = AuthorInfo(id=author_id, name=self.name)

        self._publications = self._fetcher.fetch_publications(
            author_id, max_results=max_results
        )

        if self._if_database is not None:
            self._publications = self._if_database.enrich_publications(
                self._publications
            )

        return self

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def metrics(self) -> AuthorMetrics:
        """Compute bibliometric metrics from the fetched publications.

        Returns:
            An :class:`~papertrail.models.AuthorMetrics` instance.

        Raises:
            RuntimeError: If :meth:`fetch` has not been called yet.
        """
        if not self._publications and self._author_info is None:
            raise RuntimeError(
                "No publications loaded.  Call fetch() before metrics()."
            )
        info = self._author_info
        source_analysis = self._fetcher.fetch_analyze_metrics(self._publications)
        return compute_metrics(
            author_name=self.name,
            publications=self._publications,
            openalex_id=info.id if info else None,
            orcid=info.orcid if info else None,
            source_analysis=source_analysis,
        )

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------

    def export_bibtex(self, path: str | Path) -> None:
        """Export publications to a BibTeX ``.bib`` file.

        Args:
            path: Destination file path.

        Raises:
            ExportError: If the file cannot be written.
        """
        bibtex_mod.export_bibtex(self._publications, Path(path))

    def export_publications(
        self,
        path: str | Path,
        *,
        fmt: ExportFormat = "json",
    ) -> None:
        """Export the publication list to a file.

        Args:
            path: Destination file path.
            fmt: Output format - ``"json"`` (default) or ``"csv"``.

        Raises:
            ValueError: If *fmt* is not supported.
            ExportError: If the file cannot be written.
        """
        dest = Path(path)
        if fmt == "json":
            json_exporter.export_publications_json(self._publications, dest)
        elif fmt == "csv":
            csv_exporter.export_publications_csv(self._publications, dest)
        else:
            raise ValueError(f"Unsupported export format: {fmt!r}")

    def export_metrics(
        self,
        path: str | Path,
        *,
        fmt: ExportFormat = "json",
    ) -> None:
        """Compute and export metrics to a file.

        Args:
            path: Destination file path.
            fmt: Output format - ``"json"`` (default) or ``"csv"``.

        Raises:
            ValueError: If *fmt* is not supported.
            ExportError: If the file cannot be written.
        """
        m = self.metrics()
        dest = Path(path)
        if fmt == "json":
            json_exporter.export_metrics_json(m, dest)
        elif fmt == "csv":
            csv_exporter.export_metrics_csv(m, dest)
        else:
            raise ValueError(f"Unsupported export format: {fmt!r}")

    def dashboard(self) -> object:
        """Build the default interactive Bokeh dashboard for this profile.

        Returns:
            A Bokeh layout containing the available plots.

        Raises:
            RuntimeError: If :meth:`fetch` has not been called yet.
        """
        return build_author_dashboard(self.metrics())

    def export_dashboard(
        self,
        path: str | Path,
        *,
        fmt: PlotFormat = "html",
    ) -> None:
        """Export the default interactive dashboard.

        Args:
            path: Destination file path.
            fmt: Output format - ``"html"`` for standalone interactive output
                or ``"json"`` for embeddable Bokeh JSON. Static exports are
                also supported with ``"png"`` and ``"pdf"``.
        """
        export_dashboard(self.metrics(), Path(path), fmt=fmt)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        n_pubs = len(self._publications)
        return f"AuthorProfile(name={self.name!r}, publications={n_pubs})"
