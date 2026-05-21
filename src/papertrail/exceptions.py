"""Custom exceptions for the papertrail package."""


class PapertrailError(Exception):
    """Base exception for all papertrail errors."""


class AuthorNotFoundError(PapertrailError):
    """Raised when no author matches the given name or ID."""


class MultipleAuthorsFoundError(PapertrailError):
    """Raised when a name matches multiple authors and disambiguation is needed.

    Attributes:
        candidates: List of candidate author display names and IDs.
    """

    def __init__(self, message: str, candidates: list[str]) -> None:
        super().__init__(message)
        self.candidates = candidates


class FetchError(PapertrailError):
    """Raised when an external API request fails."""


class ExportError(PapertrailError):
    """Raised when exporting data to a file fails."""
