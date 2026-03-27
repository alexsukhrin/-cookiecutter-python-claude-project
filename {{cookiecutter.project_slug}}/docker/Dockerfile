FROM python:{{ cookiecutter.python_version }}-slim

# Install Node.js for MCP servers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

# Install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy project
COPY . .

ENTRYPOINT ["python", "-m", "{{ cookiecutter.project_slug | replace('-', '_') }}.cli"]
