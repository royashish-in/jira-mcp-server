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
        ),
        Tool(
            name="create_issue",
            description="Create a new JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key (e.g., KW)"},
                    "summary": {"type": "string", "description": "Issue title/summary"},
                    "description": {"type": "string", "description": "Detailed description"},
                    "issue_type": {"type": "string", "description": "Issue type (Task, Bug, Story, etc.)"},
                    "priority": {"type": "string", "description": "Priority (Low, Medium, High, Critical)"},
                    "assignee": {"type": "string", "description": "Username to assign (optional)"}
                },
                "required": ["project", "summary"]
            }
        ),
        Tool(
            name="update_issue",
            description="Update an existing JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"},
                    "summary": {"type": "string", "description": "New issue title/summary"},
                    "description": {"type": "string", "description": "New detailed description"},
                    "priority": {"type": "string", "description": "New priority (Low, Medium, High, Critical)"},
                    "assignee": {"type": "string", "description": "New assignee username"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="advanced_jql_search",
            description="Advanced JIRA search with custom fields and expand options",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL query string"},
                    "fields": {"type": "array", "items": {"type": "string"}, "description": "Specific fields to return"},
                    "expand": {"type": "array", "items": {"type": "string"}, "description": "Additional data to expand (changelog, transitions, etc.)"},
                    "limit": {"type": "integer", "description": "Max results", "minimum": 1, "maximum": 100}
                },
                "required": ["jql"]
            }
        ),
        Tool(
            name="transition_issue",
            description="Transition JIRA issue to different status",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"},
                    "transition": {"type": "string", "description": "Transition name or ID"}
                },
                "required": ["key", "transition"]
            }
        ),
        Tool(
            name="get_transitions",
            description="Get available transitions for JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="add_comment",
            description="Add comment to JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"},
                    "comment": {"type": "string", "description": "Comment text"}
                },
                "required": ["key", "comment"]
            }
        ),
        Tool(
            name="list_attachments",
            description="List attachments for JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="get_issue_types",
            description="Get available issue types for project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key (e.g., KW)"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="bulk_update_issues",
            description="Update multiple JIRA issues at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "Array of issue keys"},
                    "updates": {"type": "object", "description": "Fields to update (priority, assignee, etc.)"}
                },
                "required": ["keys", "updates"]
            }
        ),
        Tool(
            name="upload_attachment",
            description="Upload file attachment to JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"},
                    "file_path": {"type": "string", "description": "Path to file to upload"}
                },
                "required": ["key", "file_path"]
            }
        ),
        Tool(
            name="download_attachment",
            description="Download attachment from JIRA issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "attachment_url": {"type": "string", "description": "Attachment URL from list_attachments"},
                    "save_path": {"type": "string", "description": "Path to save downloaded file"}
                },
                "required": ["attachment_url", "save_path"]
            }
        ),
        Tool(
            name="bulk_transition_issues",
            description="Transition multiple issues at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "Array of issue keys"},
                    "transition": {"type": "string", "description": "Transition name or ID"}
                },
                "required": ["keys", "transition"]
            }
        ),
        Tool(
            name="assign_issue",
            description="Assign issue to user",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "JIRA issue key (e.g., KW-41)"},
                    "assignee": {"type": "string", "description": "Username to assign (or null to unassign)"}
                },
                "required": ["key", "assignee"]
            }
        ),
        Tool(
            name="get_project_components",
            description="Get project components",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key (e.g., KW)"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="get_project_versions",
            description="Get project versions/releases",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "JIRA project key (e.g., KW)"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="get_custom_fields",
            description="Get available custom fields",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_sprints",
            description="Get sprints for agile board",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "Agile board ID"}
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="add_to_sprint",
            description="Add issues to sprint",
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_id": {"type": "string", "description": "Sprint ID"},
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "Array of issue keys"}
                },
                "required": ["sprint_id", "keys"]
            }
        ),
        Tool(
            name="get_boards",
            description="Get available agile boards",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_sprint_issues",
            description="Get issues in specific sprint",
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_id": {"type": "string", "description": "Sprint ID"}
                },
                "required": ["sprint_id"]
            }
        ),
        Tool(
            name="link_issues",
            description="Create link between issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "inward_key": {"type": "string", "description": "Source issue key"},
                    "outward_key": {"type": "string", "description": "Target issue key"},
                    "link_type": {"type": "string", "description": "Link type (Blocks, Relates, etc.)"}
                },
                "required": ["inward_key", "outward_key", "link_type"]
            }
        ),
        Tool(
            name="get_subtasks",
            description="Get subtasks of an issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Parent issue key"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="add_worklog",
            description="Add time log to issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Issue key"},
                    "time_spent": {"type": "string", "description": "Time spent (e.g., '2h', '30m')"},
                    "comment": {"type": "string", "description": "Work description"}
                },
                "required": ["key", "time_spent"]
            }
        ),
        Tool(
            name="get_users",
            description="Get assignable users for project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project key"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="create_subtask",
            description="Create subtask under parent issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_key": {"type": "string", "description": "Parent issue key"},
                    "summary": {"type": "string", "description": "Subtask summary"},
                    "description": {"type": "string", "description": "Subtask description"}
                },
                "required": ["parent_key", "summary"]
            }
        ),
        Tool(
            name="list_webhooks",
            description="List configured webhooks",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="add_watcher",
            description="Add watcher to issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Issue key"},
                    "username": {"type": "string", "description": "Username to add as watcher"}
                },
                "required": ["key", "username"]
            }
        ),
        Tool(
            name="get_watchers",
            description="Get watchers of issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Issue key"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="get_issue_links",
            description="Get all linked issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Issue key"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="clone_issue",
            description="Clone/duplicate issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Source issue key"},
                    "summary": {"type": "string", "description": "New issue summary"}
                },
                "required": ["key", "summary"]
            }
        ),
        Tool(
            name="get_time_tracking_report",
            description="Get time tracking report for project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project key"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="get_project_roles",
            description="Get project roles and permissions",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project key"}
                },
                "required": ["project"]
            }
        ),
        Tool(
            name="export_issues",
            description="Export issues to specified format",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL query"},
                    "format": {"type": "string", "description": "Export format (json, csv)"}
                },
                "required": ["jql", "format"]
            }
        ),
        Tool(
            name="create_webhook",
            description="Create new webhook",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Webhook name"},
                    "url": {"type": "string", "description": "Webhook URL"},
                    "events": {"type": "array", "items": {"type": "string"}, "description": "Event types"}
                },
                "required": ["name", "url", "events"]
            }
        ),
        Tool(
            name="create_version",
            description="Create project version/release",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project key"},
                    "name": {"type": "string", "description": "Version name"},
                    "description": {"type": "string", "description": "Version description"}
                },
                "required": ["project", "name"]
            }
        ),
        Tool(
            name="get_user_permissions",
            description="Get user permissions for project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project key"},
                    "username": {"type": "string", "description": "Username"}
                },
                "required": ["project", "username"]
            }
        ),
        Tool(
            name="get_workflows",
            description="Get available workflows",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="release_version",
            description="Mark version as released",
            inputSchema={
                "type": "object",
                "properties": {
                    "version_id": {"type": "string", "description": "Version ID"},
                    "release_date": {"type": "string", "description": "Release date (YYYY-MM-DD)"}
                },
                "required": ["version_id"]
            }
        ),
        Tool(
            name="get_burndown_data",
            description="Get sprint burndown data",
            inputSchema={
                "type": "object",
                "properties": {
                    "sprint_id": {"type": "string", "description": "Sprint ID"}
                },
                "required": ["sprint_id"]
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
        elif name == "create_issue":
            return await create_issue(arguments)
        elif name == "update_issue":
            return await update_issue(arguments)
        elif name == "advanced_jql_search":
            return await advanced_jql_search(arguments)
        elif name == "transition_issue":
            return await transition_issue(arguments)
        elif name == "get_transitions":
            return await get_transitions(arguments)
        elif name == "add_comment":
            return await add_comment(arguments)
        elif name == "list_attachments":
            return await list_attachments(arguments)
        elif name == "get_issue_types":
            return await get_issue_types(arguments)
        elif name == "bulk_update_issues":
            return await bulk_update_issues(arguments)
        elif name == "upload_attachment":
            return await upload_attachment(arguments)
        elif name == "download_attachment":
            return await download_attachment(arguments)
        elif name == "bulk_transition_issues":
            return await bulk_transition_issues(arguments)
        elif name == "assign_issue":
            return await assign_issue(arguments)
        elif name == "get_project_components":
            return await get_project_components(arguments)
        elif name == "get_project_versions":
            return await get_project_versions(arguments)
        elif name == "get_custom_fields":
            return await get_custom_fields(arguments)
        elif name == "get_sprints":
            return await get_sprints(arguments)
        elif name == "add_to_sprint":
            return await add_to_sprint(arguments)
        elif name == "get_boards":
            return await get_boards(arguments)
        elif name == "get_sprint_issues":
            return await get_sprint_issues(arguments)
        elif name == "link_issues":
            return await link_issues(arguments)
        elif name == "get_subtasks":
            return await get_subtasks(arguments)
        elif name == "add_worklog":
            return await add_worklog(arguments)
        elif name == "get_users":
            return await get_users(arguments)
        elif name == "create_subtask":
            return await create_subtask(arguments)
        elif name == "list_webhooks":
            return await list_webhooks(arguments)
        elif name == "add_watcher":
            return await add_watcher(arguments)
        elif name == "get_watchers":
            return await get_watchers(arguments)
        elif name == "get_issue_links":
            return await get_issue_links(arguments)
        elif name == "clone_issue":
            return await clone_issue(arguments)
        elif name == "get_time_tracking_report":
            return await get_time_tracking_report(arguments)
        elif name == "get_project_roles":
            return await get_project_roles(arguments)
        elif name == "export_issues":
            return await export_issues(arguments)
        elif name == "create_webhook":
            return await create_webhook(arguments)
        elif name == "create_version":
            return await create_version(arguments)
        elif name == "get_user_permissions":
            return await get_user_permissions(arguments)
        elif name == "get_workflows":
            return await get_workflows(arguments)
        elif name == "release_version":
            return await release_version(arguments)
        elif name == "get_burndown_data":
            return await get_burndown_data(arguments)
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

async def create_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Create a new JIRA issue."""
    project = args.get("project")
    summary = args.get("summary")
    description = args.get("description", "")
    issue_type = args.get("issue_type", "Task")
    priority = args.get("priority", "Medium")
    assignee = args.get("assignee", "")
    
    if not project or not summary:
        return [TextContent(type="text", text="Error: Missing required parameters 'project' and 'summary'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Creating issue in project: {sanitize_for_log(project)}")
    
    # Prepare issue data with Atlassian Document Format for description
    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": description
                    }
                ]
            }
        ]
    } if description else None
    
    issue_data = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "priority": {"name": priority}
        }
    }
    
    # Add description in ADF format if provided
    if description_adf:
        issue_data["fields"]["description"] = description_adf
    
    # Add assignee if provided
    if assignee:
        issue_data["fields"]["assignee"] = {"name": assignee}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue",
                json=issue_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                created_issue = response.json()
                issue_key = created_issue["key"]
                
                # Get full issue details
                detail_response = await client.get(
                    f"{JIRA_URL}/rest/api/3/issue/{issue_key}",
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                
                if detail_response.status_code == 200:
                    issue = detail_response.json()
                    fields = issue.get("fields", {})
                    
                    result = f"✅ Created issue {issue_key}: {fields.get('summary', 'No summary')}\n"
                    result += f"Type: {fields.get('issuetype', {}).get('name', 'Unknown')}\n"
                    result += f"Status: {fields.get('status', {}).get('name', 'Unknown')}\n"
                    result += f"Priority: {fields.get('priority', {}).get('name', 'Unknown')}\n"
                    if fields.get('assignee'):
                        result += f"Assignee: {fields['assignee'].get('displayName', 'Unknown')}\n"
                    result += f"URL: {JIRA_URL}/browse/{issue_key}"
                    
                    logger.info(f"Created JIRA issue: {issue_key}")
                    return [TextContent(type="text", text=result)]
                else:
                    return [TextContent(type="text", text=f"Issue created ({issue_key}) but failed to fetch details")]
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = f"Invalid issue data: {error_data.get('errors', response.text)}"
                return [TextContent(type="text", text=error_msg)]
            elif response.status_code == 401:
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in create_issue: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def update_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Update an existing JIRA issue."""
    key = args.get("key")
    summary = args.get("summary")
    description = args.get("description")
    priority = args.get("priority")
    assignee = args.get("assignee")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Updating issue: {sanitize_for_log(key)}")
    
    # Build update data with only provided fields
    update_data = {"fields": {}}
    
    if summary:
        update_data["fields"]["summary"] = summary
    
    if description:
        update_data["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description
                        }
                    ]
                }
            ]
        }
    
    if priority:
        update_data["fields"]["priority"] = {"name": priority}
    
    if assignee:
        update_data["fields"]["assignee"] = {"name": assignee}
    
    if not update_data["fields"]:
        return [TextContent(type="text", text="Error: No fields provided to update")]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.put(
                f"{JIRA_URL}/rest/api/3/issue/{key}",
                json=update_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 204:
                # Get updated issue details
                detail_response = await client.get(
                    f"{JIRA_URL}/rest/api/3/issue/{key}",
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                
                if detail_response.status_code == 200:
                    issue = detail_response.json()
                    fields = issue.get("fields", {})
                    
                    result = f"✅ Updated issue {key}: {fields.get('summary', 'No summary')}\n"
                    result += f"Type: {fields.get('issuetype', {}).get('name', 'Unknown')}\n"
                    result += f"Status: {fields.get('status', {}).get('name', 'Unknown')}\n"
                    result += f"Priority: {fields.get('priority', {}).get('name', 'Unknown')}\n"
                    if fields.get('assignee'):
                        result += f"Assignee: {fields['assignee'].get('displayName', 'Unknown')}\n"
                    result += f"URL: {JIRA_URL}/browse/{key}"
                    
                    logger.info(f"Updated JIRA issue: {key}")
                    return [TextContent(type="text", text=result)]
                else:
                    return [TextContent(type="text", text=f"Issue updated but failed to fetch details")]
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = f"Invalid update data: {error_data.get('errors', response.text)}"
                return [TextContent(type="text", text=error_msg)]
            elif response.status_code == 404:
                return [TextContent(type="text", text=f"Error: Issue '{key}' not found. Check issue key and permissions.")]
            elif response.status_code == 401:
                return [TextContent(type="text", text="Error: Authentication failed (401). Generate new API token at https://id.atlassian.com/manage-profile/security/api-tokens")]
            elif response.status_code == 403:
                return [TextContent(type="text", text="Error: Access denied (403). Check JIRA project permissions and API access.")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in update_issue: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def advanced_jql_search(args: Dict[str, Any]) -> List[TextContent]:
    """Advanced JIRA search with custom fields and expand options."""
    jql = args.get("jql")
    fields = args.get("fields", [])
    expand = args.get("expand", [])
    limit = min(args.get("limit", 50), 100)
    
    if not jql:
        return [TextContent(type="text", text="Error: Missing required 'jql' parameter")]
    
    logger.info(f"Advanced JQL search: {sanitize_for_log(jql)}, limit: {limit}")
    
    # Build query parameters
    params = {
        "jql": jql,
        "maxResults": limit
    }
    
    if fields:
        params["fields"] = ",".join(fields)
    
    if expand:
        params["expand"] = ",".join(expand)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search",
                params=params,
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
                total = data.get("total", 0)
                logger.info(f"Found {len(issues_data)} of {total} issues")
                
                # Process issues with requested fields
                issues = []
                for issue in issues_data:
                    try:
                        issue_info = {
                            "key": issue.get("key", "Unknown"),
                            "self": issue.get("self", "")
                        }
                        
                        # Add requested fields or default fields
                        fields_data = issue.get("fields", {})
                        if fields:
                            for field in fields:
                                if field in fields_data:
                                    if field == "assignee" and fields_data[field]:
                                        issue_info[field] = fields_data[field].get("displayName", "Unknown")
                                    elif field in ["status", "priority", "issuetype"] and fields_data[field]:
                                        issue_info[field] = fields_data[field].get("name", "Unknown")
                                    else:
                                        issue_info[field] = fields_data[field]
                                else:
                                    issue_info[field] = None
                        else:
                            # Default fields
                            issue_info.update({
                                "summary": fields_data.get("summary", "No summary"),
                                "status": fields_data.get("status", {}).get("name", "Unknown"),
                                "issueType": fields_data.get("issuetype", {}).get("name", "Unknown"),
                                "priority": fields_data.get("priority", {}).get("name", "None") if fields_data.get("priority") else "None",
                                "assignee": fields_data.get("assignee", {}).get("displayName", "Unassigned") if fields_data.get("assignee") else "Unassigned"
                            })
                        
                        # Add expanded data if requested
                        if expand:
                            for exp in expand:
                                if exp in issue:
                                    issue_info[exp] = issue[exp]
                        
                        issues.append(issue_info)
                    except Exception as e:
                        logger.error(f"Error processing issue {sanitize_for_log(issue.get('key', 'unknown'))}: {e}")
                        continue
                
                result = {
                    "total": total,
                    "maxResults": limit,
                    "startAt": data.get("startAt", 0),
                    "issues": issues
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
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
            logger.error(f"Unexpected error in advanced_jql_search: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def transition_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Transition JIRA issue to different status."""
    key = args.get("key")
    transition = args.get("transition")
    
    if not key or not transition:
        return [TextContent(type="text", text="Error: Missing required parameters 'key' and 'transition'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Transitioning issue {sanitize_for_log(key)} to {sanitize_for_log(transition)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get available transitions
            transitions_response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}/transitions",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if transitions_response.status_code != 200:
                return [TextContent(type="text", text=f"Error: Failed to get transitions - {transitions_response.status_code}")]
            
            transitions_data = transitions_response.json()
            available_transitions = transitions_data.get("transitions", [])
            
            # Find matching transition
            transition_id = None
            for t in available_transitions:
                if (t.get("name", "").lower() == transition.lower() or 
                    t.get("id") == transition):
                    transition_id = t.get("id")
                    break
            
            if not transition_id:
                available = [t.get("name") for t in available_transitions]
                return [TextContent(type="text", text=f"Error: Transition '{transition}' not available. Available: {', '.join(available)}")]
            
            # Perform transition
            transition_data = {
                "transition": {"id": transition_id}
            }
            
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue/{key}/transitions",
                json=transition_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 204:
                # Get updated issue details
                detail_response = await client.get(
                    f"{JIRA_URL}/rest/api/3/issue/{key}",
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                
                if detail_response.status_code == 200:
                    issue = detail_response.json()
                    fields = issue.get("fields", {})
                    
                    result = f"✅ Transitioned issue {key} to {fields.get('status', {}).get('name', 'Unknown')}\n"
                    result += f"Summary: {fields.get('summary', 'No summary')}\n"
                    result += f"URL: {JIRA_URL}/browse/{key}"
                    
                    logger.info(f"Transitioned JIRA issue: {key}")
                    return [TextContent(type="text", text=result)]
                else:
                    return [TextContent(type="text", text=f"Issue transitioned but failed to fetch details")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in transition_issue: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_transitions(args: Dict[str, Any]) -> List[TextContent]:
    """Get available transitions for JIRA issue."""
    key = args.get("key")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Getting transitions for issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}/transitions",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                transitions = data.get("transitions", [])
                
                result = {
                    "issue": key,
                    "availableTransitions": [
                        {
                            "id": t.get("id"),
                            "name": t.get("name"),
                            "to": t.get("to", {}).get("name")
                        } for t in transitions
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_transitions: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def add_comment(args: Dict[str, Any]) -> List[TextContent]:
    """Add comment to JIRA issue."""
    key = args.get("key")
    comment = args.get("comment")
    
    if not key or not comment:
        return [TextContent(type="text", text="Error: Missing required parameters 'key' and 'comment'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Adding comment to issue: {sanitize_for_log(key)}")
    
    # Prepare comment in ADF format
    comment_data = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment
                        }
                    ]
                }
            ]
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue/{key}/comment",
                json=comment_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                comment_response = response.json()
                result = f"✅ Added comment to issue {key}\n"
                result += f"Comment ID: {comment_response.get('id')}\n"
                result += f"Author: {comment_response.get('author', {}).get('displayName', 'Unknown')}\n"
                result += f"URL: {JIRA_URL}/browse/{key}"
                
                logger.info(f"Added comment to JIRA issue: {key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in add_comment: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def list_attachments(args: Dict[str, Any]) -> List[TextContent]:
    """List attachments for JIRA issue."""
    key = args.get("key")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Listing attachments for issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}?fields=attachment",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                attachments = data.get("fields", {}).get("attachment", [])
                
                result = {
                    "issue": key,
                    "attachmentCount": len(attachments),
                    "attachments": [
                        {
                            "id": att.get("id"),
                            "filename": att.get("filename"),
                            "size": att.get("size"),
                            "mimeType": att.get("mimeType"),
                            "created": att.get("created"),
                            "author": att.get("author", {}).get("displayName"),
                            "content": att.get("content")
                        } for att in attachments
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in list_attachments: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_issue_types(args: Dict[str, Any]) -> List[TextContent]:
    """Get available issue types for project."""
    project = args.get("project")
    
    if not project:
        return [TextContent(type="text", text="Error: Missing required parameter 'project'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting issue types for project: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/project/{project}",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issue_types = data.get("issueTypes", [])
                
                result = {
                    "project": project,
                    "issueTypes": [
                        {
                            "id": it.get("id"),
                            "name": it.get("name"),
                            "description": it.get("description"),
                            "iconUrl": it.get("iconUrl")
                        } for it in issue_types
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_issue_types: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def bulk_update_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Update multiple JIRA issues at once."""
    keys = args.get("keys", [])
    updates = args.get("updates", {})
    
    if not keys or not updates:
        return [TextContent(type="text", text="Error: Missing required parameters 'keys' and 'updates'")]
    
    # Validate all keys
    for key in keys:
        if not validate_issue_key(key):
            return [TextContent(type="text", text=f"Error: Invalid issue key format: {key}")]
    
    logger.info(f"Bulk updating {len(keys)} issues")
    
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for key in keys:
            try:
                # Build update data
                update_data = {"fields": {}}
                
                if "priority" in updates:
                    update_data["fields"]["priority"] = {"name": updates["priority"]}
                if "assignee" in updates:
                    update_data["fields"]["assignee"] = {"name": updates["assignee"]}
                if "summary" in updates:
                    update_data["fields"]["summary"] = updates["summary"]
                
                response = await client.put(
                    f"{JIRA_URL}/rest/api/3/issue/{key}",
                    json=update_data,
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                
                if response.status_code == 204:
                    results.append(f"✅ {key}: Updated successfully")
                else:
                    results.append(f"❌ {key}: Failed - {response.status_code}")
                    
            except Exception as e:
                results.append(f"❌ {key}: Error - {str(e)}")
    
    result_text = f"Bulk update results ({len(keys)} issues):\n" + "\n".join(results)
    return [TextContent(type="text", text=result_text)]

async def upload_attachment(args: Dict[str, Any]) -> List[TextContent]:
    """Upload file attachment to JIRA issue."""
    key = args.get("key")
    file_path = args.get("file_path")
    
    if not key or not file_path:
        return [TextContent(type="text", text="Error: Missing required parameters 'key' and 'file_path'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    if not os.path.exists(file_path):
        return [TextContent(type="text", text=f"Error: File not found: {file_path}")]
    
    logger.info(f"Uploading attachment to issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                
                response = await client.post(
                    f"{JIRA_URL}/rest/api/3/issue/{key}/attachments",
                    files=files,
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN),
                    headers={'X-Atlassian-Token': 'no-check'}
                )
            
            if response.status_code == 200:
                attachments = response.json()
                if attachments:
                    att = attachments[0]
                    result = f"✅ Uploaded attachment to issue {key}\n"
                    result += f"Filename: {att.get('filename')}\n"
                    result += f"Size: {att.get('size')} bytes\n"
                    result += f"ID: {att.get('id')}\n"
                    result += f"URL: {JIRA_URL}/browse/{key}"
                    
                    logger.info(f"Uploaded attachment to JIRA issue: {key}")
                    return [TextContent(type="text", text=result)]
                else:
                    return [TextContent(type="text", text="Upload completed but no attachment data returned")]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in upload_attachment: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def download_attachment(args: Dict[str, Any]) -> List[TextContent]:
    """Download attachment from JIRA issue."""
    attachment_url = args.get("attachment_url")
    save_path = args.get("save_path")
    
    if not attachment_url or not save_path:
        return [TextContent(type="text", text="Error: Missing required parameters 'attachment_url' and 'save_path'")]
    
    logger.info(f"Downloading attachment to: {sanitize_for_log(save_path)}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.get(
                attachment_url,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                result = f"✅ Downloaded attachment\n"
                result += f"Saved to: {save_path}\n"
                result += f"Size: {len(response.content)} bytes"
                
                logger.info(f"Downloaded attachment to: {save_path}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in download_attachment: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def bulk_transition_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Transition multiple issues at once."""
    keys = args.get("keys", [])
    transition = args.get("transition")
    
    if not keys or not transition:
        return [TextContent(type="text", text="Error: Missing required parameters 'keys' and 'transition'")]
    
    for key in keys:
        if not validate_issue_key(key):
            return [TextContent(type="text", text=f"Error: Invalid issue key format: {key}")]
    
    logger.info(f"Bulk transitioning {len(keys)} issues to {sanitize_for_log(transition)}")
    
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for key in keys:
            try:
                # Get transitions for this issue
                transitions_response = await client.get(
                    f"{JIRA_URL}/rest/api/3/issue/{key}/transitions",
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                
                if transitions_response.status_code != 200:
                    results.append(f"❌ {key}: Failed to get transitions")
                    continue
                
                transitions_data = transitions_response.json()
                available_transitions = transitions_data.get("transitions", [])
                
                # Find matching transition
                transition_id = None
                for t in available_transitions:
                    if (t.get("name", "").lower() == transition.lower() or 
                        t.get("id") == transition):
                        transition_id = t.get("id")
                        break
                
                if not transition_id:
                    results.append(f"❌ {key}: Transition '{transition}' not available")
                    continue
                
                # Perform transition
                transition_data = {"transition": {"id": transition_id}}
                response = await client.post(
                    f"{JIRA_URL}/rest/api/3/issue/{key}/transitions",
                    json=transition_data,
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                
                if response.status_code == 204:
                    results.append(f"✅ {key}: Transitioned to {transition}")
                else:
                    results.append(f"❌ {key}: Failed - {response.status_code}")
                    
            except Exception as e:
                results.append(f"❌ {key}: Error - {str(e)}")
    
    result_text = f"Bulk transition results ({len(keys)} issues):\n" + "\n".join(results)
    return [TextContent(type="text", text=result_text)]

async def assign_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Assign issue to user."""
    key = args.get("key")
    assignee = args.get("assignee")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Assigning issue {sanitize_for_log(key)} to {sanitize_for_log(assignee)}")
    
    update_data = {
        "fields": {
            "assignee": {"name": assignee} if assignee and assignee.lower() != "null" else None
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.put(
                f"{JIRA_URL}/rest/api/3/issue/{key}",
                json=update_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 204:
                assignee_text = assignee if assignee and assignee.lower() != "null" else "Unassigned"
                result = f"✅ Assigned issue {key} to {assignee_text}\n"
                result += f"URL: {JIRA_URL}/browse/{key}"
                
                logger.info(f"Assigned JIRA issue: {key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in assign_issue: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_project_components(args: Dict[str, Any]) -> List[TextContent]:
    """Get project components."""
    project = args.get("project")
    
    if not project:
        return [TextContent(type="text", text="Error: Missing required parameter 'project'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting components for project: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/project/{project}/components",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                components = response.json()
                
                result = {
                    "project": project,
                    "components": [
                        {
                            "id": comp.get("id"),
                            "name": comp.get("name"),
                            "description": comp.get("description"),
                            "lead": comp.get("lead", {}).get("displayName") if comp.get("lead") else None
                        } for comp in components
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_project_components: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_project_versions(args: Dict[str, Any]) -> List[TextContent]:
    """Get project versions/releases."""
    project = args.get("project")
    
    if not project:
        return [TextContent(type="text", text="Error: Missing required parameter 'project'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting versions for project: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/project/{project}/versions",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                versions = response.json()
                
                result = {
                    "project": project,
                    "versions": [
                        {
                            "id": ver.get("id"),
                            "name": ver.get("name"),
                            "description": ver.get("description"),
                            "released": ver.get("released"),
                            "releaseDate": ver.get("releaseDate")
                        } for ver in versions
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_project_versions: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_custom_fields(args: Dict[str, Any]) -> List[TextContent]:
    """Get available custom fields."""
    logger.info("Getting custom fields")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/field",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                fields = response.json()
                custom_fields = [f for f in fields if f.get("custom", False)]
                
                result = {
                    "totalCustomFields": len(custom_fields),
                    "customFields": [
                        {
                            "id": field.get("id"),
                            "name": field.get("name"),
                            "description": field.get("description"),
                            "fieldType": field.get("schema", {}).get("type")
                        } for field in custom_fields
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_custom_fields: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_sprints(args: Dict[str, Any]) -> List[TextContent]:
    """Get sprints for agile board."""
    board_id = args.get("board_id")
    
    if not board_id:
        return [TextContent(type="text", text="Error: Missing required parameter 'board_id'")]
    
    logger.info(f"Getting sprints for board: {sanitize_for_log(board_id)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                sprints = data.get("values", [])
                
                result = {
                    "boardId": board_id,
                    "sprints": [
                        {
                            "id": sprint.get("id"),
                            "name": sprint.get("name"),
                            "state": sprint.get("state"),
                            "startDate": sprint.get("startDate"),
                            "endDate": sprint.get("endDate"),
                            "goal": sprint.get("goal")
                        } for sprint in sprints
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_sprints: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def add_to_sprint(args: Dict[str, Any]) -> List[TextContent]:
    """Add issues to sprint."""
    sprint_id = args.get("sprint_id")
    keys = args.get("keys", [])
    
    if not sprint_id or not keys:
        return [TextContent(type="text", text="Error: Missing required parameters 'sprint_id' and 'keys'")]
    
    for key in keys:
        if not validate_issue_key(key):
            return [TextContent(type="text", text=f"Error: Invalid issue key format: {key}")]
    
    logger.info(f"Adding {len(keys)} issues to sprint {sanitize_for_log(sprint_id)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get issue IDs
            issue_ids = []
            for key in keys:
                issue_response = await client.get(
                    f"{JIRA_URL}/rest/api/3/issue/{key}?fields=id",
                    auth=(JIRA_USERNAME, JIRA_API_TOKEN)
                )
                if issue_response.status_code == 200:
                    issue_data = issue_response.json()
                    issue_ids.append(issue_data.get("id"))
            
            if not issue_ids:
                return [TextContent(type="text", text="Error: No valid issues found")]
            
            # Add to sprint
            sprint_data = {"issues": issue_ids}
            response = await client.post(
                f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue",
                json=sprint_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 204:
                result = f"✅ Added {len(issue_ids)} issues to sprint {sprint_id}\n"
                result += f"Issues: {', '.join(keys)}"
                
                logger.info(f"Added issues to sprint: {sprint_id}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in add_to_sprint: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_boards(args: Dict[str, Any]) -> List[TextContent]:
    """Get available agile boards."""
    logger.info("Getting agile boards")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/agile/1.0/board",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                boards = data.get("values", [])
                
                result = {
                    "boards": [
                        {
                            "id": board.get("id"),
                            "name": board.get("name"),
                            "type": board.get("type"),
                            "location": board.get("location", {}).get("name")
                        } for board in boards
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_boards: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_sprint_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Get issues in specific sprint."""
    sprint_id = args.get("sprint_id")
    
    if not sprint_id:
        return [TextContent(type="text", text="Error: Missing required parameter 'sprint_id'")]
    
    logger.info(f"Getting issues for sprint: {sanitize_for_log(sprint_id)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                result = {
                    "sprintId": sprint_id,
                    "issueCount": len(issues),
                    "issues": [
                        {
                            "key": issue.get("key"),
                            "summary": issue.get("fields", {}).get("summary"),
                            "status": issue.get("fields", {}).get("status", {}).get("name"),
                            "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName") if issue.get("fields", {}).get("assignee") else "Unassigned"
                        } for issue in issues
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_sprint_issues: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def link_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Create link between issues."""
    inward_key = args.get("inward_key")
    outward_key = args.get("outward_key")
    link_type = args.get("link_type")
    
    if not inward_key or not outward_key or not link_type:
        return [TextContent(type="text", text="Error: Missing required parameters")]
    
    if not validate_issue_key(inward_key) or not validate_issue_key(outward_key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Linking issues {sanitize_for_log(inward_key)} -> {sanitize_for_log(outward_key)}")
    
    link_data = {
        "type": {"name": link_type},
        "inwardIssue": {"key": inward_key},
        "outwardIssue": {"key": outward_key}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issueLink",
                json=link_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                result = f"✅ Linked issues: {inward_key} {link_type} {outward_key}\n"
                result += f"Link type: {link_type}\n"
                result += f"View: {JIRA_URL}/browse/{inward_key}"
                
                logger.info(f"Linked JIRA issues: {inward_key} -> {outward_key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in link_issues: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_subtasks(args: Dict[str, Any]) -> List[TextContent]:
    """Get subtasks of an issue."""
    key = args.get("key")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Getting subtasks for issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}?fields=subtasks",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                subtasks = data.get("fields", {}).get("subtasks", [])
                
                result = {
                    "parentIssue": key,
                    "subtaskCount": len(subtasks),
                    "subtasks": [
                        {
                            "key": subtask.get("key"),
                            "summary": subtask.get("fields", {}).get("summary"),
                            "status": subtask.get("fields", {}).get("status", {}).get("name"),
                            "assignee": subtask.get("fields", {}).get("assignee", {}).get("displayName") if subtask.get("fields", {}).get("assignee") else "Unassigned"
                        } for subtask in subtasks
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_subtasks: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def add_worklog(args: Dict[str, Any]) -> List[TextContent]:
    """Add time log to issue."""
    key = args.get("key")
    time_spent = args.get("time_spent")
    comment = args.get("comment", "")
    
    if not key or not time_spent:
        return [TextContent(type="text", text="Error: Missing required parameters 'key' and 'time_spent'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Adding worklog to issue: {sanitize_for_log(key)}")
    
    worklog_data = {
        "timeSpent": time_spent,
        "comment": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment
                        }
                    ]
                }
            ]
        } if comment else None
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue/{key}/worklog",
                json=worklog_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                worklog = response.json()
                result = f"✅ Added worklog to issue {key}\n"
                result += f"Time spent: {worklog.get('timeSpent')}\n"
                result += f"Author: {worklog.get('author', {}).get('displayName')}\n"
                result += f"URL: {JIRA_URL}/browse/{key}"
                
                logger.info(f"Added worklog to JIRA issue: {key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in add_worklog: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_users(args: Dict[str, Any]) -> List[TextContent]:
    """Get assignable users for project."""
    project = args.get("project")
    
    if not project:
        return [TextContent(type="text", text="Error: Missing required parameter 'project'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting users for project: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/user/assignable/search?project={project}",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                users = response.json()
                
                result = {
                    "project": project,
                    "userCount": len(users),
                    "users": [
                        {
                            "accountId": user.get("accountId"),
                            "displayName": user.get("displayName"),
                            "emailAddress": user.get("emailAddress"),
                            "active": user.get("active")
                        } for user in users
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_users: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def create_subtask(args: Dict[str, Any]) -> List[TextContent]:
    """Create subtask under parent issue."""
    parent_key = args.get("parent_key")
    summary = args.get("summary")
    description = args.get("description", "")
    
    if not parent_key or not summary:
        return [TextContent(type="text", text="Error: Missing required parameters 'parent_key' and 'summary'")]
    
    if not validate_issue_key(parent_key):
        return [TextContent(type="text", text="Error: Invalid parent issue key format")]
    
    logger.info(f"Creating subtask for parent: {sanitize_for_log(parent_key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get parent issue to determine project
            parent_response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{parent_key}?fields=project",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if parent_response.status_code != 200:
                return [TextContent(type="text", text=f"Error: Parent issue not found - {parent_response.status_code}")]
            
            parent_data = parent_response.json()
            project_key = parent_data.get("fields", {}).get("project", {}).get("key")
            
            # Create subtask
            subtask_data = {
                "fields": {
                    "project": {"key": project_key},
                    "parent": {"key": parent_key},
                    "summary": summary,
                    "issuetype": {"name": "Sub-task"},
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": description
                                    }
                                ]
                            }
                        ]
                    } if description else None
                }
            }
            
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue",
                json=subtask_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                created_subtask = response.json()
                subtask_key = created_subtask["key"]
                
                result = f"✅ Created subtask {subtask_key} under {parent_key}\n"
                result += f"Summary: {summary}\n"
                result += f"URL: {JIRA_URL}/browse/{subtask_key}"
                
                logger.info(f"Created JIRA subtask: {subtask_key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in create_subtask: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def list_webhooks(args: Dict[str, Any]) -> List[TextContent]:
    """List configured webhooks."""
    logger.info("Listing webhooks")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/webhooks/1.0/webhook",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                webhooks = response.json()
                
                result = {
                    "webhookCount": len(webhooks),
                    "webhooks": [
                        {
                            "name": webhook.get("name"),
                            "url": webhook.get("url"),
                            "events": webhook.get("events"),
                            "enabled": webhook.get("enabled")
                        } for webhook in webhooks
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in list_webhooks: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def add_watcher(args: Dict[str, Any]) -> List[TextContent]:
    """Add watcher to issue."""
    key = args.get("key")
    username = args.get("username")
    
    if not key or not username:
        return [TextContent(type="text", text="Error: Missing required parameters 'key' and 'username'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Adding watcher to issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue/{key}/watchers",
                data=f'"{username}"',
                auth=(JIRA_USERNAME, JIRA_API_TOKEN),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                result = f"✅ Added watcher to issue {key}\n"
                result += f"Watcher: {username}\n"
                result += f"URL: {JIRA_URL}/browse/{key}"
                
                logger.info(f"Added watcher to JIRA issue: {key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in add_watcher: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_watchers(args: Dict[str, Any]) -> List[TextContent]:
    """Get watchers of issue."""
    key = args.get("key")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Getting watchers for issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}/watchers",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                watchers = data.get("watchers", [])
                
                result = {
                    "issue": key,
                    "watcherCount": len(watchers),
                    "watchers": [
                        {
                            "displayName": watcher.get("displayName"),
                            "emailAddress": watcher.get("emailAddress"),
                            "active": watcher.get("active")
                        } for watcher in watchers
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_watchers: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_issue_links(args: Dict[str, Any]) -> List[TextContent]:
    """Get all linked issues."""
    key = args.get("key")
    
    if not key:
        return [TextContent(type="text", text="Error: Missing required parameter 'key'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Getting issue links for: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}?fields=issuelinks",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issue_links = data.get("fields", {}).get("issuelinks", [])
                
                links = []
                for link in issue_links:
                    link_type = link.get("type", {}).get("name", "Unknown")
                    if "outwardIssue" in link:
                        target = link["outwardIssue"]
                        direction = "outward"
                    elif "inwardIssue" in link:
                        target = link["inwardIssue"]
                        direction = "inward"
                    else:
                        continue
                    
                    links.append({
                        "linkType": link_type,
                        "direction": direction,
                        "linkedIssue": {
                            "key": target.get("key"),
                            "summary": target.get("fields", {}).get("summary"),
                            "status": target.get("fields", {}).get("status", {}).get("name")
                        }
                    })
                
                result = {
                    "issue": key,
                    "linkCount": len(links),
                    "links": links
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_issue_links: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def clone_issue(args: Dict[str, Any]) -> List[TextContent]:
    """Clone/duplicate issue."""
    key = args.get("key")
    summary = args.get("summary")
    
    if not key or not summary:
        return [TextContent(type="text", text="Error: Missing required parameters 'key' and 'summary'")]
    
    if not validate_issue_key(key):
        return [TextContent(type="text", text="Error: Invalid issue key format")]
    
    logger.info(f"Cloning issue: {sanitize_for_log(key)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get original issue
            original_response = await client.get(
                f"{JIRA_URL}/rest/api/3/issue/{key}",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if original_response.status_code != 200:
                return [TextContent(type="text", text=f"Error: Original issue not found - {original_response.status_code}")]
            
            original = original_response.json()
            original_fields = original.get("fields", {})
            
            # Create clone with modified summary
            clone_data = {
                "fields": {
                    "project": original_fields.get("project"),
                    "summary": summary,
                    "description": original_fields.get("description"),
                    "issuetype": original_fields.get("issuetype"),
                    "priority": original_fields.get("priority")
                }
            }
            
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/issue",
                json=clone_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                cloned_issue = response.json()
                clone_key = cloned_issue["key"]
                
                result = f"✅ Cloned issue {key} to {clone_key}\n"
                result += f"Original: {original_fields.get('summary')}\n"
                result += f"Clone: {summary}\n"
                result += f"URL: {JIRA_URL}/browse/{clone_key}"
                
                logger.info(f"Cloned JIRA issue: {key} -> {clone_key}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in clone_issue: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_time_tracking_report(args: Dict[str, Any]) -> List[TextContent]:
    """Get time tracking report for project."""
    project = args.get("project")
    
    if not project:
        return [TextContent(type="text", text="Error: Missing required parameter 'project'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting time tracking report for project: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get issues with worklog data
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search?jql=project={project}&fields=key,summary,worklog,timetracking",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                total_logged = 0
                issue_reports = []
                
                for issue in issues:
                    fields = issue.get("fields", {})
                    worklog = fields.get("worklog", {})
                    time_tracking = fields.get("timetracking", {})
                    
                    logged_seconds = sum(w.get("timeSpentSeconds", 0) for w in worklog.get("worklogs", []))
                    total_logged += logged_seconds
                    
                    issue_reports.append({
                        "key": issue.get("key"),
                        "summary": fields.get("summary"),
                        "timeSpent": time_tracking.get("timeSpent"),
                        "originalEstimate": time_tracking.get("originalEstimate"),
                        "remainingEstimate": time_tracking.get("remainingEstimate"),
                        "loggedHours": round(logged_seconds / 3600, 2) if logged_seconds else 0
                    })
                
                result = {
                    "project": project,
                    "totalLoggedHours": round(total_logged / 3600, 2),
                    "issueCount": len(issues),
                    "issues": issue_reports
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_time_tracking_report: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_project_roles(args: Dict[str, Any]) -> List[TextContent]:
    """Get project roles and permissions."""
    project = args.get("project")
    
    if not project:
        return [TextContent(type="text", text="Error: Missing required parameter 'project'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting project roles for: {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/project/{project}/role",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                roles = response.json()
                
                result = {
                    "project": project,
                    "roles": [
                        {
                            "name": role_name,
                            "url": role_url
                        } for role_name, role_url in roles.items()
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_project_roles: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def export_issues(args: Dict[str, Any]) -> List[TextContent]:
    """Export issues to specified format."""
    jql = args.get("jql")
    format_type = args.get("format", "json").lower()
    
    if not jql:
        return [TextContent(type="text", text="Error: Missing required parameter 'jql'")]
    
    logger.info(f"Exporting issues with JQL: {sanitize_for_log(jql)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/search?jql={jql}&maxResults=100",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                if format_type == "csv":
                    # Simple CSV format
                    csv_lines = ["Key,Summary,Status,Assignee,Priority"]
                    for issue in issues:
                        fields = issue.get("fields", {})
                        assignee = fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
                        csv_lines.append(f"{issue.get('key')},\"{fields.get('summary', '')}\",{fields.get('status', {}).get('name', '')},{assignee},{fields.get('priority', {}).get('name', '')}")
                    
                    result = "\n".join(csv_lines)
                else:
                    # JSON format
                    export_data = {
                        "exportDate": "now",
                        "jql": jql,
                        "totalIssues": len(issues),
                        "issues": [
                            {
                                "key": issue.get("key"),
                                "summary": issue.get("fields", {}).get("summary"),
                                "status": issue.get("fields", {}).get("status", {}).get("name"),
                                "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName") if issue.get("fields", {}).get("assignee") else "Unassigned",
                                "priority": issue.get("fields", {}).get("priority", {}).get("name"),
                                "created": issue.get("fields", {}).get("created")
                            } for issue in issues
                        ]
                    }
                    result = json.dumps(export_data, indent=2)
                
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in export_issues: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def create_webhook(args: Dict[str, Any]) -> List[TextContent]:
    """Create new webhook."""
    name = args.get("name")
    url = args.get("url")
    events = args.get("events", [])
    
    if not name or not url or not events:
        return [TextContent(type="text", text="Error: Missing required parameters")]
    
    logger.info(f"Creating webhook: {sanitize_for_log(name)}")
    
    webhook_data = {
        "name": name,
        "url": url,
        "events": events,
        "enabled": True
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/webhooks/1.0/webhook",
                json=webhook_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                webhook = response.json()
                result = f"✅ Created webhook: {name}\n"
                result += f"URL: {url}\n"
                result += f"Events: {', '.join(events)}\n"
                result += f"ID: {webhook.get('self', 'Unknown')}"
                
                logger.info(f"Created webhook: {name}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in create_webhook: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def create_version(args: Dict[str, Any]) -> List[TextContent]:
    """Create project version/release."""
    project = args.get("project")
    name = args.get("name")
    description = args.get("description", "")
    
    if not project or not name:
        return [TextContent(type="text", text="Error: Missing required parameters 'project' and 'name'")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Creating version {sanitize_for_log(name)} for project {sanitize_for_log(project)}")
    
    version_data = {
        "name": name,
        "description": description,
        "project": project,
        "released": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{JIRA_URL}/rest/api/3/version",
                json=version_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 201:
                version = response.json()
                result = f"✅ Created version: {name}\n"
                result += f"Project: {project}\n"
                result += f"Description: {description}\n"
                result += f"ID: {version.get('id')}"
                
                logger.info(f"Created version: {name}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in create_version: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_user_permissions(args: Dict[str, Any]) -> List[TextContent]:
    """Get user permissions for project."""
    project = args.get("project")
    username = args.get("username")
    
    if not project or not username:
        return [TextContent(type="text", text="Error: Missing required parameters")]
    
    if not validate_project_key(project):
        return [TextContent(type="text", text="Error: Invalid project key format")]
    
    logger.info(f"Getting permissions for user {sanitize_for_log(username)} in project {sanitize_for_log(project)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/mypermissions?projectKey={project}",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                permissions = response.json()
                
                result = {
                    "project": project,
                    "username": username,
                    "permissions": {
                        key: perm.get("havePermission", False) 
                        for key, perm in permissions.get("permissions", {}).items()
                    }
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_user_permissions: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_workflows(args: Dict[str, Any]) -> List[TextContent]:
    """Get available workflows."""
    logger.info("Getting workflows")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{JIRA_URL}/rest/api/3/workflow/search",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                workflows = data.get("values", [])
                
                result = {
                    "workflowCount": len(workflows),
                    "workflows": [
                        {
                            "name": wf.get("name"),
                            "description": wf.get("description"),
                            "isActive": wf.get("isActive"),
                            "isDraft": wf.get("isDraft")
                        } for wf in workflows
                    ]
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_workflows: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def release_version(args: Dict[str, Any]) -> List[TextContent]:
    """Mark version as released."""
    version_id = args.get("version_id")
    release_date = args.get("release_date")
    
    if not version_id:
        return [TextContent(type="text", text="Error: Missing required parameter 'version_id'")]
    
    logger.info(f"Releasing version: {sanitize_for_log(version_id)}")
    
    release_data = {
        "released": True,
        "releaseDate": release_date if release_date else None
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.put(
                f"{JIRA_URL}/rest/api/3/version/{version_id}",
                json=release_data,
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                version = response.json()
                result = f"✅ Released version: {version.get('name')}\n"
                result += f"Release date: {version.get('releaseDate', 'Not set')}\n"
                result += f"Project: {version.get('project', {}).get('key', 'Unknown')}"
                
                logger.info(f"Released version: {version_id}")
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in release_version: {e}", exc_info=VERBOSE_LOGGING)
            return [TextContent(type="text", text=f"Error: {str(e)}")]

async def get_burndown_data(args: Dict[str, Any]) -> List[TextContent]:
    """Get sprint burndown data."""
    sprint_id = args.get("sprint_id")
    
    if not sprint_id:
        return [TextContent(type="text", text="Error: Missing required parameter 'sprint_id'")]
    
    logger.info(f"Getting burndown data for sprint: {sanitize_for_log(sprint_id)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get sprint issues with story points
            response = await client.get(
                f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue?fields=summary,status,customfield_10016",
                auth=(JIRA_USERNAME, JIRA_API_TOKEN)
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                total_points = 0
                completed_points = 0
                
                for issue in issues:
                    fields = issue.get("fields", {})
                    story_points = fields.get("customfield_10016", 0) or 0
                    status = fields.get("status", {}).get("name", "")
                    
                    total_points += story_points
                    if status.lower() in ["done", "closed", "resolved"]:
                        completed_points += story_points
                
                result = {
                    "sprintId": sprint_id,
                    "totalStoryPoints": total_points,
                    "completedStoryPoints": completed_points,
                    "remainingStoryPoints": total_points - completed_points,
                    "completionPercentage": round((completed_points / total_points * 100) if total_points > 0 else 0, 2),
                    "issueCount": len(issues)
                }
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            else:
                return [TextContent(type="text", text=f"Error: HTTP {response.status_code} - {response.text}")]
                
        except httpx.RequestError as e:
            return [TextContent(type="text", text=f"Error: Connection failed - {str(e)}")]
        except Exception as e:
            logger.error(f"Unexpected error in get_burndown_data: {e}", exc_info=VERBOSE_LOGGING)
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
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    main()