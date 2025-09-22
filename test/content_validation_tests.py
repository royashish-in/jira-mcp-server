#!/usr/bin/env python3
"""Content validation test suite for JIRA MCP Server - Tests actual data content and structure."""

import json
import subprocess
import sys
import os
import re
from typing import Dict, Any, List, Optional

class ContentValidationTester:
    def __init__(self, use_docker=True):
        self.use_docker = use_docker
        self.test_results = []
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_root, ".env")
        self.docker_cmd = [
            "docker", "run", "-i", "--rm", "--env-file", env_path,
            "royashish/jira-mcp-server:latest"
        ] if use_docker else ["python", "server.py"]
        
    def send_mcp_request(self, method: str, params: Dict[str, Any] = None) -> Dict:
        """Send MCP request and return response."""
        messages = [
            json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}
            }),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": method, "params": params or {}})
        ]
        
        input_data = "\n".join(messages) + "\n"
        
        try:
            original_cwd = os.getcwd()
            if self.use_docker:
                os.chdir(os.path.dirname(os.getcwd()))
            
            process = subprocess.Popen(
                self.docker_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True
            )
            
            stdout, stderr = process.communicate(input=input_data, timeout=30)
            os.chdir(original_cwd)
            
            if stdout:
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            response = json.loads(line)
                            if response.get("id") == 2:
                                return response
                        except json.JSONDecodeError:
                            continue
            
            return {"error": {"code": -1, "message": f"No response. stderr: {stderr}"}}
            
        except Exception as e:
            return {"error": {"code": -3, "message": str(e)}}

    def get_response_text(self, response: Dict) -> Optional[str]:
        """Extract text content from MCP response."""
        if "error" in response:
            return None
        result = response.get("result", {})
        content = result.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "")
        return None

    def validate_json_structure(self, text: str, expected_keys: List[str]) -> bool:
        """Validate JSON response contains expected keys."""
        try:
            data = json.loads(text)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]  # Check first item in array
            return all(key in data for key in expected_keys)
        except:
            return False

    def validate_issue_key_format(self, text: str) -> bool:
        """Validate issue keys follow PROJECT-NUMBER format."""
        issue_keys = re.findall(r'\b[A-Z]+-\d+\b', text)
        return len(issue_keys) > 0

    def validate_project_structure(self, text: str) -> bool:
        """Validate project data structure."""
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for project in data:
                    if not all(key in project for key in ['key', 'name']):
                        return False
                return True
            return 'key' in data and 'name' in data
        except:
            return False

    def test_content_validation(self, tool_name: str, arguments: Dict[str, Any], 
                              validation_func, description: str) -> bool:
        """Test tool and validate content structure."""
        print(f"Testing {tool_name}: {description}")
        
        response = self.send_mcp_request("tools/call", {
            "name": tool_name, "arguments": arguments
        })
        
        text = self.get_response_text(response)
        if not text:
            print(f"  ❌ FAILED: No response text")
            self.test_results.append({"tool": tool_name, "status": "FAILED", "reason": "No response"})
            return False
        
        if "Error:" in text:
            print(f"  ⚠️  ERROR: {text[:100]}...")
            self.test_results.append({"tool": tool_name, "status": "ERROR", "reason": text[:100]})
            return False
        
        if validation_func(text):
            print(f"  ✅ VALID: Content structure validated")
            self.test_results.append({"tool": tool_name, "status": "VALID", "content_length": len(text)})
            return True
        else:
            print(f"  ❌ INVALID: Content validation failed")
            print(f"    Sample: {text[:200]}...")
            self.test_results.append({"tool": tool_name, "status": "INVALID", "sample": text[:200]})
            return False

    def run_content_validation_tests(self):
        """Run content validation tests for key JIRA tools."""
        print("🔍 Starting Content Validation Test Suite")
        print("=" * 60)
        
        # Test 1: User Stories - Validate issue structure
        print("\n📋 Testing User Stories Content")
        self.test_content_validation(
            "get_user_stories", 
            {"project": "KW", "limit": 3},
            lambda text: self.validate_json_structure(text, ['key', 'summary']) and self.validate_issue_key_format(text),
            "User stories should have key and summary fields with valid issue keys"
        )
        
        # Test 2: Projects - Validate project structure
        print("\n🏗️ Testing Projects Content")
        self.test_content_validation(
            "get_projects",
            {},
            self.validate_project_structure,
            "Projects should have key and name fields"
        )
        
        # Test 3: Issue Details - Validate comprehensive issue data
        print("\n🎫 Testing Issue Details Content")
        self.test_content_validation(
            "get_issue",
            {"key": "KW-40"},
            lambda text: self.validate_json_structure(text, ['key', 'fields', 'summary']) and 'KW-40' in text,
            "Issue should contain key, fields, summary and match requested issue key"
        )
        
        # Test 4: Search Results - Validate search functionality
        print("\n🔍 Testing Search Results Content")
        self.test_content_validation(
            "search_issues",
            {"jql": "project = KW", "limit": 5},
            lambda text: self.validate_json_structure(text, ['issues']) or self.validate_issue_key_format(text),
            "Search should return issues array or contain valid issue keys"
        )
        
        # Test 5: Project Stats - Validate statistical data
        print("\n📊 Testing Project Statistics Content")
        self.test_content_validation(
            "get_project_stats",
            {"project": "KW"},
            lambda text: any(keyword in text.lower() for keyword in ['total', 'count', 'issues', 'status']),
            "Project stats should contain statistical information"
        )
        
        # Test 6: Issue Types - Validate issue type structure
        print("\n🏷️ Testing Issue Types Content")
        self.test_content_validation(
            "get_issue_types",
            {"project": "KW"},
            lambda text: self.validate_json_structure(text, ['name']) or 'story' in text.lower() or 'task' in text.lower(),
            "Issue types should contain name field or common issue type names"
        )
        
        # Test 7: Transitions - Validate workflow transitions
        print("\n🔄 Testing Transitions Content")
        self.test_content_validation(
            "get_transitions",
            {"key": "KW-40"},
            lambda text: any(status in text.lower() for status in ['progress', 'done', 'todo', 'review']),
            "Transitions should contain workflow status names"
        )
        
        # Test 8: Comments - Validate comment addition
        print("\n💬 Testing Comment Addition")
        self.test_content_validation(
            "add_comment",
            {"key": "KW-40", "comment": "Content validation test comment"},
            lambda text: 'comment' in text.lower() and ('added' in text.lower() or 'created' in text.lower()),
            "Comment addition should confirm comment was added"
        )
        
        # Test 9: Boards - Validate agile board data
        print("\n🏃 Testing Agile Boards Content")
        self.test_content_validation(
            "get_boards",
            {},
            lambda text: self.validate_json_structure(text, ['name']) or 'board' in text.lower(),
            "Boards should contain name field or board-related content"
        )
        
        # Test 10: Custom Fields - Validate field definitions
        print("\n🔧 Testing Custom Fields Content")
        self.test_content_validation(
            "get_custom_fields",
            {},
            lambda text: 'field' in text.lower() and ('custom' in text.lower() or 'name' in text.lower()),
            "Custom fields should contain field definitions with names"
        )

    def run_data_integrity_tests(self):
        """Run tests that verify data integrity and relationships."""
        print("\n🔗 Data Integrity Tests")
        print("-" * 40)
        
        # Test issue existence before operations
        print("\n🎫 Verifying Issue Exists Before Operations")
        response = self.send_mcp_request("tools/call", {
            "name": "get_issue", "arguments": {"key": "KW-40"}
        })
        
        text = self.get_response_text(response)
        if text and "KW-40" in text and "Error:" not in text:
            print("  ✅ Issue KW-40 exists and accessible")
            
            # Test that issue operations reference the same issue
            print("\n🔄 Testing Issue Operation Consistency")
            transitions_response = self.send_mcp_request("tools/call", {
                "name": "get_transitions", "arguments": {"key": "KW-40"}
            })
            
            transitions_text = self.get_response_text(transitions_response)
            if transitions_text and "Error:" not in transitions_text:
                print("  ✅ Transitions retrieved for same issue")
                self.test_results.append({"tool": "data_integrity", "status": "VALID", "test": "issue_consistency"})
            else:
                print("  ❌ Transitions failed for existing issue")
                self.test_results.append({"tool": "data_integrity", "status": "INVALID", "test": "issue_consistency"})
        else:
            print("  ⚠️  Issue KW-40 not accessible - skipping integrity tests")
            self.test_results.append({"tool": "data_integrity", "status": "SKIPPED", "test": "issue_not_found"})

    def run_response_format_tests(self):
        """Test response format consistency."""
        print("\n📋 Response Format Tests")
        print("-" * 40)
        
        tools_to_test = [
            ("get_projects", {}),
            ("get_user_stories", {"project": "KW", "limit": 2}),
            ("search_issues", {"jql": "project = KW", "limit": 2})
        ]
        
        for tool_name, args in tools_to_test:
            response = self.send_mcp_request("tools/call", {
                "name": tool_name, "arguments": args
            })
            
            text = self.get_response_text(response)
            if text:
                # Check if response is valid JSON
                try:
                    json.loads(text)
                    print(f"  ✅ {tool_name}: Valid JSON format")
                    self.test_results.append({"tool": f"{tool_name}_format", "status": "VALID", "format": "JSON"})
                except json.JSONDecodeError:
                    # Check if it's structured text
                    if any(indicator in text for indicator in [':', '-', '|', '\n']):
                        print(f"  ✅ {tool_name}: Structured text format")
                        self.test_results.append({"tool": f"{tool_name}_format", "status": "VALID", "format": "TEXT"})
                    else:
                        print(f"  ❌ {tool_name}: Unstructured response")
                        self.test_results.append({"tool": f"{tool_name}_format", "status": "INVALID", "format": "UNKNOWN"})

    def print_detailed_summary(self):
        """Print detailed test results summary."""
        print("\n" + "=" * 60)
        print("📊 CONTENT VALIDATION RESULTS")
        print("=" * 60)
        
        valid_count = len([r for r in self.test_results if r["status"] == "VALID"])
        invalid_count = len([r for r in self.test_results if r["status"] == "INVALID"])
        error_count = len([r for r in self.test_results if r["status"] == "ERROR"])
        failed_count = len([r for r in self.test_results if r["status"] == "FAILED"])
        skipped_count = len([r for r in self.test_results if r["status"] == "SKIPPED"])
        total_count = len(self.test_results)
        
        print(f"✅ VALID:    {valid_count}/{total_count} tests")
        print(f"❌ INVALID:  {invalid_count}/{total_count} tests")
        print(f"⚠️  ERROR:    {error_count}/{total_count} tests")
        print(f"💥 FAILED:   {failed_count}/{total_count} tests")
        print(f"⏭️  SKIPPED:  {skipped_count}/{total_count} tests")
        
        if invalid_count > 0:
            print(f"\n❌ INVALID CONTENT STRUCTURE:")
            for result in self.test_results:
                if result["status"] == "INVALID":
                    print(f"  • {result['tool']}: {result.get('sample', 'No sample')[:100]}...")
        
        if error_count > 0:
            print(f"\n⚠️  ERRORS (likely missing data/permissions):")
            for result in self.test_results:
                if result["status"] == "ERROR":
                    print(f"  • {result['tool']}: {result.get('reason', 'Unknown error')}")
        
        validation_rate = (valid_count / total_count) * 100 if total_count > 0 else 0
        print(f"\n🎯 Content Validation Rate: {validation_rate:.1f}%")
        
        if validation_rate >= 80:
            print("🎉 EXCELLENT: Content structure is well-formed!")
        elif validation_rate >= 60:
            print("👍 GOOD: Most content validates correctly")
        elif validation_rate >= 40:
            print("⚠️  FAIR: Some content structure issues")
        else:
            print("❌ POOR: Major content validation failures")

def main():
    """Main test runner."""
    use_docker = "--local" not in sys.argv
    
    print(f"🚀 Running content validation tests {'with Docker' if use_docker else 'locally'}")
    
    tester = ContentValidationTester(use_docker=use_docker)
    
    try:
        tester.run_content_validation_tests()
        tester.run_data_integrity_tests()
        tester.run_response_format_tests()
        tester.print_detailed_summary()
        
        # Exit based on validation rate
        valid_count = len([r for r in tester.test_results if r["status"] == "VALID"])
        total_count = len(tester.test_results)
        validation_rate = (valid_count / total_count) * 100 if total_count > 0 else 0
        
        sys.exit(0 if validation_rate >= 60 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Content validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Content validation crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()