#!/usr/bin/env python3
"""TDD test for Priority 1 missing tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_priority1_tools_mcp():
    """Test Priority 1 missing tools via real MCP JSON-RPC protocol"""
    
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
        
        # Test get_boards
        print("Testing get_boards...")
        boards_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_boards",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(boards_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        boards_response = json.loads(response)
        
        assert boards_response["id"] == 2
        content = boards_response["result"]["content"][0]["text"]
        assert "board" in content.lower()
        print("✅ get_boards passed")
        
        # Test get_sprint_issues
        print("Testing get_sprint_issues...")
        sprint_issues_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_sprint_issues",
                "arguments": {
                    "sprint_id": "1"
                }
            }
        }
        
        process.stdin.write(json.dumps(sprint_issues_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        sprint_issues_response = json.loads(response)
        
        assert sprint_issues_response["id"] == 3
        content = sprint_issues_response["result"]["content"][0]["text"]
        assert "sprint" in content.lower() or "issues" in content.lower()
        print("✅ get_sprint_issues passed")
        
        # Test link_issues
        print("Testing link_issues...")
        link_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "link_issues",
                "arguments": {
                    "inward_key": "KW-41",
                    "outward_key": "KW-40",
                    "link_type": "Relates"
                }
            }
        }
        
        process.stdin.write(json.dumps(link_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        link_response = json.loads(response)
        
        assert link_response["id"] == 4
        content = link_response["result"]["content"][0]["text"]
        assert "link" in content.lower()
        print("✅ link_issues passed")
        
        # Test get_subtasks
        print("Testing get_subtasks...")
        subtasks_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_subtasks",
                "arguments": {
                    "key": "KW-41"
                }
            }
        }
        
        process.stdin.write(json.dumps(subtasks_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        subtasks_response = json.loads(response)
        
        assert subtasks_response["id"] == 5
        content = subtasks_response["result"]["content"][0]["text"]
        assert "subtask" in content.lower() or "parent" in content.lower()
        print("✅ get_subtasks passed")
        
        print("🎉 Priority 1 tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_priority1_tools_mcp())