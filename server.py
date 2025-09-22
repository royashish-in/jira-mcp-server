#!/usr/bin/env python3
"""JIRA MCP Server - FastMCP 2.0 implementation with 46 tools."""

import json
import os
import re
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

# JIRA configuration
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

# Validation
if not all([JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN]):
    raise ValueError("Missing JIRA configuration: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")

# Global HTTP session
session = requests.Session()
session.auth = (JIRA_USERNAME, JIRA_API_TOKEN)
session.timeout = 30.0

# Validation patterns
PROJECT_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')
ISSUE_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*-\d+$')

# Initialize FastMCP
mcp = FastMCP("JIRA MCP Server")

def validate_project_key(project: str) -> bool:
    return bool(PROJECT_KEY_PATTERN.match(project))

def validate_issue_key(key: str) -> bool:
    return bool(ISSUE_KEY_PATTERN.match(key))

# Core JIRA Operations
@mcp.tool
def get_user_stories(project: str = "", limit: int = 10) -> Dict[str, Any]:
    """Get user stories from JIRA"""
    if project and not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    limit = min(limit, 100)
    jql = f"project = {project} AND issuetype = Story ORDER BY created DESC" if project else "issuetype = Story ORDER BY created DESC"
    
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": jql, "maxResults": limit})
    response.raise_for_status()
    
    data = response.json()
    stories = []
    for issue in data.get("issues", []):
        desc = issue.get("fields", {}).get("description", "")
        if isinstance(desc, dict):
            desc = str(desc.get("content", ""))
        stories.append({
            "key": issue.get("key"),
            "summary": issue.get("fields", {}).get("summary"),
            "status": issue.get("fields", {}).get("status", {}).get("name"),
            "description": desc
        })
    
    return {"stories": stories}

@mcp.tool
def get_issue(key: str) -> Dict[str, Any]:
    """Get specific JIRA issue by key"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}")
    response.raise_for_status()
    
    issue = response.json()
    fields = issue.get("fields", {})
    desc = fields.get("description", "")
    if isinstance(desc, dict):
        desc = str(desc.get("content", ""))
    
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
        "reporter": fields.get("reporter", {}).get("displayName"),
        "priority": fields.get("priority", {}).get("name"),
        "issuetype": fields.get("issuetype", {}).get("name"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "description": desc
    }

@mcp.tool
def get_projects() -> Dict[str, Any]:
    """Get all accessible JIRA projects"""
    response = session.get(f"{JIRA_URL}/rest/api/3/project")
    response.raise_for_status()
    
    projects = response.json()
    project_list = []
    for project in projects:
        project_list.append({
            "key": project.get("key"),
            "name": project.get("name"),
            "projectTypeKey": project.get("projectTypeKey"),
            "lead": project.get("lead", {}).get("displayName")
        })
    
    return {"projects": project_list}

@mcp.tool
def search_issues(jql: str, limit: int = 10) -> Dict[str, Any]:
    """Search JIRA issues using JQL"""
    limit = min(limit, 100)
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": jql, "maxResults": limit})
    response.raise_for_status()
    
    data = response.json()
    issues = []
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        desc = fields.get("description", "") or ""
        if isinstance(desc, dict):
            desc = str(desc.get("content", ""))
        
        issues.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
            "priority": fields.get("priority", {}).get("name"),
            "issuetype": fields.get("issuetype", {}).get("name"),
            "created": fields.get("created"),
            "description": desc[:200] + "..." if desc and len(desc) > 200 else desc
        })
    
    return {"total": data.get("total", 0), "returned": len(issues), "issues": issues}

@mcp.tool
def get_project_stats(project: str) -> Dict[str, Any]:
    """Get project statistics including issue counts by status and type"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    # Get total issues
    total_response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": f"project = {project}", "maxResults": 0})
    total_response.raise_for_status()
    total_issues = total_response.json().get("total", 0)
    
    # Get by status
    status_counts = {}
    for status in ["To Do", "In Progress", "Done"]:
        response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": f"project = {project} AND status = '{status}'", "maxResults": 0})
        if response.status_code == 200:
            status_counts[status] = response.json().get("total", 0)
    
    # Get by type
    type_counts = {}
    for issue_type in ["Story", "Task", "Bug", "Sub-task"]:
        response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": f"project = {project} AND issuetype = '{issue_type}'", "maxResults": 0})
        if response.status_code == 200:
            type_counts[issue_type] = response.json().get("total", 0)
    
    return {
        "project": project,
        "total_issues": total_issues,
        "by_status": status_counts,
        "by_type": type_counts
    }

