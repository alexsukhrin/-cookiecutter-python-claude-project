"""Tests for the Agent class."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from {{ cookiecutter.project_slug | replace('-', '_') }}.agent import Agent, AgentError


class TestAgent:
    def test_build_command(self, config):
        agent = Agent(role="developer", config=config)
        cmd = agent._build_command("implement feature X")
        assert cmd[0] == "claude"
        assert "-p" in cmd
        assert "implement feature X" in cmd

    def test_system_prompt_loaded(self, config):
        agent = Agent(role="developer", config=config)
        prompt = agent.system_prompt
        assert "Agent: developer" in prompt

    def test_missing_agent_raises(self, config):
        agent = Agent(role="nonexistent", config=config)
        with pytest.raises(FileNotFoundError):
            _ = agent.system_prompt

    @patch("subprocess.run")
    def test_run_success(self, mock_run, config):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Done", stderr=""
        )
        agent = Agent(role="developer", config=config)
        result = agent.run("implement feature")
        assert result == "Done"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_failure(self, mock_run, config):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error occurred"
        )
        agent = Agent(role="developer", config=config)
        with pytest.raises(AgentError, match="error occurred"):
            agent.run("bad command")
