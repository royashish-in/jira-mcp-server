#!/usr/bin/env python3
"""
Working MCP Protocol Test for JIRA MCP Server

This script demonstrates and tests the complete Model Context Protocol (MCP) communication
flow with the JIRA MCP server. It performs real JSON-RPC communication over stdio,
following the official MCP specification.

What this script does:
1. Starts the JIRA MCP server as a subprocess
2. Sends proper MCP initialization sequence
3. Lists available tools from the server
4. Calls the get_user_stories tool with real JIRA data
5. Validates responses and reports success/failure

This is a REAL MCP protocol test - it uses actual JSON-RPC messages over stdin/stdout,
not direct function calls. This is how Claude Desktop and other MCP clients communicate
with MCP servers.

Prerequisites:
- JIRA_URL environment variable (your Atlassian instance URL)
- JIRA_USERNAME environment variable (your email)
- JIRA_API_TOKEN environment variable (generate at https://id.atlassian.com/manage-profile/security/api-tokens)
- .env file with the above variables (recommended)

Usage:
    # With environment variables set:
    uv run python test_mcp_working.py
    
    # Or with .env file:
    echo "JIRA_URL=https://your-company.atlassian.net" > .env
    echo "JIRA_USERNAME=your-email@company.com" >> .env
    echo "JIRA_API_TOKEN=your-api-token" >> .env
    uv run python test_mcp_working.py

Expected Output:
- Successful initialization with protocol version
- List of available tools (get_user_stories, get_issue)
- Real JIRA user stories data in JSON format
- "MCP protocol working!" success message

Troubleshooting:
- "Missing JIRA environment variables" - Set JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
- "Authentication failed" - Generate new API token at Atlassian
- "Connection failed" - Check JIRA_URL format (https://company.atlassian.net)
- "Invalid request parameters" - This script fixes the common MCP initialization issue

MCP Protocol Flow Implemented:
1. initialize → Server responds with capabilities
2. notifications/initialized → Required notification after init
3. tools/list → Server returns available tools
4. tools/call → Execute specific tool with parameters

This script serves as both a test and documentation for proper MCP protocol usage.
"""

import asyncio
import json
import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

