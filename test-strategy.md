# JIRA MCP Server - End User Test Strategy

## Prerequisites
- Docker Desktop installed and running
- JIRA instance with API access
- Docker Hub account (for publishing)

## 1. Clean Docker Environment

```bash
# Stop and remove all containers
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove all images
docker rmi $(docker images -q) --force 2>/dev/null || true

# Clean system
docker system prune -af --volumes

# Verify clean state
docker ps -a
docker images
```

## 2. Build and Test Locally

```bash
# Clone and setup
git clone <your-repo-url>
cd jira-mcp-server-standalone

# Create environment file
cp .env.example .env
# Edit .env with your JIRA credentials

# Build image
docker build -t jira-mcp-server:test .

# Test basic functionality
docker run --rm --env-file .env jira-mcp-server:test python test_connection.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | docker run --rm -i --env-file .env jira-mcp-server:test
```

## 3. Integration Tests

```bash
# Test get_user_stories
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"limit":5}}}' | docker run --rm -i --env-file .env jira-mcp-server:test

# Test get_issue (replace KW-123 with actual issue)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_issue","arguments":{"key":"KW-123"}}}' | docker run --rm -i --env-file .env jira-mcp-server:test

# Test with Docker Compose
docker-compose up -d
docker-compose logs
docker-compose down
```

## 4. Deploy to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag for Docker Hub (replace 'yourusername')
docker tag jira-mcp-server:test yourusername/jira-mcp-server:latest
docker tag jira-mcp-server:test yourusername/jira-mcp-server:v1.0.0

# Push to Docker Hub
docker push yourusername/jira-mcp-server:latest
docker push yourusername/jira-mcp-server:v1.0.0

# Verify deployment
docker pull yourusername/jira-mcp-server:latest
docker run --rm --env-file .env yourusername/jira-mcp-server:latest python test_connection.py
```

## 5. End User Verification

```bash
# Clean pull test
docker rmi yourusername/jira-mcp-server:latest
docker pull yourusername/jira-mcp-server:latest

# Quick test
docker run --rm \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your-email@company.com \
  -e JIRA_API_TOKEN=your-token \
  yourusername/jira-mcp-server:latest python test_connection.py
```

## 6. Automated Test Script

```bash
# Make executable and run
chmod +x test-end-to-end.sh
./test-end-to-end.sh
```

## Expected Results
- ✅ Connection test passes
- ✅ MCP tools/list returns 2 tools
- ✅ get_user_stories returns JSON with stories
- ✅ get_issue returns specific issue data
- ✅ Docker Hub deployment successful
- ✅ Clean pull and run works