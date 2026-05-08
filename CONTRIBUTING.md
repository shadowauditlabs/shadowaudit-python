# Contributing to ShadowAudit

Thank you for your interest in contributing. This document covers development setup, testing, and the pull request process.

## Development Setup

```bash
git clone https://github.com/AnshumanKumar14/shadowaudit-python.git
cd shadowaudit-python
pip install -e ".[dev,langchain]"
```

This installs ShadowAudit in editable mode with development dependencies (pytest, mypy, ruff) and the LangChain adapter.

## Running Tests

```bash
# Full test suite
pytest tests/ -q

# With coverage
pytest tests/ --cov=shadowaudit --cov-report=term-missing

# Type checking
mypy --strict shadowaudit/

# Linting
ruff check shadowaudit/ tests/
```

All tests must pass before a PR is merged. The current baseline is **205 passed, 1 skipped** (the skipped test is for optional `pytest-asyncio`).

## Pull Request Process

1. **Branch from `main`** — use a descriptive branch name: `fix/scanner-perf`, `feature/mcp-healthcheck`, `docs/telemetry-guide`.
2. **Write tests** — every new module must have corresponding tests in `tests/`. Aim for coverage of edge cases and error paths, not just happy paths.
3. **Run the full suite** — `pytest tests/ -q` must pass locally before pushing.
4. **Type-check** — `mypy --strict shadowaudit/` must report zero errors.
5. **Lint** — `ruff check shadowaudit/ tests/` must pass.
6. **Update docs** — if your change affects user-facing behavior, update `README.md`, `docs/CLI.md`, or `docs/FEATURES.md` as appropriate.
7. **Open a PR** — fill out the pull request template. Link related issues.
8. **Wait for CI** — GitHub Actions runs the same checks. A maintainer will review once CI is green.

## Coding Standards

- **Python 3.10+** — use modern syntax (union types `|`, match statements where appropriate).
- **Type hints everywhere** — public APIs must be fully typed. Use `Any` sparingly and document why when you do.
- **No `print()` in library code** — use the `logging` module. CLI commands may use `click.echo()` or `click.secho()`.
- **No emoji in logs** — keep output machine-parseable and terminal-agnostic.
- **Fail-closed by default** — any new gate or enforcement mechanism must default to blocking, not allowing.
- **SQLite for state** — avoid adding new external dependencies for persistence. If you need something beyond SQLite, open an issue first.
- **Docstrings for public APIs** — every public class and method should have a Google-style or Sphinx-style docstring.

## Adding a Taxonomy

1. Create a JSON file in `shadowaudit/taxonomies/` following the schema in `shadowaudit/core/taxonomy.py`.
2. Add a test in `tests/test_taxonomy_<name>.py` that loads the taxonomy and validates structure.
3. Update `docs/FEATURES.md` to list the new taxonomy.
4. If the taxonomy is domain-specific (e.g., healthcare, insurance), mention it in the README under "Vertical Taxonomies".

## Adding a Framework Adapter

1. Create a new file in `shadowaudit/framework/<framework>.py`.
2. Follow the pattern of existing adapters:
   - Define an `AgentActionBlocked` exception.
   - Provide a transparent wrapper class that intercepts tool calls.
   - Call `Gate.evaluate()` with the appropriate `risk_category`.
   - Re-raise `AgentActionBlocked` on block.
3. Add tests in `tests/test_framework_<framework>.py`.
4. Add an example in `examples/<framework>_demo.py`.
5. Update `README.md` and `docs/FEATURES.md`.

## Reporting Security Issues

Do **not** file public issues for security bugs. See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

## Questions?

Open a [GitHub Discussion](https://github.com/AnshumanKumar14/shadowaudit-python/discussions) for questions that aren't bug reports or feature requests.
