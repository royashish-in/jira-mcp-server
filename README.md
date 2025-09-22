# JIRA MCP Server

A Model Context Protocol (MCP) server for JIRA integration built with **FastMCP 2.0** that allows AI assistants to read user stories and issues from JIRA projects.

## 🚀 Quick Start with Docker

```bash
# Pull from Docker Hub
docker pull royashish/jira-mcp-server:latest

# Test MCP protocol
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"roots":{"listChanged":true},"sampling":{}},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"project":"KW","limit":3}}}' | docker run -i --env-file .env royashish/jira-mcp-server:latest
```

## 📋 Features

- **47 JIRA Tools**: Complete JIRA operations ecosystem (including global statistics)
- **FastMCP 2.0**: Modern, efficient implementation with 90% less code
- **Core Operations**: User stories, issues, projects, search, stats
- **Workflow Management**: Transitions, comments, assignments, worklogs
- **Agile Support**: Boards, sprints, backlogs, burndown charts
- **File Management**: Upload, download, list attachments
- **Advanced Features**: Webhooks, reporting, batch operations
- **MCP Protocol**: Standard Model Context Protocol for AI integration
- **Auto Schema Generation**: FastMCP handles validation and type safety
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
# Interactive MCP mode (recommended)
docker run -i --env-file .env royashish/jira-mcp-server:latest

# Background daemon mode
docker run -d \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  --name jira-mcp \
  royashish/jira-mcp-server:latest
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  jira-mcp-server:
    image: royashish/jira-mcp-server:latest
    environment:
      - JIRA_URL=https://your-company.atlassian.net
      - JIRA_USERNAME=your-email@company.com
      - JIRA_API_TOKEN=your-api-token
    restart: unless-stopped
```

### Using Kubernetes (Helm)

```bash
# Install with Helm
helm install jira-mcp ./helm-chart \
  --set jira.url=https://your-company.atlassian.net \
  --set jira.username=your-email@company.com \
  --set jira.apiToken=your-api-token
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

# Run server (FastMCP 2.0)
uv run python server.py
```

## 🔌 MCP Integration

### With Claude Desktop

Add to `~/.config/Claude Desktop/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--env-file", "/path/to/.env",
        "royashish/jira-mcp-server:latest"
      ]
    }
  }
}
```

### With Other MCP Clients

**Cline (VSCode)** - Add to settings:
```json
{
  "cline.mcpServers": {
    "jira": {
      "command": "docker",
      "args": ["run", "-i", "--env-file", ".env", "royashish/jira-mcp-server:latest"]
    }
  }
}
```

**Continue** - Add to config:
```json
{
  "mcpServers": {
    "jira": {
      "command": "docker",
      "args": ["run", "-i", "--env-file", ".env", "royashish/jira-mcp-server:latest"]
    }
  }
}
```

### Manual Testing

```bash
# Send MCP requests via stdin
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | docker run -i --env-file .env royashish/jira-mcp-server:latest
```

## 📖 Available Tools (47 Total)

### Core JIRA Operations (10 tools)
- `get_user_stories` - Fetch user stories from projects
- `get_issue` - Get specific issue by key
- `get_projects` - List all accessible projects
- `search_issues` - Search issues with JQL
- `get_project_stats` - Get project statistics
- `get_recent_issues` - Get recently updated issues
- `get_issues_by_assignee` - Get issues by assignee
- `create_issue` - Create new issues
- `update_issue` - Update existing issues
- `advanced_jql_search` - Advanced JQL search

### Workflow Management (6 tools)
- `transition_issue` - Change issue status
- `bulk_transition_issues` - Bulk status changes
- `get_transitions` - Get available transitions
- `add_comment` - Add comments to issues
- `assign_issue` - Assign issues to users
- `add_worklog` - Log work time

### File & Attachment Management (3 tools)
- `upload_attachment` - Upload files to issues
- `download_attachment` - Download attachments
- `list_attachments` - List issue attachments

### Project & User Management (5 tools)
- `get_issue_types` - Get project issue types
- `get_project_components` - Get project components
- `get_project_versions` - Get project versions
- `get_custom_fields` - Get custom field definitions
- `get_users` - Get project users

### Agile & Sprint Management (4 tools)
- `get_boards` - Get agile boards
- `get_sprints` - Get board sprints
- `get_sprint_issues` - Get sprint issues
- `add_to_sprint` - Add issues to sprints

### Issue Relationships & Hierarchy (4 tools)
- `link_issues` - Create issue links
- `get_issue_links` - Get issue relationships
- `get_subtasks` - Get issue subtasks
- `create_subtask` - Create subtasks

### Batch Operations (2 tools)
- `bulk_update_issues` - Bulk update multiple issues
- `bulk_transition_issues` - Bulk transition multiple issues

### Webhooks & Notifications (3 tools)
- `list_webhooks` - List configured webhooks
- `add_watcher` - Add issue watchers
- `get_watchers` - Get issue watchers

### Advanced Issue Operations (1 tool)
- `clone_issue` - Clone existing issues

### Reporting & Analytics (3 tools)
- `get_time_tracking_report` - Get time tracking data
- `get_project_roles` - Get project role assignments
- `export_issues` - Export issues in various formats

### Advanced Admin & Edge Cases (6 tools)
- `create_webhook` - Create new webhooks
- `create_version` - Create project versions
- `get_user_permissions` - Get user permissions
- `get_workflows` - Get workflow definitions
- `release_version` - Release project versions
- `get_burndown_data` - Get sprint burndown data
- `get_jira_statistics` - Get comprehensive JIRA instance statistics

**Example Usage:**
```json
{
  "name": "get_user_stories",
  "arguments": {
    "project": "KW",
    "limit": 20
  }
}
```

## 🧪 Testing

```bash
# Run comprehensive test suite (all 47 tools)
python test/test_suite.py

# Test locally (without Docker)
python test/test_suite.py --local
```

See [test/TEST_GUIDE.md](test/TEST_GUIDE.md) for detailed testing instructions.

## 🔒 Security

- Uses JIRA API tokens (not passwords)
- Validates input parameters
- Rate limiting and timeout protection
- No data persistence or logging of sensitive information

## 🧪 Testing

Comprehensive test suite validates all 47 tools:

```bash
# Test all tools with Docker
python test/test_suite.py

# Test locally
python test/test_suite.py --local
```

See [test/TEST_GUIDE.md](test/TEST_GUIDE.md) for details.

## 🔧 Technical Details

- **HTTP Client**: Uses synchronous `requests` library (resolves MCP TaskGroup conflicts with async httpx)
- **MCP Protocol**: JSON-RPC 2.0 over stdin/stdout
- **Dependencies**: `fastmcp>=2.0.0`, `requests>=2.25.0`, `python-dotenv>=1.0.0`
- **Python**: 3.10+ required

### MCP TaskGroup Fix

This server uses the synchronous `requests` library instead of `httpx.AsyncClient` to avoid TaskGroup management conflicts with MCP server frameworks. The async `httpx` client can cause 424 status codes and task cleanup issues when used within MCP's event loop management.

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