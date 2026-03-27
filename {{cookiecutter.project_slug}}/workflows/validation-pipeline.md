# Validation Pipeline

Every project follows this pipeline. No step can be skipped.

```
User Request
    |
    v
+-----------------+
| PROJECT MANAGER |  Intake -> task file{% if cookiecutter.enable_linear_mcp == "yes" %} + Linear issue{% endif %}{% if cookiecutter.enable_jira_mcp == "yes" %} + Jira issue{% endif %}
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
| PROJECT MANAGER |  Close task{% if cookiecutter.enable_linear_mcp == "yes" %} -> Linear Done{% endif %}{% if cookiecutter.enable_jira_mcp == "yes" %} -> Jira Done{% endif %}
+-----------------+
```

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
For small, well-understood changes:
1. Tech Lead writes single task
2. Developer implements (Architect reviews post-hoc)
3. Tester writes minimal coverage
4. Tech Lead signs off

```bash
make pipeline REQUEST="fix typo" FAST=1
```
