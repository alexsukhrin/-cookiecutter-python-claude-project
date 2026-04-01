.PHONY: install test lint format pipeline agent setup

PYTHON ?= python{{ cookiecutter.python_version }}
VENV ?= .venv
PACKAGE = {{ cookiecutter.project_slug | replace('-', '_') }}

install: $(VENV)/bin/activate

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -e ".[dev]"

setup:
	bash scripts/setup.sh

test:
	$(VENV)/bin/pytest tests/ -v

lint:
	$(VENV)/bin/ruff check src/ tests/
	$(VENV)/bin/mypy src/

format:
	$(VENV)/bin/ruff format src/ tests/
	$(VENV)/bin/ruff check --fix src/ tests/

pipeline:
	$(VENV)/bin/python -m $(PACKAGE).cli run "$(REQUEST)"

agent:
	$(VENV)/bin/python -m $(PACKAGE).cli agent --role $(ROLE) --task $(TASK)
{% if cookiecutter.enable_jira_mcp == "yes" %}
jira-run:
	$(VENV)/bin/python -m $(PACKAGE).cli jira-run $(ISSUE)

jira-watch:
	$(VENV)/bin/python -m $(PACKAGE).cli jira-watch
{% endif %}{% if cookiecutter.enable_slack_mcp == "yes" %}
slack-watch:
	$(VENV)/bin/python -m $(PACKAGE).cli slack-watch
{% endif %}
status:
	$(VENV)/bin/python -m $(PACKAGE).cli status
{% if cookiecutter.use_docker == "yes" %}
docker-build:
	docker compose -f docker/docker-compose.yml build

docker-run:
	docker compose -f docker/docker-compose.yml up
{% endif %}
