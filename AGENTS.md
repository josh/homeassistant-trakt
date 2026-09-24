# Development

Trakt now playing status as a media player entity. Keep documentation minimal and never hard-wrap Markdown.

Targets the latest Home Assistant release only. `requires-python` mirrors Home Assistant's own value, so raising one means raising the other.

```sh
uv sync --locked
uv run ruff format --diff .
uv run ruff check .
uv run mypy .
```

There are no tests. `mypy --strict` against the locked Home Assistant is the gate that catches API drift.

Run these locally before committing; neither is installed by `uv sync` or checked in CI.

```sh
uvx ssort .
uvx pyproject-fmt pyproject.toml
```

Sort functions in dependency order. Avoid superfluous comments and docstrings; only include them when they clarify complex logic.
