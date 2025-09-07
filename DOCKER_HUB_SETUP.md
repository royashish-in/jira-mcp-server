# Docker Hub Setup Guide

## 🚀 Publishing to Docker Hub

### Prerequisites

1. **Docker Hub Account**: Create account at [hub.docker.com](https://hub.docker.com)
2. **Docker CLI**: Install Docker Desktop or Docker CLI
3. **Repository Access**: Push access to your Docker Hub repository

### Step 1: Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password
```

### Step 2: Update Configuration

Edit `build-and-push.sh` and update:

```bash
DOCKER_USERNAME="your-dockerhub-username"  # Replace with your username
```

### Step 3: Build and Push

```bash
# Build and push latest version
./build-and-push.sh

# Build and push specific version
VERSION=1.0.0 ./build-and-push.sh
```

### Step 4: Verify on Docker Hub

1. Go to [hub.docker.com](https://hub.docker.com)
2. Navigate to your repository
3. Verify the image was pushed successfully

## 📋 Repository Setup

### Create Repository on Docker Hub

1. Go to Docker Hub → Repositories → Create Repository
2. **Name**: `jira-mcp-server`
3. **Description**: "JIRA MCP Server for AI integration"
4. **Visibility**: Public (recommended) or Private
5. Click "Create"

### Repository Settings

**Description Template:**
```
🔌 JIRA MCP Server for AI Integration

A Model Context Protocol (MCP) server that enables AI assistants to read user stories and issues from JIRA projects.

✨ Features:
• Fetch user stories from JIRA projects
• Get specific issues by key
• Standard MCP protocol support
• Docker-ready deployment
• Secure API token authentication

🚀 Quick Start:
docker run -d \
  -e JIRA_URL=https://company.atlassian.net \
  -e JIRA_USERNAME=user@company.com \
  -e JIRA_API_TOKEN=your-token \
  yourusername/jira-mcp-server:latest

📖 Documentation: https://github.com/yourusername/jira-mcp-server
```

**Tags to add:**
- `mcp`
- `jira`
- `ai`
- `model-context-protocol`
- `atlassian`
- `python`
- `docker`

## 🔄 Automated Builds (Optional)

### GitHub Actions Integration

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: yourusername/jira-mcp-server
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

### Required GitHub Secrets

Add these secrets to your GitHub repository:
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token (not password)

## 📊 Usage Analytics

Monitor your Docker Hub repository for:
- Pull statistics
- Star ratings
- User feedback
- Download trends

## 🔒 Security Best Practices

1. **Use Access Tokens**: Never use passwords in CI/CD
2. **Scan Images**: Enable Docker Hub vulnerability scanning
3. **Regular Updates**: Keep base images updated
4. **Minimal Images**: Use slim/alpine variants when possible

## 📞 Support

If you encounter issues:
1. Check Docker Hub build logs
2. Verify credentials and permissions
3. Test locally before pushing
4. Review Docker Hub documentation