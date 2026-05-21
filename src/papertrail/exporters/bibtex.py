"""BibTeX export for papertrail publications."""

from __future__ import annotations

import re
from pathlib import Path

from papertrail.models import Publication


def _make_cite_key(pub: Publication) -> str:
    """Generate a BibTeX cite key from a publication.

    The key follows the pattern ``{LastName}{Year}{FirstTitleWord}``.

    Args:
        pub: The publication to generate a key for.

    Returns:
        A string suitable for use as a BibTeX cite key.
    """
    last_name = pub.authors[0].name.split()[-1] if pub.authors else "Unknown"
    first_word = pub.title.split()[0] if pub.title else "Untitled"
    # Strip any characters that are not alphanumeric
    last_name = re.sub(r"[^A-Za-z0-9]", "", last_name)
    first_word = re.sub(r"[^A-Za-z0-9]", "", first_word)
    return f"{last_name}{pub.year}{first_word}"


def _escape_bibtex(value: str) -> str:
    """Minimally escape a string for safe use inside BibTeX braces.

    Args:
        value: Raw string value.

    Returns:
        Escaped string.
    """
    # Escape unbalanced braces and backslashes
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def to_bibtex_entry(pub: Publication) -> str:
    """Convert a :class:`~papertrail.models.Publication` to a BibTeX entry string.

    Args:
        pub: Publication to convert.

    Returns:
        A complete BibTeX entry as a string, including the trailing newline.

    Example:
        >>> from papertrail.models import Publication, AuthorInfo, JournalInfo
        >>> pub = Publication(
        ...     id="W1",
        ...     title="Test Paper",
        ...     year=2023,
        ...     doi="10.1234/test",
        ...     authors=[AuthorInfo(name="Jane Doe")],
        ...     journal=JournalInfo(name="Nature"),
        ... )
        >>> entry = to_bibtex_entry(pub)
        >>> "@article" in entry
        True
    """
    entry_type = "article" if pub.type == "journal-article" else "misc"
    cite_key = _make_cite_key(pub)

    fields: dict[str, str] = {}
    fields["title"] = "{" + _escape_bibtex(pub.title) + "}"

    if pub.authors:
        author_str = " and ".join(a.name for a in pub.authors)
        fields["author"] = "{" + _escape_bibtex(author_str) + "}"

    fields["year"] = str(pub.year)

    if pub.journal:
        fields["journal"] = "{" + _escape_bibtex(pub.journal.name) + "}"
        if pub.journal.issn:
            fields["issn"] = pub.journal.issn[0]
        if pub.journal.publisher:
            fields["publisher"] = "{" + _escape_bibtex(pub.journal.publisher) + "}"

    if pub.doi:
        fields["doi"] = pub.doi
    if pub.url:
        fields["url"] = "{" + pub.url + "}"
    if pub.abstract:
        fields["abstract"] = "{" + _escape_bibtex(pub.abstract) + "}"

    field_lines = "\n".join(f"  {k} = {v}," for k, v in fields.items())
    return f"@{entry_type}{{{cite_key},\n{field_lines}\n}}\n"


def export_bibtex(publications: list[Publication], path: Path) -> None:
    """Write a list of publications to a ``.bib`` file.

    Args:
        publications: Publications to export.
        path: Destination file path (will be created or overwritten).

    Raises:
        ExportError: If the file cannot be written.
    """
    from papertrail.exceptions import ExportError

    entries = [to_bibtex_entry(p) for p in publications]
    try:
        path.write_text("\n".join(entries), encoding="utf-8")
    except OSError as exc:
        raise ExportError(f"Could not write BibTeX file to '{path}'") from exc
