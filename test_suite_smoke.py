#!/usr/bin/env python3
"""
Smoke Test Suite for JIRA MCP Server
Quick validation of essential functionality
"""

import asyncio
import json
import subprocess
import sys

async def smoke_test():
    """Quick smoke test of essential JIRA MCP Server functionality"""
    print("💨 JIRA MCP SERVER SMOKE TEST")
    print("=" * 40)
    
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Initialize MCP
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smoke-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        init_response = json.loads(response)
        assert init_response["id"] == 1
        print("✅ MCP initialization")
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test tools list
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        tools_response = json.loads(response)
        assert tools_response["id"] == 2
        assert "result" in tools_response
        tools_count = len(tools_response["result"]["tools"])
        print(f"✅ Tools available: {tools_count}")
        
        # Test one essential tool
        test_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_projects",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(test_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        test_response = json.loads(response)
        
        assert test_response["id"] == 3
        assert "result" in test_response
        print("✅ Tool execution")
        
        print("\n🎉 SMOKE TEST PASSED!")
        print(f"🚀 JIRA MCP Server is operational with {tools_count} tools")
        return True
        
    except Exception as e:
        print(f"❌ SMOKE TEST FAILED: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    success = asyncio.run(smoke_test())
    sys.exit(0 if success else 1)