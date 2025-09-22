FROM python:3.12-slim

LABEL maintainer="Roy Ashish"
LABEL description="JIRA MCP Server - FastMCP 2.0 implementation"
LABEL version="2.0.0"

WORKDIR /app

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies with uv
RUN uv pip install --system fastmcp>=2.0.0 requests>=2.25.0 python-dotenv>=1.0.0

# Copy server file
COPY server.py ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}}}' | python server.py > /dev/null || exit 1

# Run the FastMCP server
CMD ["python", "server.py"]