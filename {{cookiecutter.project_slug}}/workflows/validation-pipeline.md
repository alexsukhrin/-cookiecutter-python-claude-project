# Validation Pipeline

Every project follows this pipeline. No step can be skipped.

```
{% if cookiecutter.enable_jira_mcp == "yes" %}Jira Ticket (assigned){% else %}User Request{% endif %}
    |
    v
+--------------------+
| BUSINESS ANALYST   |  Triage -> evaluate value, estimate, decide
+--------+-----------+
         |
    +----+----+----+
    |         |    |
    v         v    v
 Approved  Needs  On Hold / Decline
    |      Info     -> back to reporter
    |        |
    |        v
    |   (wait for reporter response)
    |
    v
+-----------------+
| PROJECT MANAGER |  Validate & enrich -> task file{% if cookiecutter.enable_linear_mcp == "yes" %} + Linear issue{% endif %}{% if cookiecutter.enable_jira_mcp == "yes" %} + Jira update{% endif %}
+-------+---------+
        |
        v
+-------------+
|  TECH LEAD  |  Decompose -> spec.md + subtasks
+------+------+
       |
       v
+-------------+
|  ARCHITECT  |  Design -> architecture.md
+------+------+
       |
       v
+-------------+
|  TECH LEAD  |  Validate architecture
+------+------+
       |
       v
+-------------+
|  DEVELOPER  |  Implement -> code + self-review
+------+------+
       |
       v
+-------------+
|  ARCHITECT  |  Validate code matches design
+------+------+
       |
       v
+-------------+
|   TESTER    |  Test -> results + bug reports
+------+------+
       |
       v
+-------------+
|  DEVELOPER  |  Fix defects -> loop back to Tester
+------+------+
       |
       v
+-------------+
|  TECH LEAD  |  Final sign-off
+------+------+
       |
       v
+-----------------+
| PROJECT MANAGER |  Close task{% if cookiecutter.enable_confluence_mcp == "yes" %} -> Confluence docs{% endif %}{% if cookiecutter.enable_jira_mcp == "yes" %} -> Jira Review{% endif %}{% if cookiecutter.enable_linear_mcp == "yes" %} -> Linear Done{% endif %}
+-----------------+
```

## BA Triage Decisions

| Decision | Action | Jira Status |
|---|---|---|
| **Approved** | Proceed to PM, start pipeline | In Progress |
| **Needs Info** | Comment with questions, return to reporter | Waiting for Customer |
| **On Hold** | Flag for stakeholder review | Waiting for Customer |
| **Decline** | Comment with reasoning, close | Won't Do |
{% if cookiecutter.enable_jira_mcp == "yes" %}
## Jira-Driven Flow

```bash
# Process a specific Jira ticket (BA triage -> full pipeline)
{{ cookiecutter.project_slug }} jira-run PROJ-123

# Watch for new assigned tickets and process them
{{ cookiecutter.project_slug }} jira-watch --assignee bot@company.com
```
{% endif %}
## Agent Invocation

Each step invokes Claude CLI with the agent's CLAUDE.md as system prompt:

```bash
claude -p "$(cat agents/<role>/CLAUDE.md)" --mcp-config .mcp.json "<prompt>"
```

Or via the Python orchestrator:

```bash
make pipeline REQUEST="your task description"
```

## Fast Track (S complexity)
For small, well-understood changes (BA can approve directly):
1. Tech Lead writes single task
2. Developer implements (Architect reviews post-hoc)
3. Tester writes minimal coverage
4. Tech Lead signs off

```bash
make pipeline REQUEST="fix typo" FAST=1
```
