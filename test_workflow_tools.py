#!/usr/bin/env python3
"""TDD test for workflow tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_workflow_tools_mcp():
    """Test workflow tools via real MCP JSON-RPC protocol"""
    
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
        
        response = process.stdout.readline()
        init_response = json.loads(response)
        assert init_response["id"] == 1
        
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test add_comment
        print("Testing add_comment...")
        comment_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add_comment",
                "arguments": {
                    "key": "KW-41",
                    "comment": "This is a test comment added via MCP"
                }
            }
        }
        
        process.stdin.write(json.dumps(comment_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        comment_response = json.loads(response)
        
        assert comment_response["id"] == 2
        content = comment_response["result"]["content"][0]["text"]
        assert "comment" in content.lower() and "added" in content.lower()
        print("✅ add_comment passed")
        
        print("🎉 All workflow tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_workflow_tools_mcp())