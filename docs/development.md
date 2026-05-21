# Development

papertrail is a free open-source project.

Anyone who finds it interesting or useful is welcome to contribute.

Please follow these steps:

1. check first [Discussions](https://github.com/HealthyPear/papertrail/discussions) or
   [Issues](https://github.com/HealthyPear/papertrail/issues), someone might have already stumbled on your problem and even proposed a solution!
2. if not, please start a new discussion or issue first so we can understand the scope
3. make sure your `main` branch is up to date
4. branch off with `git switch -c xxx-yyy` where `xxx` is e.g. `feature`, `fix`, `docs` and `yyy` is an issue reference such as `issue-123`
5. while you edit your code, please run the project tools below
6. open your Pull Request

## Pre-commit

Before pushing commits, please install the hooks,

```bash
pixi run -e dev pre-commit install
```

## Quality Commands

These are the supported quality commands. Please run them before pushing.

```bash
pixi run -e dev test
pixi run -e dev lint
pixi run -e dev fmt
pixi run -e dev typecheck
```

In particular, the project uses:

- Formatting and linting: [Ruff](https://docs.astral.sh/ruff/)
- Type checking: [mypy](https://mypy.readthedocs.io/en/stable/)
- Tests: [pytest](https://docs.pytest.org/en/8.0.x/)
- API docs: [mkdocstrings](https://mkdocstrings.github.io/) (Google-style docstrings)
- Packaging: [Hatch](https://hatch.pypa.io/1.7/) with ``src`` layout

## Documentation Commands

Documentation should be updated together with code changes (except very small
changes such as typo-only fixes).

```bash
pixi run -e dev docs-serve
pixi run -e dev docs-build
```

## Tooling Summary


