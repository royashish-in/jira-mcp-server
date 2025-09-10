#!/usr/bin/env python3
"""TDD test for Priority 2 tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_priority2_tools_mcp():
    """Test Priority 2 tools via real MCP JSON-RPC protocol"""
    
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
        
        # Test add_worklog
        print("Testing add_worklog...")
        worklog_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "add_worklog",
                "arguments": {
                    "key": "KW-41",
                    "time_spent": "2h",
                    "comment": "Test worklog entry"
                }
            }
        }
        
        process.stdin.write(json.dumps(worklog_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        worklog_response = json.loads(response)
        
        assert worklog_response["id"] == 2
        content = worklog_response["result"]["content"][0]["text"]
        assert "worklog" in content.lower() or "time" in content.lower()
        print("✅ add_worklog passed")
        
        # Test get_users
        print("Testing get_users...")
        users_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_users",
                "arguments": {
                    "project": "KW"
                }
            }
        }
        
        process.stdin.write(json.dumps(users_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        users_response = json.loads(response)
        
        assert users_response["id"] == 3
        content = users_response["result"]["content"][0]["text"]
        assert "user" in content.lower()
        print("✅ get_users passed")
        
        # Test create_subtask
        print("Testing create_subtask...")
        subtask_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "create_subtask",
                "arguments": {
                    "parent_key": "KW-41",
                    "summary": "Test subtask",
                    "description": "Created via TDD test"
                }
            }
        }
        
        process.stdin.write(json.dumps(subtask_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        subtask_response = json.loads(response)
        
        assert subtask_response["id"] == 4
        content = subtask_response["result"]["content"][0]["text"]
        assert "subtask" in content.lower() or "created" in content.lower()
        print("✅ create_subtask passed")
        
        print("🎉 Priority 2 tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_priority2_tools_mcp())