"""CLI entry point for agent orchestration."""
from __future__ import annotations

import logging
import sys

import click

from .config import Config
from .orchestrator import Pipeline


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def main(verbose: bool) -> None:
    """{{ cookiecutter.project_name }} -- multi-agent orchestration CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


@main.command()
@click.argument("request")
@click.option("--fast", is_flag=True, help="Use fast-track pipeline (S-complexity).")
def run(request: str, fast: bool) -> None:
    """Run the agent pipeline on a request."""
    config = Config()
    if not config.anthropic_api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set. Check your .env file.", err=True)
        sys.exit(1)

    pipeline = Pipeline(config=config)
    try:
        if fast:
            results = pipeline.run_fast_track(request)
        else:
            results = pipeline.run(request)
        click.echo("\n=== Pipeline Results ===")
        for step, output in results.items():
            click.echo(f"\n--- {step} ---")
            click.echo(output[:500] if len(output) > 500 else output)
    except Exception as e:
        click.echo(f"Pipeline failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--role", "-r", required=True, help="Agent role (e.g., developer, tester).")
@click.option("--task", "-t", required=True, help="Task ID or description.")
def agent(role: str, task: str) -> None:
    """Run a single agent with a task."""
    from .agent import Agent

    config = Config()
    if not config.anthropic_api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set. Check your .env file.", err=True)
        sys.exit(1)

    try:
        a = Agent(role=role, config=config)
        result = a.run(task)
        click.echo(result)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Agent failed: {e}", err=True)
        sys.exit(1)


@main.command()
def status() -> None:
    """Show current project and task status."""
    config = Config()
    tasks_dir = config.tasks_dir

    if not tasks_dir.exists():
        click.echo("No tasks/ directory found.")
        return

    task_files = sorted(tasks_dir.glob("*.md"))
    if not task_files:
        click.echo("No tasks found.")
        return

    click.echo(f"Found {len(task_files)} task(s):")
    for tf in task_files:
        click.echo(f"  - {tf.name}")


if __name__ == "__main__":
    main()
