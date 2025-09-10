# Deployment Guide

## PyPI Package ✅

```bash
# Latest published: v1.0.1 (46 tools)
pip install jira-mcp-server

# Verify installation
python -c "import jira_mcp_server; print('46 tools available')"

# Run server
jira-mcp-server
```

## Docker Hub ✅

```bash
# Pull and run (46 JIRA tools available)
docker pull royashish/jira-mcp-server:latest
docker run -d -e JIRA_URL=... -e JIRA_USERNAME=... -e JIRA_API_TOKEN=... royashish/jira-mcp-server:latest
```

## MCP Client Integration

### Claude Desktop
```bash
# Copy config to Claude Desktop
cp claude-desktop-config.json ~/.config/claude-desktop/mcp_servers.json
```

### Cline
```bash
# Use mcp-clients/cline-config.json
```

### Continue.dev
```bash
# Use mcp-clients/continue-config.json
```

## Kubernetes (Helm)

```bash
# Install chart
helm install jira-mcp ./helm-chart \
  --set jira.url=https://company.atlassian.net \
  --set jira.username=user@company.com \
  --set jira.apiToken=token
```

## Multi-Instance Setup

```bash
# Generate config for multiple JIRA instances
python multi-instance-config.py > multi-jira-config.json
```

## Publishing

```bash
# Publish to PyPI
./publish-pypi.sh

# Submit to MCP registry
# Use mcp-registry.yaml
```