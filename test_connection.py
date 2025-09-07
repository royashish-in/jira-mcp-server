#!/usr/bin/env python3
"""Test JIRA connection and configuration."""

import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_connection():
    """Test JIRA API connection."""
    jira_url = os.getenv("JIRA_URL")
    jira_username = os.getenv("JIRA_USERNAME")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_username, jira_api_token]):
        print("❌ Missing required environment variables:")
        if not jira_url:
            print("  - JIRA_URL")
        if not jira_username:
            print("  - JIRA_USERNAME")
        if not jira_api_token:
            print("  - JIRA_API_TOKEN")
        return False
    
    print(f"🔗 Testing connection to: {jira_url}")
    print(f"👤 Using username: {jira_username}")
    print(f"🔑 API token length: {len(jira_api_token)} characters")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{jira_url}/rest/api/3/myself",
                auth=(jira_username, jira_api_token)
            )
            
            print(f"📡 HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    user_info = response.json()
                    print(f"✅ Connected to JIRA as: {user_info.get('displayName', 'Unknown')}")
                    print(f"   Email: [REDACTED]@[DOMAIN].com")
                    return True
                except ValueError:
                    print("❌ Invalid JSON response from JIRA")
                    return False
            elif response.status_code == 401:
                print("❌ Authentication failed (401)")
                print("💡 Solutions:")
                print("   1. Generate new API token: https://id.atlassian.com/manage-profile/security/api-tokens")
                print("   2. Verify your email matches your Atlassian account")
                print("   3. Check if API token has expired")
                print(f"🔍 Server response: {response.text[:100]}")
                return False
            elif response.status_code == 403:
                print("❌ Access denied (403) - insufficient permissions")
                print("💡 Solutions:")
                print("   1. Check JIRA project permissions")
                print("   2. Verify API access is enabled for your account")
                print(f"🔍 Server response: {response.text[:100]}")
                return False
            else:
                print(f"❌ Connection failed with status: {response.status_code}")
                print(f"🔍 Server response: {response.text[:200]}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Connection timeout - check JIRA URL")
        return False
    except httpx.ConnectError as e:
        print(f"❌ Connection failed - check JIRA URL: {str(e)}")
        return False
    except httpx.RequestError as e:
        print(f"❌ Request error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)