@mcp.tool
def get_recent_issues(days: int = 7, limit: int = 10) -> Dict[str, Any]:
    """Get recently updated issues"""
    if not 1 <= days <= 365:
        raise ValueError("Days must be between 1 and 365")
    
    limit = min(limit, 100)
    jql = f"updated >= -{days}d ORDER BY updated DESC"
    
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": jql, "maxResults": limit})
    response.raise_for_status()
    
    data = response.json()
    issues = []
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        issues.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
            "updated": fields.get("updated"),
            "issuetype": fields.get("issuetype", {}).get("name")
        })
    
    return {"days_back": days, "total_found": data.get("total"), "returned": len(issues), "issues": issues}

@mcp.tool
def get_issues_by_assignee(assignee: str, limit: int = 10) -> Dict[str, Any]:
    """Get issues assigned to a specific user"""
    limit = min(limit, 100)
    jql = f"assignee = {assignee} ORDER BY updated DESC"
    
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": jql, "maxResults": limit})
    response.raise_for_status()
    
    data = response.json()
    issues = []
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        issues.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "issuetype": fields.get("issuetype", {}).get("name"),
            "updated": fields.get("updated")
        })
    
    return {"assignee": assignee, "total_found": data.get("total"), "returned": len(issues), "issues": issues}

@mcp.tool
def create_issue(project: str, summary: str, description: str = "", issue_type: str = "Task", priority: str = "Medium", assignee: Optional[str] = None) -> Dict[str, Any]:
    """Create a new JIRA issue"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    issue_data = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type}
        }
    }
    
    if description:
        issue_data["fields"]["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
        }
    
    if priority:
        issue_data["fields"]["priority"] = {"name": priority}
    
    if assignee:
        issue_data["fields"]["assignee"] = {"name": assignee}
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=issue_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": "Issue created successfully", "key": result.get("key"), "id": result.get("id")}

@mcp.tool
def update_issue(key: str, summary: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, assignee: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing JIRA issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    update_fields = {}
    
    if summary:
        update_fields["summary"] = summary
    
    if description:
        update_fields["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
        }
    
    if priority:
        update_fields["priority"] = {"name": priority}
    
    if assignee:
        update_fields["assignee"] = None if assignee.lower() == "null" else {"name": assignee}
    
    if not update_fields:
        raise ValueError("At least one field to update is required")
    
    response = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}", json={"fields": update_fields}, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    return {"success": True, "message": f"Issue {key} updated successfully", "updated_fields": list(update_fields.keys())}

@mcp.tool
def advanced_jql_search(jql: str, fields: Optional[List[str]] = None, expand: Optional[List[str]] = None, limit: int = 10) -> Dict[str, Any]:
    """Advanced JIRA search with custom fields and expand options"""
    limit = min(limit, 100)
    params = {"jql": jql, "maxResults": limit}
    
    if fields:
        params["fields"] = ",".join(fields)
    
    if expand:
        params["expand"] = ",".join(expand)
    
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params=params)
    response.raise_for_status()
    
    data = response.json()
    return {
        "jql": jql,
        "total": data.get("total"),
        "returned": len(data.get("issues", [])),
        "fields_requested": fields or "all",
        "expand_requested": expand or "none",
        "issues": data.get("issues", [])
    }

# Workflow Management
@mcp.tool
def transition_issue(key: str, transition: str) -> Dict[str, Any]:
    """Transition JIRA issue to different status"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    # Get available transitions
    transitions_response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions")
    transitions_response.raise_for_status()
    
    available_transitions = transitions_response.json().get("transitions", [])
    transition_id = None
    
    for t in available_transitions:
        if t.get("name", "").lower() == transition.lower() or t.get("id") == transition:
            transition_id = t.get("id")
            break
    
    if not transition_id:
        available_names = [t.get("name") for t in available_transitions]
        raise ValueError(f"Transition '{transition}' not available. Available: {available_names}")
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", json={"transition": {"id": transition_id}}, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    return {"success": True, "message": f"Issue {key} transitioned to {transition}"}

@mcp.tool
def get_transitions(key: str) -> Dict[str, Any]:
    """Get available transitions for JIRA issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions")
    response.raise_for_status()
    
    data = response.json()
    transitions = []
    for transition in data.get("transitions", []):
        transitions.append({
            "id": transition.get("id"),
            "name": transition.get("name"),
            "to_status": transition.get("to", {}).get("name")
        })
    
    return {"issue": key, "available_transitions": transitions}

@mcp.tool
def add_comment(key: str, comment: str) -> Dict[str, Any]:
    """Add comment to JIRA issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    comment_data = {
        "body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
        }
    }
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/comment", json=comment_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": f"Comment added to {key}", "comment_id": result.get("id"), "created": result.get("created")}

