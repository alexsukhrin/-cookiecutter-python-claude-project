# cookiecutter-python-claude-project

Cookiecutter template for multi-agent AI orchestration projects powered by **Claude CLI**.

Generates a fully structured Python project where 5 specialized AI agents (Project Manager, Tech Lead, Architect, Developer, Tester) collaborate through a sequential validation pipeline.

## Features

- **Multi-agent pipeline** -- 5 agents with defined roles, responsibilities, and validation relationships
- **Claude CLI integration** -- agents invoke Claude Code under the hood via subprocess
- **MCP server support** -- Linear, Jira, GitHub, Slack, Telegram, PostgreSQL, Filesystem
- **Python package** -- proper `src/` layout with Click CLI, pytest tests, ruff linting
- **Orchestration engine** -- full pipeline and fast-track modes
- **CI/CD** -- GitHub Actions for testing and manual pipeline dispatch
- **Docker** -- optional containerized setup with Node.js for MCP servers
- **Git workflow** -- conventional commits, feature branches, PR-based reviews

## Quick Start

```bash
pip install cookiecutter
cookiecutter gh:alexsukhrin/cookiecutter-python-claude-project
```

Or with pipx:
```bash
pipx run cookiecutter gh:alexsukhrin/cookiecutter-python-claude-project
```

## Template Variables

| Variable | Default | Description |
|---|---|---|
| `project_name` | My Claude Agent Project | Human-readable project name |
| `project_slug` | (auto-generated) | Directory/package name |
| `project_description` | Multi-agent AI orchestration... | One-line description |
| `author_name` | Your Name | Author name |
| `author_email` | you@example.com | Author email |
| `github_username` | | GitHub username |
| `python_version` | 3.12 | Python version (3.11, 3.12, 3.13) |
| `primary_llm` | claude-sonnet-4-6 | Claude model for agents |
| `license` | MIT | MIT, Apache-2.0, or none |

### MCP Integrations

| Variable | Default | Required when enabled |
|---|---|---|
| `enable_linear_mcp` | no | `linear_workspace` |
| `enable_jira_mcp` | no | `jira_instance_url`, `jira_project_key` |
| `enable_github_mcp` | yes | -- |
| `enable_slack_mcp` | no | `slack_team_id` |
| `enable_telegram_mcp` | no | `telegram_bot_token` |
| `enable_postgres_mcp` | no | `postgres_connection_string` |
| `enable_filesystem_mcp` | yes | -- |

### Infrastructure

| Variable | Default | Description |
|---|---|---|
| `use_docker` | no | Generate Dockerfile and docker-compose |
| `ci_provider` | github-actions | CI setup (github-actions or none) |

## What You Get

```
my-claude-agent-project/
+-- CLAUDE.md                    # Auto-loaded by Claude Code
+-- .mcp.json                    # MCP server configurations
+-- pyproject.toml               # Python project config
+-- Makefile                     # Dev commands
+-- agents/
|   +-- project-manager/CLAUDE.md
|   +-- tech-lead/CLAUDE.md
|   +-- architect/CLAUDE.md
|   +-- developer/CLAUDE.md
|   +-- tester/CLAUDE.md
+-- src/<package>/
|   +-- cli.py                   # Click CLI entry point
|   +-- agent.py                 # Base agent (wraps Claude CLI)
|   +-- orchestrator.py          # Pipeline orchestrator
|   +-- config.py                # Configuration loader
|   +-- agents/                  # Agent role implementations
+-- tests/                       # pytest test suite
+-- workflows/
|   +-- validation-pipeline.md
|   +-- project-setup.md
+-- projects/.templates/         # spec.md, architecture.md, task.md
+-- scripts/                     # setup.sh, run_pipeline.sh, run_agent.sh
+-- docker/                      # (optional) Dockerfile, docker-compose.yml
+-- .github/workflows/           # (optional) CI + agent pipeline dispatch
```

## Agent Pipeline

```
User -> PM (intake) -> Tech Lead (decompose) -> Architect (design)
     -> Tech Lead (validate) -> Developer (implement)
     -> Architect (validate code) -> Tester (test)
     -> Developer (fix) -> Tech Lead (sign-off) -> PM (close)
```

Each agent:
- Has a dedicated `CLAUDE.md` defining its role, tools, and decision authority
- Is invoked via Claude CLI with MCP server access
- Validates the previous agent's output before passing to the next

## Usage After Generation

```bash
cd my-claude-agent-project

# Setup
bash scripts/setup.sh
cp .env.example .env  # Add ANTHROPIC_API_KEY

# Run full pipeline
make pipeline REQUEST="Add user authentication with JWT"

# Run single agent
make agent ROLE=developer TASK=TASK-001

# Direct Claude CLI
claude -p "$(cat agents/developer/CLAUDE.md)" --mcp-config .mcp.json "implement TASK-001"
```

## Prerequisites

- Python 3.11+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+ (for MCP servers)
- An [Anthropic API key](https://console.anthropic.com/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test template generation: `cookiecutter . --no-input`
4. Submit a pull request

## License

MIT
