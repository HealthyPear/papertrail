# papertrail

papertrail retrieves an author's publications and computes bibliometric
metrics, with interfaces to both [OpenAlex](https://openalex.org/) and [NASA ADS](https://ui.adsabs.harvard.edu/).

## What To Read Next

- [Getting Started](getting-started.md)
- [Plotting](plotting.md)
- [Data Sources](data-sources.md)
- [Impact Factor](impact-factor.md)
- [Development](development.md)
- [API Reference](reference/index.md)

## Quick examples

```bash
papertrail metrics "Marie Curie"
```

```bash
export ADS_API_TOKEN="your_ads_token"
papertrail metrics "Marie Curie" --source ads --ads-author-query "Curie, M"
```

```bash
papertrail plots "Marie Curie"
```

```bash
papertrail user-data-app
```