@mcp.tool
def bulk_transition_issues(keys: List[str], transition: str) -> Dict[str, Any]:
    """Transition multiple issues at once"""
    results = []
    
    for key in keys:
        if not validate_issue_key(key):
            results.append({"key": key, "status": "error", "message": "Invalid key format"})
            continue
        
        try:
            # Get transitions
            trans_response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions")
            if trans_response.status_code != 200:
                results.append({"key": key, "status": "error", "message": "Cannot get transitions"})
                continue
            
            transitions = trans_response.json().get("transitions", [])
            transition_id = None
            
            for t in transitions:
                if t.get("name", "").lower() == transition.lower() or t.get("id") == transition:
                    transition_id = t.get("id")
                    break
            
            if not transition_id:
                results.append({"key": key, "status": "error", "message": f"Transition '{transition}' not available"})
                continue
            
            # Perform transition
            response = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/transitions", json={"transition": {"id": transition_id}}, headers={"Content-Type": "application/json"})
            
            if response.status_code == 204:
                results.append({"key": key, "status": "success", "message": f"Transitioned to {transition}"})
            else:
                results.append({"key": key, "status": "error", "message": f"HTTP {response.status_code}"})
        
        except Exception as e:
            results.append({"key": key, "status": "error", "message": str(e)})
    
    success_count = len([r for r in results if r["status"] == "success"])
    return {"total_issues": len(keys), "successful": success_count, "failed": len(keys) - success_count, "results": results}

@mcp.tool
def assign_issue(key: str, assignee: str) -> Dict[str, Any]:
    """Assign issue to user"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    if assignee.lower() == "null" or assignee == "":
        assignee_data = {"accountId": None}
    else:
        # Try to find user by name first
        user_response = session.get(f"{JIRA_URL}/rest/api/3/user/search", params={"query": assignee})
        if user_response.status_code == 200:
            users = user_response.json()
            if users:
                assignee_data = {"accountId": users[0].get("accountId")}
            else:
                raise ValueError(f"User '{assignee}' not found")
        else:
            # Fallback to name-based assignment
            assignee_data = {"name": assignee}
    
    response = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}/assignee", json=assignee_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    action = "unassigned" if assignee.lower() in ["null", ""] else f"assigned to {assignee}"
    return {"success": True, "message": f"Issue {key} {action}"}

@mcp.tool
def add_worklog(key: str, time_spent: str, comment: str = "") -> Dict[str, Any]:
    """Add time log to issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    worklog_data = {"timeSpent": time_spent}
    
    if comment:
        worklog_data["comment"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
        }
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/worklog", json=worklog_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": f"Worklog added to {key}", "time_spent": time_spent, "worklog_id": result.get("id")}

# File & Attachment Management
@mcp.tool
def list_attachments(key: str) -> Dict[str, Any]:
    """List attachments for JIRA issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "attachment"})
    response.raise_for_status()
    
    issue = response.json()
    attachments = issue.get("fields", {}).get("attachment", [])
    
    attachment_list = []
    for attachment in attachments:
        attachment_list.append({
            "id": attachment.get("id"),
            "filename": attachment.get("filename"),
            "size": attachment.get("size"),
            "mimeType": attachment.get("mimeType"),
            "created": attachment.get("created"),
            "author": attachment.get("author", {}).get("displayName"),
            "content": attachment.get("content")
        })
    
    return {"issue": key, "attachment_count": len(attachment_list), "attachments": attachment_list}

# Project & User Management
@mcp.tool
def get_issue_types(project: str) -> Dict[str, Any]:
    """Get available issue types for project"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/project/{project}")
    response.raise_for_status()
    
    project_data = response.json()
    types_list = []
    for issue_type in project_data.get("issueTypes", []):
        types_list.append({
            "id": issue_type.get("id"),
            "name": issue_type.get("name"),
            "description": issue_type.get("description", ""),
            "subtask": issue_type.get("subtask", False)
        })
    
    return {"project": project, "issue_types": types_list}

@mcp.tool
def get_project_components(project: str) -> Dict[str, Any]:
    """Get project components"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/project/{project}/components")
    response.raise_for_status()
    
    components = response.json()
    component_list = []
    for component in components:
        component_list.append({
            "id": component.get("id"),
            "name": component.get("name"),
            "description": component.get("description", ""),
            "lead": component.get("lead", {}).get("displayName") if component.get("lead") else "No lead"
        })
    
    return {"project": project, "component_count": len(component_list), "components": component_list}

@mcp.tool
def get_project_versions(project: str) -> Dict[str, Any]:
    """Get project versions/releases"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/project/{project}/versions")
    response.raise_for_status()
    
    versions = response.json()
    version_list = []
    for version in versions:
        version_list.append({
            "id": version.get("id"),
            "name": version.get("name"),
            "description": version.get("description", ""),
            "released": version.get("released", False),
            "releaseDate": version.get("releaseDate", "Not set"),
            "archived": version.get("archived", False)
        })
    
    return {"project": project, "version_count": len(version_list), "versions": version_list}

