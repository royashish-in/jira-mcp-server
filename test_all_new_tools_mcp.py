#!/usr/bin/env python3
"""Comprehensive test for all new MCP tools via real JSON-RPC protocol"""

import asyncio
import json
import subprocess
import sys

async def test_all_new_tools_mcp():
    """Test all new tools via real MCP JSON-RPC protocol"""
    
    # Start server process
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Initialize
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
        
        # Read initialize response
        response = process.stdout.readline()
        init_response = json.loads(response)
        assert init_response["id"] == 1
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test 1: create_issue
        print("Testing create_issue...")
        create_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "project": "KW",
                    "summary": "TDD Test Issue",
                    "description": "Created via TDD testing",
                    "issue_type": "Task",
                    "priority": "Low"
                }
            }
        }
        
        process.stdin.write(json.dumps(create_request) + "\n")
        process.stdin.flush()
        response = process.stdout.readline()
        create_response = json.loads(response)
        
        assert create_response["id"] == 2
        content = create_response["result"]["content"][0]["text"]
        assert "created" in content.lower() or "KW-" in content
        print("✅ create_issue passed")
        
        # Extract created issue key for update test
        import re
        issue_key_match = re.search(r'KW-\d+', content)
        created_key = issue_key_match.group() if issue_key_match else "KW-41"
        
        # Test 2: update_issue
        print("Testing update_issue...")
        update_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "update_issue",
                "arguments": {
                    "key": created_key,
                    "summary": "Updated TDD Test Issue",
                    "priority": "Medium"
                }
            }
        }
        
        process.stdin.write(json.dumps(update_request) + "\n")
        process.stdin.flush()
        response = process.stdout.readline()
        update_response = json.loads(response)
        
        assert update_response["id"] == 3
        content = update_response["result"]["content"][0]["text"]
        assert "updated" in content.lower() or created_key in content
        print("✅ update_issue passed")
        
        # Test 3: advanced_jql_search
        print("Testing advanced_jql_search...")
        jql_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "advanced_jql_search",
                "arguments": {
                    "jql": "project = KW",
                    "fields": ["summary", "status", "priority"],
                    "limit": 5
                }
            }
        }
        
        process.stdin.write(json.dumps(jql_request) + "\n")
        process.stdin.flush()
        response = process.stdout.readline()
        jql_response = json.loads(response)
        
        assert jql_response["id"] == 4
        content = jql_response["result"]["content"][0]["text"]
        assert "total" in content and "issues" in content
        print("✅ advanced_jql_search passed")
        
        print("\n🎉 All new TDD tools passed comprehensive testing!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_all_new_tools_mcp())