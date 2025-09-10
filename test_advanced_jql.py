#!/usr/bin/env python3
"""TDD test for advanced_jql_search tool via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_advanced_jql_mcp():
    """Test advanced_jql_search tool via real MCP JSON-RPC protocol"""
    
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
        
        # Test advanced_jql_search tool call with complex query
        jql_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "advanced_jql_search",
                "arguments": {
                    "jql": "project = KW",
                    "fields": ["summary", "status", "priority", "assignee", "created", "updated"],
                    "expand": ["changelog"],
                    "limit": 10
                }
            }
        }
        
        process.stdin.write(json.dumps(jql_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        jql_response = json.loads(response)
        
        print(f"Advanced JQL response: {json.dumps(jql_response, indent=2)}")
        
        # Verify response structure
        assert jql_response["id"] == 2
        assert "result" in jql_response
        assert "content" in jql_response["result"]
        
        # Should contain search results with expanded fields
        content = jql_response["result"]["content"][0]["text"]
        assert "issues" in content.lower() or "found" in content.lower()
        
        print("✅ advanced_jql_search tool test passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_advanced_jql_mcp())