@mcp.tool
def get_custom_fields() -> Dict[str, Any]:
    """Get available custom fields"""
    response = session.get(f"{JIRA_URL}/rest/api/3/field")
    response.raise_for_status()
    
    fields = response.json()
    custom_fields = []
    
    for field in fields:
        if field.get("custom", False):
            custom_fields.append({
                "id": field.get("id"),
                "name": field.get("name"),
                "description": field.get("description", ""),
                "type": field.get("schema", {}).get("type", "Unknown")
            })
    
    return {"custom_field_count": len(custom_fields), "custom_fields": custom_fields}

@mcp.tool
def get_users(project: str) -> Dict[str, Any]:
    """Get assignable users for project"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/user/assignable/search", params={"project": project})
    response.raise_for_status()
    
    users = response.json()
    user_list = []
    
    for user in users:
        user_list.append({
            "accountId": user.get("accountId"),
            "displayName": user.get("displayName"),
            "emailAddress": user.get("emailAddress", "Not available"),
            "active": user.get("active", True)
        })
    
    return {"project": project, "user_count": len(user_list), "users": user_list}

# Agile & Sprint Management
@mcp.tool
def get_boards() -> Dict[str, Any]:
    """Get available agile boards"""
    response = session.get(f"{JIRA_URL}/rest/agile/1.0/board")
    response.raise_for_status()
    
    data = response.json()
    boards = data.get("values", [])
    
    board_list = []
    for board in boards:
        board_list.append({
            "id": board.get("id"),
            "name": board.get("name"),
            "type": board.get("type"),
            "location": board.get("location", {}).get("name", "Unknown")
        })
    
    return {"total": data.get("total", len(board_list)), "boards": board_list}

@mcp.tool
def get_sprints(board_id: str) -> Dict[str, Any]:
    """Get sprints for agile board"""
    try:
        response = session.get(f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint")
        response.raise_for_status()
        
        data = response.json()
        sprints = data.get("values", [])
        
        sprint_list = []
        for sprint in sprints:
            sprint_list.append({
                "id": sprint.get("id"),
                "name": sprint.get("name"),
                "state": sprint.get("state"),
                "startDate": sprint.get("startDate", "Not set"),
                "endDate": sprint.get("endDate", "Not set"),
                "goal": sprint.get("goal", "")
            })
        
        return {"board_id": board_id, "sprint_count": len(sprint_list), "sprints": sprint_list}
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"board_id": board_id, "sprint_count": 0, "sprints": [], "error": f"Board {board_id} not found or not accessible"}
        else:
            raise ValueError(f"Failed to get sprints for board {board_id}: {e.response.status_code}")

# Issue Relationships & Hierarchy
@mcp.tool
def get_issue_links(key: str) -> Dict[str, Any]:
    """Get all linked issues"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "issuelinks"})
    response.raise_for_status()
    
    issue = response.json()
    issue_links = issue.get("fields", {}).get("issuelinks", [])
    
    links = []
    for link in issue_links:
        link_type = link.get("type", {}).get("name", "Unknown")
        
        if "outwardIssue" in link:
            linked_issue = link["outwardIssue"]
            direction = "outward"
        elif "inwardIssue" in link:
            linked_issue = link["inwardIssue"]
            direction = "inward"
        else:
            continue
        
        links.append({
            "link_type": link_type,
            "direction": direction,
            "linked_issue_key": linked_issue.get("key"),
            "linked_issue_summary": linked_issue.get("fields", {}).get("summary", "No summary"),
            "linked_issue_status": linked_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        })
    
    return {"issue": key, "link_count": len(links), "links": links}

