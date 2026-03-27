# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A **cookiecutter template** that generates multi-agent AI orchestration projects powered by Claude CLI. The template itself lives in this repo; generated projects are separate.

## Commands

```bash
# Generate a project from this template
pip install cookiecutter
cookiecutter .                        # interactive
cookiecutter . --no-input             # defaults only
cookiecutter . --no-input enable_linear_mcp=yes linear_workspace=myteam  # with overrides

# Test the template
cd tests && pytest test_generation.py -v
```

## Template Structure

- `cookiecutter.json` -- all template variables with defaults and choices
- `hooks/pre_gen_project.py` -- input validation (slug format, required MCP fields)
- `hooks/post_gen_project.py` -- cleanup (remove conditional dirs, fix JSON, git init)
- `{{cookiecutter.project_slug}}/` -- the generated project template root

## Key Patterns

### Jinja2 Conditionals for MCP
MCP integrations use `enable_X_mcp` choice variables ("yes"/"no"):
```
{% if cookiecutter.enable_linear_mcp == "yes" %}...{% endif %}
```

### ASCII Only
Do NOT use Unicode box-drawing characters (| + - etc. only). Cookiecutter's binary detection incorrectly flags files with Unicode as binary and skips Jinja2 rendering.

### JSON Trailing Commas
Jinja2 conditionals in `.mcp.json` create trailing comma issues. The `post_gen_project.py` hook cleans these with regex + re-serialization. A `_placeholder` key is used as a fallback.

### Package Name
`project_slug` uses hyphens but Python needs underscores. Use the filter:
```
{{ cookiecutter.project_slug | replace('-', '_') }}
```
This works in both file content and directory names.

## Agent Architecture

Five agents form a validation pipeline: PM -> Tech Lead -> Architect -> Developer -> Tester. Each agent's `CLAUDE.md` defines role, MCP tools (conditional), responsibilities, and decision authority (CAN/CANNOT).

The Python package in `src/` wraps Claude CLI via `subprocess.run` in the `Agent` base class, orchestrated by `Pipeline` in `orchestrator.py`.
