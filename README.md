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

- **46 JIRA Tools**: Complete JIRA operations ecosystem
- **Core Operations**: User stories, issues, projects, search, stats
- **Workflow Management**: Transitions, comments, assignments, worklogs
- **Agile Support**: Boards, sprints, backlogs, burndown charts
- **File Management**: Upload, download, list attachments
- **Advanced Features**: Webhooks, reporting, batch operations
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

## 📖 Available Tools (46 Total)

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

### Advanced Admin & Edge Cases (5 tools)
- `create_webhook` - Create new webhooks
- `create_version` - Create project versions
- `get_user_permissions` - Get user permissions
- `get_workflows` - Get workflow definitions
- `release_version` - Release project versions
- `get_burndown_data` - Get sprint burndown data

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
# Run all tests (recommended)
python run_tests.py

# Quick validation (30 seconds)
python run_tests.py --smoke

# Core functionality (2 minutes)
python run_tests.py --unit

# All 46 tools (5 minutes)
python run_tests.py --comprehensive

# Test JIRA connection
python test_connection.py
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