@mcp.tool
def get_subtasks(key: str) -> Dict[str, Any]:
    """Get subtasks of an issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}", params={"fields": "subtasks"})
    response.raise_for_status()
    
    issue = response.json()
    subtasks = issue.get("fields", {}).get("subtasks", [])
    
    subtask_list = []
    for subtask in subtasks:
        subtask_list.append({
            "key": subtask.get("key"),
            "summary": subtask.get("fields", {}).get("summary", "No summary"),
            "status": subtask.get("fields", {}).get("status", {}).get("name", "Unknown"),
            "assignee": subtask.get("fields", {}).get("assignee", {}).get("displayName", "Unassigned") if subtask.get("fields", {}).get("assignee") else "Unassigned"
        })
    
    return {"parent_issue": key, "subtask_count": len(subtask_list), "subtasks": subtask_list}

@mcp.tool
def create_subtask(parent_key: str, summary: str, description: str = "") -> Dict[str, Any]:
    """Create subtask under parent issue"""
    if not validate_issue_key(parent_key):
        raise ValueError("Invalid parent issue key format")
    
    # Get parent issue to determine project
    parent_response = session.get(f"{JIRA_URL}/rest/api/3/issue/{parent_key}", params={"fields": "project"})
    parent_response.raise_for_status()
    
    parent_data = parent_response.json()
    project_key = parent_data.get("fields", {}).get("project", {}).get("key")
    
    subtask_data = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": summary,
            "issuetype": {"name": "Sub-task"}
        }
    }
    
    if description:
        subtask_data["fields"]["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
        }
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=subtask_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": "Subtask created successfully", "subtask_key": result.get("key"), "parent_key": parent_key}

# Batch Operations
@mcp.tool
def bulk_update_issues(keys: List[str], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update multiple JIRA issues at once"""
    results = []
    
    for key in keys:
        if not validate_issue_key(key):
            results.append({"key": key, "status": "error", "message": "Invalid key format"})
            continue
        
        try:
            update_fields = {}
            
            if "priority" in updates:
                update_fields["priority"] = {"name": updates["priority"]}
            
            if "assignee" in updates:
                update_fields["assignee"] = None if updates["assignee"].lower() == "null" else {"name": updates["assignee"]}
            
            if "summary" in updates:
                update_fields["summary"] = updates["summary"]
            
            if not update_fields:
                results.append({"key": key, "status": "error", "message": "No valid update fields"})
                continue
            
            response = session.put(f"{JIRA_URL}/rest/api/3/issue/{key}", json={"fields": update_fields}, headers={"Content-Type": "application/json"})
            
            if response.status_code == 204:
                results.append({"key": key, "status": "success", "message": "Updated successfully"})
            else:
                results.append({"key": key, "status": "error", "message": f"HTTP {response.status_code}"})
        
        except Exception as e:
            results.append({"key": key, "status": "error", "message": str(e)})
    
    success_count = len([r for r in results if r["status"] == "success"])
    return {"total_issues": len(keys), "successful": success_count, "failed": len(keys) - success_count, "results": results}

