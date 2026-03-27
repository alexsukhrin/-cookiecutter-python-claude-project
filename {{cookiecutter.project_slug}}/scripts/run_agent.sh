#!/usr/bin/env bash
set -euo pipefail

# Run a single agent via Claude CLI
ROLE="${1:?Usage: run_agent.sh <role> <prompt>}"
PROMPT="${2:?Usage: run_agent.sh <role> <prompt>}"

AGENT_MD="agents/${ROLE}/CLAUDE.md"
if [ ! -f "$AGENT_MD" ]; then
    echo "Error: Agent definition not found: $AGENT_MD"
    echo "Available roles: project-manager, tech-lead, architect, developer, tester"
    exit 1
fi

claude -p "$(cat "$AGENT_MD")" --mcp-config .mcp.json "$PROMPT"
