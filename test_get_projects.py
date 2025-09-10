#!/usr/bin/env python3
"""
TDD Test for get_projects MCP Tool

Tests the get_projects tool via real MCP JSON-RPC protocol communication.
This test follows TDD principles - test first, then implement.
"""

import asyncio
import json
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_get_projects_mcp():
    """Test get_projects tool via real MCP protocol."""
    
    # Validate environment variables
    env = os.environ.copy()
    required_vars = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not env.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("Testing get_projects tool via MCP protocol...")
    
    # Start MCP server
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    try:
        # Step 1: Initialize MCP server
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
        
        init_response = process.stdout.readline()
        init_data = json.loads(init_response)
        
        if "error" in init_data:
            print(f"Initialization failed: {init_data['error']}")
            return False
        
        # Step 2: Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        
        # Step 3: List tools to verify get_projects exists
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(list_request) + "\n")
        process.stdin.flush()
        
        tools_response = process.stdout.readline()
        tools_data = json.loads(tools_response)
        
        if "error" in tools_data:
            print(f"Tools list failed: {tools_data['error']}")
            return False
        
        tools = tools_data.get("result", {}).get("tools", [])
        tool_names = [tool["name"] for tool in tools]
        
        if "get_projects" not in tool_names:
            print("get_projects tool not found in tools list")
            print(f"Available tools: {tool_names}")
            return False
        
        print("get_projects tool found in tools list")
        
        # Step 4: Call get_projects tool
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_projects",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        call_response = process.stdout.readline()
        response_data = json.loads(call_response)
        
        if "error" in response_data:
            print(f"get_projects call failed: {response_data['error']}")
            return False
        
        # Validate response structure
        result = response_data.get("result")
        if not result or "content" not in result:
            print("Invalid response structure")
            return False
        
        content = result["content"][0]["text"]
        projects_data = json.loads(content)
        
        # Validate projects data structure
        if "projects" not in projects_data:
            print("Missing 'projects' key in response")
            return False
        
        projects = projects_data["projects"]
        if not isinstance(projects, list):
            print("Projects should be a list")
            return False
        
        print(f"Successfully retrieved {len(projects)} projects")
        
        # Validate project structure
        if projects:
            first_project = projects[0]
            required_fields = ["key", "name", "projectTypeKey"]
            for field in required_fields:
                if field not in first_project:
                    print(f"Missing required field '{field}' in project")
                    return False
            
            print(f"Example project: {first_project['key']} - {first_project['name']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"Test error: {e}")
        return False
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

if __name__ == "__main__":
    print("TDD Test: get_projects MCP Tool")
    print("=" * 40)
    
    success = asyncio.run(test_get_projects_mcp())
    
    if success:
        print("TEST PASSED: get_projects tool working correctly")
        sys.exit(0)
    else:
        print("TEST FAILED: get_projects tool needs implementation")
        sys.exit(1)