@mcp.tool
def clone_issue(key: str, summary: str) -> Dict[str, Any]:
    """Clone/duplicate issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    # Get source issue
    source_response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}")
    source_response.raise_for_status()
    
    source_issue = source_response.json()
    source_fields = source_issue.get("fields", {})
    
    # Build clone data
    clone_data = {
        "fields": {
            "project": source_fields.get("project"),
            "summary": summary,
            "issuetype": source_fields.get("issuetype"),
            "description": source_fields.get("description")
        }
    }
    
    # Copy priority if exists
    if source_fields.get("priority"):
        clone_data["fields"]["priority"] = source_fields["priority"]
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=clone_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": "Issue cloned successfully", "source_key": key, "cloned_key": result.get("key"), "cloned_id": result.get("id")}

# Agile & Sprint Management (continued)
@mcp.tool
def get_sprint_issues(sprint_id: str) -> Dict[str, Any]:
    """Get issues in specific sprint"""
    try:
        response = session.get(f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue")
        response.raise_for_status()
        
        data = response.json()
        issues = []
        for issue in data.get("issues", []):
            fields = issue.get("fields", {})
            issues.append({
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                "storyPoints": fields.get("customfield_10016"),  # Common story points field
                "issuetype": fields.get("issuetype", {}).get("name")
            })
        
        return {"sprint_id": sprint_id, "issue_count": len(issues), "issues": issues}
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"sprint_id": sprint_id, "issue_count": 0, "issues": [], "error": f"Sprint {sprint_id} not found or not accessible"}
        else:
            raise ValueError(f"Failed to get issues for sprint {sprint_id}: {e.response.status_code}")

@mcp.tool
def add_to_sprint(sprint_id: str, keys: List[str]) -> Dict[str, Any]:
    """Add issues to sprint"""
    issue_data = {"issues": keys}
    
    response = session.post(f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue", json=issue_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    return {"success": True, "message": f"Added {len(keys)} issues to sprint {sprint_id}", "sprint_id": sprint_id, "added_issues": keys}

@mcp.tool
def get_burndown_data(sprint_id: str) -> Dict[str, Any]:
    """Get sprint burndown data"""
    # Get sprint info first
    sprint_response = session.get(f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}")
    sprint_response.raise_for_status()
    sprint_data = sprint_response.json()
    
    # Get issues in sprint with story points
    issues_response = session.get(f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue", params={"fields": "summary,status,customfield_10016"})
    issues_response.raise_for_status()
    issues_data = issues_response.json()
    
    total_points = 0
    completed_points = 0
    in_progress_points = 0
    todo_points = 0
    
    for issue in issues_data.get("issues", []):
        points = issue.get("fields", {}).get("customfield_10016", 0) or 0
        status = issue.get("fields", {}).get("status", {}).get("name", "")
        
        total_points += points
        if status.lower() in ["done", "closed", "resolved"]:
            completed_points += points
        elif status.lower() in ["in progress", "in review"]:
            in_progress_points += points
        else:
            todo_points += points
    
    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint_data.get("name"),
        "sprint_state": sprint_data.get("state"),
        "total_story_points": total_points,
        "completed_points": completed_points,
        "in_progress_points": in_progress_points,
        "todo_points": todo_points,
        "completion_percentage": round((completed_points / total_points * 100) if total_points > 0 else 0, 2)
    }

# Issue Relationships & Hierarchy (continued)
@mcp.tool
def link_issues(inward_key: str, outward_key: str, link_type: str) -> Dict[str, Any]:
    """Create link between issues"""
    if not validate_issue_key(inward_key) or not validate_issue_key(outward_key):
        raise ValueError("Invalid issue key format")
    
    link_data = {
        "type": {"name": link_type},
        "inwardIssue": {"key": inward_key},
        "outwardIssue": {"key": outward_key}
    }
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issueLink", json=link_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    return {"success": True, "message": f"Linked {inward_key} to {outward_key} with type {link_type}"}

# File & Attachment Management (continued)
@mcp.tool
def upload_attachment(key: str, file_path: str) -> Dict[str, Any]:
    """Upload file attachment to JIRA issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    import os
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/attachments", files=files, headers={"X-Atlassian-Token": "no-check"})
    
    response.raise_for_status()
    result = response.json()
    
    return {"success": True, "message": f"File uploaded to {key}", "attachment_id": result[0].get("id"), "filename": result[0].get("filename")}

@mcp.tool
def download_attachment(attachment_url: str, save_path: str) -> Dict[str, Any]:
    """Download attachment from JIRA issue"""
    response = session.get(attachment_url, stream=True)
    response.raise_for_status()
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return {"success": True, "message": f"Attachment downloaded to {save_path}", "file_size": len(response.content)}

# Webhooks & Notifications
@mcp.tool
def list_webhooks() -> Dict[str, Any]:
    """List configured webhooks"""
    response = session.get(f"{JIRA_URL}/rest/webhooks/1.0/webhook")
    response.raise_for_status()
    
    webhooks = response.json()
    webhook_list = []
    for webhook in webhooks:
        webhook_list.append({
            "id": webhook.get("id"),
            "name": webhook.get("name"),
            "url": webhook.get("url"),
            "events": webhook.get("events", []),
            "enabled": webhook.get("enabled", True)
        })
    
    return {"webhook_count": len(webhook_list), "webhooks": webhook_list}

@mcp.tool
def create_webhook(name: str, url: str, events: List[str]) -> Dict[str, Any]:
    """Create new webhook"""
    webhook_data = {
        "name": name,
        "url": url,
        "events": events,
        "enabled": True
    }
    
    response = session.post(f"{JIRA_URL}/rest/webhooks/1.0/webhook", json=webhook_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": "Webhook created successfully", "webhook_id": result.get("id"), "name": name}

@mcp.tool
def add_watcher(key: str, username: str) -> Dict[str, Any]:
    """Add watcher to issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.post(f"{JIRA_URL}/rest/api/3/issue/{key}/watchers", json=username, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    return {"success": True, "message": f"Added {username} as watcher to {key}"}

@mcp.tool
def get_watchers(key: str) -> Dict[str, Any]:
    """Get watchers of issue"""
    if not validate_issue_key(key):
        raise ValueError("Invalid issue key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/issue/{key}/watchers")
    response.raise_for_status()
    
    data = response.json()
    watchers = []
    for watcher in data.get("watchers", []):
        watchers.append({
            "accountId": watcher.get("accountId"),
            "displayName": watcher.get("displayName"),
            "emailAddress": watcher.get("emailAddress", "Not available")
        })
    
    return {"issue": key, "watcher_count": len(watchers), "watchers": watchers}

# Reporting & Analytics
@mcp.tool
def get_time_tracking_report(project: str) -> Dict[str, Any]:
    """Get time tracking report for project"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    # Get issues with time tracking data
    jql = f"project = {project} AND timespent > 0"
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": jql, "fields": "summary,timespent,timeoriginalestimate,assignee", "maxResults": 100})
    response.raise_for_status()
    
    data = response.json()
    total_logged = 0
    total_estimated = 0
    issues_with_time = []
    
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        time_spent = fields.get("timespent", 0) or 0
        time_estimated = fields.get("timeoriginalestimate", 0) or 0
        
        total_logged += time_spent
        total_estimated += time_estimated
        
        issues_with_time.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "time_spent_seconds": time_spent,
            "time_spent_hours": round(time_spent / 3600, 2),
            "time_estimated_seconds": time_estimated,
            "time_estimated_hours": round(time_estimated / 3600, 2),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
        })
    
    return {
        "project": project,
        "total_logged_hours": round(total_logged / 3600, 2),
        "total_estimated_hours": round(total_estimated / 3600, 2),
        "issues_with_time_tracking": len(issues_with_time),
        "issues": issues_with_time
    }

