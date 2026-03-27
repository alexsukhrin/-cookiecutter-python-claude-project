"""Project configuration."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def get_project_root() -> Path:
    """Walk up from cwd to find CLAUDE.md (project root marker)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    return current


@dataclass
class Config:
    """Project configuration."""

    root: Path = field(default_factory=get_project_root)
    llm_model: str = "{{ cookiecutter.primary_llm }}"

    def __post_init__(self) -> None:
        load_dotenv(self.root / ".env")

    @property
    def agents_dir(self) -> Path:
        return self.root / "agents"

    @property
    def tasks_dir(self) -> Path:
        return self.root / "tasks"

    @property
    def projects_dir(self) -> Path:
        return self.root / "projects"

    @property
    def mcp_config_path(self) -> Path:
        return self.root / ".mcp.json"

    def agent_prompt(self, role: str) -> str:
        """Read an agent's CLAUDE.md as the system prompt."""
        path = self.agents_dir / role / "CLAUDE.md"
        if not path.exists():
            raise FileNotFoundError(f"Agent definition not found: {path}")
        return path.read_text()

    def mcp_config(self) -> dict:
        """Load MCP server configuration."""
        if self.mcp_config_path.exists():
            return json.loads(self.mcp_config_path.read_text())
        return {"mcpServers": {}}

    @property
    def anthropic_api_key(self) -> str | None:
        return os.getenv("ANTHROPIC_API_KEY")
