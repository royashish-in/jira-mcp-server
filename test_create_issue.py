#!/usr/bin/env python3
"""TDD test for create_issue tool via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_create_issue_mcp():
    """Test create_issue tool via real MCP JSON-RPC protocol"""
    
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
        
        # Test create_issue tool call
        create_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "create_issue",
                "arguments": {
                    "project": "KW",
                    "summary": "Test issue created via MCP",
                    "description": "This is a test issue created through the MCP protocol",
                    "issue_type": "Task"
                }
            }
        }
        
        process.stdin.write(json.dumps(create_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        create_response = json.loads(response)
        
        print(f"Create issue response: {json.dumps(create_response, indent=2)}")
        
        # Verify response structure
        assert create_response["id"] == 2
        assert "result" in create_response
        assert "content" in create_response["result"]
        
        # Should contain created issue key
        content = create_response["result"]["content"][0]["text"]
        assert "KW-" in content or "created" in content.lower()
        
        print("✅ create_issue tool test passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_create_issue_mcp())