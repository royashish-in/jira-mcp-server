#!/usr/bin/env python3
"""
TDD Test for search_issues MCP Tool

Tests the search_issues tool via real MCP JSON-RPC protocol communication.
"""

import asyncio
import json
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_search_issues_mcp():
    """Test search_issues tool via real MCP protocol."""
    
    env = os.environ.copy()
    required_vars = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not env.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("Testing search_issues tool via MCP protocol...")
    
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
        process.stdout.readline()  # Read init response
        
        # Send initialized notification
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()
        
        # Test 1: Verify tool exists
        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        process.stdin.write(json.dumps(list_request) + "\n")
        process.stdin.flush()
        
        tools_response = json.loads(process.stdout.readline())
        tool_names = [tool["name"] for tool in tools_response["result"]["tools"]]
        
        if "search_issues" not in tool_names:
            print("search_issues tool not found")
            return False
        
        print("search_issues tool found")
        
        # Test 2: Call with basic JQL
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_issues",
                "arguments": {
                    "jql": "project = KW ORDER BY created DESC",
                    "limit": 5
                }
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        response_data = json.loads(process.stdout.readline())
        
        if "error" in response_data:
            print(f"search_issues call failed: {response_data['error']}")
            return False
        
        # Validate response structure
        content = response_data["result"]["content"][0]["text"]
        search_data = json.loads(content)
        
        if "issues" not in search_data:
            print("Missing 'issues' key in response")
            return False
        
        issues = search_data["issues"]
        print(f"Found {len(issues)} issues")
        
        # Test 3: Validate issue structure
        if issues:
            first_issue = issues[0]
            required_fields = ["key", "summary", "status", "issueType"]
            for field in required_fields:
                if field not in first_issue:
                    print(f"Missing field '{field}' in issue")
                    return False
            
            print(f"Example issue: {first_issue['key']} - {first_issue['summary']}")
        
        # Test 4: Test invalid JQL handling
        invalid_call = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "search_issues",
                "arguments": {
                    "jql": "INVALID JQL SYNTAX",
                    "limit": 5
                }
            }
        }
        
        process.stdin.write(json.dumps(invalid_call) + "\n")
        process.stdin.flush()
        
        invalid_response = json.loads(process.stdout.readline())
        
        # Should handle invalid JQL gracefully
        if "error" not in invalid_response and "Error" not in invalid_response.get("result", {}).get("content", [{}])[0].get("text", ""):
            print("Should handle invalid JQL with error message")
            return False
        
        print("Invalid JQL handled correctly")
        
        return True
        
    except Exception as e:
        print(f"Test error: {e}")
        return False
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

if __name__ == "__main__":
    print("TDD Test: search_issues MCP Tool")
    print("=" * 40)
    
    success = asyncio.run(test_search_issues_mcp())
    
    if success:
        print("TEST PASSED: search_issues tool working correctly")
        sys.exit(0)
    else:
        print("TEST FAILED: search_issues tool needs implementation")
        sys.exit(1)