# End User Examples - JIRA MCP Server

## Quick Start Commands

### 1. Clean Docker Environment
```bash
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker system prune -f
```

### 2. Pull and Test Connection
```bash
# Basic connection test
docker run --rm \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  yourusername/jira-mcp-server:latest python test_connection.py

# With verbose logging
docker run --rm \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  -e VERBOSE_LOGGING=true \
  yourusername/jira-mcp-server:latest python test_connection.py
```

### 3. Use MCP Tools

#### List Available Tools
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
docker run --rm -i \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  yourusername/jira-mcp-server:latest
```

#### Get User Stories (Any Project)
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"limit":5}}}' | \
docker run --rm -i \
  -e JIRA_URL=https://royashish.atlassian.net \
  -e JIRA_USERNAME=royashish@gmail.com \
  -e JIRA_API_TOKEN=ATATT3xFfGF0Ii8ku_ibQ7l_xsYwLWP4mIE43TG8-2HZ3Zwp9AOBLqjizMR6PJjoUTkBb5PS_6RzUQfY1Y1xEH8Zejm57Kp675iybC9RzzsUDuxw9W3NbsjgPkRQRiQoGW07VM68O2Yvwhti06LhSHHo5H0KJTkB9Vuv5se9NaE-Hm6AC5n4lqk=6C43DE08 \
  -e VERBOSE_LOGGING=true \
  royashish/jira-mcp-server:latest
```

#### Get Stories from Specific Project
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"project":"KW","limit":10}}}' | \
docker run --rm -i \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  -e VERBOSE_LOGGING=true \
  yourusername/jira-mcp-server:latest
```

#### Get Specific Issue
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_issue","arguments":{"key":"KW-123"}}}' | \
docker run --rm -i \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  -e VERBOSE_LOGGING=true \
  yourusername/jira-mcp-server:latest
```

### 4. Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  jira-mcp-server:
    image: yourusername/jira-mcp-server:latest
    environment:
      - JIRA_URL=https://your-company.atlassian.net
      - JIRA_USERNAME=your-email@company.com
      - JIRA_API_TOKEN=your-api-token
      - VERBOSE_LOGGING=true
    restart: unless-stopped
```

```bash
# Run with compose
docker-compose up -d
docker-compose logs -f

# Test while running
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
docker-compose exec -T jira-mcp-server uv run python server.py

docker-compose down
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_URL` | Yes | - | Your JIRA instance URL |
| `JIRA_USERNAME` | Yes | - | Your JIRA email |
| `JIRA_API_TOKEN` | Yes | - | JIRA API token |
| `VERBOSE_LOGGING` | No | `false` | Enable detailed logging |

## Expected Outputs

### Connection Test Success
```
✅ JIRA connection successful
✅ Authentication verified
✅ API access confirmed
```

### Tools List Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_user_stories",
        "description": "Get user stories from JIRA"
      },
      {
        "name": "get_issue",
        "description": "Get specific JIRA issue by key"
      }
    ]
  }
}
```

### User Stories Response
```json
{
  "stories": [
    {
      "key": "KW-123",
      "summary": "As a user, I want to...",
      "status": "In Progress",
      "description": "Detailed description..."
    }
  ]
}
```

## Troubleshooting

### Enable Verbose Logging
Add `-e VERBOSE_LOGGING=true` to see detailed logs

### Common Issues
- **401 Error**: Invalid JIRA_API_TOKEN
- **403 Error**: Insufficient JIRA permissions
- **Connection Error**: Check JIRA_URL format
- **No Stories Found**: Check project permissions