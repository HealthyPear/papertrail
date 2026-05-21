# Getting Started

## Installation

```bash
# Recommended: pixi environment
pixi install -e dev

# Alternative: pip editable install with dev extras
pip install -e ".[dev]"
```

## Environment Configuration

For data sources that require tokens, place them in a `.env` file in your
working directory (project root recommended):

```env
ADS_API_TOKEN=your_ads_token
```

papertrail loads `.env` automatically with [python-dotenv](https://saurabh-kumar.com/python-dotenv/).

If you run commands from subdirectories, ensure `.env` is discoverable from
your current working directory.

## CLI Guide

### Search Author Candidates (OpenAlex)

```bash
papertrail search "John Smith"
```

Use this to disambiguate common names and then pass the desired author ID to `metrics`.

### Compute Metrics

```bash
papertrail metrics "Marie Curie"
```

### Explicit OpenAlex Author ID

```bash
papertrail metrics "John Smith" --author-id "https://openalex.org/A123456789"
```

### Export Outputs

```bash
papertrail metrics "Marie Curie" \
  --bib curie.bib \
  --pubs-json curie_pubs.json \
  --pubs-csv curie_pubs.csv \
  --metrics-json curie_metrics.json \
  --metrics-csv curie_metrics.csv
```

### Limit Number of Publications

```bash
papertrail metrics "Marie Curie" --max 50
```

### ADS Source (Astronomy Workflow)

```bash
# .env
# ADS_API_TOKEN="your_ads_token"

papertrail metrics "Marie Curie" \
  --source ads \
  --ads-author-query "Curie, M."
```

When `--source ads` is used, metrics include refereed and non-refereed publication counts.

papertrail loads `.env` automatically via `python-dotenv`, so `ADS_API_TOKEN` does not need to be exported manually.

### Export Interactive Plots

```bash
papertrail plots "Marie Curie"
```

This writes a standalone interactive HTML dashboard in the current directory.

### Browse Local User Data

```bash
papertrail user-data-app
```

```bash
papertrail plots "Marie Curie" \
  --source ads \
  --ads-author-query "Curie, M." \
  --html marie_dashboard.html \
  --json marie_dashboard.json \
  --png marie_dashboard.png \
  --pdf marie_dashboard.pdf
```


## Python API

papertrail is also a Python library, so you can take advantage of its API if you want
to build over it:

```python
from papertrail import AuthorProfile

profile = AuthorProfile("Marie Curie").fetch()
metrics = profile.metrics()

print(metrics.total_publications)
print(metrics.h_index)
```

After `fetch()`, papertrail also writes local SQLite user data at:

- `.papertrail/user-data.sqlite3` (relative to your current working directory)

The user-data database stores:

- fetched publication records
- journal impact value at publication time when available (or proxy values)
- equivalent metrics snapshots (computed author metrics JSON)

You can disable this behavior if needed:

```python
profile = AuthorProfile("Marie Curie", enable_user_data=False).fetch()
```

Or set a custom user-data location:

```python
profile = AuthorProfile(
  "Marie Curie",
  user_data_path="/path/to/papertrail_user_data.sqlite3",
).fetch()
```

`enable_local_cache` and `cache_path` are still accepted as backward-compatible aliases.

### Export Data

```python
profile.export_bibtex("curie.bib")
profile.export_publications("curie_pubs.json", fmt="json")
profile.export_publications("curie_pubs.csv", fmt="csv")
profile.export_metrics("curie_metrics.json", fmt="json")
profile.export_metrics("curie_metrics.csv", fmt="csv")
profile.export_dashboard("curie_dashboard.html", fmt="html")
profile.export_dashboard("curie_dashboard.json", fmt="json")
```

### Custom Impact Factor Database

```python
from pathlib import Path
from papertrail import AuthorProfile, ImpactFactorDatabase

db = ImpactFactorDatabase()
db.load_csv(Path("my_impact_factors.csv"))  # issn, year, impact_factor

profile = AuthorProfile("John Smith").use_impact_factor_database(db).fetch()
```

Expected CSV columns:

| issn | year | impact_factor |
|------|------|---------------|
| 0028-0836 | 2022 | 64.8 |
