#!/usr/bin/env python3
"""Multi-instance JIRA MCP server configuration generator"""

import json
import os
from typing import Dict, List

def generate_multi_instance_config(instances: List[Dict]) -> Dict:
    """Generate Claude Desktop config for multiple JIRA instances"""
    config = {"mcpServers": {}}
    
    for i, instance in enumerate(instances):
        server_name = f"jira-{instance.get('name', f'instance{i+1}')}"
        config["mcpServers"][server_name] = {
            "command": "docker",
            "args": [
                "run", "--rm", "-i",
                "-e", f"JIRA_URL={instance['url']}",
                "-e", f"JIRA_USERNAME={instance['username']}",
                "-e", f"JIRA_API_TOKEN={instance['token']}",
                "royashish/jira-mcp-server:latest"
            ]
        }
    
    return config

# Example usage
if __name__ == "__main__":
    instances = [
        {
            "name": "prod",
            "url": "https://company.atlassian.net",
            "username": "prod@company.com",
            "token": "prod-token"
        },
        {
            "name": "staging", 
            "url": "https://staging.atlassian.net",
            "username": "staging@company.com",
            "token": "staging-token"
        }
    ]
    
    config = generate_multi_instance_config(instances)
    print(json.dumps(config, indent=2))