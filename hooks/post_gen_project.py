"""Post-generation cleanup and setup hook."""
import json
import os
import re
import shutil
import subprocess


def cleanup():
    # Remove Docker files if not needed
    if "{{ cookiecutter.use_docker }}" == "no":
        shutil.rmtree("docker", ignore_errors=True)

    # Remove CI files if not needed
    if "{{ cookiecutter.ci_provider }}" == "none":
        shutil.rmtree(".github", ignore_errors=True)

    # Remove LICENSE if none selected
    if "{{ cookiecutter.license }}" == "none":
        for f in ("LICENSE",):
            if os.path.exists(f):
                os.remove(f)

    # Fix .mcp.json — remove trailing commas from Jinja2 conditional output
    mcp_path = ".mcp.json"
    if os.path.exists(mcp_path):
        with open(mcp_path) as f:
            content = f.read()
        content = re.sub(r",\s*([}\]])", r"\1", content)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"mcpServers": {}}
        if not parsed.get("mcpServers"):
            parsed["mcpServers"] = {}
        # Remove placeholder key used for valid JSON fallback
        parsed.get("mcpServers", {}).pop("_placeholder", None)
        with open(mcp_path, "w") as f:
            json.dump(parsed, f, indent=2)
            f.write("\n")

    # Create .env from .env.example
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")

    # Init git repo
    subprocess.run(["git", "init"], capture_output=True)
    subprocess.run(["git", "add", "."], capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial scaffold from cookiecutter-python-claude-project"],
        capture_output=True,
    )


def print_next_steps():
    project = "{{ cookiecutter.project_slug }}"
    print(
        f"""
{'=' * 60}
  {project} created successfully!
{'=' * 60}

Next steps:
  cd {project}
  bash scripts/setup.sh          # Create venv & install deps
  cp .env.example .env           # Add your ANTHROPIC_API_KEY
  make pipeline REQUEST="..."    # Run full agent pipeline

Docs:
  cat CLAUDE.md                  # Project overview
  cat workflows/validation-pipeline.md  # Pipeline details
"""
    )


if __name__ == "__main__":
    cleanup()
    print_next_steps()
else:
    cleanup()
    print_next_steps()
