#!/usr/bin/env python3
"""Comprehensive Real Tests - Combines all real content validation tests."""

import sys
import os
import subprocess
from typing import Dict, Any, List

def run_test_suite(test_file: str, description: str, use_docker: bool = True) -> Dict[str, Any]:
    """Run a test suite and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    cmd = ["python", test_file]
    if not use_docker:
        cmd.append("--local")
    
    try:
        result = subprocess.run(
            cmd,
            cwd="/Users/royashish/AI/jira-mcp-server-standalone",
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        return {
            "name": description,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {description} took too long")
        return {
            "name": description,
            "exit_code": -1,
            "success": False,
            "error": "Timeout"
        }
    except Exception as e:
        print(f"❌ ERROR: {description} failed: {e}")
        return {
            "name": description,
            "exit_code": -2,
            "success": False,
            "error": str(e)
        }

def extract_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from test results."""
    metrics = {}
    stdout = results.get("stdout", "")
    
    # Extract success rates
    if "Success Rate:" in stdout:
        import re
        rates = re.findall(r'Success Rate: ([\d.]+)%', stdout)
        if rates:
            metrics["success_rate"] = float(rates[-1])
    
    if "Implementation Rate:" in stdout:
        import re
        rates = re.findall(r'Implementation Rate: ([\d.]+)%', stdout)
        if rates:
            metrics["implementation_rate"] = float(rates[-1])
    
    if "Quality Score:" in stdout:
        import re
        scores = re.findall(r'Quality Score: ([\d.]+)%', stdout)
        if scores:
            metrics["quality_score"] = float(scores[-1])
    
    if "Integration Test Success Rate:" in stdout:
        import re
        rates = re.findall(r'Integration Test Success Rate: ([\d.]+)%', stdout)
        if rates:
            metrics["integration_rate"] = float(rates[-1])
    
    # Extract tool counts
    if "Found" in stdout and "tools" in stdout:
        import re
        tools = re.findall(r'Found (\d+) tools', stdout)
        if tools:
            metrics["total_tools"] = int(tools[-1])
    
    if "Working:" in stdout and "tools" in stdout:
        import re
        working = re.findall(r'Working: (\d+) tools', stdout)
        if working:
            metrics["working_tools"] = int(working[-1])
    
    return metrics

def print_comprehensive_summary(all_results: List[Dict[str, Any]]):
    """Print comprehensive summary of all test results."""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE REAL CONTENT TEST SUMMARY")
    print(f"{'='*80}")
    
    successful_suites = len([r for r in all_results if r["success"]])
    total_suites = len(all_results)
    
    print(f"\n🎯 Test Suite Results: {successful_suites}/{total_suites} suites passed")
    
    # Individual suite results
    for result in all_results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"  {status}: {result['name']}")
        
        if not result["success"] and "error" in result:
            print(f"    Error: {result['error']}")
    
    # Extract and display key metrics
    print(f"\n📈 Key Metrics:")
    
    all_metrics = {}
    for result in all_results:
        metrics = extract_metrics(result)
        all_metrics[result["name"]] = metrics
    
    # Display metrics by category
    for suite_name, metrics in all_metrics.items():
        if metrics:
            print(f"\n  {suite_name}:")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    print(f"    {metric.replace('_', ' ').title()}: {value:.1f}%")
                else:
                    print(f"    {metric.replace('_', ' ').title()}: {value}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    # Check JIRA connectivity
    integration_results = next((r for r in all_results if "Integration" in r["name"]), None)
    if integration_results and integration_results["success"]:
        print("  🎉 JIRA Integration: WORKING")
    else:
        print("  ❌ JIRA Integration: FAILED")
    
    # Check implementation status
    content_results = next((r for r in all_results if "Content Analysis" in r["name"]), None)
    if content_results:
        metrics = extract_metrics(content_results)
        impl_rate = metrics.get("implementation_rate", 0)
        if impl_rate >= 80:
            print("  🎉 Implementation: EXCELLENT")
        elif impl_rate >= 50:
            print("  👍 Implementation: GOOD")
        elif impl_rate >= 25:
            print("  ⚠️  Implementation: PARTIAL")
        else:
            print("  ❌ Implementation: POOR")
    
    # Check data quality
    if content_results:
        metrics = extract_metrics(content_results)
        quality_score = metrics.get("quality_score", 0)
        if quality_score >= 60:
            print("  🎉 Data Quality: EXCELLENT")
        elif quality_score >= 40:
            print("  👍 Data Quality: GOOD")
        elif quality_score >= 20:
            print("  ⚠️  Data Quality: FAIR")
        else:
            print("  ❌ Data Quality: POOR")
    
    # Final recommendation
    overall_success_rate = (successful_suites / total_suites) * 100
    print(f"\n🎯 Overall Success Rate: {overall_success_rate:.1f}%")
    
    if overall_success_rate >= 80:
        print("🎉 RECOMMENDATION: Server is production-ready!")
    elif overall_success_rate >= 60:
        print("👍 RECOMMENDATION: Server is functional with minor issues")
    elif overall_success_rate >= 40:
        print("⚠️  RECOMMENDATION: Server needs significant improvements")
    else:
        print("❌ RECOMMENDATION: Server requires major fixes before use")

def main():
    """Main comprehensive test runner."""
    use_docker = "--local" not in sys.argv
    
    print("🚀 COMPREHENSIVE REAL CONTENT TEST SUITE")
    print(f"Running tests {'with Docker' if use_docker else 'locally'}")
    
    # Define test suites to run
    test_suites = [
        ("test/real_content_tests.py", "Real Content Analysis"),
        ("test/jira_integration_tests.py", "JIRA Integration Tests"),
        ("test/content_validation_tests.py", "Content Validation Tests"),
    ]
    
    all_results = []
    
    try:
        # Run each test suite
        for test_file, description in test_suites:
            result = run_test_suite(test_file, description, use_docker)
            all_results.append(result)
        
        # Print comprehensive summary
        print_comprehensive_summary(all_results)
        
        # Exit with appropriate code
        successful_suites = len([r for r in all_results if r["success"]])
        total_suites = len(all_results)
        success_rate = (successful_suites / total_suites) * 100
        
        sys.exit(0 if success_rate >= 60 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Comprehensive tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Comprehensive tests crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()