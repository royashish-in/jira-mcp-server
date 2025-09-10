#!/usr/bin/env python3
"""Final comprehensive TDD test for ALL implemented features via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_final_comprehensive():
    """Test ALL features via real MCP JSON-RPC protocol"""
    
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
        
        # Test ALL tools (original + new implementations)
        all_tools = [
            # Original tools
            ("get_user_stories", {"project": "KW", "limit": 2}),
            ("get_issue", {"key": "KW-41"}),
            ("get_projects", {}),
            ("search_issues", {"jql": "project = KW", "limit": 2}),
            ("get_project_stats", {"project": "KW"}),
            ("get_recent_issues", {"days": 7, "limit": 2}),
            ("get_issues_by_assignee", {"assignee": "currentUser()", "limit": 2}),
            
            # TDD implemented tools - Core CRUD
            ("create_issue", {"project": "KW", "summary": "Final comprehensive test"}),
            ("update_issue", {"key": "KW-41", "priority": "Low"}),
            ("advanced_jql_search", {"jql": "project = KW", "limit": 2}),
            
            # TDD implemented tools - Workflow
            ("get_transitions", {"key": "KW-41"}),
            ("add_comment", {"key": "KW-41", "comment": "Final test comment"}),
            
            # TDD implemented tools - Attachments
            ("list_attachments", {"key": "KW-41"}),
            
            # TDD implemented tools - Project Management
            ("get_issue_types", {"project": "KW"}),
            ("bulk_update_issues", {"keys": ["KW-41"], "updates": {"priority": "Medium"}}),
            
            # TDD implemented tools - Advanced Workflow
            ("assign_issue", {"key": "KW-41", "assignee": "null"}),
            ("get_project_components", {"project": "KW"}),
            ("get_project_versions", {"project": "KW"}),
            
            # TDD implemented tools - Custom Fields & Sprints
            ("get_custom_fields", {}),
        ]
        
        passed_tests = []
        failed_tests = []
        
        for tool_name, arguments in all_tools:
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
            
            try:
                assert test_response["id"] == test_id
                assert "result" in test_response
                passed_tests.append(tool_name)
                print(f"✅ {tool_name} passed")
            except AssertionError:
                failed_tests.append(tool_name)
                print(f"❌ {tool_name} failed")
            
            test_id += 1
        
        print(f"\n🎉 FINAL RESULTS:")
        print(f"✅ Passed: {len(passed_tests)}/{len(all_tools)} tools")
        print(f"❌ Failed: {len(failed_tests)} tools")
        
        if failed_tests:
            print(f"Failed tools: {', '.join(failed_tests)}")
        
        print(f"\n🚀 JIRA MCP Server now supports {len(passed_tests)} tools!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_final_comprehensive())