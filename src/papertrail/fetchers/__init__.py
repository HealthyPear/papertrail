"""Fetcher sub-package for papertrail."""

from papertrail.fetchers.ads import ADSFetcher
from papertrail.fetchers.base import BaseFetcher
from papertrail.fetchers.openalex import OpenAlexFetcher

__all__ = ["ADSFetcher", "BaseFetcher", "OpenAlexFetcher"]
