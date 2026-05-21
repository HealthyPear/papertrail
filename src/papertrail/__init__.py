"""papertrail - retrieve author publications and compute bibliometric metrics.

Example:
    >>> from papertrail import AuthorProfile
    >>> profile = AuthorProfile("Marie Curie").fetch()
    >>> metrics = profile.metrics()
    >>> print(metrics.h_index)
"""

from papertrail.author import AuthorProfile
from papertrail.exceptions import AuthorNotFoundError, ExportError, FetchError
from papertrail.fetchers.ads import ADSFetcher
from papertrail.metrics.impact_factor import ImpactFactorDatabase
from papertrail.models import AuthorInfo, AuthorMetrics, JournalInfo, Publication
from papertrail.plots import (
    build_author_dashboard,
    build_citations_per_year_plot,
    build_publications_per_year_plot,
    build_refereed_breakdown_plot,
    export_dashboard,
)

__version__ = "0.1.0"

__all__ = [
    "ADSFetcher",
    "AuthorInfo",
    "AuthorMetrics",
    "AuthorNotFoundError",
    "AuthorProfile",
    "ExportError",
    "FetchError",
    "ImpactFactorDatabase",
    "JournalInfo",
    "Publication",
    "build_author_dashboard",
    "build_citations_per_year_plot",
    "build_publications_per_year_plot",
    "build_refereed_breakdown_plot",
    "export_dashboard",
]
