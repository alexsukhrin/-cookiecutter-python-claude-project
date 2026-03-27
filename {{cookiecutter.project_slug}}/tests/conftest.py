"""Shared test fixtures."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from {{ cookiecutter.project_slug | replace('-', '_') }}.config import Config


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing."""
    (tmp_path / "CLAUDE.md").write_text("# Test Project")
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {}}')
    (tmp_path / "tasks").mkdir()
    agents_dir = tmp_path / "agents"
    for role in ("project-manager", "tech-lead", "architect", "developer", "tester"):
        role_dir = agents_dir / role
        role_dir.mkdir(parents=True)
        (role_dir / "CLAUDE.md").write_text(f"# Agent: {role}")
    return tmp_path


@pytest.fixture
def config(project_root: Path) -> Config:
    """Config pointing to the test project root."""
    return Config(root=project_root)
