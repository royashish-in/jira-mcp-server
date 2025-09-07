# JIRA MCP Server

A Model Context Protocol (MCP) server for JIRA integration that allows AI assistants to read user stories and issues from JIRA projects.

## 🚀 Quick Start with Docker

```bash
# Pull from Docker Hub
docker pull yourusername/jira-mcp-server:latest

# Run with environment variables
docker run -d \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  --name jira-mcp-server \
  yourusername/jira-mcp-server:latest
```

## 📋 Features

- **Get User Stories**: Fetch user stories from JIRA projects
- **Get Issues**: Retrieve specific JIRA issues by key
- **MCP Protocol**: Standard Model Context Protocol for AI integration
- **Docker Ready**: Pre-built Docker images available
- **Secure**: Uses JIRA API tokens for authentication

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `JIRA_URL` | Your JIRA instance URL | `https://company.atlassian.net` |
| `JIRA_USERNAME` | Your JIRA email | `user@company.com` |
| `JIRA_API_TOKEN` | JIRA API token | `ATATT3xFfGF0...` |

### Getting JIRA API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the generated token

## 🐳 Docker Usage

### Using Docker Hub Image

```bash
# Basic usage
docker run -d \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  yourusername/jira-mcp-server:latest

# With custom name and restart policy
docker run -d \
  --name jira-mcp \
  --restart unless-stopped \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  yourusername/jira-mcp-server:latest
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  jira-mcp-server:
    image: yourusername/jira-mcp-server:latest
    environment:
      - JIRA_URL=https://your-company.atlassian.net
      - JIRA_USERNAME=your-email@company.com
      - JIRA_API_TOKEN=your-api-token
    restart: unless-stopped
```

## 🛠️ Local Development

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/jira-mcp-server.git
cd jira-mcp-server

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your JIRA credentials
nano .env

# Test connection
uv run python test_connection.py

# Run server
uv run python server.py
```

## 🔌 MCP Integration

### With Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": [
        "exec", "-i", "jira-mcp-server",
        "uv", "run", "python", "server.py"
      ]
    }
  }
}
```

### With Other MCP Clients

The server communicates via stdio using the standard MCP protocol:

```bash
# Send MCP requests via stdin
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | docker exec -i jira-mcp-server uv run python server.py
```

## 📖 Available Tools

### `get_user_stories`

Fetch user stories from JIRA projects.

**Parameters:**
- `project` (optional): JIRA project key (e.g., "KW")
- `limit` (optional): Maximum number of stories (default: 10, max: 100)

**Example:**
```json
{
  "name": "get_user_stories",
  "arguments": {
    "project": "KW",
    "limit": 20
  }
}
```

### `get_issue`

Get a specific JIRA issue by key.

**Parameters:**
- `key` (required): JIRA issue key (e.g., "KW-123")

**Example:**
```json
{
  "name": "get_issue",
  "arguments": {
    "key": "KW-123"
  }
}
```

## 🧪 Testing

```bash
# Run all tests
./run_tests.sh

# Unit tests only
uv run python -m pytest test_unit.py -v

# Integration test (requires JIRA access)
uv run python test_integration.py

# Test MCP protocol
uv run python test_mcp_client.py
```

## 🔒 Security

- Uses JIRA API tokens (not passwords)
- Validates input parameters
- Rate limiting and timeout protection
- No data persistence or logging of sensitive information

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/jira-mcp-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/jira-mcp-server/discussions)

## 🏷️ Tags

`mcp` `jira` `ai` `model-context-protocol` `docker` `python` `atlassian`