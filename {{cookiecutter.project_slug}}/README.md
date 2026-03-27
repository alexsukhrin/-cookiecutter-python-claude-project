# {{ cookiecutter.project_name }}

{{ cookiecutter.project_description }}

## Overview

Multi-agent AI orchestration project powered by **Claude CLI**. Five specialized agents collaborate through a structured validation pipeline to deliver high-quality software.

### Agent Pipeline

```
User -> PM -> Tech Lead -> Architect -> Developer -> Tester -> Tech Lead -> PM -> Done
```

| Agent | Responsibility |
|---|---|
| Project Manager | Task intake, tracking, stakeholder communication |
| Tech Lead | Decomposition, prioritization, final sign-off |
| Architect | System design, data models, API contracts |
| Developer | Implementation following architecture specs |
| Tester | Validation, test plans, defect reporting |

## Prerequisites

- Python {{ cookiecutter.python_version }}+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+ (for MCP servers)

## Installation

```bash
# Setup environment
bash scripts/setup.sh

# Or manually
python{{ cookiecutter.python_version }} -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

## Usage

### Run full pipeline
```bash
make pipeline REQUEST="Add user authentication with JWT tokens"
```

### Run single agent
```bash
make agent ROLE=developer TASK=TASK-001
```

### Direct Claude CLI
```bash
claude -p "$(cat agents/developer/CLAUDE.md)" --mcp-config .mcp.json "implement TASK-001"
```

## MCP Integrations
{% if cookiecutter.enable_github_mcp == "yes" %}
- **GitHub** -- Issue tracking, PR management
{%- endif %}
{%- if cookiecutter.enable_linear_mcp == "yes" %}
- **Linear** -- Task management (workspace: {{ cookiecutter.linear_workspace }})
{%- endif %}
{%- if cookiecutter.enable_jira_mcp == "yes" %}
- **Jira** -- Issue tracking ({{ cookiecutter.jira_instance_url }})
{%- endif %}
{%- if cookiecutter.enable_slack_mcp == "yes" %}
- **Slack** -- Team notifications
{%- endif %}
{%- if cookiecutter.enable_telegram_mcp == "yes" %}
- **Telegram** -- Bot notifications
{%- endif %}
{%- if cookiecutter.enable_postgres_mcp == "yes" %}
- **PostgreSQL** -- Database access
{%- endif %}
{%- if cookiecutter.enable_filesystem_mcp == "yes" %}
- **Filesystem** -- File operations
{%- endif %}

Run `/mcp` in Claude Code to authenticate MCP servers.

## Development

```bash
make test       # Run tests
make lint       # Lint & type-check
make format     # Auto-format code
```

## Project Structure

See `CLAUDE.md` for detailed architecture and agent descriptions.
{% if cookiecutter.license != "none" %}
## License

{{ cookiecutter.license }}
{% endif %}
