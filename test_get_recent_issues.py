#!/usr/bin/env python3
"""
TDD Test for get_recent_issues MCP Tool
"""

import asyncio
import json
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_get_recent_issues_mcp():
    """Test get_recent_issues tool via real MCP protocol."""
    
    env = os.environ.copy()
    required_vars = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not env.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("Testing get_recent_issues tool via MCP protocol...")
    
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
        
        if "get_recent_issues" not in tool_names:
            print("get_recent_issues tool not found")
            return False
        
        print("get_recent_issues tool found")
        
        # Test with default parameters
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_recent_issues",
                "arguments": {"days": 30, "limit": 10}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response_data = json.loads(process.stdout.readline())
        
        if "error" in response_data:
            print(f"get_recent_issues call failed: {response_data['error']}")
            return False
        
        # Validate response structure
        content = response_data["result"]["content"][0]["text"]
        issues_data = json.loads(content)
        
        if "issues" not in issues_data:
            print("Missing 'issues' key in response")
            return False
        
        issues = issues_data["issues"]
        print(f"Found {len(issues)} recent issues")
        
        # Validate issue structure
        if issues:
            first_issue = issues[0]
            required_fields = ["key", "summary", "status", "updated", "created"]
            for field in required_fields:
                if field not in first_issue:
                    print(f"Missing field '{field}' in issue")
                    return False
            
            print(f"Example recent issue: {first_issue['key']} - {first_issue['summary']}")
        
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

if __name__ == "__main__":
    print("TDD Test: get_recent_issues MCP Tool")
    print("=" * 40)
    
    success = asyncio.run(test_get_recent_issues_mcp())
    
    if success:
        print("TEST PASSED: get_recent_issues tool working correctly")
        sys.exit(0)
    else:
        print("TEST FAILED: get_recent_issues tool needs implementation")
        sys.exit(1)