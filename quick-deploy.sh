#!/bin/bash
set -e

# Quick deployment script for patched version
DOCKER_USER=${1:-"yourusername"}
VERSION=${2:-"latest"}

echo "🧹 Cleaning Docker..."
docker system prune -f

echo "🔧 Building patched version..."
docker build -t jira-mcp-server:$VERSION .

echo "🏷️ Tagging..."
docker tag jira-mcp-server:$VERSION $DOCKER_USER/jira-mcp-server:$VERSION

echo "🚀 Pushing to Docker Hub..."
docker push $DOCKER_USER/jira-mcp-server:$VERSION

echo "✅ Deployed $DOCKER_USER/jira-mcp-server:$VERSION"
echo "📋 End users can now run:"
echo "docker pull $DOCKER_USER/jira-mcp-server:$VERSION"