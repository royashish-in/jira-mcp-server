FROM python:3.12-slim

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="JIRA MCP Server for AI integration"
LABEL version="1.0.0"

WORKDIR /app

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy all files needed for installation
COPY pyproject.toml README.md ./
COPY server.py test_connection.py test_mcp_working.py ./

# Install dependencies with pip
RUN pip install --no-cache-dir .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python test_connection.py || exit 1

# Run the MCP server
CMD ["python", "server.py"]