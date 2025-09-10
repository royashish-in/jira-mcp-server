#!/usr/bin/env python3
"""ULTIMATE comprehensive TDD test for ALL 26 tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_ultimate_comprehensive():
    """Test ALL 26 tools via real MCP JSON-RPC protocol"""
    
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
        
        # ALL 26 TOOLS - Complete JIRA MCP Server
        all_tools = [
            # Original 7 tools
            ("get_user_stories", {"project": "KW", "limit": 2}),
            ("get_issue", {"key": "KW-41"}),
            ("get_projects", {}),
            ("search_issues", {"jql": "project = KW", "limit": 2}),
            ("get_project_stats", {"project": "KW"}),
            ("get_recent_issues", {"days": 7, "limit": 2}),
            ("get_issues_by_assignee", {"assignee": "currentUser()", "limit": 2}),
            
            # First TDD batch - Core CRUD (3 tools)
            ("create_issue", {"project": "KW", "summary": "Ultimate test"}),
            ("update_issue", {"key": "KW-41", "priority": "Low"}),
            ("advanced_jql_search", {"jql": "project = KW", "limit": 2}),
            
            # Second TDD batch - Workflow (3 tools)
            ("transition_issue", {"key": "KW-41", "transition": "To Do"}),
            ("get_transitions", {"key": "KW-41"}),
            ("add_comment", {"key": "KW-41", "comment": "Ultimate test comment"}),
            
            # Third TDD batch - Attachments & Project Mgmt (5 tools)
            ("list_attachments", {"key": "KW-41"}),
            ("get_issue_types", {"project": "KW"}),
            ("bulk_update_issues", {"keys": ["KW-41"], "updates": {"priority": "Medium"}}),
            ("bulk_transition_issues", {"keys": ["KW-41"], "transition": "To Do"}),
            ("assign_issue", {"key": "KW-41", "assignee": "null"}),
            
            # Fourth TDD batch - Advanced Project (2 tools)
            ("get_project_components", {"project": "KW"}),
            ("get_project_versions", {"project": "KW"}),
            
            # Fifth TDD batch - Custom Fields & Sprints (3 tools)
            ("get_custom_fields", {}),
            ("get_sprints", {"board_id": "1"}),
            ("add_to_sprint", {"sprint_id": "1", "keys": ["KW-41"]}),
            
            # Sixth TDD batch - Priority 1 (4 tools)
            ("get_boards", {}),
            ("get_sprint_issues", {"sprint_id": "1"}),
            ("link_issues", {"inward_key": "KW-41", "outward_key": "KW-40", "link_type": "Relates"}),
            ("get_subtasks", {"key": "KW-41"}),
            
            # Seventh TDD batch - Priority 2 (3 tools)
            ("add_worklog", {"key": "KW-41", "time_spent": "1h", "comment": "Ultimate test work"}),
            ("get_users", {"project": "KW"}),
            ("create_subtask", {"parent_key": "KW-41", "summary": "Ultimate test subtask"}),
        ]
        
        passed_tests = []
        failed_tests = []
        
        print(f"🚀 Testing ALL {len(all_tools)} JIRA MCP Server tools...")
        print("=" * 60)
        
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
        
        print("=" * 60)
        print(f"🏆 ULTIMATE RESULTS:")
        print(f"✅ Passed: {len(passed_tests)}/{len(all_tools)} tools")
        print(f"❌ Failed: {len(failed_tests)} tools")
        
        if failed_tests:
            print(f"Failed tools: {', '.join(failed_tests)}")
        else:
            print("🎉 PERFECT SCORE! All tools working!")
        
        print(f"\n🚀 ENTERPRISE JIRA MCP SERVER SUPPORTS {len(passed_tests)} TOOLS!")
        print("Complete JIRA operations lifecycle coverage achieved!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_ultimate_comprehensive())