#!/usr/bin/env python3
"""TDD test for custom fields and sprint management via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_custom_fields_sprints_mcp():
    """Test custom fields and sprint management via real MCP JSON-RPC protocol"""
    
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
        
        # Test get_custom_fields
        print("Testing get_custom_fields...")
        custom_fields_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_custom_fields",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(custom_fields_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        custom_fields_response = json.loads(response)
        
        assert custom_fields_response["id"] == 2
        content = custom_fields_response["result"]["content"][0]["text"]
        assert "fields" in content.lower() or "custom" in content.lower()
        print("✅ get_custom_fields passed")
        
        # Test get_sprints
        print("Testing get_sprints...")
        sprints_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_sprints",
                "arguments": {
                    "board_id": "1"
                }
            }
        }
        
        process.stdin.write(json.dumps(sprints_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        sprints_response = json.loads(response)
        
        assert sprints_response["id"] == 3
        content = sprints_response["result"]["content"][0]["text"]
        assert "sprint" in content.lower() or "board" in content.lower()
        print("✅ get_sprints passed")
        
        print("🎉 Custom fields and sprint tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_custom_fields_sprints_mcp())