"""Journal impact factor database for enriching publications.

The :class:`ImpactFactorDatabase` lets you load historically accurate journal
impact factors from your own CSV or JSON files and attach them to retrieved
publications.

**Why a custom database?**

OpenAlex exposes ``2yr_mean_citedness`` on each source record, which serves as
a freely available *proxy* for the traditional Journal Impact Factor (JIF).
However, it reflects the **current** value at retrieval time, not the
historical value at the year of publication.  If you need historically
accurate JIFs (e.g. from Clarivate JCR exports), load them via this class.

**CSV format expected by** :meth:`ImpactFactorDatabase.load_csv`:

.. code-block:: text

    issn,year,impact_factor
    0028-0836,2022,64.8
    0028-0836,2021,49.96
    0036-8075,2022,56.9

**JSON format expected by** :meth:`ImpactFactorDatabase.load_json`:

.. code-block:: json

    {
      "0028-0836": {"2022": 64.8, "2021": 49.96},
      "0036-8075": {"2022": 56.9}
    }
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from papertrail.models import Publication


class ImpactFactorDatabase:
    """In-memory store of journal impact factors indexed by ISSN and year.

    Example:
        >>> from pathlib import Path
        >>> db = ImpactFactorDatabase()
        >>> db.load_csv(Path("jif_data.csv"))
        >>> enriched = db.enrich_publications(publications)
    """

    def __init__(self) -> None:
        # issn -> {year -> impact_factor}
        self._data: dict[str, dict[int, float]] = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_csv(self, path: Path) -> None:
        """Load impact factors from a CSV file.

        The file must contain at minimum the columns ``issn``, ``year``, and
        ``impact_factor``.  Additional columns are silently ignored.

        Args:
            path: Path to the CSV file.

        Raises:
            FileNotFoundError: If *path* does not exist.
            KeyError: If a required column is missing.
            ValueError: If a numeric field cannot be parsed.
        """
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                issn = row["issn"].strip()
                year = int(row["year"].strip())
                value = float(row["impact_factor"].strip())
                self._data.setdefault(issn, {})[year] = value

    def load_json(self, path: Path) -> None:
        """Load impact factors from a JSON file.

        The file must be a JSON object mapping ISSN strings to objects that
        map year strings (or integers) to float values.

        Args:
            path: Path to the JSON file.

        Raises:
            FileNotFoundError: If *path* does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
            ValueError: If a numeric field cannot be parsed.
        """
        raw: dict[str, dict[str, float]] = json.loads(path.read_text(encoding="utf-8"))
        for issn, year_map in raw.items():
            entry = self._data.setdefault(issn, {})
            for year_key, value in year_map.items():
                entry[int(year_key)] = float(value)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_impact_factor(
        self,
        issn: str,
        year: int,
        *,
        tolerance: int = 1,
    ) -> float | None:
        """Return the impact factor for a journal in a given year.

        If an exact match is not found, values within ``±tolerance`` years
        are checked in order of proximity.

        Args:
            issn: ISSN string (e.g. ``"0028-0836"``).
            year: Target year.
            tolerance: How many years to search around *year* when an exact
                match is unavailable.  Defaults to ``1``.

        Returns:
            The impact factor as a float, or ``None`` if no data is available.
        """
        yearly = self._data.get(issn)
        if yearly is None:
            return None
        if year in yearly:
            return yearly[year]
        for delta in range(1, tolerance + 1):
            if (year - delta) in yearly:
                return yearly[year - delta]
            if (year + delta) in yearly:
                return yearly[year + delta]
        return None

    def enrich_publications(
        self,
        publications: list[Publication],
        *,
        tolerance: int = 1,
    ) -> list[Publication]:
        """Return a copy of *publications* enriched with IF data from this database.

        For each publication that has a journal with at least one ISSN, an IF
        lookup is performed.  If a value is found, the publication's
        :attr:`~papertrail.models.JournalInfo.impact_factor` and
        :attr:`~papertrail.models.JournalInfo.impact_factor_year` fields are
        updated.

        Args:
            publications: Original list of publications.
            tolerance: Year tolerance passed to :meth:`get_impact_factor`.

        Returns:
            A new list of :class:`~papertrail.models.Publication` objects.
            Publications without journal data are returned unchanged.
        """
        result: list[Publication] = []
        for pub in publications:
            if pub.journal and pub.journal.issn:
                for issn in pub.journal.issn:
                    if_val = self.get_impact_factor(issn, pub.year, tolerance=tolerance)
                    if if_val is not None:
                        new_journal = pub.journal.model_copy(
                            update={
                                "impact_factor": if_val,
                                "impact_factor_year": pub.year,
                            }
                        )
                        pub = pub.model_copy(update={"journal": new_journal})
                        break
            result.append(pub)
        return result
