#!/bin/bash
set -e

# Get credentials
read -p "JIRA URL (https://company.atlassian.net): " JIRA_URL
read -p "JIRA Username (email): " JIRA_USERNAME
read -s -p "JIRA API Token: " JIRA_API_TOKEN
echo
read -p "Docker Hub username: " DOCKER_USER

echo "🧹 Cleaning Docker environment..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker system prune -f

echo "🔧 Building image..."
docker build -t jira-mcp-server:test .

echo "🔗 Testing connection (basic logging)..."
docker run --rm \
  -e JIRA_URL="$JIRA_URL" \
  -e JIRA_USERNAME="$JIRA_USERNAME" \
  -e JIRA_API_TOKEN="$JIRA_API_TOKEN" \
  jira-mcp-server:test python test_connection.py

echo "🔗 Testing connection (verbose logging)..."
docker run --rm \
  -e JIRA_URL="$JIRA_URL" \
  -e JIRA_USERNAME="$JIRA_USERNAME" \
  -e JIRA_API_TOKEN="$JIRA_API_TOKEN" \
  -e VERBOSE_LOGGING=true \
  jira-mcp-server:test python test_connection.py

echo "🛠️ Testing MCP tools list..."
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
docker run --rm -i \
  -e JIRA_URL="$JIRA_URL" \
  -e JIRA_USERNAME="$JIRA_USERNAME" \
  -e JIRA_API_TOKEN="$JIRA_API_TOKEN" \
  jira-mcp-server:test

echo "📋 Testing get_user_stories (any project)..."
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"limit":3}}}' | \
docker run --rm -i \
  -e JIRA_URL="$JIRA_URL" \
  -e JIRA_USERNAME="$JIRA_USERNAME" \
  -e JIRA_API_TOKEN="$JIRA_API_TOKEN" \
  -e VERBOSE_LOGGING=true \
  jira-mcp-server:test

read -p "Enter a JIRA issue key to test (e.g., KW-123): " ISSUE_KEY
if [ ! -z "$ISSUE_KEY" ]; then
  echo "🎫 Testing get_issue..."
  echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"get_issue\",\"arguments\":{\"key\":\"$ISSUE_KEY\"}}}" | \
  docker run --rm -i \
    -e JIRA_URL="$JIRA_URL" \
    -e JIRA_USERNAME="$JIRA_USERNAME" \
    -e JIRA_API_TOKEN="$JIRA_API_TOKEN" \
    -e VERBOSE_LOGGING=true \
    jira-mcp-server:test
fi

echo "🏷️ Tagging for Docker Hub..."
docker tag jira-mcp-server:test $DOCKER_USER/jira-mcp-server:latest

echo "🚀 Pushing to Docker Hub..."
docker push $DOCKER_USER/jira-mcp-server:latest

echo "✅ Testing deployed image..."
docker rmi $DOCKER_USER/jira-mcp-server:latest
docker pull $DOCKER_USER/jira-mcp-server:latest
docker run --rm \
  -e JIRA_URL="$JIRA_URL" \
  -e JIRA_USERNAME="$JIRA_USERNAME" \
  -e JIRA_API_TOKEN="$JIRA_API_TOKEN" \
  $DOCKER_USER/jira-mcp-server:latest python test_connection.py

echo "🎉 All tests passed! End users can now run:"
echo "docker pull $DOCKER_USER/jira-mcp-server:latest"