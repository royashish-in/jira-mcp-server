#!/usr/bin/env python3
"""
TDD Test for get_project_stats MCP Tool
"""

import asyncio
import json
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_get_project_stats_mcp():
    """Test get_project_stats tool via real MCP protocol."""
    
    env = os.environ.copy()
    required_vars = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not env.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("Testing get_project_stats tool via MCP protocol...")
    
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        # Initialize MCP
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        process.stdout.readline()
        
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()
        
        # Verify tool exists
        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        process.stdin.write(json.dumps(list_request) + "\n")
        process.stdin.flush()
        
        tools_response = json.loads(process.stdout.readline())
        tool_names = [tool["name"] for tool in tools_response["result"]["tools"]]
        
        if "get_project_stats" not in tool_names:
            print("get_project_stats tool not found")
            return False
        
        print("get_project_stats tool found")
        
        # Test with project key
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_project_stats",
                "arguments": {"project": "KW"}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response_data = json.loads(process.stdout.readline())
        
        if "error" in response_data:
            print(f"get_project_stats call failed: {response_data['error']}")
            return False
        
        # Validate response structure
        content = response_data["result"]["content"][0]["text"]
        stats_data = json.loads(content)
        
        required_fields = ["project", "totalIssues", "issuesByStatus", "issuesByType"]
        for field in required_fields:
            if field not in stats_data:
                print(f"Missing field '{field}' in stats")
                return False
        
        print(f"Project: {stats_data['project']}")
        print(f"Total Issues: {stats_data['totalIssues']}")
        print(f"Status breakdown: {len(stats_data['issuesByStatus'])} statuses")
        print(f"Type breakdown: {len(stats_data['issuesByType'])} types")
        
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

if __name__ == "__main__":
    print("TDD Test: get_project_stats MCP Tool")
    print("=" * 40)
    
    success = asyncio.run(test_get_project_stats_mcp())
    
    if success:
        print("TEST PASSED: get_project_stats tool working correctly")
        sys.exit(0)
    else:
        print("TEST FAILED: get_project_stats tool needs implementation")
        sys.exit(1)