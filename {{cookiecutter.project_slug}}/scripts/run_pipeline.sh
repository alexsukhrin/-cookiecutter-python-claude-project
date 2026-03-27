#!/usr/bin/env bash
set -euo pipefail

# Run the full agent pipeline
REQUEST="${1:?Usage: run_pipeline.sh <request>}"

# Check deps
command -v claude >/dev/null 2>&1 || {
    echo "Error: Claude CLI not found. Install: npm install -g @anthropic-ai/claude-code"
    exit 1
}

if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

python -m {{ cookiecutter.project_slug | replace('-', '_') }}.cli run "$REQUEST"
