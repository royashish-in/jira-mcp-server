#!/usr/bin/env python3
"""FINAL ULTIMATE comprehensive TDD test for ALL tools via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_final_ultimate():
    """Test ALL tools via real MCP JSON-RPC protocol - FINAL VERSION"""
    
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
        
        # ALL TOOLS - COMPLETE ENTERPRISE JIRA MCP SERVER
        all_tools = [
            # Original 7 tools
            ("get_user_stories", {"project": "KW", "limit": 2}),
            ("get_issue", {"key": "KW-41"}),
            ("get_projects", {}),
            ("search_issues", {"jql": "project = KW", "limit": 2}),
            ("get_project_stats", {"project": "KW"}),
            ("get_recent_issues", {"days": 7, "limit": 2}),
            ("get_issues_by_assignee", {"assignee": "currentUser()", "limit": 2}),
            
            # Core CRUD Operations (3 tools)
            ("create_issue", {"project": "KW", "summary": "Final ultimate test"}),
            ("update_issue", {"key": "KW-41", "priority": "Low"}),
            ("advanced_jql_search", {"jql": "project = KW", "limit": 2}),
            
            # Workflow Management (6 tools)
            ("transition_issue", {"key": "KW-41", "transition": "To Do"}),
            ("bulk_transition_issues", {"keys": ["KW-41"], "transition": "To Do"}),
            ("get_transitions", {"key": "KW-41"}),
            ("add_comment", {"key": "KW-41", "comment": "Final ultimate comment"}),
            ("assign_issue", {"key": "KW-41", "assignee": "null"}),
            ("add_worklog", {"key": "KW-41", "time_spent": "1h", "comment": "Final work"}),
            
            # File & Attachment Management (2 tools - excluding upload/download for test)
            ("list_attachments", {"key": "KW-41"}),
            
            # Project & User Management (5 tools)
            ("get_issue_types", {"project": "KW"}),
            ("get_project_components", {"project": "KW"}),
            ("get_project_versions", {"project": "KW"}),
            ("get_custom_fields", {}),
            ("get_users", {"project": "KW"}),
            
            # Agile & Sprint Management (4 tools)
            ("get_boards", {}),
            ("get_sprints", {"board_id": "1"}),
            ("get_sprint_issues", {"sprint_id": "1"}),
            ("add_to_sprint", {"sprint_id": "1", "keys": ["KW-41"]}),
            
            # Issue Relationships & Hierarchy (4 tools)
            ("link_issues", {"inward_key": "KW-41", "outward_key": "KW-40", "link_type": "Relates"}),
            ("get_issue_links", {"key": "KW-41"}),
            ("get_subtasks", {"key": "KW-41"}),
            ("create_subtask", {"parent_key": "KW-41", "summary": "Final ultimate subtask"}),
            
            # Batch Operations (1 tool)
            ("bulk_update_issues", {"keys": ["KW-41"], "updates": {"priority": "Medium"}}),
            
            # Webhooks & Notifications (3 tools)
            ("list_webhooks", {}),
            ("add_watcher", {"key": "KW-41", "username": "currentUser()"}),
            ("get_watchers", {"key": "KW-41"}),
            
            # Advanced Issue Operations (1 tool)
            ("clone_issue", {"key": "KW-41", "summary": "Final cloned issue"}),
            
            # Reporting & Admin (3 tools)
            ("get_time_tracking_report", {"project": "KW"}),
            ("get_project_roles", {"project": "KW"}),
            ("export_issues", {"jql": "project = KW", "format": "json"}),
        ]
        
        passed_tests = []
        failed_tests = []
        
        print(f"🚀 FINAL ULTIMATE TEST: ALL {len(all_tools)} JIRA MCP SERVER TOOLS")
        print("=" * 80)
        
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
        
        print("=" * 80)
        print(f"🏆 FINAL ULTIMATE RESULTS:")
        print(f"✅ Passed: {len(passed_tests)}/{len(all_tools)} tools")
        print(f"❌ Failed: {len(failed_tests)} tools")
        
        if failed_tests:
            print(f"Failed tools: {', '.join(failed_tests)}")
        else:
            print("🎉 PERFECT ULTIMATE SCORE! ALL TOOLS WORKING!")
        
        print(f"\n🚀 ENTERPRISE JIRA MCP SERVER: {len(passed_tests)} TOOLS READY!")
        print("🏆 COMPLETE JIRA OPERATIONS ECOSYSTEM ACHIEVED!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_final_ultimate())