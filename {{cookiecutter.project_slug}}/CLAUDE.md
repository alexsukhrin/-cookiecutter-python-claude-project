# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**{{ cookiecutter.project_name }}** -- {{ cookiecutter.project_description }}

Multi-agent system where specialized AI agents collaborate through a structured validation pipeline, powered by Claude CLI.

## Quick Start

1. Read this file
2. Check `tasks/` for active tasks
3. Load agent role from `agents/<role>/CLAUDE.md`
4. Follow validation pipeline in `workflows/validation-pipeline.md`

## Agent Pipeline

```
Ticket -> BA (triage) -> PM (intake) -> Tech Lead (decompose) -> Architect (design) -> Developer (implement) -> Tester (validate) -> Tech Lead (sign-off) -> PM (close + docs)
```

| Agent | Role | Artifacts |
|---|---|---|
| **Business Analyst** | Triage, value assessment, estimation, priority | BA analysis comment |
| **Project Manager** | Task intake, tracking, stakeholder comms | `tasks/`, issue tracker |
| **Tech Lead** | Decompose, acceptance criteria, sign-off | `spec.md` |
| **Architect** | System design, data models, API contracts | `architecture.md` |
| **Developer** | Implementation, self-review | Source code |
| **Tester** | Test plans, validation, bug reports | Test results |

**Rules:**
- Every output validated by at least one other agent
- Status flow: `draft -> in_review -> approved -> in_progress -> done`
- No pipeline step can be skipped

## Running Agents

### Full pipeline
```bash
make pipeline REQUEST="your task description"
```

### Single agent
```bash
make agent ROLE=developer TASK=TASK-001
```

### Direct Claude CLI
```bash
claude -p "$(cat agents/developer/CLAUDE.md)" --mcp-config .mcp.json "implement TASK-001"
```
{% if cookiecutter.enable_jira_mcp == "yes" %}
### Jira-driven flow
```bash
# Process a specific ticket (BA triage -> full pipeline -> Confluence)
{{ cookiecutter.project_slug }} jira-run PROJ-123

# Watch for new assigned tickets
{{ cookiecutter.project_slug }} jira-watch
```
{% endif %}

## Structure

```
{{ cookiecutter.project_slug }}/
+-- agents/                  # Agent role definitions (CLAUDE.md per agent)
+-- src/                     # Python orchestration package
+-- tests/                   # Test suite
+-- tasks/                   # Task files
+-- projects/                # Project workspaces
|   +-- .templates/          # spec.md, architecture.md, task.md
+-- workflows/               # Pipeline definitions
+-- scripts/                 # Shell utilities
+-- CLAUDE.md                # This file
```
{% if cookiecutter.enable_linear_mcp == "yes" %}
## Linear Integration

- Workspace: [{{ cookiecutter.linear_workspace }}](https://linear.app/{{ cookiecutter.linear_workspace }})
- MCP configured in `.mcp.json`
- Run `/mcp` to authenticate
{% endif %}{% if cookiecutter.enable_jira_mcp == "yes" %}
## Jira Integration

- Instance: {{ cookiecutter.jira_instance_url }}
- Project: {{ cookiecutter.jira_project_key }}
- MCP configured in `.mcp.json`
{% endif %}{% if cookiecutter.enable_slack_mcp == "yes" %}
## Slack Integration

- Team ID: {{ cookiecutter.slack_team_id }}
- MCP configured in `.mcp.json` for notifications
{% endif %}{% if cookiecutter.enable_telegram_mcp == "yes" %}
## Telegram Integration

- Bot configured in `.mcp.json` for notifications
{% endif %}
## Infrastructure

| Component | Value |
|---|---|
| Python | {{ cookiecutter.python_version }} |
| LLM | {{ cookiecutter.primary_llm }} |
{% if cookiecutter.enable_postgres_mcp == "yes" %}| PostgreSQL | `{{ cookiecutter.postgres_connection_string }}` |
{% endif %}
## Team

Built with [cookiecutter-python-claude-project](https://github.com/{{ cookiecutter.github_username }}/cookiecutter-python-claude-project)
