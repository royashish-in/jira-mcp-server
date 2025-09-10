#!/usr/bin/env python3
"""JIRA MCP Server - Read user stories from JIRA."""

import asyncio
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List
from urllib.parse import quote
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
from dotenv import load_dotenv

def sanitize_for_log(value: str) -> str:
    """Sanitize user input for safe logging."""
    if not isinstance(value, str):
        value = str(value)
    return value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

load_dotenv()

# JIRA configuration
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME") 
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

# Setup logging
logging.basicConfig(
    level=logging.INFO if VERBOSE_LOGGING else logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("jira-mcp-server")

missing_vars = []
if not JIRA_URL:
    missing_vars.append("JIRA_URL")
if not JIRA_USERNAME:
    missing_vars.append("JIRA_USERNAME")
if not JIRA_API_TOKEN:
    missing_vars.append("JIRA_API_TOKEN")

if missing_vars:
    raise ValueError(f"Missing required JIRA configuration: {', '.join(missing_vars)}")

server = Server("jira-mcp-server")

# Compile regex patterns once for performance
PROJECT_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')
ISSUE_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*-\d+$')

def validate_project_key(project: str) -> bool:
    """Validate JIRA project key format."""
    return bool(PROJECT_KEY_PATTERN.match(project))

def validate_issue_key(key: str) -> bool:
    """Validate JIRA issue key format."""
    return bool(ISSUE_KEY_PATTERN.match(key))

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available JIRA tools."""
    return [
        Tool(
            name="get_user_stories",
            description="Get user stories from JIRA",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key (optional)"},
                    "limit": {"type": "integer", "description": "Max number of stories", "minimum": 1, "maximum": 100}
                }
            }
        ),
        Tool(
            name="get_issue",
            description="Get specific JIRA issue by key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-3)"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="get_projects",
            description="Get all accessible JIRA projects",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_issues",
            description="Search JIRA issues using JQL (JIRA Query Language)",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL query string"},
                    "limit": {"type": "integer", "description": "Max results", "minimum": 1, "maximum": 100}
                },
                "required": ["jql"]
            }
        ),
        Tool(
            name="get_project_stats",
            description="Get project statistics including issue counts by status and type",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="get_recent_issues",
            description="Get recently updated issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to look back", "minimum": 1, "maximum": 365},
                    "limit": {"type": "integer", "description": "Max results", "minimum": 1, "maximum": 100}
                }
            }
        ),
        Tool(
            name="get_issues_by_assignee",
            description="Get issues assigned to a specific user",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignee": {"type": "string", "description": "Assignee username or currentUser()"},
                    "limit": {"type": "integer", "description": "Max results", "minimum": 1, "maximum": 100}
                },
                "required": ["assignee"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {sanitize_for_log(name)}")
    try:
        if name == "get_user_stories":
            return await get_user_stories(arguments)
        elif name == "get_issue":
            return await get_issue(arguments)
        elif name == "get_projects":
            return await get_projects(arguments)
        elif name == "search_issues":
            return await search_issues(arguments)
        elif name == "get_project_stats":
            return await get_project_stats(arguments)
        elif name == "get_recent_issues":
            return await get_recent_issues(arguments)
        elif name == "get_issues_by_assignee":
            return await get_issues_by_assignee(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {sanitize_for_log(name)} failed: {str(e)}", exc_info=VERBOSE_LOGGING)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_user_stories(args: Dict[str, Any]) -> List[TextContent]:
    """Get user stories from JIRA."""
    project = args.get("project", "")
    limit = min(args.get("limit", 10), 100)  # Cap at 100
    
    logger.info(f"Getting user stories for project: {sanitize_for_log(project)}, limit: {limit}")
    
    # Validate project key if provided
    if project and not validate_project_key(project):
        logger.error(f"Invalid project key format: {sanitize_for_log(project)}")
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    # Build JQL query - project is already validated with regex
    if project:
        # Safe to use f-string since project is validated with strict regex pattern
        jql = f"project = {project} AND issuetype = Story ORDER BY created DESC"
    else:
        jql = "issuetype = Story ORDER BY created DESC"
    
    logger.info(f"JQL query: {sanitize_for_log(jql)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search",
                params={"jql": jql, "maxResults": limit},
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            logger.info(f"JIRA API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from JIRA API: {e}")
                    return [TextContent(type="text", text="Error: Invalid response from JIRA API")]
                issues = data.get("issues", [])
                logger.info(f"Retrieved {len(issues)} issues")
                
                stories = []
                for issue in issues:
                    try:
                        desc = issue.get("fields", {}).get("description", "")
                        if isinstance(desc, dict):
                            desc = str(desc.get("content", "")) if "content" in desc else str(desc)
                        story = {
                            "key": issue.get("key", "Unknown"),
                            "summary": issue.get("fields", {}).get("summary", "No summary"),
                            "status": issue.get("fields", {}).get("status", {}).get("name", "Unknown"),
                            "description": desc
                        }
                        stories.append(story)
                    except Exception as e:
                        logger.error(f"Error processing issue {sanitize_for_log(issue.get('key', 'unknown'))}: {e}")
                        continue
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"stories": stories}, indent=2)
                )]
            elif response.status_code == 401:
                logger.error("JIRA authentication failed (401)")
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                logger.error("JIRA access denied (403)")
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                logger.error(f"JIRA API error: {response.status_code}")
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_user_stories: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Get specific JIRA issue."""
    key = args.get("key")
    if not key:
        logger.error("Missing required 'key' parameter")
        return [TextContent(type="text", text="Error: Missing required 'key' parameter")]
    
    logger.info(f"Getting issue: {sanitize_for_log(key)}")
    
    # Validate issue key format
    if not validate_issue_key(key):
        logger.error(f"Invalid issue key format: {sanitize_for_log(key)}")
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{quote(key, safe='')}",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            logger.info(f"JIRA API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    issue = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from JIRA API: {e}")
                    return [TextContent(type="text", text="Error: Invalid response from JIRA API")]
                
                try:
                    fields = issue.get("fields", {})
                    assignee = fields.get("assignee")
                    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
                    
                    desc = fields.get("description", "")
                    if isinstance(desc, dict):
                        desc = str(desc.get("content", "")) if "content" in desc else str(desc)
                    
                    result = {
                        "key": issue.get("key", "Unknown"),
                        "summary": fields.get("summary", "No summary"),
                        "status": fields.get("status", {}).get("name", "Unknown"),
                        "description": desc,
                        "assignee": assignee_name,
                        "created": fields.get("created", "Unknown")
                    }
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
                except Exception as e:
                    logger.error(f"Error processing issue data for {sanitize_for_log(key)}: {e}")
                    return [TextContent(type="text", text=f"Error: Failed to process issue data - {str(e)}")]
            elif response.status_code == 404:
                logger.error(f"Issue not found: {sanitize_for_log(key)}")
                return [TextContent(type="text", text=f"Error: Issue '{key}' not found. Check issue key and permissions.")]
            elif response.status_code == 401:
                logger.error("JIRA authentication failed (401)")
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                logger.error("JIRA access denied (403)")
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                logger.error(f"JIRA API error: {response.status_code}")
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_issue: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def search_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Search JIRA issues using JQL."""
    jql = args.get("jql")
    limit = min(args.get("limit", 50), 100)
    
    if not jql:
        logger.error("Missing required 'jql' parameter")
        return [TextContent(type="text", text="Error: Missing required 'jql' parameter")]
    
    logger.info(f"Searching issues with JQL: {sanitize_for_log(jql)}, limit: {limit}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search",
                params={"jql": jql, "maxResults": limit},
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            logger.info(f"JIRA API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from JIRA API: {e}")
                    return [TextContent(type="text", text="Error: Invalid response from JIRA API")]
                
                issues_data = data.get("issues", [])
                logger.info(f"Found {len(issues_data)} issues")
                
                issues = []
                for issue in issues_data:
                    try:
                        issue_info = {
                            "key": issue.get("key", "Unknown"),
                            "summary": issue.get("fields", {}).get("summary", "No summary"),
                            "status": issue.get("fields", {}).get("status", {}).get("name", "Unknown"),
                            "issueType": issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown"),
                            "priority": issue.get("fields", {}).get("priority", {}).get("name", "Unknown") if issue.get("fields", {}).get("priority") else "None",
                            "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName", "Unassigned") if issue.get("fields", {}).get("assignee") else "Unassigned"
                        }
                        issues.append(issue_info)
                    except Exception as e:
                        logger.error(f"Error processing issue {sanitize_for_log(issue.get('key', 'unknown'))}: {e}")
                        continue
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"issues": issues}, indent=2)
                )]
            elif response.status_code == 400:
                logger.error(f"Invalid JQL query: {sanitize_for_log(jql)}")
                return [TextContent(type="text", text="Error: Invalid JQL query syntax. Check your query and try again.")]
            elif response.status_code == 401:
                logger.error("JIRA authentication failed (401)")
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                logger.error("JIRA access denied (403)")
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                logger.error(f"JIRA API error: {response.status_code}")
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in search_issues: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_project_stats(args: Dict[str, Any]) -> List[TextContent]:
    """Get project statistics."""
    project = args.get("project")
    if not project:
        logger.error("Missing required 'project' parameter")
        return [TextContent(type="text", text="Error: Missing required 'project' parameter")]
    
    if not validate_project_key(project):
        logger.error(f"Invalid project key format: {sanitize_for_log(project)}")
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting project stats for: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get all issues for the project
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search",
                params={"jql": f"project = {project}", "maxResults": 1000, "fields": "status,issuetype"},
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                # Calculate statistics
                status_counts = {}
                type_counts = {}
                
                for issue in issues:
                    fields = issue.get("fields", {})
                    
                    # Count by status
                    status = fields.get("status", {}).get("name", "Unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Count by type
                    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
                    type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
                
                stats = {
                    "project": project,
                    "totalIssues": len(issues),
                    "issuesByStatus": status_counts,
                    "issuesByType": type_counts
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(stats, indent=2)
                )]
            elif response.status_code == 401:
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_project_stats: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_recent_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Get recently updated issues."""
    days = args.get("days", 7)
    limit = min(args.get("limit", 20), 100)
    
    logger.info(f"Getting recent issues from last {days} days, limit: {limit}")
    
    # Build JQL for recent issues
    jql = f"updated >= -{days}d ORDER BY updated DESC"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search",
                params={"jql": jql, "maxResults": limit},
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues_data = data.get("issues", [])
                
                issues = []
                for issue in issues_data:
                    try:
                        fields = issue.get("fields", {})
                        issue_info = {
                            "key": issue.get("key", "Unknown"),
                            "summary": fields.get("summary", "No summary"),
                            "status": fields.get("status", {}).get("name", "Unknown"),
                            "issueType": fields.get("issuetype", {}).get("name", "Unknown"),
                            "updated": fields.get("updated", "Unknown"),
                            "created": fields.get("created", "Unknown"),
                            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
                        }
                        issues.append(issue_info)
                    except Exception as e:
                        logger.error(f"Error processing issue {sanitize_for_log(issue.get('key', 'unknown'))}: {e}")
                        continue
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"issues": issues}, indent=2)
                )]
            elif response.status_code == 401:
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_recent_issues: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_issues_by_assignee(args: Dict[str, Any]) -> List[TextContent]:
    """Get issues by assignee."""
    assignee = args.get("assignee")
    limit = min(args.get("limit", 50), 100)
    
    if not assignee:
        return [TextContent(type="text", text="Error: Missing required 'assignee' parameter")]
    
    logger.info(f"Getting issues for assignee: {sanitize_for_log(assignee)}, limit: {limit}")
    
    # Build JQL - assignee is safe to use in JQL
    jql = f"assignee = {assignee} ORDER BY updated DESC"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search",
                params={"jql": jql, "maxResults": limit},
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues_data = data.get("issues", [])
                
                issues = []
                for issue in issues_data:
                    try:
                        fields = issue.get("fields", {})
                        issue_info = {
                            "key": issue.get("key", "Unknown"),
                            "summary": fields.get("summary", "No summary"),
                            "status": fields.get("status", {}).get("name", "Unknown"),
                            "issueType": fields.get("issuetype", {}).get("name", "Unknown"),
                            "priority": fields.get("priority", {}).get("name", "None") if fields.get("priority") else "None"
                        }
                        issues.append(issue_info)
                    except Exception as e:
                        logger.error(f"Error processing issue {sanitize_for_log(issue.get('key', 'unknown'))}: {e}")
                        continue
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"issues": issues}, indent=2)
                )]
            elif response.status_code == 400:
                return [TextContent(type="text", text="Error: Invalid assignee or JQL query")]
            elif response.status_code == 401:
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_issues_by_assignee: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_projects(args: Dict[str, Any]) -> List[TextContent]:
    """Get all accessible JIRA projects."""
    logger.info("Getting JIRA projects")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/project",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            logger.info(f"JIRA API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    projects_data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response from JIRA API: {e}")
                    return [TextContent(type="text", text="Error: Invalid response from JIRA API")]
                
                projects = []
                for project in projects_data:
                    try:
                        project_info = {
                            "key": project.get("key", "Unknown"),
                            "name": project.get("name", "No name"),
                            "projectTypeKey": project.get("projectTypeKey", "Unknown"),
                            "lead": project.get("lead", {}).get("displayName", "Unknown") if project.get("lead") else "Unknown"
                        }
                        projects.append(project_info)
                    except Exception as e:
                        logger.error(f"Error processing project {sanitize_for_log(project.get('key', 'unknown'))}: {e}")
                        continue
                
                logger.info(f"Retrieved {len(projects)} projects")
                return [TextContent(
                    type="text",
                    text=json.dumps({"projects": projects}, indent=2)
                )]
            elif response.status_code == 401:
                logger.error("JIRA authentication failed (401)")
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                logger.error("JIRA access denied (403)")
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                logger.error(f"JIRA API error: {response.status_code}")
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code}. Check JIRA URL and network connectivity.")]
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_projects: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server."""
    try:
        logger.info(f"Starting JIRA MCP Server (verbose logging: {VERBOSE_LOGGING})")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)

def main():
    """Main entry point for console script"""
    asyncio.run(run_server())

async def run_server():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    main()