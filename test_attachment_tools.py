#!/usr/bin/env python3
"""TDD test for attachment tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_attachment_tools_mcp():
    """Test attachment tools via real MCP JSON-RPC protocol"""
    
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
        
        # Test list_attachments
        print("Testing list_attachments...")
        attachments_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "list_attachments",
                "arguments": {
                    "key": "KW-41"
                }
            }
        }
        
        process.stdin.write(json.dumps(attachments_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        attachments_response = json.loads(response)
        
        assert attachments_response["id"] == 2
        content = attachments_response["result"]["content"][0]["text"]
        assert "attachments" in content.lower()
        print("✅ list_attachments passed")
        
        print("🎉 Attachment tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_attachment_tools_mcp())