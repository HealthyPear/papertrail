# Data Sources

papertrail supports two publication sources.

## OpenAlex (Default)

- No token required
- Broad multidisciplinary coverage
- Good for general bibliometric workflows

CLI default:

```bash
papertrail metrics "Marie Curie" --source openalex
```

## NASA ADS (Astrophysics Focus)

- Uses the official `ads` Python client
- Requires `ADS_API_TOKEN`
- Typically better coverage for astronomy and astrophysics
- Exposes refereed/non-refereed metadata used in metrics

Example:

```bash
# .env
# ADS_API_TOKEN="your_ads_token"

papertrail metrics "Marie Curie" --source ads --ads-author-query "Curie, M."
```

papertrail loads `.env` automatically, so a project-root `.env` file is sufficient.

## ADS and SciX

SciX is the evolution of ADS, extending those capabilities into additional
domains. ADS is still the backend integrated in papertrail today via the
official `ads` Python client, but SciX is expected to become the sole
interface in late 2026.

The current plotting layer is intentionally built on papertrail's internal
metrics rather than hard-coding ADS UI responses, so it can be adapted to
future SciX-backed retrieval with minimal surface change.

## Choosing a Source

- Use OpenAlex for general-purpose workflows and ease of setup.
- Use ADS if you work in astronomy/astrophysics-specific subjects.

!!! note
	More sources can be added of course, so if I do not do it before, feel free to start a contribution!
