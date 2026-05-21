# Impact Factor

papertrail can attach journal impact information to publications and aggregate it in metrics.

!!! important
  While implementing this part, I stumbled on the fact that it seems that impact factor is being more and more monetized.
  While this might seem ethically wrong (it's all public info after all..) it's undeniable that work is needed to aggraget this info
  and that someone might want his work to be recognized in some way.
  Therefore I can only for the moment propose a way to create your own database manually and save it so that you can use those
  metrics when you want to filter or update your academic output.
  This part is not really tested yet, but should be a good starting point.

!!! note
  The term "Impact Factor" can mean maany things, but it is historically linked to the metric
  built by [Clarivate's Web of Science](https://clarivate.com/academia-government/scientific-and-academic-research/research-discovery-and-referencing/web-of-science/)
  wich unfrotunately requires a paid license (your institute might have one!).
  I plan to support other related indices.

## Default Behavior

By default, papertrail uses OpenAlex `2yr_mean_citedness` as an impact-factor proxy when available.

## Historical JIF Support

For historical Journal Impact Factor (JIF) values by year, you can load your own dataset with `ImpactFactorDatabase`.

### CSV Format

Required columns:

- `issn`
- `year`
- `impact_factor`

Example:

| issn | year | impact_factor |
|------|------|---------------|
| 0028-0836 | 2022 | 64.8 |

### JSON Format

```json
{
  "0028-0836": {"2022": 64.8, "2021": 49.96},
  "0036-8075": {"2022": 56.9}
}
```

### Python Example

```python
from pathlib import Path
from papertrail import AuthorProfile, ImpactFactorDatabase

db = ImpactFactorDatabase()
db.load_csv(Path("jif.csv"))

profile = AuthorProfile("Jane Doe").use_impact_factor_database(db).fetch()
metrics = profile.metrics()

print(metrics.avg_impact_factor)
print(metrics.median_impact_factor)
```

## Building a Local Metrics Database

Recommended workflow:

1. Pull publications for the author with papertrail.
2. Collect ISSNs from publication venues.
3. Build a local CSV or JSON dataset keyed by ISSN and year.
4. Load that dataset with `ImpactFactorDatabase`.
5. Re-run the author fetch/metrics workflow using the custom database.

This gives reproducible local enrichment and avoids repeated remote lookups.

## Automatic Local User-Data Storage

After `AuthorProfile(...).fetch()`, papertrail creates a local SQLite user-data
database at `.papertrail/user-data.sqlite3` (from your current working directory).
It stores:

- publication records
- journal impact value (historical IF when available, otherwise source proxy)
- metrics snapshots for the fetch

## Equivalent Metrics

Depending on source access, you may load equivalent journal metrics instead of
JIF (for example, source-specific impact proxies). Keep the same CSV schema for
now (`issn`, `year`, `impact_factor`) to integrate directly with
`ImpactFactorDatabase`.

When using proxy values, document the source and metric definition in your
project notes for transparency.
