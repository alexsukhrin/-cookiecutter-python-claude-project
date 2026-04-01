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

# End-to-end test: generate + install + run generated project's tests
pipx run cookiecutter . --no-input && cd my-claude-agent-project && pip install -e ".[dev]" && pytest
```

There is no top-level test suite for the template itself — tests live inside the generated project at `{{cookiecutter.project_slug}}/tests/`.

## Template Structure

- `cookiecutter.json` -- all template variables with defaults and choices
- `hooks/pre_gen_project.py` -- input validation (slug format, required MCP fields when integration enabled)
- `hooks/post_gen_project.py` -- cleanup (remove conditional dirs/files, fix `.mcp.json` trailing commas, create `.env`, git init)
- `{{cookiecutter.project_slug}}/` -- the generated project template root

## Key Patterns

### Jinja2 Conditionals for MCP
MCP integrations use `enable_X_mcp` choice variables ("yes"/"no"):
```
{% if cookiecutter.enable_linear_mcp == "yes" %}...{% endif %}
```
Conditionals gate entire file sections, Makefile targets, agent tool lists, and `.mcp.json` entries.

### ASCII Only
Do NOT use Unicode box-drawing characters or emoji in template files (`| + -` etc. only). Cookiecutter's binary detection incorrectly flags files with Unicode as binary and skips Jinja2 rendering.

### JSON Trailing Commas
Jinja2 conditionals in `.mcp.json` create trailing comma issues. The `post_gen_project.py` hook fixes these with regex replacement + JSON re-serialization. A `_placeholder` key is used as a fallback when no MCPs are enabled.

### Package Name
`project_slug` uses hyphens but Python needs underscores:
```
{{ cookiecutter.project_slug | replace('-', '_') }}
```
This filter is used in both file content and directory names.

### Post-Generation Hook Responsibilities
`hooks/post_gen_project.py` does significant work after generation:
1. Removes Docker files, CI workflows, LICENSE based on user choices
2. Regex-fixes `.mcp.json` trailing commas and re-serializes as valid JSON
3. Copies `.env.example` to `.env`
4. Runs `git init` + initial commit

## Agent Architecture

Seven agents form a validation pipeline with a BA triage gate:

```
Business Analyst -> Project Manager -> Tech Lead -> Architect -> Developer -> Tester -> Tech Lead (sign-off)
```

Plus a **DevOps** agent for deployment. The BA can reject/pause tickets before any development starts.

Each agent's `CLAUDE.md` (in `agents/<role>/`) defines role, MCP tools (conditional on enabled integrations), responsibilities, output format, and decision authority (CAN/CANNOT).

### Python Implementation

- `src/<package>/agent.py` -- `Agent` dataclass wraps Claude CLI via `subprocess.run`. Code-writing roles (developer, tester) auto-create `agent/<slug>` feature branches and auto-commit.
- `src/<package>/orchestrator.py` -- `Pipeline` runs 9-step full pipeline or 4-step fast-track. Parses BA decision keywords (approved/decline/needs info/on hold). Auto-creates merge requests via git push options (GitLab syntax — needs adaptation for GitHub).
- `src/<package>/cli.py` -- Click CLI: `run`, `agent`, `jira-run`, `jira-watch`, `slack-watch`, `status`.
- `src/<package>/config.py` -- Finds project root by walking up to `CLAUDE.md`, loads `.env`, provides agent prompts and MCP config.
- `src/<package>/integrations/` -- Lightweight HTTP clients (no SDKs) for Jira, Confluence, Linear, Slack, Telegram. `NotificationHub` dispatches pipeline events to all enabled services.
- `src/<package>/watchers/` -- Polling loops for Jira tickets and Slack messages.

### Slash Commands

`.claude/commands/` contains 9 slash commands (`/ba`, `/pm`, `/tech-lead`, `/architect`, `/develop`, `/test`, `/review`, `/pipeline`, `/deploy`) for interactive use in Claude Code. Each references its agent's `CLAUDE.md` and accepts `$ARGUMENTS`.

## Gotchas

- **Auto-MR uses GitLab push options** (`-o merge_request.create`) — GitHub repos need a different flow (e.g., `gh pr create`).
- **Agent timeouts**: developer=1800s, tester/architect=900s, others=600s. May need tuning.
- **BA decision parsing** is case-insensitive substring matching; check order matters (decline before approved).
- **Jira `customfield_10100`** is hardcoded for acceptance criteria — differs per Jira instance.
- **No pipeline checkpointing** — failure mid-run requires restarting from the beginning.
- **Node.js 18+** required at runtime for npx-based MCP servers (GitHub, Slack, Telegram, PostgreSQL).
