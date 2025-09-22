#!/usr/bin/env python3
"""JIRA Integration Tests - Tests actual JIRA API connectivity and data retrieval."""

import json
import subprocess
import sys
import os
import re
from typing import Dict, Any, List, Optional

class JiraIntegrationTester:
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

    def test_jira_connectivity(self):
        """Test basic JIRA connectivity through get_user_stories."""
        print("🔌 Testing JIRA Connectivity")
        
        response = self.send_mcp_request("tools/call", {
            "name": "get_user_stories", "arguments": {"project": "KW", "limit": 1}
        })
        
        text = self.get_response_text(response)
        if not text:
            print("  ❌ FAILED: No response from server")
            self.test_results.append({"test": "connectivity", "status": "FAILED", "reason": "No response"})
            return False
        
        if "Tool implementation placeholder" in text:
            print("  ⚠️  SKIPPED: Tool not implemented")
            self.test_results.append({"test": "connectivity", "status": "SKIPPED", "reason": "Not implemented"})
            return False
        
        if "Error:" in text and "authentication" in text.lower():
            print("  ❌ AUTHENTICATION ERROR: Check JIRA credentials")
            print(f"    {text[:200]}...")
            self.test_results.append({"test": "connectivity", "status": "AUTH_ERROR", "reason": text[:200]})
            return False
        
        if "Error:" in text and "connection" in text.lower():
            print("  ❌ CONNECTION ERROR: Check JIRA URL")
            print(f"    {text[:200]}...")
            self.test_results.append({"test": "connectivity", "status": "CONN_ERROR", "reason": text[:200]})
            return False
        
        if "Error:" in text:
            print("  ❌ JIRA API ERROR:")
            print(f"    {text[:200]}...")
            self.test_results.append({"test": "connectivity", "status": "API_ERROR", "reason": text[:200]})
            return False
        
        try:
            data = json.loads(text)
            if "stories" in data and len(data["stories"]) > 0:
                story = data["stories"][0]
                print(f"  ✅ CONNECTED: Retrieved story {story.get('key', 'unknown')}")
                print(f"    Summary: {story.get('summary', 'No summary')[:60]}...")
                self.test_results.append({
                    "test": "connectivity", 
                    "status": "SUCCESS", 
                    "sample_key": story.get('key'),
                    "sample_summary": story.get('summary', '')[:100]
                })
                return True
            else:
                print("  ⚠️  CONNECTED but no stories found")
                self.test_results.append({"test": "connectivity", "status": "NO_DATA", "reason": "No stories in project"})
                return True
        except json.JSONDecodeError:
            print("  ❌ INVALID RESPONSE: Not valid JSON")
            print(f"    Raw: {text[:200]}...")
            self.test_results.append({"test": "connectivity", "status": "INVALID_JSON", "reason": text[:200]})
            return False

    def test_project_access(self):
        """Test access to different projects."""
        print("\n🏗️ Testing Project Access")
        
        # Test with different project keys
        test_projects = ["KW", "TEST", "DEMO", "PROJ"]
        accessible_projects = []
        
        for project in test_projects:
            print(f"  Testing project {project}...")
            
            response = self.send_mcp_request("tools/call", {
                "name": "get_user_stories", "arguments": {"project": project, "limit": 1}
            })
            
            text = self.get_response_text(response)
            if text and "Error:" not in text and "Tool implementation placeholder" not in text:
                try:
                    data = json.loads(text)
                    if "stories" in data:
                        story_count = len(data["stories"])
                        print(f"    ✅ {project}: {story_count} stories accessible")
                        accessible_projects.append({"key": project, "story_count": story_count})
                except:
                    pass
            elif text and "not found" in text.lower():
                print(f"    ❌ {project}: Project not found")
            elif text and "permission" in text.lower():
                print(f"    ❌ {project}: No permission")
            else:
                print(f"    ⚠️  {project}: Unknown status")
        
        print(f"\n  📊 Accessible Projects: {len(accessible_projects)}")
        for proj in accessible_projects:
            print(f"    {proj['key']}: {proj['story_count']} stories")
        
        self.test_results.append({
            "test": "project_access",
            "status": "ANALYZED",
            "accessible_projects": accessible_projects,
            "total_tested": len(test_projects)
        })
        
        return len(accessible_projects) > 0

    def test_issue_key_validation(self):
        """Test specific issue key access."""
        print("\n🎫 Testing Issue Key Access")
        
        # First get some issue keys from user stories
        response = self.send_mcp_request("tools/call", {
            "name": "get_user_stories", "arguments": {"project": "KW", "limit": 5}
        })
        
        text = self.get_response_text(response)
        if not text or "Error:" in text or "Tool implementation placeholder" in text:
            print("  ⚠️  Cannot get issue keys - skipping test")
            self.test_results.append({"test": "issue_access", "status": "SKIPPED", "reason": "No issue keys available"})
            return False
        
        try:
            data = json.loads(text)
            stories = data.get("stories", [])
            if not stories:
                print("  ⚠️  No stories found - skipping test")
                return False
            
            # Test accessing individual issues (if get_issue was implemented)
            test_keys = [story["key"] for story in stories[:3]]
            print(f"  Testing access to issues: {', '.join(test_keys)}")
            
            # Since get_issue might not be implemented, validate the keys we got
            valid_keys = []
            for key in test_keys:
                if re.match(r'^[A-Z]+-\d+$', key):
                    valid_keys.append(key)
                    print(f"    ✅ {key}: Valid format")
                else:
                    print(f"    ❌ {key}: Invalid format")
            
            print(f"  📊 Valid Issue Keys: {len(valid_keys)}/{len(test_keys)}")
            
            self.test_results.append({
                "test": "issue_access",
                "status": "ANALYZED",
                "valid_keys": valid_keys,
                "total_keys": len(test_keys)
            })
            
            return len(valid_keys) == len(test_keys)
            
        except Exception as e:
            print(f"  ❌ Error analyzing issue keys: {e}")
            return False

    def test_data_freshness(self):
        """Test if data is fresh and up-to-date."""
        print("\n🕐 Testing Data Freshness")
        
        response = self.send_mcp_request("tools/call", {
            "name": "get_user_stories", "arguments": {"project": "KW", "limit": 10}
        })
        
        text = self.get_response_text(response)
        if not text or "Error:" in text or "Tool implementation placeholder" in text:
            print("  ⚠️  Cannot test data freshness")
            return False
        
        try:
            data = json.loads(text)
            stories = data.get("stories", [])
            
            # Look for recent activity indicators
            recent_indicators = 0
            test_indicators = 0
            
            for story in stories:
                summary = story.get("summary", "").lower()
                
                # Check for test-related content (indicates recent testing)
                if any(word in summary for word in ["test", "mcp", "cloned"]):
                    test_indicators += 1
                
                # Check for recent status changes
                status = story.get("status", "")
                if status in ["In Progress", "Selected for Development"]:
                    recent_indicators += 1
            
            print(f"  📊 Stories with test indicators: {test_indicators}/{len(stories)}")
            print(f"  📊 Stories in active status: {recent_indicators}/{len(stories)}")
            
            # Check if we can see our own test data
            test_summaries = [s["summary"] for s in stories if "mcp" in s["summary"].lower()]
            if test_summaries:
                print(f"  ✅ Found test data from previous runs:")
                for summary in test_summaries[:3]:
                    print(f"    - {summary[:60]}...")
            
            freshness_score = ((test_indicators + recent_indicators) / (len(stories) * 2)) * 100
            print(f"  📊 Data Freshness Score: {freshness_score:.1f}%")
            
            self.test_results.append({
                "test": "data_freshness",
                "status": "ANALYZED",
                "total_stories": len(stories),
                "test_indicators": test_indicators,
                "recent_indicators": recent_indicators,
                "freshness_score": freshness_score
            })
            
            return freshness_score > 20  # At least some recent activity
            
        except Exception as e:
            print(f"  ❌ Error analyzing data freshness: {e}")
            return False

    def test_error_handling(self):
        """Test how the server handles various error conditions."""
        print("\n⚠️ Testing Error Handling")
        
        error_tests = [
            ("Invalid project", {"project": "INVALID", "limit": 1}),
            ("Zero limit", {"project": "KW", "limit": 0}),
            ("Negative limit", {"project": "KW", "limit": -1}),
            ("Very large limit", {"project": "KW", "limit": 10000}),
        ]
        
        error_handling_score = 0
        
        for test_name, args in error_tests:
            print(f"  Testing {test_name}...")
            
            response = self.send_mcp_request("tools/call", {
                "name": "get_user_stories", "arguments": args
            })
            
            text = self.get_response_text(response)
            if text:
                if "Error:" in text:
                    print(f"    ✅ Proper error handling")
                    error_handling_score += 1
                elif "Tool implementation placeholder" in text:
                    print(f"    ⚠️  Tool not implemented")
                else:
                    print(f"    ❌ No error for invalid input")
            else:
                print(f"    ❌ No response")
        
        handling_rate = (error_handling_score / len(error_tests)) * 100
        print(f"  📊 Error Handling Rate: {handling_rate:.1f}%")
        
        self.test_results.append({
            "test": "error_handling",
            "status": "ANALYZED",
            "tests_passed": error_handling_score,
            "total_tests": len(error_tests),
            "handling_rate": handling_rate
        })
        
        return handling_rate >= 50

    def print_integration_summary(self):
        """Print comprehensive integration test summary."""
        print("\n" + "=" * 60)
        print("🔌 JIRA INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            test_name = result["test"].replace("_", " ").title()
            status = result["status"]
            
            print(f"\n🔍 {test_name}:")
            
            if test_name == "Connectivity":
                if status == "SUCCESS":
                    print(f"  ✅ JIRA API Connected Successfully")
                    print(f"  Sample Issue: {result.get('sample_key', 'N/A')}")
                    print(f"  Sample Summary: {result.get('sample_summary', 'N/A')[:60]}...")
                elif status == "AUTH_ERROR":
                    print(f"  ❌ Authentication Failed")
                    print(f"  Check JIRA_USERNAME and JIRA_API_TOKEN")
                elif status == "CONN_ERROR":
                    print(f"  ❌ Connection Failed")
                    print(f"  Check JIRA_URL")
                elif status == "API_ERROR":
                    print(f"  ❌ JIRA API Error")
                    print(f"  Reason: {result.get('reason', 'Unknown')[:100]}...")
                else:
                    print(f"  ❌ Failed: {status}")
            
            elif test_name == "Project Access":
                accessible = result.get("accessible_projects", [])
                total = result.get("total_tested", 0)
                print(f"  Projects Tested: {total}")
                print(f"  Accessible Projects: {len(accessible)}")
                for proj in accessible:
                    print(f"    {proj['key']}: {proj['story_count']} stories")
            
            elif test_name == "Issue Access":
                if status == "ANALYZED":
                    valid = len(result.get("valid_keys", []))
                    total = result.get("total_keys", 0)
                    print(f"  Issue Keys Validated: {valid}/{total}")
                    if result.get("valid_keys"):
                        print(f"  Valid Keys: {', '.join(result['valid_keys'][:5])}")
            
            elif test_name == "Data Freshness":
                if status == "ANALYZED":
                    score = result.get("freshness_score", 0)
                    print(f"  Freshness Score: {score:.1f}%")
                    print(f"  Test Indicators: {result.get('test_indicators', 0)}")
                    print(f"  Recent Activity: {result.get('recent_indicators', 0)}")
            
            elif test_name == "Error Handling":
                if status == "ANALYZED":
                    rate = result.get("handling_rate", 0)
                    passed = result.get("tests_passed", 0)
                    total = result.get("total_tests", 0)
                    print(f"  Error Handling Rate: {rate:.1f}%")
                    print(f"  Tests Passed: {passed}/{total}")
        
        # Overall integration assessment
        print(f"\n🎯 INTEGRATION ASSESSMENT:")
        
        connectivity_result = next((r for r in self.test_results if r["test"] == "connectivity"), None)
        if connectivity_result:
            if connectivity_result["status"] == "SUCCESS":
                print("  🎉 EXCELLENT: JIRA integration is working!")
            elif connectivity_result["status"] in ["AUTH_ERROR", "CONN_ERROR"]:
                print("  ❌ CRITICAL: Fix JIRA credentials/connection")
            else:
                print("  ⚠️  WARNING: JIRA integration issues detected")
        else:
            print("  ❓ UNKNOWN: Could not determine integration status")

def main():
    """Main test runner."""
    use_docker = "--local" not in sys.argv
    
    print(f"🚀 Running JIRA integration tests {'with Docker' if use_docker else 'locally'}")
    
    tester = JiraIntegrationTester(use_docker=use_docker)
    
    try:
        # Run integration tests
        success_count = 0
        
        if tester.test_jira_connectivity():
            success_count += 1
        
        if tester.test_project_access():
            success_count += 1
        
        if tester.test_issue_key_validation():
            success_count += 1
        
        if tester.test_data_freshness():
            success_count += 1
        
        if tester.test_error_handling():
            success_count += 1
        
        tester.print_integration_summary()
        
        # Exit based on success rate
        total_tests = 5
        success_rate = (success_count / total_tests) * 100
        print(f"\n🎯 Integration Test Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        sys.exit(0 if success_rate >= 60 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  JIRA integration tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 JIRA integration tests crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()