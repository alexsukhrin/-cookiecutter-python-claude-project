"""Tests for the Pipeline orchestrator."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from {{ cookiecutter.project_slug | replace('-', '_') }}.orchestrator import Pipeline


class TestPipeline:
    @patch("{{ cookiecutter.project_slug | replace('-', '_') }}.orchestrator.Agent")
    def test_full_pipeline_calls_all_agents(self, MockAgent, config):
        mock_instance = MagicMock()
        mock_instance.run.return_value = "agent output"
        MockAgent.return_value = mock_instance

        pipeline = Pipeline(config=config)
        results = pipeline.run("build a login page")

        assert len(results) == 9  # 9 steps in full pipeline
        assert mock_instance.run.call_count == 9

    @patch("{{ cookiecutter.project_slug | replace('-', '_') }}.orchestrator.Agent")
    def test_fast_track_calls_fewer_agents(self, MockAgent, config):
        mock_instance = MagicMock()
        mock_instance.run.return_value = "agent output"
        MockAgent.return_value = mock_instance

        pipeline = Pipeline(config=config)
        results = pipeline.run_fast_track("fix typo in readme")

        assert len(results) == 4  # 4 steps in fast track
        assert mock_instance.run.call_count == 4
