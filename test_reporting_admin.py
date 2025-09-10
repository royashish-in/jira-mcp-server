#!/usr/bin/env python3
"""TDD test for reporting and admin features via MCP protocol"""

import asyncio
import json
import subprocess
import sys

async def test_reporting_admin_mcp():
    """Test reporting and admin features via real MCP JSON-RPC protocol"""
    
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
        
        # Test get_time_tracking_report
        print("Testing get_time_tracking_report...")
        report_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_time_tracking_report",
                "arguments": {
                    "project": "KW"
                }
            }
        }
        
        process.stdin.write(json.dumps(report_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        report_response = json.loads(response)
        
        assert report_response["id"] == 2
        content = report_response["result"]["content"][0]["text"]
        assert "time" in content.lower() or "report" in content.lower()
        print("✅ get_time_tracking_report passed")
        
        # Test get_project_roles
        print("Testing get_project_roles...")
        roles_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_project_roles",
                "arguments": {
                    "project": "KW"
                }
            }
        }
        
        process.stdin.write(json.dumps(roles_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        roles_response = json.loads(response)
        
        assert roles_response["id"] == 3
        content = roles_response["result"]["content"][0]["text"]
        assert "role" in content.lower()
        print("✅ get_project_roles passed")
        
        # Test export_issues
        print("Testing export_issues...")
        export_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "export_issues",
                "arguments": {
                    "jql": "project = KW",
                    "format": "json"
                }
            }
        }
        
        process.stdin.write(json.dumps(export_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        export_response = json.loads(response)
        
        assert export_response["id"] == 4
        content = export_response["result"]["content"][0]["text"]
        assert "export" in content.lower() or "issues" in content.lower()
        print("✅ export_issues passed")
        
        print("🎉 Reporting and admin tools passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_reporting_admin_mcp())