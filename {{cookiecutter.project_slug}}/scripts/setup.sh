#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python{{ cookiecutter.python_version }}}"
VENV="${VENV:-.venv}"

echo "=== {{ cookiecutter.project_name }} Setup ==="

# Check Python
if ! command -v "$PYTHON" &>/dev/null; then
    echo "Error: $PYTHON not found. Install Python {{ cookiecutter.python_version }}+."
    exit 1
fi

# Check Claude CLI
if ! command -v claude &>/dev/null; then
    echo "Warning: Claude CLI not found. Install: npm install -g @anthropic-ai/claude-code"
fi

# Create venv
echo "Creating virtual environment..."
$PYTHON -m venv "$VENV"
source "$VENV/bin/activate"

# Install deps
echo "Installing dependencies..."
pip install -e ".[dev]"

# Pre-commit
if command -v pre-commit &>/dev/null; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi

# .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example -- edit it with your API keys."
fi

echo ""
echo "Setup complete! Next:"
echo "  source $VENV/bin/activate"
echo "  edit .env with your ANTHROPIC_API_KEY"
echo "  make pipeline REQUEST=\"your first task\""
