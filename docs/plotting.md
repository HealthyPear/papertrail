# Plotting

papertrail uses `bokeh` for interactive, exportable visualisations.

Dashboards are rendered with horizontal tabs, so each plot is shown in its own
view without squeezing the layout.

## Current Plot Set

The first set is modeled on common ADS-style author views:

- publications per year
- citations per year
- refereed vs non-refereed breakdown when the source provides that metadata
- citation distribution buckets (0, 1-4, 5-9, 10-24, 25-49, 50-99, 100+)
- publication type breakdown (e.g., journal-article, proceedings)
- top journals/venues by publication count
- publications vs year in grouped/stacked, total/normalized modes
- citations vs year in grouped/stacked, total/normalized modes
- index-vs-time overlays (total vs refereed)
- cumulative index-vs-time overlays (total vs refereed)
- index snapshot panel (total vs refereed) including `m` and `riq`

These views are intended to mirror the core summary analyses available in ADS
Analyze for author-centric bibliometric exploration.

When `--source ads` is used, papertrail also queries the ADS Metrics API
(`POST /v1/metrics`) to enrich index time-series data. ADS provides native
time-series values for `h`, `g`, `i10`, `i100`, `read10`, and `tori`. ADS
provides `m` and `riq` as indicators, but not as native time-series in the
documented response types.

For this reason, the dashboard includes both:

- time-series plots for indices where yearly series are available
- a dedicated snapshot panel where `m` and `riq` are shown from ADS indicator
  payloads (and all indices are displayed in total vs refereed form)

## Export Formats

- `html`: standalone interactive dashboard that can be opened directly in a browser
- `json`: embeddable Bokeh JSON suitable for integration into a web page
- `png`: static image export
- `pdf`: static document export

## CLI Usage

```bash
papertrail plots "Marie Curie"
```

This writes a standalone HTML dashboard by default.

## User-Data Browser App

papertrail can also open an interactive Bokeh server page to browse the local
user-data database and export the current table as CSV or JSON:

```bash
papertrail user-data-app
```

Optional flags:

- `--db-path .papertrail/user-data.sqlite3`
- `--port 5006`
- `--show/--no-show`

```bash
papertrail plots "Marie Curie" \
  --source ads \
  --ads-author-query "Curie, M" \
  --html michele_dashboard.html \
  --json michele_dashboard.json \
  --png michele_dashboard.png \
  --pdf michele_dashboard.pdf
```

## Python API

```python
from papertrail import AuthorProfile

profile = AuthorProfile("Marie Curie").fetch()
dashboard = profile.dashboard()
profile.export_dashboard("curie_dashboard.html", fmt="html")
profile.export_dashboard("curie_dashboard.json", fmt="json")
profile.export_dashboard("curie_dashboard.png", fmt="png")
profile.export_dashboard("curie_dashboard.pdf", fmt="pdf")
```

## Why Bokeh

Bokeh gives us interactive browser-based plots while also providing exportable
artifacts that are easy to embed into web pages and other digital materials.

For static CV inclusion, the HTML output is useful as a linked artifact, while
the JSON output is suitable for custom embedding in a personal site.