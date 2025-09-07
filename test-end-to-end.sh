#!/bin/bash
"""
End-to-End Test Script for JIRA MCP Server

This script performs a complete end-to-end test of the JIRA MCP server including:
1. Docker environment cleanup
2. Image building and local testing
3. MCP protocol validation
4. Docker Hub deployment
5. Deployed image verification

Prerequisites:
- Docker installed and running
- .env file with JIRA credentials and DOCKER_USER
- Docker Hub account with push permissions
- Valid JIRA instance and API token

Usage:
    bash test-end-to-end.sh

Environment Variables Required:
- JIRA_URL: Your Atlassian JIRA instance URL
- JIRA_USERNAME: Your JIRA email address
- JIRA_API_TOKEN: Your JIRA API token
- DOCKER_USER: Your Docker Hub username

This script will:
- Clean up any existing Docker containers/images
- Build a fresh Docker image
- Test JIRA connectivity within the container
- Validate MCP protocol functionality
- Push the image to Docker Hub
- Pull and test the deployed image
"""

# Exit immediately if any command fails
# This ensures we catch errors early and don't continue with broken state
set -e

# Step 1: Clean Docker Environment
# This ensures we start with a clean slate and don't have conflicts
# with existing containers or images from previous runs
echo "🧹 Cleaning Docker environment..."

# Stop all running containers (ignore errors if none are running)
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all containers (ignore errors if none exist)
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove all images forcefully (ignore errors if none exist)
# This ensures we build from scratch and test the complete build process
docker rmi $(docker images -q) --force 2>/dev/null || true

# Clean up Docker system (networks, volumes, build cache)
# -a: Remove all unused images, not just dangling ones
# -f: Don't prompt for confirmation
# --volumes: Remove unused volumes as well
docker system prune -af --volumes

# Step 2: Build Docker Image
# Build the JIRA MCP server image from the current directory
# Tag it as 'test' to distinguish from production builds
echo "🔧 Building image..."
docker build -t jira-mcp-server:test .

# Step 3: Test JIRA Connection
# Verify that the container can connect to JIRA using the credentials
# This tests both the container environment and JIRA authentication
echo "🔗 Testing JIRA connection..."
# --rm: Remove container after it exits
# --env-file: Load environment variables from .env file
docker run --rm --env-file .env jira-mcp-server:test python test_connection.py

# Step 4: Test MCP Protocol
# Use the comprehensive MCP test that handles proper initialization
echo "🛠️ Testing MCP protocol..."
docker run --rm --env-file .env jira-mcp-server:test python test_mcp_working.py

# Step 6: Tag Image for Docker Hub
# Load environment variables from .env file to get DOCKER_USER
# Tag the local test image with the Docker Hub repository name
echo "🏷️ Tagging for Docker Hub..."
source .env  # Load DOCKER_USER from .env file
docker tag jira-mcp-server:test $DOCKER_USER/jira-mcp-server:latest

# Step 7: Push to Docker Hub
# Upload the image to Docker Hub so others can use it
# Requires Docker Hub authentication (docker login)
echo "🚀 Pushing to Docker Hub..."
docker push $DOCKER_USER/jira-mcp-server:latest

# Step 8: Test Deployed Image
# Verify the image works correctly after being pushed and pulled
# This simulates what end users will experience
echo "✅ Testing deployed image..."

# Remove the local image to ensure we're testing the deployed version
docker rmi $DOCKER_USER/jira-mcp-server:latest

# Pull the image from Docker Hub (simulates end user experience)
docker pull $DOCKER_USER/jira-mcp-server:latest

# Test the pulled image to ensure it works correctly
# This verifies the complete deployment pipeline
docker run --rm --env-file .env $DOCKER_USER/jira-mcp-server:latest python test_connection.py

# Step 9: Success Message
# If we reach this point, all tests have passed successfully
echo "🎉 All tests passed! Image ready for end users."
echo "Users can now run: docker pull $DOCKER_USER/jira-mcp-server:latest"
echo "Users can now run: docker pull $DOCKER_USER/jira-mcp-server:latest"