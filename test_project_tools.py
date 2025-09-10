#!/usr/bin/env python3
"""TDD test for project tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_project_tools_mcp():
    """Test project tools via real MCP JSON-RPC protocol"""
    
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
        
        # Test get_issue_types
        print("Testing get_issue_types...")
        types_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_issue_types",
                "arguments": {
                    "project": "KW"
                }
            }
        }
        
        process.stdin.write(json.dumps(types_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        types_response = json.loads(response)
        
        assert types_response["id"] == 2
        content = types_response["result"]["content"][0]["text"]
        assert "types" in content.lower() or "task" in content.lower()
        print("✅ get_issue_types passed")
        
        print("🎉 Project tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_project_tools_mcp())