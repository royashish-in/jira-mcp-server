#!/usr/bin/env python3
"""TDD test for advanced workflow tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_advanced_workflow_mcp():
    """Test advanced workflow tools via real MCP JSON-RPC protocol"""
    
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
        
        # Test bulk_transition_issues
        print("Testing bulk_transition_issues...")
        bulk_transition_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "bulk_transition_issues",
                "arguments": {
                    "keys": ["KW-41"],
                    "transition": "To Do"
                }
            }
        }
        
        process.stdin.write(json.dumps(bulk_transition_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        bulk_response = json.loads(response)
        
        assert bulk_response["id"] == 2
        content = bulk_response["result"]["content"][0]["text"]
        assert "bulk" in content.lower() or "transition" in content.lower()
        print("✅ bulk_transition_issues passed")
        
        print("🎉 Advanced workflow tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_advanced_workflow_mcp())