@mcp.tool
def get_project_roles(project: str) -> Dict[str, Any]:
    """Get project roles and permissions"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/project/{project}/role")
    response.raise_for_status()
    
    roles_data = response.json()
    roles = []
    
    for role_url in roles_data.values():
        role_response = session.get(role_url)
        if role_response.status_code == 200:
            role_data = role_response.json()
            actors = []
            for actor in role_data.get("actors", []):
                actors.append({
                    "type": actor.get("type"),
                    "name": actor.get("name"),
                    "displayName": actor.get("displayName")
                })
            
            roles.append({
                "id": role_data.get("id"),
                "name": role_data.get("name"),
                "description": role_data.get("description", ""),
                "actors": actors
            })
    
    return {"project": project, "role_count": len(roles), "roles": roles}

@mcp.tool
def export_issues(jql: str, format: str) -> Dict[str, Any]:
    """Export issues to specified format"""
    if format.lower() not in ["json", "csv"]:
        raise ValueError("Format must be 'json' or 'csv'")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": jql, "maxResults": 1000})
    response.raise_for_status()
    
    data = response.json()
    issues = []
    
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        issue_data = {
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
            "reporter": fields.get("reporter", {}).get("displayName"),
            "priority": fields.get("priority", {}).get("name"),
            "issuetype": fields.get("issuetype", {}).get("name"),
            "created": fields.get("created"),
            "updated": fields.get("updated")
        }
        issues.append(issue_data)
    
    if format.lower() == "json":
        return {"format": "json", "total_issues": len(issues), "issues": issues}
    else:  # CSV
        import csv
        import io
        output = io.StringIO()
        if issues:
            writer = csv.DictWriter(output, fieldnames=issues[0].keys())
            writer.writeheader()
            writer.writerows(issues)
        
        return {"format": "csv", "total_issues": len(issues), "csv_data": output.getvalue()}

# Advanced Admin & Edge Cases
@mcp.tool
def create_version(project: str, name: str, description: str = "") -> Dict[str, Any]:
    """Create project version/release"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    version_data = {
        "name": name,
        "description": description,
        "project": project,
        "released": False
    }
    
    response = session.post(f"{JIRA_URL}/rest/api/3/version", json=version_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    result = response.json()
    return {"success": True, "message": f"Version {name} created for project {project}", "version_id": result.get("id"), "name": name}

@mcp.tool
def release_version(version_id: str, release_date: Optional[str] = None) -> Dict[str, Any]:
    """Mark version as released"""
    from datetime import datetime
    
    version_data = {
        "released": True,
        "releaseDate": release_date or datetime.now().strftime("%Y-%m-%d")
    }
    
    response = session.put(f"{JIRA_URL}/rest/api/3/version/{version_id}", json=version_data, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    return {"success": True, "message": f"Version {version_id} marked as released", "release_date": version_data["releaseDate"]}

@mcp.tool
def get_user_permissions(project: str, username: str) -> Dict[str, Any]:
    """Get user permissions for project"""
    if not validate_project_key(project):
        raise ValueError("Invalid project key format")
    
    response = session.get(f"{JIRA_URL}/rest/api/3/mypermissions", params={"projectKey": project, "username": username})
    response.raise_for_status()
    
    data = response.json()
    permissions = []
    
    for perm_key, perm_data in data.get("permissions", {}).items():
        permissions.append({
            "key": perm_key,
            "name": perm_data.get("name"),
            "type": perm_data.get("type"),
            "description": perm_data.get("description", ""),
            "havePermission": perm_data.get("havePermission", False)
        })
    
    return {"project": project, "username": username, "permission_count": len(permissions), "permissions": permissions}

@mcp.tool
def get_workflows() -> Dict[str, Any]:
    """Get available workflows"""
    response = session.get(f"{JIRA_URL}/rest/api/3/workflow")
    response.raise_for_status()
    
    workflows = response.json()
    workflow_list = []
    
    for workflow in workflows:
        workflow_list.append({
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "description": workflow.get("description", ""),
            "isActive": workflow.get("isActive", False),
            "isDraft": workflow.get("isDraft", False)
        })
    
    return {"workflow_count": len(workflow_list), "workflows": workflow_list}

@mcp.tool
def get_jira_statistics() -> Dict[str, Any]:
    """Get comprehensive JIRA instance statistics"""
    stats = {"instance_url": JIRA_URL, "collected_at": ""}
    
    from datetime import datetime
    stats["collected_at"] = datetime.now().isoformat()
    
    try:
        # Get total projects
        projects_response = session.get(f"{JIRA_URL}/rest/api/3/project")
        if projects_response.status_code == 200:
            projects = projects_response.json()
            stats["total_projects"] = len(projects)
        else:
            stats["total_projects"] = "Error: Unable to fetch"
        
        # Get total issues across all projects
        issues_response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": "order by created DESC", "maxResults": 0})
        if issues_response.status_code == 200:
            issues_data = issues_response.json()
            stats["total_issues"] = issues_data.get("total", 0)
        else:
            stats["total_issues"] = "Error: Unable to fetch"
        
        # Get total users (assignable users across all projects)
        users_response = session.get(f"{JIRA_URL}/rest/api/3/users/search", params={"maxResults": 1000})
        if users_response.status_code == 200:
            users = users_response.json()
            stats["total_users"] = len(users)
        else:
            stats["total_users"] = "Error: Unable to fetch"
        
        # Get total boards
        boards_response = session.get(f"{JIRA_URL}/rest/agile/1.0/board")
        if boards_response.status_code == 200:
            boards_data = boards_response.json()
            stats["total_boards"] = boards_data.get("total", len(boards_data.get("values", [])))
        else:
            stats["total_boards"] = "Error: Unable to fetch"
        
        # Get total custom fields
        fields_response = session.get(f"{JIRA_URL}/rest/api/3/field")
        if fields_response.status_code == 200:
            fields = fields_response.json()
            custom_fields = [f for f in fields if f.get("custom", False)]
            stats["total_custom_fields"] = len(custom_fields)
            stats["total_system_fields"] = len(fields) - len(custom_fields)
        else:
            stats["total_custom_fields"] = "Error: Unable to fetch"
            stats["total_system_fields"] = "Error: Unable to fetch"
        
        # Get total workflows
        workflows_response = session.get(f"{JIRA_URL}/rest/api/3/workflow")
        if workflows_response.status_code == 200:
            workflows = workflows_response.json()
            stats["total_workflows"] = len(workflows)
        else:
            stats["total_workflows"] = "Error: Unable to fetch"
        
        # Get issue type statistics
        issue_types = {}
        for issue_type in ["Story", "Task", "Bug", "Sub-task", "Epic"]:
            type_response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": f"issuetype = '{issue_type}'", "maxResults": 0})
            if type_response.status_code == 200:
                type_data = type_response.json()
                issue_types[issue_type.lower()] = type_data.get("total", 0)
            else:
                issue_types[issue_type.lower()] = "Error"
        
        stats["issues_by_type"] = issue_types
        
        # Get status statistics
        status_counts = {}
        for status in ["To Do", "In Progress", "Done", "Open", "Closed"]:
            status_response = session.get(f"{JIRA_URL}/rest/api/3/search", params={"jql": f"status = '{status}'", "maxResults": 0})
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_counts[status.lower().replace(" ", "_")] = status_data.get("total", 0)
            else:
                status_counts[status.lower().replace(" ", "_")] = "Error"
        
        stats["issues_by_status"] = status_counts
        
        # Calculate summary metrics
        if isinstance(stats["total_issues"], int) and isinstance(stats["total_projects"], int):
            stats["avg_issues_per_project"] = round(stats["total_issues"] / stats["total_projects"], 2) if stats["total_projects"] > 0 else 0
        
        return stats
    
    except Exception as e:
        return {"error": f"Failed to collect JIRA statistics: {str(e)}", "instance_url": JIRA_URL}

if __name__ == "__main__":
    mcp.run()