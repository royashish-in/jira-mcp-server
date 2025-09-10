#!/usr/bin/env python3
"""TDD test for update_issue tool via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_update_issue_mcp():
    """Test update_issue tool via real MCP JSON-RPC protocol"""
    
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
        
        # Test update_issue tool call
        update_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "update_issue",
                "arguments": {
                    "key": "KW-41",
                    "summary": "Updated test issue via MCP",
                    "description": "This issue was updated through the MCP protocol",
                    "priority": "High"
                }
            }
        }
        
        process.stdin.write(json.dumps(update_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        update_response = json.loads(response)
        
        print(f"Update issue response: {json.dumps(update_response, indent=2)}")
        
        # Verify response structure
        assert update_response["id"] == 2
        assert "result" in update_response
        assert "content" in update_response["result"]
        
        # Should contain updated confirmation
        content = update_response["result"]["content"][0]["text"]
        assert "updated" in content.lower() or "KW-41" in content
        
        print("✅ update_issue tool test passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_update_issue_mcp())