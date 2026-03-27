"""Pre-generation validation hook."""
import re
import sys


def validate():
    slug = "{{ cookiecutter.project_slug }}"
    if not re.match(r"^[a-z][a-z0-9-]*$", slug):
        print(f"ERROR: '{slug}' is not a valid project slug (lowercase letters, digits, hyphens).")
        sys.exit(1)

    checks = [
        (
            "{{ cookiecutter.enable_linear_mcp }}" == "yes"
            and not "{{ cookiecutter.linear_workspace }}".strip(),
            "Linear MCP enabled but linear_workspace is empty.",
        ),
        (
            "{{ cookiecutter.enable_jira_mcp }}" == "yes"
            and not "{{ cookiecutter.jira_instance_url }}".strip(),
            "Jira MCP enabled but jira_instance_url is empty.",
        ),
        (
            "{{ cookiecutter.enable_slack_mcp }}" == "yes"
            and not "{{ cookiecutter.slack_team_id }}".strip(),
            "Slack MCP enabled but slack_team_id is empty.",
        ),
    ]

    for condition, message in checks:
        if condition:
            print(f"ERROR: {message}")
            sys.exit(1)


if __name__ == "__main__":
    validate()
else:
    validate()
