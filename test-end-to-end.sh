#!/bin/bash
set -e

echo "🧹 Cleaning Docker environment..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker rmi $(docker images -q) --force 2>/dev/null || true
docker system prune -af --volumes

echo "🔧 Building image..."
docker build -t jira-mcp-server:test .

echo "🔗 Testing JIRA connection..."
docker run --rm --env-file .env jira-mcp-server:test python test_connection.py

echo "🛠️ Testing MCP tools..."
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | docker run --rm -i --env-file .env jira-mcp-server:test

echo "📋 Testing get_user_stories..."
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_user_stories","arguments":{"limit":3}}}' | docker run --rm -i --env-file .env jira-mcp-server:test

echo "🏷️ Tagging for Docker Hub..."
read -p "Enter your Docker Hub username: " DOCKER_USER
docker tag jira-mcp-server:test $DOCKER_USER/jira-mcp-server:latest

echo "🚀 Pushing to Docker Hub..."
docker push $DOCKER_USER/jira-mcp-server:latest

echo "✅ Testing deployed image..."
docker rmi $DOCKER_USER/jira-mcp-server:latest
docker pull $DOCKER_USER/jira-mcp-server:latest
docker run --rm --env-file .env $DOCKER_USER/jira-mcp-server:latest python test_connection.py

echo "🎉 All tests passed! Image ready for end users."