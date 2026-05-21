# papertrail

> Retrieve author publications and compute bibliometric metrics.

![papertrail logo](logo.svg)

[![Pixi Badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/prefix-dev/pixi/main/assets/badge/v0.json)](https://pixi.sh)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/type--checked-mypy-blue)](http://mypy-lang.org/)

## Why does this exist?

- I was bored
- I though it was fun
- I saw interesting possibilities of improvement for the tool itself
- ...?

For sure there is something fancier out there.

## Features

- **Author lookup** via [OpenAlex](https://openalex.org/) (free, open, no API key required)
- **Astronomy-focused retrieval** via [NASA ADS](https://ui.adsabs.harvard.edu/) using the official `ads` Python client
- **Full publication list** retrieval with titles, DOIs, years, citation counts
- **Bibliometric metrics**: h-index, i10-index, total citations, average IF, per-year breakdowns
- **Refereed vs non-refereed counts** when using ADS source
- **Impact factor**: OpenAlex 2-year mean citedness as proxy; enrich with a custom IF database (CSV/JSON)
- **Interactive plots** with Bokeh, exportable as HTML, JSON, PNG, or PDF
- **BibTeX export** (`.bib`)
- **Publications & metrics export** to JSON and CSV
- **CLI** for interactive use

> [!WARNING]
> I just started this mostly as an experiment, expect changes and/or unstable developments.
> You are of course very welcome to use it and contribute to it!

## Installation

We do not yet have a published package, so for now you will have to install from source
by first cloning this repo.

We support pixi and recommend using it to install the package

```bash
pixi install -e dev
```

## Usage

### CLI

```bash
# Show metrics in the terminal
papertrail metrics "Marie Curie"

# Search for author candidates (useful when name is ambiguous)
papertrail search "John Smith"

# Export everything
papertrail metrics "Marie Curie" \
    --bib curie.bib \
    --pubs-json curie_pubs.json \
    --metrics-csv curie_metrics.csv \
    --email your@email.com

# Astronomy workflow with ADS (official ads client)
# .env
# ADS_API_TOKEN="your_ads_token"

papertrail metrics "Marie Curie" \
    --source ads \
    --ads-author-query "Curie, M."

# Interactive author dashboard
papertrail plots "Marie Curie" --png curie_dashboard.png --pdf curie_dashboard.pdf

# Browse the local user-data database in a Bokeh server app
papertrail user-data-app
```

### Python API

```python
from papertrail import AuthorProfile

# Fetch publications for an author (uses OpenAlex)
profile = AuthorProfile("Marie Curie").fetch()

# Compute metrics
metrics = profile.metrics()
print(f"h-index: {metrics.h_index}")
print(f"Total citations: {metrics.total_citations}")

# Export
profile.export_bibtex("curie.bib")
profile.export_publications("curie_pubs.json", fmt="json")
profile.export_metrics("curie_metrics.csv", fmt="csv")
```

### Data source selection

- `--source openalex` (default): broad, free, no token needed
- `--source ads`: optimized for astrophysics records and provides refereed/non-refereed tagging

For ADS, set `ADS_API_TOKEN` in a `.env` file at the project root or in your environment.

You can start from [.env.example](.env.example).

papertrail currently integrates ADS directly. SciX is the evolution of ADS and
is expected to become the sole interface in late 2026.

## Development tools

All development tools can be run from the ``dev`` environment as

```bash
pixi run tool
```

where tool can be any of ``test``, ``lint``,  ``fmt``,  ``typecheck``,  ``pre-commit``,

E.g. before committing, please install the pre-commit hooks:

```bash
pixi run -e dev pre-commit install
```

Please, note that we support the use of VSCode dev containers, so you can
either start one locally of use GitHub Codespaces!

## Documentation

```bash
pixi run -e dev docs-build # build locally and open manually later
pixi run -e dev docs-serve # build and live-preview

```

Official more detailed documetation will be online soon!
