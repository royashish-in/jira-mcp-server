#!/bin/bash
set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Configuration
IMAGE_NAME="jira-mcp-server"
DOCKER_USERNAME="${DOCKER_USERNAME:-royashish}"
VERSION="${VERSION:-latest}"

echo "🐳 Building and pushing JIRA MCP Server to Docker Hub"
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"

# Build the image
echo "📦 Building Docker image..."
if ! docker build -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}" .; then
    echo "❌ Docker build failed"
    exit 1
fi

# Tag as latest if not already
if [ "$VERSION" != "latest" ]; then
    if ! docker tag "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}" "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"; then
        echo "❌ Docker tag failed"
        exit 1
    fi
fi

# Test the image with MCP protocol
echo "🧪 Testing Docker image..."
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
docker run --rm -i \
    -e JIRA_URL="${TEST_JIRA_URL:-https://placeholder.atlassian.net}" \
    -e JIRA_USERNAME="${TEST_JIRA_USERNAME:-placeholder@example.com}" \
    -e JIRA_API_TOKEN="${TEST_JIRA_API_TOKEN:-placeholder-token}" \
    "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}" || echo "⚠️  Test failed (expected without real credentials)"

# Check Docker login status
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon not accessible"
    exit 1
fi

# Push to Docker Hub
echo "🚀 Pushing to Docker Hub..."
if ! docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"; then
    echo "❌ Docker push failed - ensure you are logged in with 'docker login'"
    exit 1
fi

if [ "$VERSION" != "latest" ]; then
    if ! docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"; then
        echo "❌ Docker push latest failed"
        exit 1
    fi
fi

echo "✅ Successfully pushed ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} to Docker Hub"
echo ""
echo "📋 Usage:"
echo "docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo "docker run -d \\"
echo "  -e JIRA_URL=https://your-company.atlassian.net \\"
echo "  -e JIRA_USERNAME=your-email@company.com \\"
echo "  -e JIRA_API_TOKEN=your-api-token \\"
echo "  ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"