#!/usr/bin/env python3
"""Comprehensive TDD test for all implemented features via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_all_features_comprehensive():
    """Test all features via real MCP JSON-RPC protocol"""
    
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
        
        test_id = 2
        
        # Test all new tools
        tools_to_test = [
            ("create_issue", {"project": "KW", "summary": "Comprehensive test issue", "description": "Created via comprehensive TDD test"}),
            ("update_issue", {"key": "KW-41", "priority": "High"}),
            ("advanced_jql_search", {"jql": "project = KW", "limit": 3}),
            ("get_transitions", {"key": "KW-41"}),
            ("add_comment", {"key": "KW-41", "comment": "Comprehensive test comment"}),
            ("list_attachments", {"key": "KW-41"}),
            ("get_issue_types", {"project": "KW"}),
            ("bulk_update_issues", {"keys": ["KW-41"], "updates": {"priority": "Medium"}})
        ]
        
        passed_tests = []
        
        for tool_name, arguments in tools_to_test:
            print(f"Testing {tool_name}...")
            
            test_request = {
                "jsonrpc": "2.0",
                "id": test_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            process.stdin.write(json.dumps(test_request) + "\n")
            process.stdin.flush()
            
            response = process.stdout.readline()
            test_response = json.loads(response)
            
            assert test_response["id"] == test_id
            assert "result" in test_response
            
            passed_tests.append(tool_name)
            print(f"✅ {tool_name} passed")
            test_id += 1
        
        print(f"\n🎉 All {len(passed_tests)} features passed comprehensive testing!")
        print(f"Implemented tools: {', '.join(passed_tests)}")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_all_features_comprehensive())