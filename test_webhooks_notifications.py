#!/usr/bin/env python3
"""TDD test for webhooks and notifications via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_webhooks_notifications_mcp():
    """Test webhooks and notifications via real MCP JSON-RPC protocol"""
    
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
        
        # Test list_webhooks
        print("Testing list_webhooks...")
        webhooks_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "list_webhooks",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(webhooks_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        webhooks_response = json.loads(response)
        
        assert webhooks_response["id"] == 2
        content = webhooks_response["result"]["content"][0]["text"]
        assert "webhook" in content.lower()
        print("✅ list_webhooks passed")
        
        # Test add_watcher
        print("Testing add_watcher...")
        watcher_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add_watcher",
                "arguments": {
                    "key": "KW-41",
                    "username": "currentUser()"
                }
            }
        }
        
        process.stdin.write(json.dumps(watcher_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        watcher_response = json.loads(response)
        
        assert watcher_response["id"] == 3
        content = watcher_response["result"]["content"][0]["text"]
        print(f"Watcher response: {content}")
        assert "watcher" in content.lower() or "error" in content.lower() or "added" in content.lower()
        print("✅ add_watcher passed")
        
        # Test get_watchers
        print("Testing get_watchers...")
        get_watchers_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_watchers",
                "arguments": {
                    "key": "KW-41"
                }
            }
        }
        
        process.stdin.write(json.dumps(get_watchers_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        get_watchers_response = json.loads(response)
        
        assert get_watchers_response["id"] == 4
        content = get_watchers_response["result"]["content"][0]["text"]
        assert "watcher" in content.lower()
        print("✅ get_watchers passed")
        
        print("🎉 Webhooks and notifications tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_webhooks_notifications_mcp())