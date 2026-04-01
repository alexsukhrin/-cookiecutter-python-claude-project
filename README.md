# cookiecutter-python-claude-project

Cookiecutter template for **multi-agent AI orchestration** projects powered by Claude CLI.

## Why

Setting up a multi-agent development workflow from scratch takes days: agent roles, validation pipelines, issue tracker integration, documentation generation, CLI tooling. This template generates a production-ready project in seconds with everything wired together.

## What It Does

Generates a Python project where **6 specialized AI agents** collaborate through a structured validation pipeline:

```
Jira/Linear ticket
    |
    v
Business Analyst -- evaluate value, estimate, prioritize, decide
    |
    v  (Approved)
Project Manager -- validate ticket, enrich, create task
    |
    v
Tech Lead -- decompose into spec + subtasks
    |
    v
Architect -- design -> architecture.md
    |
    v
Developer -- implement following architecture
    |
    v
Tester -- validate, report defects
    |
    v
Tech Lead -- final sign-off
    |
    v
Project Manager -- close task, publish to Confluence
```

The BA can **reject or pause** a ticket before any development starts (Needs Info / On Hold / Decline).

## Features

- **7-agent pipeline** with Business Analyst triage gate (+ DevOps agent)
- **Two modes**: Claude Code slash commands (`/ba`, `/pipeline`, `/deploy`) for interactive use + subprocess CLI for automation
- **Feature branches** -- Developer/Tester agents work on `agent/<slug>` branch with auto-commit
- **Auto-create merge requests** after pipeline completes (via git push options)
- **Jira-driven flow** -- watch tickets, BA triage, auto-process, comment results back
- **Slack watcher** -- poll channel, respond in threads, run pipeline via `analyze` command
- **Confluence** -- auto-publish pipeline results as documentation pages
- **MCP servers** -- Jira, Linear, GitHub, Slack, Telegram, PostgreSQL, Confluence, Filesystem
- **Python CLI** -- `run`, `agent`, `jira-run`, `jira-watch`, `slack-watch`, `status` commands
- **Tested scaffold** -- 21 passing tests, ruff clean, mypy-ready
- **Optional** -- Docker, GitHub Actions CI/CD

## Quick Start

```bash
pipx run cookiecutter gh:alexsukhrin/-cookiecutter-python-claude-project
```

Then:
```bash
cd my-project
bash scripts/setup.sh
cp .env.example .env   # add ANTHROPIC_API_KEY + integration tokens
```

## Usage

```bash
# Full pipeline from a text request
make pipeline REQUEST="Add user authentication with JWT"

# Process a Jira ticket (BA triage -> pipeline -> Confluence)
make jira-run ISSUE=PROJ-123

# Watch Jira for new tickets and auto-process
make jira-watch

# Watch Slack channel and respond to messages
make slack-watch

# Run a single agent
make agent ROLE=developer TASK=TASK-001

# Show status
make status
```

### Claude Code slash commands (interactive)

Inside Claude Code, use slash commands for interactive work with full project context:

```
/ba Add user authentication with JWT
/pipeline Migrate database to PostgreSQL
/develop implement TASK-001
/test validate auth module
/review
/deploy v1.0.0
```

## Template Variables

| Variable | Default | Description |
|---|---|---|
| `project_name` | My Claude Agent Project | Human-readable project name |
| `project_slug` | *(auto-generated)* | Directory and package name |
| `project_description` | Multi-agent AI orchestration... | One-line description |
| `author_name` | Your Name | |
| `author_email` | you@example.com | |
| `github_username` | | GitHub username for links |
| `python_version` | 3.12 | 3.11 / 3.12 / 3.13 |
| `primary_llm` | claude-sonnet-4-6 | Claude model for agent invocations |
| `license` | MIT | MIT / Apache-2.0 / none |

### Integrations (pick what you need)

| Integration | Default | Config required |
|---|---|---|
| **Jira** | no | `jira_instance_url`, `jira_project_key`, `jira_assignee` |
| **Confluence** | no | `confluence_url`, `confluence_space_key` |
| **Linear** | no | `linear_workspace` |
| **GitHub** | yes | -- |
| **Slack** | no | `slack_team_id` |
| **Telegram** | no | `telegram_bot_token` |
| **PostgreSQL** | no | `postgres_connection_string` |
| **Filesystem** | yes | -- |
| **Docker** | no | -- |
| **GitHub Actions CI** | yes | -- |

## What You Get

```
my-project/
+-- CLAUDE.md                        # Auto-loaded by Claude Code
+-- .mcp.json                        # MCP server configurations
+-- .claude/commands/                 # Claude Code slash commands
|   +-- ba.md, pm.md, tech-lead.md   # /ba, /pm, /tech-lead
|   +-- architect.md, develop.md     # /architect, /develop
|   +-- test.md, review.md           # /test, /review
|   +-- deploy.md, pipeline.md       # /deploy, /pipeline
+-- pyproject.toml                   # Python project (hatchling)
+-- Makefile                         # Dev commands
+-- agents/
|   +-- business-analyst/CLAUDE.md   # Triage, estimation, priority
|   +-- project-manager/CLAUDE.md    # Intake, tracking, notifications
|   +-- tech-lead/CLAUDE.md          # Decomposition, sign-off
|   +-- architect/CLAUDE.md          # Design, data models, API contracts
|   +-- developer/CLAUDE.md          # Implementation
|   +-- tester/CLAUDE.md             # Validation, defect reporting
|   +-- devops/CLAUDE.md             # Deployment, CI/CD, infrastructure
+-- src/<package>/
|   +-- cli.py                       # Click CLI (run, agent, jira-run, jira-watch, status)
|   +-- agent.py                     # Base agent (wraps Claude CLI, feature branches)
|   +-- orchestrator.py              # Pipeline orchestrator (auto-MR)
|   +-- config.py                    # Configuration loader
|   +-- integrations/
|   |   +-- hub.py                   # Notification dispatcher
|   |   +-- jira.py                  # Jira REST API client
|   |   +-- confluence.py            # Confluence page publisher
|   |   +-- linear.py                # Linear GraphQL client
|   |   +-- slack.py                 # Slack Bot API client
|   |   +-- telegram.py              # Telegram Bot API client
|   +-- watchers/
|       +-- jira_watcher.py          # Poll Jira for new tickets
|       +-- slack_watcher.py         # Poll Slack, respond in threads
+-- tests/                           # 21 tests (pytest)
+-- workflows/                       # Pipeline docs
+-- projects/.templates/             # spec.md, architecture.md, task.md
+-- scripts/                         # setup.sh, run_pipeline.sh, run_agent.sh
+-- docker/                          # (optional)
+-- .github/workflows/               # (optional) CI + agent pipeline dispatch
```

## Prerequisites

- Python 3.11+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+ (for MCP servers)
- [Anthropic API key](https://console.anthropic.com/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test: `pipx run cookiecutter . --no-input && cd my-claude-agent-project && pip install -e ".[dev]" && pytest`
4. Submit a pull request

## License

MIT
