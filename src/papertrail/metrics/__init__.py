"""Metrics sub-package for papertrail."""

from papertrail.metrics.bibliometric import (
    compute_h_index,
    compute_i10_index,
    compute_metrics,
)
from papertrail.metrics.impact_factor import ImpactFactorDatabase

__all__ = [
    "ImpactFactorDatabase",
    "compute_h_index",
    "compute_i10_index",
    "compute_metrics",
]
