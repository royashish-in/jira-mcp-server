# Project Guidelines

## Project Type
- **UV Project**: Uses `uv` package manager for dependency management
- **Python Project**: Python 3.10+ codebase
- **FastMCP Project**: Built with FastMCP 2.0 framework for MCP server implementation

## Key Technologies
- FastMCP 2.0 for MCP protocol handling
- Requests library for HTTP calls (synchronous to avoid TaskGroup conflicts)
- Python type hints for auto-schema generation
- Decorator-based tool definitions

## Development Commands
```bash
# Install dependencies
uv sync

# Run FastMCP server (recommended)
uv run python server_fastmcp.py

# Run original server
uv run python server.py

# Run tests
uv run python test/test_suite.py
```