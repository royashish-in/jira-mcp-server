#!/usr/bin/env python3
"""Real content validation tests - Tests actual working tools with deep content analysis."""

import json
import subprocess
import sys
import os
import re
from typing import Dict, Any, List, Optional

class RealContentTester:
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

    def test_user_stories_content(self):
        """Deep validation of user stories content."""
        print("📋 Testing User Stories - Deep Content Analysis")
        
        response = self.send_mcp_request("tools/call", {
            "name": "get_user_stories", "arguments": {"project": "KW", "limit": 5}
        })
        
        text = self.get_response_text(response)
        if not text:
            print("  ❌ FAILED: No response")
            return False
        
        if "Tool implementation placeholder" in text:
            print("  ⚠️  SKIPPED: Tool not implemented")
            return False
        
        try:
            data = json.loads(text)
            print(f"  ✅ Valid JSON structure")
            
            # Check top-level structure
            if "stories" not in data:
                print("  ❌ Missing 'stories' key")
                return False
            
            stories = data["stories"]
            if not isinstance(stories, list):
                print("  ❌ 'stories' is not a list")
                return False
            
            print(f"  ✅ Found {len(stories)} stories")
            
            # Validate each story
            valid_stories = 0
            for i, story in enumerate(stories):
                print(f"    Story {i+1}:")
                
                # Check required fields
                required_fields = ['key', 'summary', 'status']
                missing_fields = [field for field in required_fields if field not in story]
                if missing_fields:
                    print(f"      ❌ Missing fields: {missing_fields}")
                    continue
                
                # Validate issue key format
                key = story['key']
                if not re.match(r'^[A-Z]+-\d+$', key):
                    print(f"      ❌ Invalid key format: {key}")
                    continue
                
                # Check summary is meaningful
                summary = story['summary']
                if len(summary) < 5:
                    print(f"      ❌ Summary too short: {summary}")
                    continue
                
                # Check status is valid
                status = story['status']
                valid_statuses = ['To Do', 'In Progress', 'Done', 'Backlog', 'Selected for Development']
                if status not in valid_statuses:
                    print(f"      ⚠️  Unusual status: {status}")
                
                print(f"      ✅ {key}: {summary[:50]}... [{status}]")
                valid_stories += 1
            
            success_rate = (valid_stories / len(stories)) * 100 if stories else 0
            print(f"  📊 Story Validation Rate: {success_rate:.1f}% ({valid_stories}/{len(stories)})")
            
            self.test_results.append({
                "tool": "get_user_stories",
                "status": "ANALYZED",
                "total_stories": len(stories),
                "valid_stories": valid_stories,
                "success_rate": success_rate
            })
            
            return success_rate >= 80
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Invalid JSON: {e}")
            print(f"  Raw response: {text[:200]}...")
            return False

    def test_tools_list_content(self):
        """Validate the tools list contains all expected tools."""
        print("\n🛠️ Testing Tools List - Comprehensive Tool Analysis")
        
        response = self.send_mcp_request("tools/list")
        
        if "error" in response:
            print(f"  ❌ FAILED: {response['error']['message']}")
            return False
        
        result = response.get("result", {})
        tools = result.get("tools", [])
        
        if not tools:
            print("  ❌ No tools found")
            return False
        
        print(f"  ✅ Found {len(tools)} tools")
        
        # Expected tool categories and counts
        expected_categories = {
            "Core Operations": ["get_user_stories", "get_issue", "get_projects", "search_issues"],
            "Workflow": ["transition_issue", "add_comment", "assign_issue"],
            "File Management": ["upload_attachment", "download_attachment", "list_attachments"],
            "Agile": ["get_boards", "get_sprints", "get_sprint_issues"]
        }
        
        tool_names = [tool.get("name", "") for tool in tools]
        
        # Validate tool structure
        valid_tools = 0
        for tool in tools:
            if all(key in tool for key in ["name", "description"]):
                valid_tools += 1
            else:
                print(f"      ❌ Invalid tool structure: {tool.get('name', 'unnamed')}")
        
        print(f"  📊 Tool Structure Validation: {valid_tools}/{len(tools)} tools valid")
        
        # Check for expected tools
        found_categories = {}
        for category, expected_tools in expected_categories.items():
            found_tools = [tool for tool in expected_tools if tool in tool_names]
            found_categories[category] = len(found_tools)
            print(f"    {category}: {len(found_tools)}/{len(expected_tools)} tools found")
        
        total_expected = sum(len(tools) for tools in expected_categories.values())
        total_found = sum(found_categories.values())
        coverage_rate = (total_found / total_expected) * 100
        
        print(f"  📊 Tool Coverage Rate: {coverage_rate:.1f}% ({total_found}/{total_expected})")
        
        self.test_results.append({
            "tool": "tools_list",
            "status": "ANALYZED",
            "total_tools": len(tools),
            "valid_tools": valid_tools,
            "coverage_rate": coverage_rate,
            "categories": found_categories
        })
        
        return coverage_rate >= 60

    def test_working_tools_identification(self):
        """Identify which tools are actually implemented vs placeholders."""
        print("\n🔍 Testing Working Tools - Implementation Analysis")
        
        # Test a sample of different tool types
        test_tools = [
            ("get_user_stories", {"project": "KW", "limit": 2}),
            ("get_projects", {}),
            ("get_issue", {"key": "KW-40"}),
            ("search_issues", {"jql": "project = KW", "limit": 2}),
            ("get_boards", {}),
            ("add_comment", {"key": "KW-40", "comment": "Test comment"}),
        ]
        
        working_tools = []
        placeholder_tools = []
        error_tools = []
        
        for tool_name, args in test_tools:
            print(f"  Testing {tool_name}...")
            
            response = self.send_mcp_request("tools/call", {
                "name": tool_name, "arguments": args
            })
            
            text = self.get_response_text(response)
            if not text:
                error_tools.append(tool_name)
                print(f"    ❌ No response")
            elif "Tool implementation placeholder" in text:
                placeholder_tools.append(tool_name)
                print(f"    ⚠️  Placeholder implementation")
            elif "Error:" in text:
                error_tools.append(tool_name)
                print(f"    ❌ Error: {text[:100]}...")
            else:
                # Qualitative validation of actual content
                if self.validate_tool_content(tool_name, text):
                    working_tools.append(tool_name)
                    print(f"    ✅ Working - Content validated")
                else:
                    error_tools.append(tool_name)
                    print(f"    ❌ Invalid content structure")
        
        print(f"\n  📊 Implementation Status:")
        print(f"    ✅ Working: {len(working_tools)} tools")
        print(f"    ⚠️  Placeholder: {len(placeholder_tools)} tools")
        print(f"    ❌ Error: {len(error_tools)} tools")
        
        if working_tools:
            print(f"    Working tools: {', '.join(working_tools)}")
        
        implementation_rate = (len(working_tools) / len(test_tools)) * 100
        print(f"  📊 Implementation Rate: {implementation_rate:.1f}%")
        
        self.test_results.append({
            "tool": "implementation_analysis",
            "status": "ANALYZED",
            "working_tools": working_tools,
            "placeholder_tools": placeholder_tools,
            "error_tools": error_tools,
            "implementation_rate": implementation_rate
        })
        
        return implementation_rate >= 50
    
    def validate_tool_content(self, tool_name: str, text: str) -> bool:
        """Validate tool content qualitatively based on expected structure."""
        try:
            data = json.loads(text)
            
            if tool_name == "get_user_stories":
                return "stories" in data and isinstance(data["stories"], list) and len(data["stories"]) > 0
            elif tool_name == "get_projects":
                return "projects" in data and isinstance(data["projects"], list)
            elif tool_name == "get_issue":
                return "key" in data and "summary" in data and "status" in data
            elif tool_name == "search_issues":
                return "issues" in data and "total" in data
            elif tool_name == "get_boards":
                return "boards" in data and isinstance(data["boards"], list)
            elif tool_name == "add_comment":
                return "success" in data and data.get("success") is True
            else:
                return True  # Default to true for unknown tools
        except json.JSONDecodeError:
            return False
    


    def test_data_quality_analysis(self):
        """Analyze the quality of data returned by working tools."""
        print("\n📊 Data Quality Analysis")
        
        # Focus on get_user_stories since we know it works
        response = self.send_mcp_request("tools/call", {
            "name": "get_user_stories", "arguments": {"project": "KW", "limit": 10}
        })
        
        text = self.get_response_text(response)
        if not text or "Tool implementation placeholder" in text:
            print("  ⚠️  No working tools for data quality analysis")
            return False
        
        try:
            data = json.loads(text)
            stories = data.get("stories", [])
            
            if not stories:
                print("  ❌ No stories data")
                return False
            
            # Analyze data quality metrics
            quality_metrics = {
                "has_description": 0,
                "has_assignee": 0,
                "has_priority": 0,
                "has_labels": 0,
                "has_components": 0,
                "meaningful_summary": 0
            }
            
            for story in stories:
                # Check for description
                if story.get("description") and len(str(story["description"])) > 10:
                    quality_metrics["has_description"] += 1
                
                # Check for assignee
                if story.get("assignee"):
                    quality_metrics["has_assignee"] += 1
                
                # Check for priority
                if story.get("priority"):
                    quality_metrics["has_priority"] += 1
                
                # Check for labels
                if story.get("labels") and len(story["labels"]) > 0:
                    quality_metrics["has_labels"] += 1
                
                # Check for components
                if story.get("components") and len(story["components"]) > 0:
                    quality_metrics["has_components"] += 1
                
                # Check for meaningful summary
                summary = story.get("summary", "")
                if len(summary) > 20 and not summary.lower().startswith("test"):
                    quality_metrics["meaningful_summary"] += 1
            
            print(f"  📊 Data Quality Metrics (out of {len(stories)} stories):")
            for metric, count in quality_metrics.items():
                percentage = (count / len(stories)) * 100
                print(f"    {metric.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
            
            # Calculate overall quality score
            total_possible = len(stories) * len(quality_metrics)
            total_actual = sum(quality_metrics.values())
            quality_score = (total_actual / total_possible) * 100
            
            print(f"  📊 Overall Data Quality Score: {quality_score:.1f}%")
            
            self.test_results.append({
                "tool": "data_quality",
                "status": "ANALYZED",
                "stories_analyzed": len(stories),
                "quality_metrics": quality_metrics,
                "quality_score": quality_score
            })
            
            return quality_score >= 40
            
        except Exception as e:
            print(f"  ❌ Data quality analysis failed: {e}")
            return False

    def print_comprehensive_summary(self):
        """Print comprehensive analysis summary."""
        print("\n" + "=" * 60)
        print("📊 REAL CONTENT ANALYSIS SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            tool = result["tool"]
            status = result["status"]
            
            print(f"\n🔍 {tool.upper().replace('_', ' ')}:")
            
            if tool == "get_user_stories":
                print(f"  Stories Found: {result['total_stories']}")
                print(f"  Valid Stories: {result['valid_stories']}")
                print(f"  Success Rate: {result['success_rate']:.1f}%")
            
            elif tool == "tools_list":
                print(f"  Total Tools: {result['total_tools']}")
                print(f"  Valid Tools: {result['valid_tools']}")
                print(f"  Coverage Rate: {result['coverage_rate']:.1f}%")
                for category, count in result['categories'].items():
                    print(f"    {category}: {count} tools")
            
            elif tool == "implementation_analysis":
                print(f"  Working Tools: {len(result['working_tools'])}")
                print(f"  Placeholder Tools: {len(result['placeholder_tools'])}")
                print(f"  Error Tools: {len(result['error_tools'])}")
                print(f"  Implementation Rate: {result['implementation_rate']:.1f}%")
                if result['working_tools']:
                    print(f"  Working: {', '.join(result['working_tools'])}")
            
            elif tool == "data_quality":
                print(f"  Stories Analyzed: {result['stories_analyzed']}")
                print(f"  Quality Score: {result['quality_score']:.1f}%")
                print("  Quality Breakdown:")
                for metric, count in result['quality_metrics'].items():
                    print(f"    {metric.replace('_', ' ').title()}: {count}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        
        # Count successful analyses
        successful_tests = len([r for r in self.test_results if r["status"] == "ANALYZED"])
        print(f"  Completed Analyses: {successful_tests}")
        
        # Find implementation rate
        impl_result = next((r for r in self.test_results if r["tool"] == "implementation_analysis"), None)
        if impl_result:
            impl_rate = impl_result["implementation_rate"]
            if impl_rate >= 80:
                print("  🎉 EXCELLENT: Most tools are fully implemented")
            elif impl_rate >= 50:
                print("  👍 GOOD: Many tools are working")
            elif impl_rate >= 25:
                print("  ⚠️  FAIR: Some tools are working")
            else:
                print("  ❌ POOR: Few tools are implemented")

def main():
    """Main test runner."""
    use_docker = "--local" not in sys.argv
    
    print(f"🚀 Running real content analysis {'with Docker' if use_docker else 'locally'}")
    
    tester = RealContentTester(use_docker=use_docker)
    
    try:
        # Run comprehensive content analysis
        success_count = 0
        
        if tester.test_user_stories_content():
            success_count += 1
        
        if tester.test_tools_list_content():
            success_count += 1
        
        if tester.test_working_tools_identification():
            success_count += 1
        
        if tester.test_data_quality_analysis():
            success_count += 1
        
        tester.print_comprehensive_summary()
        
        # Exit based on success rate
        total_tests = 4
        success_rate = (success_count / total_tests) * 100
        print(f"\n🎯 Test Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        sys.exit(0 if success_rate >= 50 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Real content analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Real content analysis crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()