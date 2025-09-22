#!/usr/bin/env python3
"""Comprehensive test suite for JIRA MCP Server - Tests all 46 tools as end users would use them."""

import json
import subprocess
import sys
import time
from typing import Dict, Any, List

class JiraMCPTester:
    def __init__(self, use_docker=True):
        self.use_docker = use_docker
        self.test_results = []
        import os
        # Get absolute path to .env file in project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_root, ".env")
        self.docker_cmd = [
            "docker", "run", "-i", "--rm", "--env-file", env_path,
            "royashish/jira-mcp-server:latest"
        ] if use_docker else ["python", "server.py"]
        
    def send_mcp_request(self, method: str, params: Dict[str, Any] = None, request_id: int = 2) -> Dict:
        """Send MCP request and return response."""
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {}
            })
        ]
        
        input_data = "\n".join(messages) + "\n"
        
        try:
            # Change to parent directory for Docker commands
            import os
            original_cwd = os.getcwd()
            if self.use_docker:
                os.chdir(os.path.dirname(os.getcwd()))
            
            # Use Popen for interactive communication
            process = subprocess.Popen(
                self.docker_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send all messages and close stdin
            stdout, stderr = process.communicate(input=input_data, timeout=30)
            
            # Restore original directory
            os.chdir(original_cwd)
            
            # Create a mock process object for compatibility
            class MockProcess:
                def __init__(self, stdout, stderr):
                    self.stdout = stdout
                    self.stderr = stderr
            
            process = MockProcess(stdout, stderr)
            
            if process.stdout:
                lines = process.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            response = json.loads(line)
                            if response.get("id") == request_id:
                                return response
                        except json.JSONDecodeError:
                            continue
            
            return {"error": {"code": -1, "message": f"No response found. stderr: {process.stderr}"}}
            
        except subprocess.TimeoutExpired:
            return {"error": {"code": -2, "message": "Request timeout"}}
        except Exception as e:
            return {"error": {"code": -3, "message": str(e)}}

    def test_tool(self, tool_name: str, arguments: Dict[str, Any], description: str) -> bool:
        """Test a specific tool and return success status."""
        print(f"Testing {tool_name}: {description}")
        
        response = self.send_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        }, request_id=2)
        
        if "error" in response:
            print(f"  ❌ FAILED: {response['error']['message']}")
            self.test_results.append({"tool": tool_name, "status": "FAILED", "error": response['error']['message']})
            return False
        elif "result" in response:
            content = response["result"].get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")
                if "Error:" in text:
                    print(f"  ⚠️  ERROR: {text[:100]}...")
                    self.test_results.append({"tool": tool_name, "status": "ERROR", "message": text[:200]})
                    return False
                else:
                    print(f"  ✅ SUCCESS: {len(text)} chars returned")
                    self.test_results.append({"tool": tool_name, "status": "SUCCESS", "response_size": len(text)})
                    return True
            else:
                print(f"  ❌ FAILED: Empty response")
                self.test_results.append({"tool": tool_name, "status": "FAILED", "error": "Empty response"})
                return False
        else:
            print(f"  ❌ FAILED: Invalid response format")
            self.test_results.append({"tool": tool_name, "status": "FAILED", "error": "Invalid response format"})
            return False

    def run_comprehensive_tests(self):
        """Run tests for all 46 JIRA tools."""
        print("🧪 Starting Comprehensive JIRA MCP Server Test Suite")
        print("=" * 60)
        
        # Core JIRA Operations (10 tools)
        print("\n📋 Core JIRA Operations")
        self.test_tool("get_user_stories", {"project": "KW", "limit": 3}, "Fetch user stories")
        self.test_tool("get_issue", {"key": "KW-40"}, "Get specific issue")
        self.test_tool("get_projects", {}, "List all projects")
        self.test_tool("search_issues", {"jql": "project = KW", "limit": 5}, "Search with JQL")
        self.test_tool("get_project_stats", {"project": "KW"}, "Get project statistics")
        self.test_tool("get_recent_issues", {"days": 7, "limit": 5}, "Get recent issues")
        self.test_tool("get_issues_by_assignee", {"assignee": "currentUser()", "limit": 5}, "Get issues by assignee")
        self.test_tool("create_issue", {"project": "KW", "summary": "Test issue from MCP", "description": "Created by test suite"}, "Create new issue")
        self.test_tool("update_issue", {"key": "KW-40", "summary": "Updated via MCP test"}, "Update existing issue")
        self.test_tool("advanced_jql_search", {"jql": "project = KW AND status = 'In Progress'", "limit": 3}, "Advanced JQL search")
        
        # Workflow Management (6 tools)
        print("\n🔄 Workflow Management")
        self.test_tool("get_transitions", {"key": "KW-40"}, "Get available transitions")
        self.test_tool("transition_issue", {"key": "KW-40", "transition": "In Progress"}, "Transition issue status")
        self.test_tool("add_comment", {"key": "KW-40", "comment": "Test comment from MCP suite"}, "Add comment to issue")
        self.test_tool("assign_issue", {"key": "KW-40", "assignee": "currentUser()"}, "Assign issue to user")
        self.test_tool("add_worklog", {"key": "KW-40", "time_spent": "1h", "comment": "Test work log"}, "Add work log")
        self.test_tool("bulk_transition_issues", {"keys": ["KW-40"], "transition": "In Progress"}, "Bulk transition issues")
        
        # File & Attachment Management (3 tools)
        print("\n📎 File & Attachment Management")
        self.test_tool("list_attachments", {"key": "KW-40"}, "List issue attachments")
        self.test_tool("upload_attachment", {"key": "KW-40", "file_path": "/tmp/test.txt"}, "Upload attachment (expected to fail)")
        self.test_tool("download_attachment", {"attachment_url": "https://example.com/file", "save_path": "/tmp/download"}, "Download attachment (expected to fail)")
        
        # Project & User Management (5 tools)
        print("\n👥 Project & User Management")
        self.test_tool("get_issue_types", {"project": "KW"}, "Get project issue types")
        self.test_tool("get_project_components", {"project": "KW"}, "Get project components")
        self.test_tool("get_project_versions", {"project": "KW"}, "Get project versions")
        self.test_tool("get_custom_fields", {}, "Get custom fields")
        self.test_tool("get_users", {"project": "KW"}, "Get project users")
        
        # Agile & Sprint Management (4 tools)
        print("\n🏃 Agile & Sprint Management")
        self.test_tool("get_boards", {}, "Get agile boards")
        self.test_tool("get_sprints", {"board_id": "1"}, "Get board sprints")
        self.test_tool("get_sprint_issues", {"sprint_id": "1"}, "Get sprint issues")
        self.test_tool("add_to_sprint", {"sprint_id": "1", "keys": ["KW-40"]}, "Add issues to sprint")
        
        # Issue Relationships & Hierarchy (4 tools)
        print("\n🔗 Issue Relationships & Hierarchy")
        self.test_tool("get_subtasks", {"key": "KW-40"}, "Get issue subtasks")
        self.test_tool("create_subtask", {"parent_key": "KW-40", "summary": "Test subtask from MCP"}, "Create subtask")
        self.test_tool("link_issues", {"inward_key": "KW-40", "outward_key": "KW-39", "link_type": "Relates"}, "Link issues")
        self.test_tool("get_issue_links", {"key": "KW-40"}, "Get issue links")
        
        # Batch Operations (2 tools)
        print("\n📦 Batch Operations")
        self.test_tool("bulk_update_issues", {"keys": ["KW-40"], "updates": {"priority": "High"}}, "Bulk update issues")
        self.test_tool("clone_issue", {"key": "KW-40", "summary": "Cloned issue from MCP test"}, "Clone issue")
        
        # Webhooks & Notifications (3 tools)
        print("\n🔔 Webhooks & Notifications")
        self.test_tool("list_webhooks", {}, "List webhooks")
        self.test_tool("add_watcher", {"key": "KW-40", "username": "currentUser()"}, "Add issue watcher")
        self.test_tool("get_watchers", {"key": "KW-40"}, "Get issue watchers")
        
        # Reporting & Analytics (3 tools)
        print("\n📊 Reporting & Analytics")
        self.test_tool("get_time_tracking_report", {"project": "KW"}, "Get time tracking report")
        self.test_tool("get_project_roles", {"project": "KW"}, "Get project roles")
        self.test_tool("export_issues", {"jql": "project = KW", "format": "json"}, "Export issues")
        
        # Advanced Admin & Edge Cases (5 tools)
        print("\n⚙️ Advanced Admin & Edge Cases")
        self.test_tool("create_webhook", {"name": "Test webhook", "url": "https://example.com/webhook", "events": ["issue_created"]}, "Create webhook")
        self.test_tool("create_version", {"project": "KW", "name": "Test Version 1.0"}, "Create project version")
        self.test_tool("get_user_permissions", {"project": "KW", "username": "currentUser()"}, "Get user permissions")
        self.test_tool("get_workflows", {}, "Get workflows")
        self.test_tool("release_version", {"version_id": "1"}, "Release version")
        self.test_tool("get_burndown_data", {"sprint_id": "1"}, "Get burndown data")

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        success_count = len([r for r in self.test_results if r["status"] == "SUCCESS"])
        error_count = len([r for r in self.test_results if r["status"] == "ERROR"])
        failed_count = len([r for r in self.test_results if r["status"] == "FAILED"])
        total_count = len(self.test_results)
        
        print(f"✅ SUCCESS: {success_count}/{total_count} tools")
        print(f"⚠️  ERROR:   {error_count}/{total_count} tools")
        print(f"❌ FAILED:  {failed_count}/{total_count} tools")
        
        if error_count > 0:
            print(f"\n⚠️  ERRORS (likely due to missing data/permissions):")
            for result in self.test_results:
                if result["status"] == "ERROR":
                    print(f"  • {result['tool']}: {result['message'][:100]}...")
        
        if failed_count > 0:
            print(f"\n❌ FAILURES (server/connection issues):")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"  • {result['tool']}: {result['error']}")
        
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: Server is working well!")
        elif success_rate >= 60:
            print("👍 GOOD: Most tools are functional")
        elif success_rate >= 40:
            print("⚠️  FAIR: Some issues need attention")
        else:
            print("❌ POOR: Major issues detected")

def main():
    """Main test runner."""
    use_docker = "--local" not in sys.argv
    
    print(f"🚀 Running tests {'with Docker' if use_docker else 'locally'}")
    
    tester = JiraMCPTester(use_docker=use_docker)
    
    try:
        tester.run_comprehensive_tests()
        tester.print_summary()
        
        # Exit with appropriate code
        success_count = len([r for r in tester.test_results if r["status"] == "SUCCESS"])
        total_count = len(tester.test_results)
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        sys.exit(0 if success_rate >= 60 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()