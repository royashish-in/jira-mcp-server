#!/usr/bin/env python3
"""
Unit Test Suite for JIRA MCP Server
Tests core functionality and edge cases
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import os

async def test_mcp_protocol():
    """Test MCP protocol initialization and basic communication"""
    print("🔧 Testing MCP Protocol...")
    
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "unit-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        init_response = json.loads(response)
        
        assert init_response["id"] == 1
        assert "result" in init_response
        assert "capabilities" in init_response["result"]
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test tools/list
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
        assert "tools" in tools_response["result"]
        
        tools = tools_response["result"]["tools"]
        assert len(tools) >= 46  # Should have all our tools
        
        print("✅ MCP Protocol tests passed")
        return True
        
    except Exception as e:
        print(f"❌ MCP Protocol test failed: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

async def test_core_crud_operations():
    """Test core CRUD operations"""
    print("🔧 Testing Core CRUD Operations...")
    
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
                "clientInfo": {"name": "unit-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Consume response
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test READ operation
        read_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_issue",
                "arguments": {"key": "KW-41"}
            }
        }
        
        process.stdin.write(json.dumps(read_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        read_response = json.loads(response)
        
        assert read_response["id"] == 2
        assert "result" in read_response
        
        print("✅ Core CRUD operations tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Core CRUD operations test failed: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

async def test_error_handling():
    """Test error handling for invalid inputs"""
    print("🔧 Testing Error Handling...")
    
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
                "clientInfo": {"name": "unit-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Consume response
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test invalid tool name
        invalid_tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(invalid_tool_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        error_response = json.loads(response)
        
        assert error_response["id"] == 2
        assert "result" in error_response
        content = error_response["result"]["content"][0]["text"]
        assert "unknown tool" in content.lower() or "error" in content.lower()
        
        print("✅ Error handling tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

async def test_batch_operations():
    """Test batch operations for efficiency"""
    print("🔧 Testing Batch Operations...")
    
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
                "clientInfo": {"name": "unit-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Consume response
        
        # Send initialized notification
        initialized = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()
        
        # Test bulk update
        bulk_update_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "bulk_update_issues",
                "arguments": {
                    "keys": ["KW-41"],
                    "updates": {"priority": "Medium"}
                }
            }
        }
        
        process.stdin.write(json.dumps(bulk_update_request) + "\n")
        process.stdin.flush()
        
        response = process.stdout.readline()
        bulk_response = json.loads(response)
        
        assert bulk_response["id"] == 2
        assert "result" in bulk_response
        
        print("✅ Batch operations tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Batch operations test failed: {e}")
        return False
    finally:
        process.terminate()
        process.wait()

async def main():
    """Run unit test suite"""
    print("🧪 JIRA MCP SERVER UNIT TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_mcp_protocol,
        test_core_crud_operations,
        test_error_handling,
        test_batch_operations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🏆 UNIT TEST RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {passed}/{len(tests)} tests")
    print(f"❌ Failed: {failed} tests")
    
    if failed == 0:
        print("\n🎉 ALL UNIT TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} unit tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)