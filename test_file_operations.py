#!/usr/bin/env python3
"""TDD test for file operations via MCP protocol"""

import asyncio
import json
import subprocess
import sys
import tempfile
import os

async def test_file_operations_mcp():
    """Test file operations via real MCP JSON-RPC protocol"""
    
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
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file content for JIRA attachment")
            test_file_path = f.name
        
        try:
            # Test upload_attachment
            print("Testing upload_attachment...")
            upload_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "upload_attachment",
                    "arguments": {
                        "key": "KW-41",
                        "file_path": test_file_path
                    }
                }
            }
            
            process.stdin.write(json.dumps(upload_request) + "\n")
            process.stdin.flush()
            
            response = process.stdout.readline()
            upload_response = json.loads(response)
            
            assert upload_response["id"] == 2
            content = upload_response["result"]["content"][0]["text"]
            assert "upload" in content.lower() or "attachment" in content.lower()
            print("✅ upload_attachment passed")
            
        finally:
            os.unlink(test_file_path)
        
        print("🎉 File operations passed!")
        
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_file_operations_mcp())