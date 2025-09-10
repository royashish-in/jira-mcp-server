#!/usr/bin/env python3
"""TDD test for get_transitions tool via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_get_transitions_mcp():
    """Test get_transitions tool via real MCP JSON-RPC protocol"""
    
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
        
        # Test get_transitions
        transitions_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_transitions",
                "arguments": {
                    "key": "KW-41"
                }
            }
        }
        
        process.stdin.write(json.dumps(transitions_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        transitions_response = json.loads(response)
        
        print(f"Transitions response: {json.dumps(transitions_response, indent=2)}")
        
        assert transitions_response["id"] == 2
        assert "result" in transitions_response
        content = transitions_response["result"]["content"][0]["text"]
        assert "transitions" in content.lower() or "available" in content.lower()
        
        print("✅ get_transitions tool test passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_get_transitions_mcp())