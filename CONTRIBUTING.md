# Contributing to aeoncord

Thank you for your interest in contributing to aeoncord.

## Development Setup

aeoncord uses [uv](https://docs.astral.sh/uv/) for dependency management.

Clone the repository and install development dependencies:

```bash
git clone https://github.com/mrf0rtuna4/aeoncord.git

cd aeoncord

uv sync --dev
````

Install the pre-commit hooks:

```bash
uv run pre-commit install
```

## Running Checks

Run Ruff:

```bash
uv run ruff check .
uv run ruff format --check .
```

Run type checking:

```bash
uv run mypy .
uv run pyright
```

Run tests:

```bash
uv run pytest
```

Build the package:

```bash
uv run python -m build
uv run twine check dist/*
```

All of these checks are also executed by GitHub Actions.

## Pull Requests

Before opening a pull request:

* Make sure all tests pass.
* Make sure Ruff passes.
* Make sure mypy and Pyright pass.
* Add or update tests when changing behavior.
* Keep changes focused on the purpose of the pull request.
* Update documentation when necessary.

Pull requests may be reviewed for correctness, API design, type safety, test coverage, and consistency with the existing architecture.

---

## PR template

```markdown
## What changed?

<!-- Describe the changes made by this pull request. -->

## Why?

<!-- Explain why these changes are needed. -->

## Testing

- [ ] Tests added or updated
- [ ] `uv run pytest`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy .`
- [ ] `uv run pyright`

## Checklist

- [ ] The change is focused and does not include unrelated modifications.
- [ ] Documentation was updated if necessary.
- [ ] Public API changes are intentional.
```
