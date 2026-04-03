# Technical Standards

This document defines the technical standards for all code-writing agents (developer, architect, tech-lead, tester). Read this before writing or reviewing code.

## Python

- Python {{ cookiecutter.python_version }}+
- `from __future__ import annotations` in every file
- Type hints on all public functions

## Code Quality

```bash
ruff check src/ tests/     # lint
ruff format --check        # format check
mypy src/                  # type check
pytest tests/ -v           # tests
```

## Architecture

Follow the architecture defined in project CLAUDE.md. Key rules:
- Respect layering boundaries — domain logic must not depend on infrastructure
- New external integrations must implement defined interfaces/protocols
- All configuration via environment variables or config files, not hardcoded
- No secrets in code

## Git

- Branch naming: `{ISSUE_ID}/short-description` (e.g. `PROJ-123/add-auth`)
- Commit messages: descriptive, explain "why" not "what"
- Feature branches from main branch. MR/PR back to main.
- Pre-commit hooks must pass

## Testing

- New features must have tests
- Bug fixes must have regression test
- Run full test suite before submitting for review

## Deployment

Refer to `agents/devops/CLAUDE.md` for environment-specific deployment procedures.
