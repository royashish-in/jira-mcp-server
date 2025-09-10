#!/usr/bin/env python3
"""TDD test for transition_issue tool via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_transition_issue_mcp():
    """Test transition_issue tool via real MCP JSON-RPC protocol"""
    
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
        
        # Test transition_issue
        transition_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "transition_issue",
                "arguments": {
                    "key": "KW-41",
                    "transition": "In Progress"
                }
            }
        }
        
        process.stdin.write(json.dumps(transition_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        transition_response = json.loads(response)
        
        print(f"Transition response: {json.dumps(transition_response, indent=2)}")
        
        assert transition_response["id"] == 2
        assert "result" in transition_response
        content = transition_response["result"]["content"][0]["text"]
        assert "transition" in content.lower() or "progress" in content.lower()
        
        print("✅ transition_issue tool test passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_transition_issue_mcp())