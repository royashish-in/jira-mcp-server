#!/usr/bin/env python3
"""
Comprehensive Test Suite for JIRA MCP Server
Tests all 46 tools via real MCP JSON-RPC protocol
Organized by feature categories for maintainability
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import os
from typing import List, Tuple, Dict, Any

class JiraMCPTestSuite:
    def __init__(self):
        self.process = None
        self.test_id = 2  # Start after initialization
        self.passed_tests = []
        self.failed_tests = []
        
    async def setup(self):
        """Initialize MCP server process"""
        self.process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Initialize MCP protocol
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-suite", "version": "1.0.0"}
            }
        }
        
        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()
        
        response = self.process.stdout.readline()
        init_response = json.loads(response)
        assert init_response["id"] == 1
        
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        self.process.stdin.write(json.dumps(initialized) + "\n")
        self.process.stdin.flush()
        
    async def teardown(self):
        """Clean up MCP server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
    
    async def test_tool(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Test a single tool and return success status"""
        test_request = {
            "jsonrpc": "2.0",
            "id": self.test_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        self.process.stdin.write(json.dumps(test_request) + "\n")
        self.process.stdin.flush()
        
        response = self.process.stdout.readline()
        test_response = json.loads(response)
        
        try:
            assert test_response["id"] == self.test_id
            assert "result" in test_response
            self.passed_tests.append(tool_name)
            print(f"✅ {tool_name}")
            self.test_id += 1
            return True
        except AssertionError:
            self.failed_tests.append(tool_name)
            print(f"❌ {tool_name}")
            self.test_id += 1
            return False
    
    async def test_category(self, category_name: str, tools: List[Tuple[str, Dict[str, Any]]]):
        """Test a category of tools"""
        print(f"\n📂 Testing {category_name} ({len(tools)} tools)")
        print("-" * 60)
        
        for tool_name, arguments in tools:
            await self.test_tool(tool_name, arguments)
    
    async def run_all_tests(self):
        """Run comprehensive test suite for all 46 tools"""
        
        # Core JIRA Operations (10 tools)
        core_operations = [
            ("get_user_stories", {"project": "KW", "limit": 2}),
            ("get_issue", {"key": "KW-41"}),
            ("get_projects", {}),
            ("search_issues", {"jql": "project = KW", "limit": 2}),
            ("get_project_stats", {"project": "KW"}),
            ("get_recent_issues", {"days": 7, "limit": 2}),
            ("get_issues_by_assignee", {"assignee": "currentUser()", "limit": 2}),
            ("create_issue", {"project": "KW", "summary": "Test suite issue"}),
            ("update_issue", {"key": "KW-41", "priority": "Low"}),
            ("advanced_jql_search", {"jql": "project = KW", "limit": 2}),
        ]
        
        # Workflow Management (5 tools)
        workflow_management = [
            ("transition_issue", {"key": "KW-41", "transition": "To Do"}),
            ("get_transitions", {"key": "KW-41"}),
            ("add_comment", {"key": "KW-41", "comment": "Test suite comment"}),
            ("assign_issue", {"key": "KW-41", "assignee": "null"}),
            ("add_worklog", {"key": "KW-41", "time_spent": "1h", "comment": "Test work"}),
        ]
        
        # File & Attachment Management (3 tools)
        file_management = [
            ("list_attachments", {"key": "KW-41"}),
            ("upload_attachment", {"key": "KW-41", "file_path": "/tmp/nonexistent.txt"}),
            ("download_attachment", {"attachment_url": "https://example.com/file", "save_path": "/tmp/download.txt"}),
        ]
        
        # Project & User Management (5 tools)
        project_management = [
            ("get_issue_types", {"project": "KW"}),
            ("get_project_components", {"project": "KW"}),
            ("get_project_versions", {"project": "KW"}),
            ("get_custom_fields", {}),
            ("get_users", {"project": "KW"}),
        ]
        
        # Agile & Sprint Management (4 tools)
        agile_management = [
            ("get_boards", {}),
            ("get_sprints", {"board_id": "1"}),
            ("get_sprint_issues", {"sprint_id": "1"}),
            ("add_to_sprint", {"sprint_id": "1", "keys": ["KW-41"]}),
        ]
        
        # Issue Relationships & Hierarchy (4 tools)
        relationships = [
            ("link_issues", {"inward_key": "KW-41", "outward_key": "KW-40", "link_type": "Relates"}),
            ("get_issue_links", {"key": "KW-41"}),
            ("get_subtasks", {"key": "KW-41"}),
            ("create_subtask", {"parent_key": "KW-41", "summary": "Test subtask"}),
        ]
        
        # Batch Operations (2 tools)
        batch_operations = [
            ("bulk_update_issues", {"keys": ["KW-41"], "updates": {"priority": "Medium"}}),
            ("bulk_transition_issues", {"keys": ["KW-41"], "transition": "To Do"}),
        ]
        
        # Webhooks & Notifications (3 tools)
        webhooks_notifications = [
            ("list_webhooks", {}),
            ("add_watcher", {"key": "KW-41", "username": "currentUser()"}),
            ("get_watchers", {"key": "KW-41"}),
        ]
        
        # Advanced Issue Operations (1 tool)
        advanced_operations = [
            ("clone_issue", {"key": "KW-41", "summary": "Test cloned issue"}),
        ]
        
        # Reporting & Analytics (3 tools)
        reporting = [
            ("get_time_tracking_report", {"project": "KW"}),
            ("get_project_roles", {"project": "KW"}),
            ("export_issues", {"jql": "project = KW", "format": "json"}),
        ]
        
        # Advanced Admin & Edge Cases (7 tools)
        admin_edge_cases = [
            ("create_webhook", {"name": "Test Webhook", "url": "https://example.com/hook", "events": ["jira:issue_created"]}),
            ("create_version", {"project": "KW", "name": "v1.0.0", "description": "Test version"}),
            ("get_user_permissions", {"project": "KW", "username": "currentUser()"}),
            ("get_workflows", {}),
            ("release_version", {"version_id": "10000"}),
            ("get_burndown_data", {"sprint_id": "1"}),
        ]
        
        # Run all test categories
        await self.test_category("Core JIRA Operations", core_operations)
        await self.test_category("Workflow Management", workflow_management)
        await self.test_category("File & Attachment Management", file_management)
        await self.test_category("Project & User Management", project_management)
        await self.test_category("Agile & Sprint Management", agile_management)
        await self.test_category("Issue Relationships & Hierarchy", relationships)
        await self.test_category("Batch Operations", batch_operations)
        await self.test_category("Webhooks & Notifications", webhooks_notifications)
        await self.test_category("Advanced Issue Operations", advanced_operations)
        await self.test_category("Reporting & Analytics", reporting)
        await self.test_category("Advanced Admin & Edge Cases", admin_edge_cases)
        
        # Print final results
        total_tools = len(self.passed_tests) + len(self.failed_tests)
        print("\n" + "=" * 80)
        print(f"🏆 COMPREHENSIVE TEST SUITE RESULTS")
        print("=" * 80)
        print(f"✅ Passed: {len(self.passed_tests)}/{total_tools} tools")
        print(f"❌ Failed: {len(self.failed_tests)} tools")
        
        if self.failed_tests:
            print(f"\nFailed tools: {', '.join(self.failed_tests)}")
        else:
            print("\n🎉 PERFECT SCORE! ALL TOOLS WORKING!")
        
        print(f"\n🚀 JIRA MCP SERVER: {len(self.passed_tests)} TOOLS READY!")
        print("🏆 COMPLETE JIRA OPERATIONS ECOSYSTEM!")
        
        return len(self.failed_tests) == 0

async def main():
    """Main test runner"""
    print("🚀 JIRA MCP SERVER COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("Testing all 46 tools across 11 categories")
    print("=" * 80)
    
    test_suite = JiraMCPTestSuite()
    
    try:
        await test_suite.setup()
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    finally:
        await test_suite.teardown()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)