async def test_mcp_step_by_step():
    """
    Test MCP protocol step by step with proper initialization sequence.
    
    This function demonstrates the complete MCP handshake:
    1. Send initialize request with protocol version and client info
    2. Receive server capabilities and info
    3. Send initialized notification (CRITICAL - often missed!)
    4. Send tools/list to get available tools
    5. Send tools/call to execute a tool
    
    Returns:
        bool: True if all MCP protocol steps succeed, False otherwise
    """
    
    # Validate environment variables are present
    env = os.environ.copy()
    required_vars = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not env.get(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Set these variables or create a .env file with:")
        print("JIRA_URL=https://your-company.atlassian.net")
        print("JIRA_USERNAME=your-email@company.com")
        print("JIRA_API_TOKEN=your-api-token")
        return False
    
    print("Testing MCP protocol step by step...")
    print(f"Using JIRA instance: {env.get('JIRA_URL')}")
    print(f"Using username: [REDACTED]@[DOMAIN].com")
    print()
    
    # Start the MCP server as a subprocess
    # This simulates how Claude Desktop or other MCP clients start MCP servers
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,   # We'll send JSON-RPC requests here
        stdout=subprocess.PIPE,  # Server sends JSON-RPC responses here
        stderr=subprocess.PIPE,  # Server logs go here
        text=True,               # Use text mode for easier JSON handling
        env=env                  # Pass environment variables to subprocess
    )
    
    try:
        # Step 1: Initialize the MCP server
        # This is the first required message in the MCP protocol
        # The server will respond with its capabilities and info
        init_request = {
            "jsonrpc": "2.0",                    # JSON-RPC version
            "id": 1,                             # Request ID for matching responses
            "method": "initialize",              # MCP initialization method
            "params": {
                "protocolVersion": "2024-11-05",  # MCP protocol version
                "capabilities": {},              # Client capabilities (none for this test)
                "clientInfo": {                  # Information about this test client
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Step 1: Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read and parse initialization response
        init_response = process.stdout.readline()
        print(f"Init response: {init_response.strip()}")
        
        # Validate initialization was successful
        try:
            init_data = json.loads(init_response)
            if "error" in init_data:
                print(f"Initialization failed: {init_data['error']}")
                return False
            print("Server initialized successfully")
        except json.JSONDecodeError:
            print("Invalid JSON in initialization response")
            return False
        
        # Step 1.5: Send initialized notification
        # CRITICAL: This notification is required after successful initialization
        # Many MCP implementations fail because they skip this step!
        # The server won't accept tool requests until this is sent
        initialized_notification = {
            "jsonrpc": "2.0",                      # JSON-RPC version
            "method": "notifications/initialized"   # MCP initialized notification
            # Note: No "id" field - this is a notification, not a request
        }
        
        print("Step 1.5: Sending initialized notification (REQUIRED!)...")
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        print("Initialized notification sent")
        
        # Step 2: List available tools
        # This requests all tools the server provides
        # Should return get_user_stories and get_issue tools
        list_request = {
            "jsonrpc": "2.0",        # JSON-RPC version
            "id": 2,                 # Request ID
            "method": "tools/list"   # MCP method to list available tools
        }
        
        print("Step 2: Requesting available tools...")
        process.stdin.write(json.dumps(list_request) + "\n")
        process.stdin.flush()
        
        # Read and validate tools response
        tools_response = process.stdout.readline()
        print(f"Tools response: {tools_response.strip()}")
        
        try:
            tools_data = json.loads(tools_response)
            if "error" in tools_data:
                print(f"Tools list failed: {tools_data['error']}")
                return False
            
            tools = tools_data.get("result", {}).get("tools", [])
            tool_names = [tool["name"] for tool in tools]
            print(f"Available tools: {', '.join(tool_names)}")
            
            if "get_user_stories" not in tool_names:
                print("get_user_stories tool not found")
                return False
                
        except json.JSONDecodeError:
            print("Invalid JSON in tools response")
            return False
        
        # Step 3: Call the get_user_stories tool
        # This will fetch real user stories from your JIRA instance
        call_request = {
            "jsonrpc": "2.0",              # JSON-RPC version
            "id": 3,                       # Request ID
            "method": "tools/call",        # MCP method to call a tool
            "params": {
                "name": "get_user_stories", # Tool name to execute
                "arguments": {              # Arguments to pass to the tool
                    "limit": 3             # Limit to 3 stories for testing
                }
            }
        }
        
        print("Step 3: Calling get_user_stories tool...")
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        # Read and validate tool call response
        call_response = process.stdout.readline()
        print(f"Call response: {call_response.strip()}")
        
        # Parse and validate the response
        try:
            response_data = json.loads(call_response)
            
            if "error" in response_data:
                print(f"Tool call failed: {response_data['error']}")
                return False
            
            if "result" in response_data:
                # Extract the actual user stories data
                result = response_data["result"]
                if "content" in result and len(result["content"]) > 0:
                    stories_text = result["content"][0]["text"]
                    stories_data = json.loads(stories_text)
                    story_count = len(stories_data.get("stories", []))
                    
                    print(f"Successfully retrieved {story_count} user stories from JIRA!")
                    print("MCP protocol working perfectly!")
                    
                    # Show first story as example
                    if story_count > 0:
                        first_story = stories_data["stories"][0]
                        print(f"Example story: {first_story['key']} - {first_story['summary']}")
                    
                    return True
                else:
                    print("No content in tool response")
                    return False
            else:
                print(f"Unexpected response format: {response_data}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in tool response: {e}")
            return False
        except Exception as e:
            print(f"Error processing response: {e}")
            return False
            
    except Exception as e:
        print(f"Unexpected error during MCP test: {e}")
        return False
    finally:
        # Always clean up the subprocess
        if process.poll() is None:  # Process is still running
            process.terminate()
            process.wait(timeout=5)  # Wait up to 5 seconds for clean shutdown

if __name__ == "__main__":
    """
    Main execution block.
    
    This script can be run directly to test the MCP protocol implementation.
    It will exit with code 0 on success, 1 on failure (useful for CI/CD).
    
    Example usage:
        uv run python test_mcp_working.py
        echo $?  # Check exit code: 0 = success, 1 = failure
    """
    print("JIRA MCP Server - Real Protocol Test")
    print("=====================================")
    print("This test demonstrates complete MCP JSON-RPC communication")
    print("over stdin/stdout, exactly like Claude Desktop does.")
    print()
    
    try:
        success = asyncio.run(test_mcp_step_by_step())
        
        print()
        print("=====================================")
        if success:
            print("MCP Protocol Test PASSED")
            print("Your JIRA MCP server is working correctly!")
            print("It can now be used with Claude Desktop or other MCP clients.")
        else:
            print("MCP Protocol Test FAILED")
            print("Check the error messages above and fix the issues.")
            print("Common issues:")
            print("- Missing or incorrect JIRA credentials")
            print("- JIRA instance not accessible")
            print("- Network connectivity problems")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)