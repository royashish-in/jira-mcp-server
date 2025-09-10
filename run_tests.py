#!/usr/bin/env python3
"""
JIRA MCP Server Test Runner
Consolidated test execution with multiple test levels
"""

import asyncio
import subprocess
import sys
import argparse
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.test_dir = Path(__file__).parent
        
    def run_test_file(self, test_file: str) -> bool:
        """Run a specific test file and return success status"""
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
                
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"❌ {test_file} timed out")
            return False
        except Exception as e:
            print(f"❌ {test_file} failed with exception: {e}")
            return False
    
    def run_smoke_tests(self) -> bool:
        """Run quick smoke tests"""
        print("🔥 RUNNING SMOKE TESTS")
        print("=" * 50)
        return self.run_test_file("test_suite_smoke.py")
    
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        print("\n🧪 RUNNING UNIT TESTS")
        print("=" * 50)
        return self.run_test_file("test_suite_unit.py")
    
    def run_comprehensive_tests(self) -> bool:
        """Run comprehensive integration tests"""
        print("\n🚀 RUNNING COMPREHENSIVE TESTS")
        print("=" * 50)
        return self.run_test_file("test_suite_comprehensive.py")
    
    def run_connection_test(self) -> bool:
        """Run JIRA connection test"""
        print("\n🔗 TESTING JIRA CONNECTION")
        print("=" * 50)
        return self.run_test_file("test_connection.py")
    
    def cleanup_old_tests(self):
        """Remove old individual test files"""
        old_test_files = [
            "test_absolute_final.py",
            "test_advanced_jql.py", 
            "test_advanced_workflow.py",
            "test_all_features_comprehensive.py",
            "test_all_new_tools_mcp.py",
            "test_all_tools_mcp.py",
            "test_attachment_tools.py",
            "test_create_issue.py",
            "test_custom_fields_sprints.py",
            "test_file_operations.py",
            "test_final_comprehensive.py",
            "test_final_edge_cases.py",
            "test_final_ultimate.py",
            "test_get_issues_by_assignee.py",
            "test_get_project_stats.py",
            "test_get_projects.py",
            "test_get_recent_issues.py",
            "test_get_transitions.py",
            "test_mcp_working.py",
            "test_priority1_tools.py",
            "test_priority2_tools.py",
            "test_project_tools.py",
            "test_reporting_admin.py",
            "test_search_issues.py",
            "test_transition_issue.py",
            "test_ultimate_comprehensive.py",
            "test_update_issue.py",
            "test_webhooks_notifications.py",
            "test_workflow_tools.py"
        ]
        
        print("🧹 CLEANING UP OLD TEST FILES")
        print("=" * 50)
        
        removed_count = 0
        for test_file in old_test_files:
            test_path = self.test_dir / test_file
            if test_path.exists():
                test_path.unlink()
                print(f"🗑️  Removed {test_file}")
                removed_count += 1
        
        if removed_count > 0:
            print(f"\n✅ Cleaned up {removed_count} old test files")
        else:
            print("✅ No old test files to clean up")
    
    def run_all_tests(self) -> bool:
        """Run all test suites"""
        print("🎯 JIRA MCP SERVER - COMPLETE TEST SUITE")
        print("=" * 60)
        
        results = []
        
        # Run connection test first
        results.append(("Connection Test", self.run_connection_test()))
        
        # Run smoke tests
        results.append(("Smoke Tests", self.run_smoke_tests()))
        
        # Run unit tests
        results.append(("Unit Tests", self.run_unit_tests()))
        
        # Run comprehensive tests
        results.append(("Comprehensive Tests", self.run_comprehensive_tests()))
        
        # Print final summary
        print("\n" + "=" * 60)
        print("🏆 FINAL TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:.<30} {status}")
            if success:
                passed += 1
            else:
                failed += 1
        
        print("-" * 60)
        print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! JIRA MCP SERVER IS READY!")
            return True
        else:
            print(f"\n⚠️  {failed} test suite(s) failed")
            return False

def main():
    parser = argparse.ArgumentParser(description="JIRA MCP Server Test Runner")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive tests only")
    parser.add_argument("--connection", action="store_true", help="Run connection test only")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old test files")
    parser.add_argument("--all", action="store_true", help="Run all test suites (default)")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.cleanup:
        runner.cleanup_old_tests()
        return 0
    
    success = False
    
    if args.smoke:
        success = runner.run_smoke_tests()
    elif args.unit:
        success = runner.run_unit_tests()
    elif args.comprehensive:
        success = runner.run_comprehensive_tests()
    elif args.connection:
        success = runner.run_connection_test()
    else:
        # Default: run all tests
        success = runner.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())